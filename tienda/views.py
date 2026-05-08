from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db.utils import DataError
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from tienda.utilities import send_email
from .models import User, Product, Category, Cart, CartItem, Image, Order, OrderItem, OrderMessage, ShippingAddress, StockReservation, StockReservationItem, VerificationCode, SavedPaymentMethod
from .forms import ProductForm, SecondaryImageForm, UserLoginForm, UserRegisterForm, ProductEditForm, EditProfileForm, ChangePasswordForm, ShippingAddressForm, ResetPasswordForm, ResetPasswordPhase2Form
from . import tasks
from .vars import (
    PAGE_SIZE,
    VAT_RATE,
    SHIPPING_COUNTRY,
    ALMERIA_POSTAL_CODE_PREFIX,
    ALMERIA_MUNICIPALITIES_DISPLAY,
    STOCK_RESERVATION_MINUTES,
)
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
import stripe
from django.db import models, transaction
from django.db.models import F
from django.core.cache import cache
import re
import unicodedata
import json
import random, string
import logging
import requests
# Create your views here.


logger = logging.getLogger("tienda")
audit_logger = logging.getLogger("tienda.audit")
STOCK_RESERVATION_SESSION_KEY = "stock_reservation_id"
STOCK_RESERVATION_PAYMENT_SESSION_KEY = "stock_reservation_payment_method"


def _invalidate_product_cache(product_ids):
    unique_product_ids = {product_id for product_id in product_ids if product_id is not None}
    if not unique_product_ids:
        return
    cache.delete_many([f"product_{product_id}" for product_id in unique_product_ids])


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


def _address_form_context(direccion=None, form=None):
    return {
        "direccion": direccion,
        "form": form,
        "almeria_municipalities": ALMERIA_MUNICIPALITIES_DISPLAY,
    }


def _get_client_ip(request: HttpRequest) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


# ==================== PAYPAL ORDERS API v2 HELPERS ====================

def _get_paypal_base_url() -> str:
    mode = getattr(settings, "PAYPAL_MODE", "sandbox")
    if mode == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def _get_paypal_access_token() -> str:
    """Obtiene un access token de la API de PayPal."""
    url = f"{_get_paypal_base_url()}/v1/oauth2/token"
    response = requests.post(
        url,
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _paypal_create_order(amount_eur: Decimal) -> dict:
    """Crea una orden PayPal y retorna el diccionario de respuesta con id y approve_link."""
    token = _get_paypal_access_token()
    url = f"{_get_paypal_base_url()}/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "EUR",
                    "value": format(amount_eur, ".2f"),
                }
            }
        ],
        "application_context": {
            "brand_name": "Comercialmeria",
            "shipping_preference": "NO_SHIPPING",
            "user_action": "PAY_NOW",
        },
    }
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def _paypal_capture_order(order_id: str) -> dict:
    """Captura una orden PayPal aprobada por el comprador."""
    token = _get_paypal_access_token()
    url = f"{_get_paypal_base_url()}/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    response = requests.post(url, headers=headers, json={}, timeout=15)
    response.raise_for_status()
    return response.json()


# ==================== STRIPE CUSTOMER HELPER ====================

def _get_or_create_stripe_customer(user) -> str:
    """Devuelve el stripe_customer_id del usuario, creando uno nuevo si es necesario."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    existing = SavedPaymentMethod.objects.filter(
        user=user,
        method_type=SavedPaymentMethod.TYPE_CARD,
        stripe_customer_id__gt="",
    ).first()
    if existing:
        return existing.stripe_customer_id
    customer = stripe.Customer.create(
        email=user.email,
        name=(f"{user.first_name} {user.last_name}".strip()) or user.username,
    )
    return customer.id

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
        form: UserLoginForm = UserLoginForm(request.POST)
        if form.is_valid():
            email: str = form.cleaned_data["email"]
            password: str = form.cleaned_data["password"]
            remember: bool = form.cleaned_data["remember"]
            client_ip = _get_client_ip(request)
            try:
                user: User = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                audit_logger.warning("LOGIN FAILED email=%s reason=user_not_found ip=%s", email, client_ip)
                messages.error(request, "El email o la contraseña es incorrecta")
                return render(request, "tienda/login.html", {"form": form})
            if user.registration_status == User.RegisterStatus.BANNED:
                # Usuario baneado.
                messages.error(request, "Esta cuenta esta bloqueada.")
                return render(request, "tienda/login.html", {"form": form})
            
            user = authenticate(request, username = username, password=password)
            
            if user is None:
                data: str = cache.get(f"tries_login_{username}")
                logins: int
                if data is None:
                    logins = 0
                else:
                    logins = int(data)
                
                if logins >= 5:
                    audit_logger.info("LOGIN FAILED email=%s reason=rate_limited", email)
                    messages.error(request, "Has sufrido de Rate Limit por fallar 5 veces la contraseña")
                    return render(request, "tienda/login.html", {"form": form})
                logins+=1
                cache.set(f"tries_login_{username}", str(logins), 600)
                messages.error(request, "El email o la contraseña es incorrecta")
                return render(request, "tienda/login.html", {"form": form})
            if user.registration_status == User.RegisterStatus.CONFIRMATION_REQUIRED:
                audit_logger.info("LOGIN_FAILED email=%s reason=not_verified", email)
                messages.error(request, "No se puede iniciar sesión porque no has verificado tu cuenta, comprueba tu email. Si eliminaste el email pero querias verificarte, contacta con el soporte tecnico")
                return render(request, "tienda/login.html", {"form": form})
            auth_login(request, user)

            if not remember:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)
            
            audit_logger.info("LOGIN_SUCCESS user_id=%s email=%s ip=%s remember=%s", user.id, user.email, client_ip, bool(remember))
            tasks.enviar_correo_bienvenida.delay(user.email, f"{user.first_name} {user.last_name}")
            messages.success(request, f"¡Bienvenido {user.first_name or user.username}!")
            return redirect("index")
    else:
        form = UserLoginForm()
    return render(request, "tienda/login.html", {"form": form})

#        
#        if user is not None:
#            auth_login(request, user)
#            
#            # Configurar duración de sesión
#            if not remember:
#                request.session.set_expiry(0)
#            else:
#                request.session.set_expiry(1209600)  # 14 días en segundos
#
#            audit_logger.info(
#                "LOGIN_SUCCESS user_id=%s email=%s ip=%s remember=%s",
#                user.id,
#                user.email,
#                client_ip,
#                bool(remember),
#            )
#            tasks.enviar_correo_bienvenida.delay(user.email, "{} {}".format(user.first_name, user.last_name))
#            # result = send_email(user.email, "Inicio de sesión correcto", login_message.format(name = "{} {}".format(user.first_name, user.last_name)))
#            messages.success(request, f"¡Bienvenido {user.first_name or user.username}!")
#            return redirect("index")
#        else:
#            user1: User = User.objects.get(username=username)
#            if user1.registration_status == User.RegisterStatus.BANNED:
#                    audit_logger.warning(
#                        "LOGIN FAILED email=%s reason=user_banned ip=%s",
#                        email,
#                        client_ip,
#                    )
#                    messages.error(request, "Error, La cuenta esta bloqueada")
#                    return render(request, "tienda/login.html")
#            audit_logger.warning(
#                "LOGIN_FAILED email=%s reason=invalid_credentials ip=%s",
#                email,
#                client_ip,
#            )
#            messages.error(request, "Correo electrónico o contraseña incorrectos.")
#            return render(request, "tienda/login.html")
#    
#    return render(request, "tienda/login.html")

def register(request: HttpRequest):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            client_ip = _get_client_ip(request)

            # Validación email
            if User.objects.filter(email=email).exists():
                audit_logger.warning("REGISTER_FAILED email=%s reason=email_exists ip=%s", email, client_ip)
                messages.error(request, "Ya existe un usuario con este correo electrónico")
                return render(request, "tienda/register.html", {"form":form})
            
            username = email.split("@")[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user = User.objects.create_user(
                username = username,
                email = email,
                password = password,
                first_name = name
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
    else:
        form = UserRegisterForm()
    return render(request, "tienda/register.html", {"form":form})


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


def _get_or_create_session_key(request: HttpRequest):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _get_reservation_owner_filters(request: HttpRequest):
    if request.user.is_authenticated:
        return {"user": request.user}
    return {"session_key": _get_or_create_session_key(request)}


def _release_expired_stock_reservations():
    now = timezone.now()
    StockReservation.objects.filter(
        status=StockReservation.STATUS_ACTIVE,
        expires_at__lte=now,
    ).update(status=StockReservation.STATUS_EXPIRED)


def _clear_stock_reservation_session(request: HttpRequest):
    request.session.pop(STOCK_RESERVATION_SESSION_KEY, None)
    request.session.pop(STOCK_RESERVATION_PAYMENT_SESSION_KEY, None)


def _cancel_active_stock_reservations_for_request(request: HttpRequest):
    _release_expired_stock_reservations()
    StockReservation.objects.filter(
        **_get_reservation_owner_filters(request),
        status=StockReservation.STATUS_ACTIVE,
        expires_at__gt=timezone.now(),
    ).update(status=StockReservation.STATUS_CANCELLED)


def _get_reserved_quantities_by_product(product_ids, exclude_reservation_ids=None):
    if not product_ids:
        return {}

    reserved_qs = StockReservationItem.objects.filter(
        product_id__in=product_ids,
        reservation__status=StockReservation.STATUS_ACTIVE,
        reservation__expires_at__gt=timezone.now(),
    )
    if exclude_reservation_ids:
        reserved_qs = reserved_qs.exclude(reservation_id__in=exclude_reservation_ids)

    reserved_totals = reserved_qs.values("product_id").annotate(total_reserved=models.Sum("quantity"))
    return {row["product_id"]: row["total_reserved"] for row in reserved_totals}


def _get_active_reservation_ids_for_request(request: HttpRequest):
    _release_expired_stock_reservations()
    return list(
        StockReservation.objects.filter(
            **_get_reservation_owner_filters(request),
            status=StockReservation.STATUS_ACTIVE,
            expires_at__gt=timezone.now(),
        ).values_list("id", flat=True)
    )


def _get_available_stock_by_product(product_ids, exclude_reservation_ids=None):
    """Calcula stock disponible con bloqueo atómico para evitar race conditions."""
    _release_expired_stock_reservations()
    
    if not product_ids:
        return {}
    
    with transaction.atomic():
        # Bloquear productos a nivel de fila para evitar race conditions
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        stocks = {product.id: product.stock for product in products}
        
        # Las reservas se consultan dentro de la transacción atómica
        # _get_reserved_quantities_by_product hace una lectura consistente
        reserved = _get_reserved_quantities_by_product(
            product_ids, 
            exclude_reservation_ids=exclude_reservation_ids
        )
        
        return {
            product_id: max(stocks.get(product_id, 0) - reserved.get(product_id, 0), 0)
            for product_id in product_ids
        }


def _get_cart_stock_issues(cart_items, exclude_reservation_ids=None):
    product_ids = [item.product_id for item in cart_items]
    available_by_product = _get_available_stock_by_product(product_ids, exclude_reservation_ids=exclude_reservation_ids)

    issues = []
    for item in cart_items:
        available = available_by_product.get(item.product_id, 0)
        if item.quantity > available:
            issues.append({
                "product_name": item.product.name,
                "requested": item.quantity,
                "available": available,
            })
    return issues


def _build_stock_issue_message(issue):
    return (
        f"No hay stock suficiente de '{issue['product_name']}'. "
        f"Disponible: {issue['available']}, solicitado: {issue['requested']}."
    )


def _create_stock_reservation_for_cart(request: HttpRequest, cart_items, payment_method: str):
    if not cart_items:
        return None, ["El carrito está vacío."]

    _release_expired_stock_reservations()

    with transaction.atomic():
        StockReservation.objects.select_for_update().filter(
            **_get_reservation_owner_filters(request),
            status=StockReservation.STATUS_ACTIVE,
            expires_at__gt=timezone.now(),
        ).update(status=StockReservation.STATUS_CANCELLED)

        product_ids = [item.product_id for item in cart_items]
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        product_stock = {product.id: product.stock for product in products}
        reserved = _get_reserved_quantities_by_product(product_ids)

        issues = []
        for item in cart_items:
            available = max(product_stock.get(item.product_id, 0) - reserved.get(item.product_id, 0), 0)
            if item.quantity > available:
                issues.append(_build_stock_issue_message({
                    "product_name": item.product.name,
                    "requested": item.quantity,
                    "available": available,
                }))

        if issues:
            return None, issues

        reservation = StockReservation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=None if request.user.is_authenticated else _get_or_create_session_key(request),
            payment_method=payment_method,
            expires_at=timezone.now() + timedelta(minutes=STOCK_RESERVATION_MINUTES),
        )
        StockReservationItem.objects.bulk_create([
            StockReservationItem(
                reservation=reservation,
                product=item.product,
                quantity=item.quantity,
            )
            for item in cart_items
        ])

    _invalidate_product_cache(product_ids)

    return reservation, []


def _get_session_stock_reservation(request: HttpRequest, payment_method: str):
    reservation_id = request.session.get(STOCK_RESERVATION_SESSION_KEY)
    reservation_payment_method = request.session.get(STOCK_RESERVATION_PAYMENT_SESSION_KEY)
    if not reservation_id or reservation_payment_method != payment_method:
        return None

    return StockReservation.objects.filter(
        id=reservation_id,
        status=StockReservation.STATUS_ACTIVE,
        expires_at__gt=timezone.now(),
        payment_method=payment_method,
        **_get_reservation_owner_filters(request),
    ).first()


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


def create_order_from_cart(request, payment_method, payment_reference="", shipping_address=None, stock_reservation=None):
    """Crea un pedido a partir del carrito actual, validando y descontando stock."""
    cart = get_or_create_cart(request)
    cart_items = list(cart.items.select_related("product", "product__creator"))

    if not cart_items:
        return None, "El carrito está vacío."

    order_total = Decimal("0.00")
    items_with_totals = []
    purchased_items = []

    for item in cart_items:
        product = item.product
        unit_price_with_vat = get_price_with_vat_decimal(product.price)
        line_total_with_vat = (unit_price_with_vat * item.quantity).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        order_total += line_total_with_vat
        items_with_totals.append((item, unit_price_with_vat, line_total_with_vat))
        purchased_items.append(
            {
                "amount": item.quantity,
                "product_name": product.name,
                "price": float(unit_price_with_vat),
            }
        )

    _release_expired_stock_reservations()

    with transaction.atomic():
        locked_reservation = None
        reserved_by_product = {}

        if stock_reservation is not None:
            locked_reservation = StockReservation.objects.select_for_update().filter(
                id=stock_reservation.id,
                status=StockReservation.STATUS_ACTIVE,
                expires_at__gt=timezone.now(),
            ).first()
            if locked_reservation is None:
                return None, (
                    f"La reserva de stock ha caducado. Tienes {STOCK_RESERVATION_MINUTES} minutos "
                    "desde que pulsas pagar. Revisa el carrito y vuelve a intentarlo."
                )

            for reservation_item in locked_reservation.items.all():
                reserved_by_product[reservation_item.product_id] = reservation_item.quantity

        product_ids = [item.product_id for item in cart_items]
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        product_map = {product.id: product for product in products}

        reserved_from_others = _get_reserved_quantities_by_product(
            product_ids,
            exclude_reservation_ids=[locked_reservation.id] if locked_reservation else None,
        )

        for item in cart_items:
            product = product_map.get(item.product_id)
            if product is None:
                return None, f"El producto '{item.product.name}' ya no está disponible."

            if locked_reservation is not None and item.quantity > reserved_by_product.get(item.product_id, 0):
                return None, (
                    f"La cantidad de '{item.product.name}' ha cambiado desde la reserva. "
                    "Vuelve a intentar el pago."
                )

            available = max(product.stock - reserved_from_others.get(item.product_id, 0), 0)
            if item.quantity > available:
                return None, _build_stock_issue_message({
                    "product_name": item.product.name,
                    "requested": item.quantity,
                    "available": available,
                })

            if product.stock < item.quantity:
                return None, _build_stock_issue_message({
                    "product_name": item.product.name,
                    "requested": item.quantity,
                    "available": product.stock,
                })

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

            product_row = product_map.get(item.product_id)
            product_row.stock = F('stock') - item.quantity
            product_row.save(update_fields=["stock"])

        _invalidate_product_cache(product_ids)

        cart.items.all().delete()

        if locked_reservation is not None:
            locked_reservation.status = StockReservation.STATUS_COMPLETED
            locked_reservation.save(update_fields=["status", "updated_at"])

    if request.user.is_authenticated and purchased_items:
        tasks.process_purchase.delay(
            request.user.id,
            purchased_items,
            payment_method,
            order.transaction_code,
        )

    return order, ""


@require_POST
def add_to_cart(request: HttpRequest, product_id: int):
    """Agrega un producto al carrito"""
    try:
        product = Product.objects.get(id=product_id)
        cart = get_or_create_cart(request)

        _cancel_active_stock_reservations_for_request(request)
        _clear_stock_reservation_session(request)
        
        # Obtener cantidad del POST o por defecto 1
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            messages.error(request, "La cantidad debe ser mayor que cero.")
            return redirect('producto', id=product_id)

        existing_item = CartItem.objects.filter(cart=cart, product=product).first()
        desired_quantity = quantity if existing_item is None else existing_item.quantity + quantity
        available = _get_available_stock_by_product([product.id]).get(product.id, 0)
        if desired_quantity > available:
            messages.error(
                request,
                f"No hay stock suficiente de '{product.name}'. Disponible: {available}, solicitado: {desired_quantity}.",
            )
            return redirect('producto', id=product_id)
        
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

    except ValueError:
        messages.error(request, "Cantidad no válida.")
        return redirect('producto', id=product_id)
    
    except Product.DoesNotExist:
        messages.error(request, "Producto no encontrado.")
        return redirect('index')


def view_cart(request: HttpRequest):
    """Muestra el contenido del carrito"""
    cart = get_or_create_cart(request)
    cart_items = list(cart.items.select_related("product"))
    active_reservation_ids = _get_active_reservation_ids_for_request(request)
    stock_issues = _get_cart_stock_issues(cart_items, exclude_reservation_ids=active_reservation_ids)
    return render(request, "tienda/cart.html", {
        "cart": cart,
        "cart_items": cart_items,
        "stock_issues": stock_issues,
    })


def update_cart_item(request: HttpRequest, item_id: int):
    """Actualiza la cantidad de un item del carrito"""
    try:
        cart = get_or_create_cart(request)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)

        _cancel_active_stock_reservations_for_request(request)
        _clear_stock_reservation_session(request)
        
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            available = _get_available_stock_by_product([cart_item.product_id]).get(cart_item.product_id, 0)
            if quantity > available:
                messages.error(
                    request,
                    f"No hay stock suficiente de '{cart_item.product.name}'. Disponible: {available}, solicitado: {quantity}.",
                )
                return redirect('view_cart')

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
    except ValueError:
        messages.error(request, "Cantidad no válida.")
        return redirect('view_cart')


def remove_from_cart(request: HttpRequest, item_id: int):
    """Elimina un producto del carrito"""
    try:
        cart = get_or_create_cart(request)
        _cancel_active_stock_reservations_for_request(request)
        _clear_stock_reservation_session(request)
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
    _cancel_active_stock_reservations_for_request(request)
    _clear_stock_reservation_session(request)
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
    total_pedidos_por_enviar = pedidos.exclude(status=OrderItem.STATUS_SHIPPED).count()

    return render(request, "tienda/pedidos_vendedor.html", {
        "pedidos": pedidos,
        "total_pedidos": total_pedidos_por_enviar
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
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            primary_image_file = form.cleaned_data.get("primary_image")
            image = None
            if primary_image_file:
                image = Image(
                    name = f"{form.cleaned_data['name']}_principal",
                    image = primary_image_file,
                )
                image.save()
            producto: Product = Product(
                name = form.cleaned_data["name"],
                briefdesc = form.cleaned_data["briefdesc"],
                description = form.cleaned_data["description"],
                price = form.cleaned_data["price"],
                stock = form.cleaned_data["stock"],
                category = form.cleaned_data["category"],
                primary_image = image,
                creator = request.user
            )
            producto.save()
            return redirect("/")
    else:
        form = ProductForm()
    return render(request, "tienda/crear_producto.html", {"form":form})

@login_required
def editar_producto(request: HttpRequest, id: int):
    """Edita un producto del usuario autenticado"""
    producto = get_object_or_404(Product, id=id, creator=request.user)

    if request.method == "POST":
        form = ProductEditForm(request.POST, request.FILES)
        if form.is_valid():
            producto.name = form.cleaned_data["name"]
            producto.briefdesc = form.cleaned_data.get("briefdesc", "") or ""
            producto.description = form.cleaned_data["description"]
            producto.price = form.cleaned_data["price"]
            producto.stock = form.cleaned_data["stock"]
            producto.category = form.cleaned_data["category"]

            primary_image_file = request.FILES.get("primary_image")
            secondary_images_files = request.FILES.getlist("secondary_images")

            if primary_image_file:
                primary_image = Image.objects.create(
                    name=f"{producto.name}_principal",
                    image=primary_image_file
                )
                producto.primary_image = primary_image

            producto.save()
            _invalidate_product_cache([producto.id])

            if secondary_images_files:
                producto.secondary_images.clear()
                for idx, img_file in enumerate(secondary_images_files):
                    secondary_img = Image.objects.create(
                        name=f"{producto.name}_secundaria_{idx+1}",
                        image=img_file
                    )
                    producto.secondary_images.add(secondary_img)

            messages.success(request, f"¡Producto '{producto.name}' actualizado exitosamente!")
            return redirect("mis_productos")
        else:
            messages.error(request, "Por favor completa todos los campos obligatorios.")
    else:
        initial = {
            "name": producto.name,
            "briefdesc": producto.briefdesc,
            "description": producto.description,
            "price": producto.price,
            "stock": producto.stock,
            "category": producto.category,
        }
        form = ProductEditForm(initial=initial)

    categories = Category.objects.all()
    return render(request, "tienda/editar_producto.html", {
        "form": form,
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
    _invalidate_product_cache([producto.id])
    producto.delete()
    messages.success(request, f"Producto '{nombre}' eliminado correctamente.")
    return redirect("mis_productos")


@login_required
def gestionar_imagenes(request: HttpRequest, id: int):
    """Gestiona las imágenes secundarias de un producto"""
    producto = get_object_or_404(Product, id=id, creator=request.user)
    secondary_images = producto.secondary_images.all()
    form = SecondaryImageForm()

    if request.method == "POST":
        form = SecondaryImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = Image(
                name = f"{producto.name}_secundaria_{secondary_images.count() + 1}",
                image = form.cleaned_data["image"],
                alt = form.cleaned_data.get("alt", "")
            )
            image.save()
            producto.secondary_images.add(image)
            _invalidate_product_cache([producto.id])
            messages.success(request, "Imagen añadida correctamente.")
            return redirect("gestionar_imagenes", id=producto.id)

    return render(request, "tienda/gestionar_imagenes.html", {
        "producto": producto,
        "secondary_images": secondary_images,
        "form": form
    })


@login_required
def eliminar_imagen_secundaria(request: HttpRequest, product_id: int, image_id: int):
    """Elimina una imagen secundaria de un producto"""
    if request.method != "POST":
        messages.error(request, "Acción no permitida.")
        return redirect("gestionar_imagenes", id=product_id)

    producto = get_object_or_404(Product, id=product_id, creator=request.user)
    image = get_object_or_404(Image, id=image_id)

    if not producto.secondary_images.filter(id=image_id).exists():
        messages.error(request, "Esta imagen no pertenece al producto.")
        return redirect("gestionar_imagenes", id=product_id)

    producto.secondary_images.remove(image)
    image.delete()
    _invalidate_product_cache([producto.id])
    messages.success(request, "Imagen eliminada correctamente.")
    return redirect("gestionar_imagenes", id=product_id)

@login_required
def checkout(request: HttpRequest):
    cart = get_or_create_cart(request)
    cart_items = list(cart.items.select_related("product"))
    active_reservation_ids = _get_active_reservation_ids_for_request(request)
    stock_issues = _get_cart_stock_issues(cart_items, exclude_reservation_ids=active_reservation_ids)
    addresses = ShippingAddress.objects.filter(user=request.user)
    saved_cards = SavedPaymentMethod.objects.filter(user=request.user, method_type=SavedPaymentMethod.TYPE_CARD)
    saved_paypal = SavedPaymentMethod.objects.filter(user=request.user, method_type=SavedPaymentMethod.TYPE_PAYPAL).first()
    return render(request, "tienda/checkout.html", {
        "cart": cart,
        "cart_items": cart_items,
        "addresses": addresses,
        "stock_issues": stock_issues,
        "reservation_minutes": STOCK_RESERVATION_MINUTES,
        "saved_cards": saved_cards,
        "saved_paypal": saved_paypal,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "paypal_client_id": settings.PAYPAL_CLIENT_ID,
    })

@csrf_exempt
def stripe_config(request):
    if request.method == "GET":
        stripe_config = {
            "publicKey": settings.STRIPE_PUBLISHABLE_KEY
        }
        return JsonResponse(stripe_config, safe=False)


@login_required
@csrf_protect
def create_checkout_session(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        shipping_address = _get_selected_shipping_address(request)
        if shipping_address is None:
            return JsonResponse({"error": "Debes seleccionar una dirección de envío válida."}, status=400)

        cart = get_or_create_cart(request)
        cart_items = list(cart.items.select_related("product"))

        if not cart_items:
            return JsonResponse({"error": "El carrito está vacío"}, status=400)

        active_reservation_ids = _get_active_reservation_ids_for_request(request)
        stock_issues = _get_cart_stock_issues(cart_items, exclude_reservation_ids=active_reservation_ids)
        if stock_issues:
            return JsonResponse({"error": _build_stock_issue_message(stock_issues[0])}, status=400)

        reservation, reservation_issues = _create_stock_reservation_for_cart(
            request,
            cart_items,
            StockReservation.PAYMENT_STRIPE,
        )
        if reservation is None:
            return JsonResponse({"error": reservation_issues[0]}, status=400)

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
        request.session[STOCK_RESERVATION_SESSION_KEY] = reservation.id
        request.session[STOCK_RESERVATION_PAYMENT_SESSION_KEY] = StockReservation.PAYMENT_STRIPE

        return JsonResponse({"sessionId": session.id})
    except Exception as e:
        logger.exception("STRIPE_CHECKOUT_SESSION_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": "Error al crear la sesión de pago. Por favor inténtalo de nuevo."}, status=500)


@login_required
def checkout_success(request: HttpRequest):
    payment_reference = request.session.get('stripe_session_id', "")
    shipping_address_id = request.session.get('selected_shipping_address_id')
    shipping_address = ShippingAddress.objects.filter(id=shipping_address_id, user=request.user).first()
    reservation = _get_session_stock_reservation(request, StockReservation.PAYMENT_STRIPE)
    order, order_error = create_order_from_cart(
        request,
        Order.PAYMENT_STRIPE,
        payment_reference,
        shipping_address,
        stock_reservation=reservation,
    )

    if order is None:
        messages.error(request, order_error)
        return redirect("checkout")

    if 'stripe_session_id' in request.session:
        del request.session['stripe_session_id']
    if 'selected_shipping_address_id' in request.session:
        del request.session['selected_shipping_address_id']
    _clear_stock_reservation_session(request)
    messages.success(request, "Pago realizado correctamente. ¡Gracias por tu compra!")
    return render(request, "tienda/checkout_success.html", {"order": order})


@login_required
def checkout_cancel(request: HttpRequest):
    _cancel_active_stock_reservations_for_request(request)
    _clear_stock_reservation_session(request)
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


def search_suggestions(request: HttpRequest):
    """API AJAX que retorna sugerencias de búsqueda en JSON"""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if query and len(query) >= 2:
        products = Product.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(briefdesc__icontains=query)
        ).values_list('name', 'id', 'price', 'primary_image_id').distinct()[:8]
        
        for name, product_id, price, image_id in products:
            suggestions.append({
                'name': name,
                'id': product_id,
                'price': float(price),
            })
    
    return JsonResponse({'suggestions': suggestions})




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
        cart_items = list(cart.items.select_related("product"))

        if not cart_items:
            return JsonResponse({"error": "El carrito está vacío"}, status=400)

        active_reservation_ids = _get_active_reservation_ids_for_request(request)
        stock_issues = _get_cart_stock_issues(cart_items, exclude_reservation_ids=active_reservation_ids)
        if stock_issues:
            return JsonResponse({"error": _build_stock_issue_message(stock_issues[0])}, status=400)

        reservation, reservation_issues = _create_stock_reservation_for_cart(
            request,
            cart_items,
            StockReservation.PAYMENT_PAYPAL,
        )
        if reservation is None:
            return JsonResponse({"error": reservation_issues[0]}, status=400)

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
            request.session[STOCK_RESERVATION_SESSION_KEY] = reservation.id
            request.session[STOCK_RESERVATION_PAYMENT_SESSION_KEY] = StockReservation.PAYMENT_PAYPAL
            
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
            reservation = _get_session_stock_reservation(request, StockReservation.PAYMENT_PAYPAL)
            order, order_error = create_order_from_cart(
                request,
                Order.PAYMENT_PAYPAL,
                payment_id,
                shipping_address,
                stock_reservation=reservation,
            )

            if order is None:
                messages.error(request, order_error)
                return redirect("checkout")
            
            # Limpiar la sesión
            if 'paypal_payment_id' in request.session:
                del request.session['paypal_payment_id']
            if 'selected_shipping_address_id' in request.session:
                del request.session['selected_shipping_address_id']
            _clear_stock_reservation_session(request)

            messages.success(request, "¡Pago realizado correctamente con PayPal! Gracias por tu compra.")
            return render(request, "tienda/checkout_success.html", {"order": order})
        else:
            error_message = payment.error.get("message", "Error desconocido")
            messages.error(request, f"Error al procesar el pago: {error_message}")
            return redirect("checkout")

    except Exception as e:
        logger.exception("PAYPAL_EXECUTE_EXCEPTION user_id=%s error=%s", request.user.id, str(e))
        messages.error(request, f"Error: {str(e)}")
        return redirect("checkout")


# ==================== STRIPE PAYMENT INTENTS ====================

@login_required
@csrf_protect
def crear_payment_intent(request: HttpRequest):
    """
    Crea un Stripe PaymentIntent para el carrito actual.
    Acepta JSON: { shipping_address_id, saved_payment_method_id (opcional), save_card (bool) }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Cuerpo de la petición inválido"}, status=400)

    shipping_address = _get_selected_shipping_address(request)
    if shipping_address is None:
        return JsonResponse({"error": "Debes seleccionar una dirección de envío válida."}, status=400)

    cart = get_or_create_cart(request)
    cart_items = list(cart.items.select_related("product"))

    if not cart_items:
        return JsonResponse({"error": "El carrito está vacío"}, status=400)

    active_reservation_ids = _get_active_reservation_ids_for_request(request)
    stock_issues = _get_cart_stock_issues(cart_items, exclude_reservation_ids=active_reservation_ids)
    if stock_issues:
        return JsonResponse({"error": _build_stock_issue_message(stock_issues[0])}, status=400)

    reservation, reservation_issues = _create_stock_reservation_for_cart(
        request, cart_items, StockReservation.PAYMENT_STRIPE,
    )
    if reservation is None:
        return JsonResponse({"error": reservation_issues[0]}, status=400)

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY

        order_total = sum(
            get_price_with_vat_decimal(item.product.price) * item.quantity
            for item in cart_items
        )
        amount_cents = int(
            (order_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100
        )

        pi_params = {
            "amount": amount_cents,
            "currency": "eur",
            "automatic_payment_methods": {"enabled": False},
            "payment_method_types": ["card"],
        }

        # If using a saved card, attach customer + payment_method
        saved_pm_id = payload.get("saved_payment_method_id")
        if saved_pm_id:
            saved_pm = SavedPaymentMethod.objects.filter(
                id=saved_pm_id,
                user=request.user,
                method_type=SavedPaymentMethod.TYPE_CARD,
            ).first()
            if saved_pm is None:
                return JsonResponse({"error": "Método de pago no encontrado."}, status=400)
            pi_params["customer"] = saved_pm.stripe_customer_id
            pi_params["payment_method"] = saved_pm.stripe_payment_method_id

        payment_intent = stripe.PaymentIntent.create(**pi_params)

        request.session[STOCK_RESERVATION_SESSION_KEY] = reservation.id
        request.session[STOCK_RESERVATION_PAYMENT_SESSION_KEY] = StockReservation.PAYMENT_STRIPE
        request.session["selected_shipping_address_id"] = shipping_address.id
        request.session["stripe_save_card"] = bool(payload.get("save_card", False))

        return JsonResponse({
            "client_secret": payment_intent.client_secret,
            "payment_intent_id": payment_intent.id,
        })

    except Exception as e:
        logger.exception("CREATE_PAYMENT_INTENT_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": "Error al crear el pago. Por favor inténtalo de nuevo."}, status=500)


@login_required
@csrf_protect
def confirmar_pago_tarjeta(request: HttpRequest):
    """
    Verificar que el PaymentIntent fue exitoso y crear el pedido.
    Acepta JSON: { payment_intent_id, payment_method_id (si nueva tarjeta) }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Cuerpo de la petición inválido"}, status=400)

    payment_intent_id = payload.get("payment_intent_id")
    if not payment_intent_id:
        return JsonResponse({"error": "Falta el ID del intento de pago"}, status=400)

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    except Exception as e:
        logger.exception("RETRIEVE_PAYMENT_INTENT_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": "Error al verificar el pago"}, status=500)

    if payment_intent.status != "succeeded":
        return JsonResponse({"error": f"El pago no fue completado (estado: {payment_intent.status})"}, status=400)

    shipping_address_id = request.session.get("selected_shipping_address_id")
    shipping_address = ShippingAddress.objects.filter(id=shipping_address_id, user=request.user).first()
    reservation = _get_session_stock_reservation(request, StockReservation.PAYMENT_STRIPE)

    order, order_error = create_order_from_cart(
        request,
        Order.PAYMENT_STRIPE,
        payment_intent_id,
        shipping_address,
        stock_reservation=reservation,
    )

    if order is None:
        return JsonResponse({"error": order_error}, status=400)

    # Optionally save the card for future use
    save_card = request.session.pop("stripe_save_card", False)
    new_payment_method_id = payload.get("payment_method_id")
    if save_card and new_payment_method_id:
        try:
            customer_id = _get_or_create_stripe_customer(request.user)
            pm = stripe.PaymentMethod.retrieve(new_payment_method_id)
            stripe.PaymentMethod.attach(new_payment_method_id, customer=customer_id)
            card = pm.card
            label = f"{card.brand.capitalize()} •••• {card.last4}"
            SavedPaymentMethod.objects.create(
                user=request.user,
                method_type=SavedPaymentMethod.TYPE_CARD,
                label=label,
                stripe_customer_id=customer_id,
                stripe_payment_method_id=new_payment_method_id,
                is_default=not SavedPaymentMethod.objects.filter(user=request.user).exists(),
            )
        except Exception as e:
            logger.warning("SAVE_CARD_ERROR user_id=%s error=%s", request.user.id, str(e))

    if "selected_shipping_address_id" in request.session:
        del request.session["selected_shipping_address_id"]
    _clear_stock_reservation_session(request)

    return JsonResponse({"success": True, "order_id": order.id, "transaction_code": order.transaction_code})


# ==================== PAYPAL ORDERS API ====================

@login_required
@csrf_protect
def crear_orden_paypal(request: HttpRequest):
    """
    Crea una orden de PayPal con el total del carrito actual (Orders API v2).
    Acepta JSON: { shipping_address_id }
    Retorna: { id: paypal_order_id }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    shipping_address = _get_selected_shipping_address(request)
    if shipping_address is None:
        return JsonResponse({"error": "Debes seleccionar una dirección de envío válida."}, status=400)

    cart = get_or_create_cart(request)
    cart_items = list(cart.items.select_related("product"))

    if not cart_items:
        return JsonResponse({"error": "El carrito está vacío"}, status=400)

    active_reservation_ids = _get_active_reservation_ids_for_request(request)
    stock_issues = _get_cart_stock_issues(cart_items, exclude_reservation_ids=active_reservation_ids)
    if stock_issues:
        return JsonResponse({"error": _build_stock_issue_message(stock_issues[0])}, status=400)

    reservation, reservation_issues = _create_stock_reservation_for_cart(
        request, cart_items, StockReservation.PAYMENT_PAYPAL,
    )
    if reservation is None:
        return JsonResponse({"error": reservation_issues[0]}, status=400)

    try:
        order_total = sum(
            get_price_with_vat_decimal(item.product.price) * item.quantity
            for item in cart_items
        )
        order_total = order_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        paypal_order = _paypal_create_order(order_total)
        paypal_order_id = paypal_order.get("id")

        request.session["paypal_order_id"] = paypal_order_id
        request.session["selected_shipping_address_id"] = shipping_address.id
        request.session[STOCK_RESERVATION_SESSION_KEY] = reservation.id
        request.session[STOCK_RESERVATION_PAYMENT_SESSION_KEY] = StockReservation.PAYMENT_PAYPAL

        return JsonResponse({"id": paypal_order_id})

    except Exception as e:
        logger.exception("CREAR_ORDEN_PAYPAL_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": "Error al crear la orden de PayPal. Por favor inténtalo de nuevo."}, status=500)


@login_required
@csrf_protect
def capturar_orden_paypal(request: HttpRequest):
    """
    Captura una orden de PayPal aprobada y crea el pedido en nuestra BD.
    Acepta JSON: { orderID }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Cuerpo de la petición inválido"}, status=400)

    paypal_order_id = payload.get("orderID")
    if not paypal_order_id:
        return JsonResponse({"error": "Falta el ID de la orden de PayPal"}, status=400)

    # Verify this order belongs to this session
    session_order_id = request.session.get("paypal_order_id")
    if session_order_id != paypal_order_id:
        logger.warning(
            "PAYPAL_ORDER_MISMATCH user_id=%s session=%s received=%s",
            request.user.id, session_order_id, paypal_order_id,
        )
        return JsonResponse({"error": "ID de orden inválido"}, status=400)

    try:
        capture_data = _paypal_capture_order(paypal_order_id)
    except Exception as e:
        logger.exception("CAPTURAR_ORDEN_PAYPAL_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": "Error al capturar el pago de PayPal. Por favor inténtalo de nuevo."}, status=500)

    capture_status = capture_data.get("status")
    if capture_status != "COMPLETED":
        return JsonResponse({"error": f"El pago de PayPal no fue completado (estado: {capture_status})"}, status=400)

    # Extract payer info to optionally save as payment method
    payer = capture_data.get("payer", {})
    payer_email = payer.get("email_address", "")
    payer_id = payer.get("payer_id", "")

    shipping_address_id = request.session.get("selected_shipping_address_id")
    shipping_address = ShippingAddress.objects.filter(id=shipping_address_id, user=request.user).first()
    reservation = _get_session_stock_reservation(request, StockReservation.PAYMENT_PAYPAL)

    order, order_error = create_order_from_cart(
        request,
        Order.PAYMENT_PAYPAL,
        paypal_order_id,
        shipping_address,
        stock_reservation=reservation,
    )

    if order is None:
        return JsonResponse({"error": order_error}, status=400)

    # Save payer info if they want to store the PayPal account (offered in the template)
    save_paypal = payload.get("save_paypal", False)
    if save_paypal and payer_email:
        already_saved = SavedPaymentMethod.objects.filter(
            user=request.user,
            method_type=SavedPaymentMethod.TYPE_PAYPAL,
            paypal_email=payer_email,
        ).exists()
        if not already_saved:
            SavedPaymentMethod.objects.create(
                user=request.user,
                method_type=SavedPaymentMethod.TYPE_PAYPAL,
                label=payer_email,
                paypal_email=payer_email,
                paypal_payer_id=payer_id,
                is_default=not SavedPaymentMethod.objects.filter(user=request.user).exists(),
            )

    if "paypal_order_id" in request.session:
        del request.session["paypal_order_id"]
    if "selected_shipping_address_id" in request.session:
        del request.session["selected_shipping_address_id"]
    _clear_stock_reservation_session(request)

    return JsonResponse({
        "success": True,
        "order_id": order.id,
        "transaction_code": order.transaction_code,
        "payer_email": payer_email,
    })


# ==================== MÉTODOS DE PAGO DEL USUARIO ====================

@login_required
def metodos_pago(request: HttpRequest):
    """Lista los métodos de pago guardados del usuario."""
    metodos = SavedPaymentMethod.objects.filter(user=request.user)
    return render(request, "tienda/metodos_pago.html", {
        "metodos": metodos,
        "cards_exist": metodos.filter(method_type=SavedPaymentMethod.TYPE_CARD).exists(),
        "paypal_exist": metodos.filter(method_type=SavedPaymentMethod.TYPE_PAYPAL).exists(),
    })


@login_required
def agregar_tarjeta(request: HttpRequest):
    """Página para añadir una nueva tarjeta usando Stripe SetupIntent."""
    return render(request, "tienda/agregar_tarjeta.html", {
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
@csrf_protect
def crear_setup_intent(request: HttpRequest):
    """
    Crea un Stripe SetupIntent y retorna el client_secret para que el frontend
    pueda montar el Card Element y confirmar sin realizar un cobro.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        customer_id = _get_or_create_stripe_customer(request.user)
        setup_intent = stripe.SetupIntent.create(
            customer=customer_id,
            payment_method_types=["card"],
        )
        return JsonResponse({
            "client_secret": setup_intent.client_secret,
            "customer_id": customer_id,
        })
    except Exception as e:
        logger.exception("CREATE_SETUP_INTENT_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": "Error al iniciar el proceso de configuración. Por favor inténtalo de nuevo."}, status=500)


@login_required
@csrf_protect
def confirmar_setup_intent(request: HttpRequest):
    """
    Tras la confirmación del SetupIntent en el frontend, guarda la tarjeta.
    Acepta JSON: { payment_method_id, setup_intent_id }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Cuerpo de la petición inválido"}, status=400)

    payment_method_id = payload.get("payment_method_id")
    if not payment_method_id:
        return JsonResponse({"error": "Falta el ID del método de pago"}, status=400)

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        customer_id = _get_or_create_stripe_customer(request.user)

        # Attach the PaymentMethod to the customer
        try:
            stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        except stripe.error.InvalidRequestError as attach_err:
            # The payment method may already be attached to a customer
            pm_check = stripe.PaymentMethod.retrieve(payment_method_id)
            if pm_check.get("customer") == customer_id:
                # Already attached to this same customer – continue normally
                pass
            else:
                logger.warning(
                    "CONFIRMAR_SETUP_INTENT_ALREADY_ATTACHED user_id=%s pm=%s error=%s",
                    request.user.id, payment_method_id, str(attach_err),
                )
                return JsonResponse(
                    {"error": "Este método de pago ya está asociado a otra cuenta. "
                              "Por favor, usa una tarjeta diferente."},
                    status=400,
                )

        pm = stripe.PaymentMethod.retrieve(payment_method_id)
        card = pm.card
        label = f"{card.brand.capitalize()} •••• {card.last4} (exp. {card.exp_month:02d}/{card.exp_year})"

        # Avoid saving duplicates in our database
        existing = SavedPaymentMethod.objects.filter(
            user=request.user,
            stripe_payment_method_id=payment_method_id,
        ).first()
        if existing:
            return JsonResponse({"success": True, "label": existing.label, "id": existing.id})

        has_existing = SavedPaymentMethod.objects.filter(user=request.user).exists()
        saved = SavedPaymentMethod.objects.create(
            user=request.user,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label=label,
            stripe_customer_id=customer_id,
            stripe_payment_method_id=payment_method_id,
            is_default=not has_existing,
        )

        return JsonResponse({"success": True, "label": label, "id": saved.id})

    except Exception as e:
        logger.exception("CONFIRMAR_SETUP_INTENT_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": "Error al guardar la tarjeta. Por favor inténtalo de nuevo."}, status=500)


@login_required
def eliminar_metodo_pago(request: HttpRequest, id: int):
    """Elimina un método de pago guardado del usuario."""
    if request.method != "POST":
        messages.error(request, "Acción no permitida.")
        return redirect("metodos_pago")

    metodo = get_object_or_404(SavedPaymentMethod, id=id, user=request.user)

    # If it's a Stripe card, detach from Stripe too
    if metodo.method_type == SavedPaymentMethod.TYPE_CARD and metodo.stripe_payment_method_id:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.PaymentMethod.detach(metodo.stripe_payment_method_id)
        except Exception as e:
            logger.warning("DETACH_PAYMENT_METHOD_ERROR user_id=%s error=%s", request.user.id, str(e))

    metodo.delete()
    messages.success(request, "Método de pago eliminado correctamente.")
    return redirect("metodos_pago")


@login_required
def agregar_paypal(request: HttpRequest):
    """Página para guardar una cuenta de PayPal como método de pago (usa un pago de verificación de 0.01 €)."""
    return render(request, "tienda/agregar_paypal.html", {
        "paypal_client_id": settings.PAYPAL_CLIENT_ID,
    })


@login_required
@csrf_protect
def crear_orden_paypal_setup(request: HttpRequest):
    """
    Crea una orden PayPal de 0.01 € para verificar/guardar la cuenta.
    Retorna { id: paypal_order_id }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    try:
        paypal_order = _paypal_create_order(Decimal("0.01"))
        return JsonResponse({"id": paypal_order.get("id")})
    except Exception as e:
        logger.exception("CREAR_ORDEN_PAYPAL_SETUP_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": "Error al iniciar la verificación de PayPal. Por favor inténtalo de nuevo."}, status=500)


@login_required
@csrf_protect
def capturar_orden_paypal_setup(request: HttpRequest):
    """
    Captura la orden de verificación de PayPal y guarda la cuenta del usuario.
    Acepta JSON: { orderID }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Cuerpo de la petición inválido"}, status=400)

    paypal_order_id = payload.get("orderID")
    if not paypal_order_id:
        return JsonResponse({"error": "Falta el ID de la orden"}, status=400)

    try:
        capture_data = _paypal_capture_order(paypal_order_id)
    except Exception as e:
        logger.exception("CAPTURAR_PAYPAL_SETUP_ERROR user_id=%s error=%s", request.user.id, str(e))
        return JsonResponse({"error": "Error al verificar la cuenta de PayPal. Por favor inténtalo de nuevo."}, status=500)

    if capture_data.get("status") != "COMPLETED":
        return JsonResponse({"error": "No se pudo verificar la cuenta de PayPal"}, status=400)

    payer = capture_data.get("payer", {})
    payer_email = payer.get("email_address", "")
    payer_id = payer.get("payer_id", "")

    if not payer_email:
        return JsonResponse({"error": "No se pudo obtener el email de PayPal"}, status=400)

    already_saved = SavedPaymentMethod.objects.filter(
        user=request.user,
        method_type=SavedPaymentMethod.TYPE_PAYPAL,
        paypal_email=payer_email,
    ).exists()

    if not already_saved:
        has_existing = SavedPaymentMethod.objects.filter(user=request.user).exists()
        SavedPaymentMethod.objects.create(
            user=request.user,
            method_type=SavedPaymentMethod.TYPE_PAYPAL,
            label=payer_email,
            paypal_email=payer_email,
            paypal_payer_id=payer_id,
            is_default=not has_existing,
        )
        return JsonResponse({"success": True, "email": payer_email, "already_existed": False})
    else:
        return JsonResponse({"success": True, "email": payer_email, "already_existed": True})


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
        form = EditProfileForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            
            if email != request.user.email and User.objects.filter(email=email).exists():
                messages.error(request, "Ya existe un usuario con este correo electrónico.")
                return render(request, "tienda/editar_perfil.html", {"form": form})
            
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            request.user.email = email
            request.user.save()
            
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("portal_usuario")
    else:
        initial = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
        }
        form = EditProfileForm(initial=initial)
    
    return render(request, "tienda/editar_perfil.html", {"form": form})


@login_required
def cambiar_contrasena(request: HttpRequest):
    """Cambia la contraseña del usuario"""
    if request.method == "POST":
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data["current_password"]
            new_password = form.cleaned_data["new_password"]
            
            if not request.user.check_password(current_password):
                messages.error(request, "La contraseña actual es incorrecta.")
                return render(request, "tienda/editar_perfil.html", {"password_form": ChangePasswordForm()})
            
            if len(new_password) < 8:
                messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
                return render(request, "tienda/editar_perfil.html", {"password_form": ChangePasswordForm()})
            
            request.user.set_password(new_password)
            request.user.save()
            
            auth_login(request, request.user)
            
            messages.success(request, "Contraseña actualizada correctamente.")
            return redirect("portal_usuario")
        else:
            messages.error(request, "Las contraseñas nuevas no coinciden o son inválidas.")
            return render(request, "tienda/editar_perfil.html", {"password_form": form})
    
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
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            city = form.cleaned_data["city"]
            postal_code = form.cleaned_data["postal_code"]
            
            if not _is_almeria_city(city):
                messages.error(request, "El pueblo/ciudad debe pertenecer a la provincia de Almería.")
                return render(request, "tienda/editar_direccion.html", _address_form_context(form=form))

            if not _is_almeria_postal_code(postal_code):
                messages.error(request, "Solo realizamos envíos en la provincia de Almería (código postal 04xxx).")
                return render(request, "tienda/editar_direccion.html", _address_form_context(form=form))
            
            ShippingAddress.objects.create(
                user=request.user,
                full_name=form.cleaned_data["full_name"],
                address_line_1=form.cleaned_data["address_line_1"],
                address_line_2=form.cleaned_data.get("address_line_2", "") or "",
                city=city,
                postal_code=postal_code,
                country=SHIPPING_COUNTRY,
                phone=form.cleaned_data["phone"],
                is_default=form.cleaned_data.get("is_default", False)
            )
            
            messages.success(request, "Dirección creada correctamente.")
            return redirect("direcciones_usuario")
        else:
            messages.error(request, "Por favor completa todos los campos obligatorios.")
    else:
        form = ShippingAddressForm()
    
    return render(request, "tienda/editar_direccion.html", _address_form_context(form=form))


@login_required
def editar_direccion(request: HttpRequest, id: int):
    """Edita una dirección de entrega existente"""
    direccion = get_object_or_404(ShippingAddress, id=id, user=request.user)
    
    if request.method == "POST":
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            city = form.cleaned_data["city"]
            postal_code = form.cleaned_data["postal_code"]
            
            if not _is_almeria_city(city):
                messages.error(request, "El pueblo/ciudad debe pertenece a la provincia de Almería.")
                return render(request, "tienda/editar_direccion.html", _address_form_context(direccion, form=form))

            if not _is_almeria_postal_code(postal_code):
                messages.error(request, "Solo realizamos envíos en la provincia de Almería (código postal 04xxx).")
                return render(request, "tienda/editar_direccion.html", _address_form_context(direccion, form=form))
            
            direccion.full_name = form.cleaned_data["full_name"]
            direccion.address_line_1 = form.cleaned_data["address_line_1"]
            direccion.address_line_2 = form.cleaned_data.get("address_line_2", "") or ""
            direccion.city = city
            direccion.postal_code = postal_code
            direccion.country = SHIPPING_COUNTRY
            direccion.phone = form.cleaned_data["phone"]
            direccion.is_default = form.cleaned_data.get("is_default", False)
            
            direccion.save()
            messages.success(request, "Dirección actualizada correctamente.")
            return redirect("direcciones_usuario")
        else:
            messages.error(request, "Por favor completa todos los campos obligatorios.")
    else:
        initial = {
            "full_name": direccion.full_name,
            "address_line_1": direccion.address_line_1,
            "address_line_2": direccion.address_line_2,
            "city": direccion.city,
            "postal_code": direccion.postal_code,
            "country": direccion.country,
            "phone": direccion.phone,
            "is_default": direccion.is_default,
        }
        form = ShippingAddressForm(initial=initial)
    
    return render(request, "tienda/editar_direccion.html", _address_form_context(direccion, form=form))


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


def rgpd(request: HttpRequest):
    return render(request, "tienda/rgpd.html", {})

def devoluciones(request: HttpRequest):
    return render(request, "tienda/devoluciones.html", {})

def aviso_legal(request: HttpRequest):
    return render(request, "tienda/aviso_legal.html", {})

def terminos(request: HttpRequest):
    return render(request, "tienda/terminos.html", {})

def cookies(request: HttpRequest):
    return render(request, "tienda/cookies.html", {})

def sobre_nosotros(request: HttpRequest):
    return render(request, "tienda/sobre_nosotros.html", {})

def ayuda(request: HttpRequest):
    return render(request, "tienda/ayuda.html", {})

def reset_password(request: HttpRequest):
    if request.method == "GET":
        form = ResetPasswordForm()
        return render(request, "tienda/reset_password.html", {"form": form})
    else:
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            tasks.enviar_correo_recuperacion.delay(form.cleaned_data["email"])
            messages.info(request, "Si tienes una cuenta con ese correo electronico, se ha enviado un correo con un enlace")
        return render(request, "tienda/index.html", {})
    
def reset_password_phase2(request: HttpRequest, code: str):
    try:
        ver_code = VerificationCode.objects.get(code=code)
    except VerificationCode.DoesNotExist:
        raise Http404()
    
    if ver_code.code_mode != VerificationCode.VerificationModes.RESET_PASSWORD: raise Http404()


    if request.method == "GET":
        form = ResetPasswordPhase2Form()
        return render(request, "tienda/reset_password_phase2.html", {"form": form, "code": code})
    elif request.method == "POST":
        form = ResetPasswordPhase2Form(request.POST)
        if form.is_valid():
            user = ver_code.user
            user.set_password(form.cleaned_data["password"])
            user.save()
            ver_code.delete()
            messages.success(request, "Se ha cambiado la contraseña!")
            return redirect(reverse("index"))
        else:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, "tienda/reset_password_phase2.html", {"form": form, "code": code})
    else:
        raise Http404()
