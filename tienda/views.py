from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Product, Category, Cart, CartItem, Image, Order, OrderItem, OrderMessage, ShippingAddress, VerificationCode
from . import tasks
from .vars import (
    PAGE_SIZE,
    VAT_RATE,
    SHIPPING_COUNTRY,
    ALMERIA_POSTAL_CODE_PREFIX,
    ALMERIA_MUNICIPALITIES_DISPLAY
)
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from decimal import Decimal, ROUND_HALF_UP
import stripe
from django.db import models, transaction
from django.core.cache import cache
import re
import unicodedata
import json
import random, string
import logging
# Create your views here.


logger = logging.getLogger("tienda")
audit_logger = logging.getLogger("tienda.audit")


def _normalize_location_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", (value or ""))
    without_accents = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    without_symbols = re.sub(r"[^a-zA-Z0-9\s-]", "", without_accents)
    collapsed = " ".join(without_symbols.replace("-", " ").lower().split())
    return collapsed


ALMERIA_MUNICIPALITIES = {
    _normalize_location_text(municipality)
    for municipality in ALMERIA_MUNICIPALITIES_DISPLAY
}
ALMERIA_MUNICIPALITIES.update(
    {
        municipality.removeprefix("la ")
        for municipality in ALMERIA_MUNICIPALITIES
        if municipality.startswith("la ")
    }
)
ALMERIA_MUNICIPALITIES.update(
    {
        municipality.removeprefix("los ")
        for municipality in ALMERIA_MUNICIPALITIES
        if municipality.startswith("los ")
    }
)


def _is_almeria_postal_code(postal_code: str) -> bool:
    """Valida que el código postal pertenezca a la provincia de Almería (04xxx)."""
    normalized = (postal_code or "").strip()
    return len(normalized) == 5 and normalized.isdigit() and normalized.startswith(ALMERIA_POSTAL_CODE_PREFIX)


def _is_almeria_city(city: str) -> bool:
    """Valida que el municipio/pueblo pertenezca a la provincia de Almería."""
    return _normalize_location_text(city) in ALMERIA_MUNICIPALITIES


def _address_form_context(direccion=None):
    return {
        "direccion": direccion,
        "almeria_municipalities": ALMERIA_MUNICIPALITIES_DISPLAY,
    }


def _get_client_ip(request: HttpRequest) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_price_with_vat_decimal(price) -> Decimal:
    """Retorna un precio con IVA aplicado y redondeado a 2 decimales."""
    return (Decimal(str(price)) * (Decimal("1") + Decimal(str(VAT_RATE)))).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

def home(request: HttpRequest):
    """Página de inicio del sitio"""
    categorias = Category.objects.all()
    # Mostrar productos destacados (últimos 8)
    featured_products = Product.objects.all().order_by('-id')[:8]
    # Contar productos y vendedores
    total_products = Product.objects.count()
    total_sellers = User.objects.filter(created_products__isnull=False).distinct().count()
    return render(request, "tienda/home.html", {
        "featured_products": featured_products,
        "categories": categorias,
        "total_products": total_products,
        "total_sellers": total_sellers
    })


def index(request: HttpRequest):
    """Página de productos (lista paginada)"""
    page = 1
    if "page" in request.GET:
        page = int(request.GET["page"])

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE

    products = Product.objects.all()[start:end]
    categorias = Category.objects.all()
    return render(request, "tienda/index.html", {"products": products, "categories": categorias})


def login(request: HttpRequest):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        remember = request.POST.get("remember")
        client_ip = _get_client_ip(request)
        
        # Buscar usuario por email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            audit_logger.warning(
                "LOGIN_FAILED email=%s reason=user_not_found ip=%s",
                email,
                client_ip,
            )
            messages.error(request, "Correo electrónico o contraseña incorrectos.")
            return render(request, "tienda/login.html")
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        user = User.objects.get(username=user.username)
        if user.registration_status == "CR":
            audit_logger.info(
                "LOGIN_FAILED email=%s reason=not_verified", email
            )
            messages.error(request, "No se puede iniciar sesión porque no has verificado tu cuenta, comprueba tu email. Si eliminaste el email pero querias verificarte, contacta con el soporte tecnico")
            return render(request, "tienda/login.html")
        
        if user is not None:
            auth_login(request, user)
            
            # Configurar duración de sesión
            if not remember:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)  # 14 días en segundos

            audit_logger.info(
                "LOGIN_SUCCESS user_id=%s email=%s ip=%s remember=%s",
                user.id,
                user.email,
                client_ip,
                bool(remember),
            )
            tasks.enviar_correo_bienvenida.delay(user.email, "{} {}".format(user.first_name, user.last_name))
            # result = send_email(user.email, "Inicio de sesión correcto", login_message.format(name = "{} {}".format(user.first_name, user.last_name)))
            messages.success(request, f"¡Bienvenido {user.first_name or user.username}!")
            return redirect("index")
        else:
            audit_logger.warning(
                "LOGIN_FAILED email=%s reason=invalid_credentials ip=%s",
                email,
                client_ip,
            )
            messages.error(request, "Correo electrónico o contraseña incorrectos.")
            return render(request, "tienda/login.html")
    
    return render(request, "tienda/login.html")


def register(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        client_ip = _get_client_ip(request)
        
        # Validaciones
        if password != password_confirm:
            audit_logger.warning("REGISTER_FAILED email=%s reason=password_mismatch ip=%s", email, client_ip)
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "tienda/register.html")
        
        if len(password) < 8:
            audit_logger.warning("REGISTER_FAILED email=%s reason=password_too_short ip=%s", email, client_ip)
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            return render(request, "tienda/register.html")
        
        if User.objects.filter(email=email).exists():
            audit_logger.warning("REGISTER_FAILED email=%s reason=email_exists ip=%s", email, client_ip)
            messages.error(request, "Ya existe un usuario con este correo electrónico.")
            return render(request, "tienda/register.html")
        
        # Crear username a partir del email
        username = email.split("@")[0]
        
        # Si el username ya existe, agregar un número
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name
        )

        audit_logger.info(
            "REGISTER_SUCCESS user_id=%s username=%s email=%s ip=%s",
            user.id,
            user.username,
            user.email,
            client_ip,
        )
        

        tasks.enviar_correo_confirmacion.delay(user.id)
        messages.success(request, f"¡Cuenta creada exitosamente! Por favor, verifica tu correo entrando al Link enviado.")
        return redirect("index")
    
    return render(request, "tienda/register.html")


def logout(request: HttpRequest):
    user_id = request.user.id if request.user.is_authenticated else None
    email = request.user.email if request.user.is_authenticated else None
    client_ip = _get_client_ip(request)
    auth_logout(request)
    audit_logger.info("LOGOUT user_id=%s email=%s ip=%s", user_id, email, client_ip)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect("index")


def producto(request: HttpRequest, id: int):
    """Vista de detalle del producto con cacheo en Redis (5 minutos)"""
    cache_key = f'product_{id}'
    
    # Intentar obtener el producto del caché
    product = cache.get(cache_key)
    
    if product is None:
        # No está en caché, obtener de la base de datos
        product = Product.objects.select_related('category', 'primary_image', 'creator').prefetch_related('secondary_images').get(id=id)
        
        # Cachear el producto por 5 minutos (300 segundos)
        cache.set(cache_key, product, 300)
    
    return render(request, "tienda/producto.html", {"product": product})

def categoria(request: HttpRequest, id: int):
    page = 1
    if "page" in request.GET:
        page = int(request.GET["page"])
    
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    category = Category.objects.get(id=id)
    categories = Category.objects.all()
    products = Product.objects.filter(category=category)[start:end]
    return render(request, "tienda/index.html", {"products": products, "categories": categories})


# Funciones auxiliares para el carrito
def get_or_create_cart(request):
    """Obtiene o crea un carrito para el usuario actual o sesión"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def _get_selected_shipping_address(request: HttpRequest):
    """Obtiene la dirección seleccionada desde JSON o form-data y valida pertenencia al usuario."""
    shipping_address_id = request.POST.get("shipping_address_id")

    if not shipping_address_id:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            shipping_address_id = payload.get("shipping_address_id")
        except (json.JSONDecodeError, UnicodeDecodeError):
            shipping_address_id = None

    if not shipping_address_id:
        return None

    try:
        shipping_address_id = int(shipping_address_id)
    except (TypeError, ValueError):
        return None

    return ShippingAddress.objects.filter(id=shipping_address_id, user=request.user).first()


def create_order_from_cart(request, payment_method, payment_reference="", shipping_address=None):
    """Crea un pedido a partir del carrito actual y lo asigna a vendedores."""
    cart = get_or_create_cart(request)
    cart_items = list(cart.items.select_related("product", "product__creator"))

    if not cart_items:
        return None

    order_total = Decimal("0.00")
    items_with_totals = []

    for item in cart_items:
        product = item.product
        unit_price_with_vat = get_price_with_vat_decimal(product.price)
        line_total_with_vat = (unit_price_with_vat * item.quantity).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        order_total += line_total_with_vat
        items_with_totals.append((item, unit_price_with_vat, line_total_with_vat))

    with transaction.atomic():
        order = Order.objects.create(
            buyer=request.user if request.user.is_authenticated else None,
            shipping_address=shipping_address,
            session_key=None if request.user.is_authenticated else request.session.session_key,
            total=float(order_total),
            status=Order.STATUS_PAID,
            payment_method=payment_method,
            payment_reference=payment_reference or "",
        )

        for item, unit_price_with_vat, line_total_with_vat in items_with_totals:
            product = item.product
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                seller=product.creator,
                quantity=item.quantity,
                unit_price=float(unit_price_with_vat),
                total_price=float(line_total_with_vat),
            )

        cart.items.all().delete()

    return order


def add_to_cart(request: HttpRequest, product_id: int):
    """Agrega un producto al carrito"""
    try:
        product = Product.objects.get(id=product_id)
        cart = get_or_create_cart(request)
        
        # Obtener cantidad del POST o por defecto 1
        quantity = int(request.POST.get('quantity', 1))
        
        # Buscar si ya existe el producto en el carrito
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Si ya existe, incrementar la cantidad
            cart_item.quantity += quantity
            cart_item.save()
            messages.success(request, f"Se actualizó la cantidad de {product.name} en el carrito.")
        else:
            messages.success(request, f"{product.name} se agregó al carrito.")
        
        # Si es una petición AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': cart.get_items_count(),
                'message': str(messages.get_messages(request))
            })
        
        return redirect('view_cart')
    
    except Product.DoesNotExist:
        messages.error(request, "Producto no encontrado.")
        return redirect('index')


def view_cart(request: HttpRequest):
    """Muestra el contenido del carrito"""
    cart = get_or_create_cart(request)
    return render(request, "tienda/cart.html", {
        "cart": cart,
        "cart_items": cart.items.all()
    })


def update_cart_item(request: HttpRequest, item_id: int):
    """Actualiza la cantidad de un item del carrito"""
    try:
        cart = get_or_create_cart(request)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Cantidad actualizada.")
        else:
            cart_item.delete()
            messages.success(request, "Producto eliminado del carrito.")
        
        return redirect('view_cart')
    
    except CartItem.DoesNotExist:
        messages.error(request, "Producto no encontrado en el carrito.")
        return redirect('view_cart')


def remove_from_cart(request: HttpRequest, item_id: int):
    """Elimina un producto del carrito"""
    try:
        cart = get_or_create_cart(request)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f"{product_name} eliminado del carrito.")
    
    except CartItem.DoesNotExist:
        messages.error(request, "Producto no encontrado en el carrito.")
    
    return redirect('view_cart')


def clear_cart(request: HttpRequest):
    """Vacía todo el carrito"""
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    messages.success(request, "Carrito vaciado.")
    return redirect('view_cart')


@login_required
def mis_productos(request: HttpRequest):
    """Muestra los productos creados por el usuario autenticado"""
    productos = Product.objects.filter(creator=request.user).select_related('category', 'primary_image')
    
    return render(request, "tienda/mis_productos.html", {
        "productos": productos,
        "total_productos": productos.count()
    })


@login_required
def pedidos_vendedor(request: HttpRequest):
    """Muestra los pedidos asignados al vendedor autenticado"""
    pedidos = OrderItem.objects.filter(seller=request.user).select_related(
        'order', 'product', 'order__buyer', 'order__shipping_address'
    ).prefetch_related('messages__sender').order_by('-created_at')

    return render(request, "tienda/pedidos_vendedor.html", {
        "pedidos": pedidos,
        "total_pedidos": pedidos.count()
    })


@login_required
def cambiar_estado_pedido(request: HttpRequest, item_id: int):
    """Cambia el estado de un pedido asignado al vendedor"""
    if request.method != "POST":
        messages.error(request, "Acción no permitida.")
        return redirect("pedidos_vendedor")

    order_item = get_object_or_404(OrderItem, id=item_id, seller=request.user)
    nuevo_estado = request.POST.get("estado")

    if nuevo_estado in dict(OrderItem.STATUS_CHOICES):
        order_item.status = nuevo_estado
        order_item.save()
        messages.success(request, f"Estado actualizado a '{order_item.get_status_display()}'.")
    else:
        messages.error(request, "Estado no válido.")

    return redirect("pedidos_vendedor")


@login_required
def enviar_mensaje_pedido(request: HttpRequest, item_id: int):
    """Envía un mensaje al comprador sobre un pedido"""
    if request.method != "POST":
        messages.error(request, "Acción no permitida.")
        return redirect("pedidos_vendedor")

    order_item = get_object_or_404(OrderItem, id=item_id, seller=request.user)
    mensaje = request.POST.get("mensaje", "").strip()

    if not mensaje:
        messages.error(request, "El mensaje no puede estar vacío.")
        return redirect("pedidos_vendedor")

    OrderMessage.objects.create(
        order_item=order_item,
        sender=request.user,
        message=mensaje
    )

    messages.success(request, "Mensaje enviado correctamente.")
    return redirect("pedidos_vendedor")


@login_required
def crear_producto(request: HttpRequest):
    """Crea un nuevo producto"""
    if request.method == "POST":
        name = request.POST.get("name")
        briefdesc = request.POST.get("briefdesc")
        description = request.POST.get("description")
        price = request.POST.get("price")
        category_id = request.POST.get("category")
        primary_image_file = request.FILES.get("primary_image")
        secondary_images_files = request.FILES.getlist("secondary_images")
        
        # Validaciones
        if not all([name, description, price, category_id]):
            messages.error(request, "Por favor completa todos los campos obligatorios.")
            categories = Category.objects.all()
            return render(request, "tienda/crear_producto.html", {"categories": categories})
        
        try:
            price = float(price)
            if price < 0:
                raise ValueError("El precio no puede ser negativo")
        except ValueError:
            messages.error(request, "El precio debe ser un número válido.")
            categories = Category.objects.all()
            return render(request, "tienda/crear_producto.html", {"categories": categories})
        
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, "Categoría no válida.")
            categories = Category.objects.all()
            return render(request, "tienda/crear_producto.html", {"categories": categories})
        
        # Crear imagen principal si se proporciona
        primary_image = None
        if primary_image_file:
            primary_image = Image.objects.create(
                name=f"{name}_principal",
                image=primary_image_file
            )
        
        # Crear producto
        producto = Product.objects.create(
            name=name,
            briefdesc=briefdesc or "",
            description=description,
            price=price,
            category=category,
            primary_image=primary_image,
            creator=request.user
        )
        
        # Agregar imágenes secundarias si se proporcionan
        if secondary_images_files:
            for idx, img_file in enumerate(secondary_images_files):
                secondary_img = Image.objects.create(
                    name=f"{name}_secundaria_{idx+1}",
                    image=img_file
                )
                producto.secondary_images.add(secondary_img)
        
        messages.success(request, f"¡Producto '{name}' creado exitosamente!")
        return redirect("mis_productos")
    
    # GET request - mostrar formulario
    categories = Category.objects.all()
    return render(request, "tienda/crear_producto.html", {"categories": categories})


@login_required
def editar_producto(request: HttpRequest, id: int):
    """Edita un producto del usuario autenticado"""
    producto = get_object_or_404(Product, id=id, creator=request.user)

    if request.method == "POST":
        name = request.POST.get("name")
        briefdesc = request.POST.get("briefdesc")
        description = request.POST.get("description")
        price = request.POST.get("price")
        category_id = request.POST.get("category")
        primary_image_file = request.FILES.get("primary_image")
        secondary_images_files = request.FILES.getlist("secondary_images")

        if not all([name, description, price, category_id]):
            messages.error(request, "Por favor completa todos los campos obligatorios.")
            categories = Category.objects.all()
            return render(request, "tienda/editar_producto.html", {
                "categories": categories,
                "producto": producto
            })

        try:
            price = float(price)
            if price < 0:
                raise ValueError("El precio no puede ser negativo")
        except ValueError:
            messages.error(request, "El precio debe ser un número válido.")
            categories = Category.objects.all()
            return render(request, "tienda/editar_producto.html", {
                "categories": categories,
                "producto": producto
            })

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, "Categoría no válida.")
            categories = Category.objects.all()
            return render(request, "tienda/editar_producto.html", {
                "categories": categories,
                "producto": producto
            })

        producto.name = name
        producto.briefdesc = briefdesc or ""
        producto.description = description
        producto.price = price
        producto.category = category

        if primary_image_file:
            primary_image = Image.objects.create(
                name=f"{name}_principal",
                image=primary_image_file
            )
            producto.primary_image = primary_image

        producto.save()

        if secondary_images_files:
            producto.secondary_images.clear()
            for idx, img_file in enumerate(secondary_images_files):
                secondary_img = Image.objects.create(
                    name=f"{name}_secundaria_{idx+1}",
                    image=img_file
                )
                producto.secondary_images.add(secondary_img)

        messages.success(request, f"¡Producto '{name}' actualizado exitosamente!")
        return redirect("mis_productos")

    categories = Category.objects.all()
    return render(request, "tienda/editar_producto.html", {
        "categories": categories,
        "producto": producto
    })


@login_required
def borrar_producto(request: HttpRequest, id: int):
    """Borra un producto del usuario autenticado"""
    if request.method != "POST":
        messages.error(request, "Acción no permitida.")
        return redirect("mis_productos")

    producto = get_object_or_404(Product, id=id, creator=request.user)
    nombre = producto.name
    producto.delete()
    messages.success(request, f"Producto '{nombre}' eliminado correctamente.")
    return redirect("mis_productos")

@login_required
def checkout(request: HttpRequest):
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related("product")
    addresses = ShippingAddress.objects.filter(user=request.user)
    return render(request, "tienda/checkout.html", {
        "cart": cart,
        "cart_items": cart_items,
        "addresses": addresses,
    })

@csrf_exempt
def stripe_config(request):
    if request.method == "GET":
        stripe_config = {
            "publicKey": settings.STRIPE_PUBLISHABLE_KEY
        }
        return JsonResponse(stripe_config, safe=False)


@login_required
@csrf_exempt
def create_checkout_session(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        shipping_address = _get_selected_shipping_address(request)
        if shipping_address is None:
            return JsonResponse({"error": "Debes seleccionar una dirección de envío válida."}, status=400)

        cart = get_or_create_cart(request)
        cart_items = cart.items.select_related("product")

        if not cart_items.exists():
            return JsonResponse({"error": "El carrito está vacío"}, status=400)

        stripe.api_key = settings.STRIPE_SECRET_KEY

        line_items = []
        for item in cart_items:
            unit_price_with_vat = get_price_with_vat_decimal(item.product.price)
            unit_amount = int((unit_price_with_vat * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if unit_amount <= 0:
                continue
            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "unit_amount": unit_amount,
                    "product_data": {
                        "name": item.product.name,
                        "description": item.product.briefdesc or item.product.description
                    },
                },
                "quantity": item.quantity,
            })

        if not line_items:
            return JsonResponse({"error": "No hay productos válidos para pagar"}, status=400)

        success_url = request.build_absolute_uri(reverse("checkout_success"))
        cancel_url = request.build_absolute_uri(reverse("checkout_cancel"))

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        request.session['stripe_session_id'] = session.id
        request.session['selected_shipping_address_id'] = shipping_address.id

        return JsonResponse({"sessionId": session.id})
    except Exception as e:
        logger.exception("STRIPE_CHECKOUT_SESSION_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": f"Error al crear sesión de pago: {str(e)}"}, status=500)


def checkout_success(request: HttpRequest):
    payment_reference = request.session.get('stripe_session_id', "")
    shipping_address_id = request.session.get('selected_shipping_address_id')
    shipping_address = ShippingAddress.objects.filter(id=shipping_address_id, user=request.user).first()
    create_order_from_cart(request, Order.PAYMENT_STRIPE, payment_reference, shipping_address)
    if 'stripe_session_id' in request.session:
        del request.session['stripe_session_id']
    if 'selected_shipping_address_id' in request.session:
        del request.session['selected_shipping_address_id']
    messages.success(request, "Pago realizado correctamente. ¡Gracias por tu compra!")
    return render(request, "tienda/checkout_success.html", {})


def checkout_cancel(request: HttpRequest):
    messages.info(request, "Pago cancelado. Puedes intentarlo de nuevo cuando quieras.")
    return render(request, "tienda/checkout_cancel.html", {})


def search(request: HttpRequest):
    """Vista para buscar productos"""
    query = request.GET.get('q', '').strip()
    products = []
    categories = Category.objects.all()
    
    if query:
        # Buscar en nombre y descripción/briefdesc
        products = Product.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(description__icontains=query) |
            models.Q(briefdesc__icontains=query)
        ).select_related('primary_image', 'creator')
    
    return render(request, "tienda/search.html", {
        "products": products,
        "query": query,
        "categories": categories
    })


# ==================== PAYPAL PAYMENT ====================

@login_required
def create_paypal_payment(request: HttpRequest):
    """Crea un pago con PayPal y redirige a PayPal"""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        shipping_address = _get_selected_shipping_address(request)
        if shipping_address is None:
            return JsonResponse({"error": "Debes seleccionar una dirección de envío válida."}, status=400)

        import paypalrestsdk
        
        cart = get_or_create_cart(request)
        cart_items = cart.items.select_related("product")

        if not cart_items.exists():
            return JsonResponse({"error": "El carrito está vacío"}, status=400)

        # Configurar PayPal
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })

        # Crear lista de items para PayPal
        payment_items = []
        payment_total = Decimal("0.00")
        for item in cart_items:
            unit_price_with_vat = get_price_with_vat_decimal(item.product.price)
            line_total_with_vat = (unit_price_with_vat * item.quantity).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            payment_total += line_total_with_vat

            payment_items.append({
                "name": item.product.name,
                "sku": f"product_{item.product.id}",
                "price": format(unit_price_with_vat, ".2f"),
                "currency": "EUR",
                "quantity": item.quantity
            })

        total = format(payment_total, ".2f")

        # Crear el pago
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(reverse("paypal_execute")),
                "cancel_url": request.build_absolute_uri(reverse("checkout_cancel"))
            },
            "transactions": [
                {
                    "amount": {
                        "total": total,
                        "currency": "EUR",
                        "details": {
                            "subtotal": total,
                            "tax": "0",
                            "shipping": "0"
                        }
                    },
                    "description": "Compra de productos",
                    "item_list": {
                        "items": payment_items
                    }
                }
            ]
        })

        # Ejecutar el pago
        if payment.create():
            # Guardar el payment ID en sesión
            request.session['paypal_payment_id'] = payment.id
            request.session['selected_shipping_address_id'] = shipping_address.id
            
            # Encontrar el link de aprobación
            for link in payment.links:
                if link.rel == "approval_url":
                    return JsonResponse({"redirect": link.href})
            
            return JsonResponse({"error": "No se encontró la URL de aprobación"}, status=400)
        else:
            # Loguear el error
            error_msg = str(payment.error) if hasattr(payment, 'error') else "Error desconocido"
            logger.error("PAYPAL_CREATE_ERROR user_id=%s error=%s", request.user.id, error_msg)
            return JsonResponse({"error": f"Error al crear el pago: {error_msg}"}, status=400)

    except ImportError:
        logger.error("PAYPAL_SDK_NOT_INSTALLED")
        return JsonResponse({"error": "SDK de PayPal no instalado"}, status=500)
    except Exception as e:
        error_msg = str(e)
        logger.exception("PAYPAL_CREATE_EXCEPTION user_id=%s error=%s", request.user.id, error_msg)
        return JsonResponse({"error": f"Error: {error_msg}"}, status=500)


@login_required
def paypal_execute(request: HttpRequest):
    """Ejecuta el pago de PayPal después de la aprobación"""
    try:
        import paypalrestsdk
    except ImportError:
        messages.error(request, "PayPal SDK no está instalado")
        return redirect("checkout")

    payment_id = request.session.get('paypal_payment_id')
    payer_id = request.GET.get('PayerID')

    if not payment_id or not payer_id:
        messages.error(request, "Error: Datos de pago incompletos")
        return redirect("checkout")

    try:
        # Configurar PayPal
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })

        # Buscar el pago
        payment = paypalrestsdk.Payment.find(payment_id)

        # Ejecutar el pago
        if payment.execute({"payer_id": payer_id}):
            # Pago exitoso - crear pedido y limpiar el carrito
            shipping_address_id = request.session.get('selected_shipping_address_id')
            shipping_address = ShippingAddress.objects.filter(id=shipping_address_id, user=request.user).first()
            create_order_from_cart(request, Order.PAYMENT_PAYPAL, payment_id, shipping_address)
            
            # Limpiar la sesión
            if 'paypal_payment_id' in request.session:
                del request.session['paypal_payment_id']
            if 'selected_shipping_address_id' in request.session:
                del request.session['selected_shipping_address_id']

            messages.success(request, "¡Pago realizado correctamente con PayPal! Gracias por tu compra.")
            return render(request, "tienda/checkout_success.html", {})
        else:
            error_message = payment.error.get("message", "Error desconocido")
            messages.error(request, f"Error al procesar el pago: {error_message}")
            return redirect("checkout")

    except Exception as e:
        logger.exception("PAYPAL_EXECUTE_EXCEPTION user_id=%s error=%s", request.user.id, str(e))
        messages.error(request, f"Error: {str(e)}")
        return redirect("checkout")
def search_suggestions(request: HttpRequest):
    """API AJAX que retorna sugerencias de búsqueda en JSON"""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if query and len(query) >= 2:  # Mínimo 2 caracteres para sugerir
        # Buscar en nombre (primario) y descripción
        products = Product.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(briefdesc__icontains=query)
        ).values_list('name', 'id', 'price', 'primary_image_id').distinct()[:8]  # Máximo 8 sugerencias
        
        for name, product_id, price, image_id in products:
            suggestions.append({
                'name': name,
                'id': product_id,
                'price': float(price)
            })
    
    return JsonResponse({'suggestions': suggestions})


# ==================== PORTAL DE USUARIO ====================

@login_required
def portal_usuario(request: HttpRequest):
    """Dashboard del portal de usuario"""
    # Obtener estadísticas del usuario
    total_orders = Order.objects.filter(buyer=request.user).count()
    total_addresses = ShippingAddress.objects.filter(user=request.user).count()
    
    # Obtener pedidos recientes (como comprador)
    recent_orders = Order.objects.filter(buyer=request.user).order_by('-created_at')[:5]
    
    # Obtener mensajes recientes sin leer (de vendedores)
    recent_messages = OrderMessage.objects.filter(
        order_item__order__buyer=request.user
    ).exclude(sender=request.user).order_by('-created_at')[:5]
    
    return render(request, "tienda/portal_usuario.html", {
        "total_orders": total_orders,
        "total_addresses": total_addresses,
        "recent_orders": recent_orders,
        "recent_messages": recent_messages,
    })


@login_required
def mis_compras(request: HttpRequest):
    """Lista completa de compras del usuario autenticado"""
    orders = Order.objects.filter(buyer=request.user).prefetch_related('items').order_by('-created_at')

    return render(request, "tienda/mis_compras.html", {
        "orders": orders,
        "total_orders": orders.count(),
    })


@login_required
def mis_recibos(request: HttpRequest):
    """Lista de recibos (pedidos pagados) del usuario autenticado"""
    receipts = Order.objects.filter(
        buyer=request.user,
        status=Order.STATUS_PAID
    ).prefetch_related('items').order_by('-created_at')

    return render(request, "tienda/mis_recibos.html", {
        "receipts": receipts,
        "total_receipts": receipts.count(),
    })


@login_required
def editar_perfil(request: HttpRequest):
    """Edita la información del perfil del usuario"""
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        
        # Validar email único (excepto el propio)
        if email != request.user.email and User.objects.filter(email=email).exists():
            messages.error(request, "Ya existe un usuario con este correo electrónico.")
            return render(request, "tienda/editar_perfil.html")
        
        # Actualizar usuario
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()
        
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect("portal_usuario")
    
    return render(request, "tienda/editar_perfil.html")


@login_required
def cambiar_contrasena(request: HttpRequest):
    """Cambia la contraseña del usuario"""
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        
        # Verificar contraseña actual
        if not request.user.check_password(current_password):
            messages.error(request, "La contraseña actual es incorrecta.")
            return render(request, "tienda/editar_perfil.html")
        
        # Validar nueva contraseña
        if new_password != confirm_password:
            messages.error(request, "Las contraseñas nuevas no coinciden.")
            return render(request, "tienda/editar_perfil.html")
        
        if len(new_password) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            return render(request, "tienda/editar_perfil.html")
        
        # Cambiar contraseña
        request.user.set_password(new_password)
        request.user.save()
        
        # Mantener la sesión activa
        auth_login(request, request.user)
        
        messages.success(request, "Contraseña actualizada correctamente.")
        return redirect("portal_usuario")
    
    return redirect("editar_perfil")


@login_required
def direcciones_usuario(request: HttpRequest):
    """Lista las direcciones de entrega del usuario"""
    direcciones = ShippingAddress.objects.filter(user=request.user)
    
    return render(request, "tienda/direcciones.html", {
        "direcciones": direcciones
    })


@login_required
def crear_direccion(request: HttpRequest):
    """Crea una nueva dirección de entrega"""
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        address_line_1 = request.POST.get("address_line_1", "").strip()
        address_line_2 = request.POST.get("address_line_2", "").strip()
        city = request.POST.get("city", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        country = SHIPPING_COUNTRY
        phone = request.POST.get("phone", "").strip()
        is_default = request.POST.get("is_default") == "on"
        
        # Validaciones
        if not all([full_name, address_line_1, city, postal_code, phone]):
            messages.error(request, "Por favor completa todos los campos obligatorios.")
            return render(request, "tienda/editar_direccion.html", _address_form_context(request.POST))

        if not _is_almeria_city(city):
            messages.error(request, "El pueblo/ciudad debe pertenecer a la provincia de Almería.")
            return render(request, "tienda/editar_direccion.html", _address_form_context(request.POST))

        if not _is_almeria_postal_code(postal_code):
            messages.error(request, "Solo realizamos envíos en la provincia de Almería (código postal 04xxx).")
            return render(request, "tienda/editar_direccion.html", _address_form_context(request.POST))
        
        # Crear dirección
        ShippingAddress.objects.create(
            user=request.user,
            full_name=full_name,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            postal_code=postal_code,
            country=country,
            phone=phone,
            is_default=is_default
        )
        
        messages.success(request, "Dirección creada correctamente.")
        return redirect("direcciones_usuario")
    
    return render(request, "tienda/editar_direccion.html", _address_form_context())


@login_required
def editar_direccion(request: HttpRequest, id: int):
    """Edita una dirección de entrega existente"""
    direccion = get_object_or_404(ShippingAddress, id=id, user=request.user)
    
    if request.method == "POST":
        direccion.full_name = request.POST.get("full_name", "").strip()
        direccion.address_line_1 = request.POST.get("address_line_1", "").strip()
        direccion.address_line_2 = request.POST.get("address_line_2", "").strip()
        direccion.city = request.POST.get("city", "").strip()
        direccion.postal_code = request.POST.get("postal_code", "").strip()
        direccion.country = SHIPPING_COUNTRY
        direccion.phone = request.POST.get("phone", "").strip()
        direccion.is_default = request.POST.get("is_default") == "on"
        
        # Validaciones
        if not all([direccion.full_name, direccion.address_line_1, direccion.city, 
                   direccion.postal_code, direccion.phone]):
            messages.error(request, "Por favor completa todos los campos obligatorios.")
            return render(request, "tienda/editar_direccion.html", _address_form_context(direccion))

        if not _is_almeria_city(direccion.city):
            messages.error(request, "El pueblo/ciudad debe pertenecer a la provincia de Almería.")
            return render(request, "tienda/editar_direccion.html", _address_form_context(direccion))

        if not _is_almeria_postal_code(direccion.postal_code):
            messages.error(request, "Solo realizamos envíos en la provincia de Almería (código postal 04xxx).")
            return render(request, "tienda/editar_direccion.html", _address_form_context(direccion))
        
        direccion.save()
        messages.success(request, "Dirección actualizada correctamente.")
        return redirect("direcciones_usuario")
    
    return render(request, "tienda/editar_direccion.html", _address_form_context(direccion))


@login_required
def eliminar_direccion(request: HttpRequest, id: int):
    """Elimina una dirección de entrega"""
    if request.method != "POST":
        messages.error(request, "Acción no permitida.")
        return redirect("direcciones_usuario")
    
    direccion = get_object_or_404(ShippingAddress, id=id, user=request.user)
    direccion.delete()
    messages.success(request, "Dirección eliminada correctamente.")
    return redirect("direcciones_usuario")


@login_required
def mensajes_comprador(request: HttpRequest):
    """Muestra los mensajes recibidos de vendedores"""
    # Obtener todos los order items del comprador con mensajes
    order_items = OrderItem.objects.filter(
        order__buyer=request.user
    ).prefetch_related(
        'messages__sender', 'product', 'seller'
    ).order_by('-created_at')
    
    return render(request, "tienda/mensajes_comprador.html", {
        "order_items": order_items
    })



def send_test_email(request: HttpRequest):
    message = """

Correo de prueba, deberias recibir esto bien
y esto deberia tener un enter
    """

    result = send_email("danilacasito8@gmail.com", "Correo de Prueba", message)
    if result[0]:
        return HttpResponse("Mira tu bandeja")
    else:
        return HttpResponse(result[1])


def verify(request: HttpRequest, code: str):
    obj = None
    try:
        obj = VerificationCode.objects.get(code=code)
    except VerificationCode.DoesNotExist:
        return HttpResponse("<h1>Error</h1><p>No existe el codigo de verificación</p>")
    if obj:
        if obj.code_mode == VerificationCode.VerificationModes.VERIFY_ACCOUNT:

            obj.user.registration_status = obj.user.RegisterStatus.ACTIVE
            obj.user.save()
            obj.delete()
            return redirect("index")
    else:
        return HttpResponse("<h1>Error</h1><p>No existe el codigo de verificación</p>")


def reset_password(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("index")
    
        
    return render(request, "tienda/reset_password", {})

def rgpd(request: HttpRequest):
    return render(request, "tienda/rgpd.html", {})

def reset_password(request: HttpRequest):
    if request.method == "GET":
        return render(request, "tienda/reset_password.html", {})
    else:
        tasks.enviar_correo_recuperacion.delay(request.POST["email"])
        messages.info(request, "Si tienes una cuenta con ese correo electronico, se ha enviado un correo con un enlace")
        return render(request, "tienda/index.html", {})
    
def reset_password_phase2(request: HttpRequest, code: str):
    try:
        ver_code = VerificationCode.objects.get(code=code)
    except VerificationCode.DoesNotExist:
        raise Http404()
    
    if ver_code.code_mode != VerificationCode.VerificationModes.RESET_PASSWORD: raise Http404()


    if request.method == "GET":
        return render(request, "tienda/reset_password_phase2.html", {
            "code": code
        })
    elif request.method == "POST":
        password = request.POST["password"]
        vpassword = request.POST["verify_password"]
        if password != vpassword:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, "tienda/reset_password_phase2.html", {"code": code})

        user = ver_code.user
        user.set_password(password)
        user.save()
        messages.success(request, "Se ha cambiado la contraseña!")
        return redirect(reverse("index"))
        
    else:
        raise Http404()
