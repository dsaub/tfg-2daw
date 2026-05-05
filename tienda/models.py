from __future__ import annotations

import unicodedata
from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.utils.crypto import get_random_string
from .vars import VAT_RATE, TRANSACTION_CODE_PREFIX, TRANSACTION_CODE_LENGTH, TRANSACTION_CODE_ALPHABET
import random, string


def generate_transaction_code() -> str:
    while True:
        code = f"{TRANSACTION_CODE_PREFIX}{get_random_string(TRANSACTION_CODE_LENGTH, TRANSACTION_CODE_ALPHABET)}"
        if not Order.objects.filter(transaction_code=code).exists():
            return code


class User(AbstractUser):
    class RegisterStatus(models.TextChoices):
        CONFIRMATION_REQUIRED = "CR", "Confirmation Required"
        ACTIVE = "AC", "Active"
        BANNED = "BN", "Banned"
    
    registration_status = models.CharField(
        max_length = 2,
        choices = RegisterStatus.choices,
        default = RegisterStatus.CONFIRMATION_REQUIRED
    )
    def to_dict(self):
        return {
            "username": self.username,
            "fullname": self.get_full_name()
        }

class VerificationCode(models.Model):
    class VerificationModes(models.TextChoices):
        VERIFY_ACCOUNT = "VA"
        RESET_PASSWORD = "RP"
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_belongsto", null=False, blank=False)
    code = models.CharField(max_length=64, default="", unique=True)
    code_mode = models.CharField(
        max_length=2,
        choices = VerificationModes.choices,
        default = VerificationModes.VERIFY_ACCOUNT   
    )
    
    def generate(user: User, code_mode: str) -> VerificationCode:
        while True:
            code = "".join(random.choices(string.ascii_letters+string.digits, k=64))
            if not VerificationCode.objects.filter(code=code).exists():
                return VerificationCode.objects.create(
                    code = code,
                    user = user,
                    code_mode = code_mode
                )

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name
    
    def to_dict(self):
        return {
            "name": self.name
        }

class Image(models.Model):
    name = models.CharField(max_length=200, default="")
    image = models.ImageField(upload_to='images/')
    alt = models.CharField(max_length=255, default="", blank=True, verbose_name="Texto alternativo")

    def __str__(self):
        return self.name
    
    def to_dict(self):
        return {
            "name": self.name,
            "image": self.image.url,
            "alt": self.alt
        }

class Product(models.Model):
    name = models.CharField(max_length=200, default="")
    description = models.TextField(default = "")
    briefdesc = models.TextField(default = "")
    price = models.FloatField(default = 0)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    primary_image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)
    secondary_images = models.ManyToManyField(Image, related_name='products_secondary', blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_products', null=True, blank=True)
    
    def __str__(self):
        return self.name + " " + str(self.price)
    
    def get_price_with_vat(self):
        """Retorna el precio con IVA incluido"""
        return round(self.price * (1 + VAT_RATE), 2)
    
    def get_vat_amount(self):
        """Retorna la cantidad de IVA"""
        return round(self.price * VAT_RATE, 2)
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "briefdesc": self.briefdesc,
            "price": self.price,
            "stock": self.stock,
            "category": self.category.to_dict(),
            "primary_image": self.primary_image.to_dict() if self.primary_image else None,
            "secondary_images": [secondary_image.to_dict() for secondary_image in self.secondary_images.all()],
            "creator": self.creator.to_dict() if self.creator else None
        }


class StockReservation(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Activa"),
        (STATUS_COMPLETED, "Completada"),
        (STATUS_CANCELLED, "Cancelada"),
        (STATUS_EXPIRED, "Expirada"),
    ]

    PAYMENT_STRIPE = "stripe"
    PAYMENT_PAYPAL = "paypal"
    PAYMENT_CHOICES = [
        (PAYMENT_STRIPE, "Stripe"),
        (PAYMENT_PAYPAL, "PayPal"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="stock_reservations")
    session_key = models.CharField(max_length=40, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reserva {self.id} - {self.user or self.session_key} ({self.status})"


class StockReservationItem(models.Model):
    reservation = models.ForeignKey(StockReservation, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_reservation_items")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("reservation", "product")

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (reserva {self.reservation_id})"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart {self.id} - {self.user or self.session_key}"
    
    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())
    
    def get_total_with_vat(self):
        """Retorna el total del carrito con IVA incluido"""
        return round(self.get_total() * (1 + VAT_RATE), 2)
    
    def get_vat_amount(self):
        """Retorna la cantidad total de IVA"""
        return round(self.get_total() * VAT_RATE, 2)
    
    def get_items_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    def get_subtotal(self):
        return self.product.price * self.quantity
    
    def get_subtotal_with_vat(self):
        """Retorna el subtotal del item con IVA incluido"""
        return round(self.get_subtotal() * (1 + VAT_RATE), 2)
    
    def get_vat_amount(self):
        """Retorna la cantidad de IVA de este item"""
        return round(self.get_subtotal() * VAT_RATE, 2)


class Order(models.Model):
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PAID, "Pagado"),
        (STATUS_CANCELLED, "Cancelado"),
    ]

    PAYMENT_STRIPE = "stripe"
    PAYMENT_PAYPAL = "paypal"
    PAYMENT_MANUAL = "manual"
    PAYMENT_CHOICES = [
        (PAYMENT_STRIPE, "Stripe"),
        (PAYMENT_PAYPAL, "PayPal"),
        (PAYMENT_MANUAL, "Manual"),
    ]

    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    shipping_address = models.ForeignKey('ShippingAddress', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    total = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PAID)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_MANUAL)
    payment_reference = models.CharField(max_length=200, blank=True, default="")
    transaction_code = models.CharField(max_length=38, unique=True, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.buyer or self.session_key}"

    def save(self, *args, **kwargs):
        if not self.transaction_code:
            self.transaction_code = generate_transaction_code()
        super().save(*args, **kwargs)

    def get_items_count(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_PROCESSING, "En preparación"),
        (STATUS_SHIPPED, "Enviado"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200, default="")
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items_to_fulfill')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.FloatField(default=0)
    total_price = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} (Pedido {self.order_id})"


class OrderMessage(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Mensaje de {self.sender} - {self.created_at}"


class SavedPaymentMethod(models.Model):
    """Métodos de pago guardados por el usuario (tarjetas Stripe o cuentas PayPal)."""
    TYPE_CARD = "card"
    TYPE_PAYPAL = "paypal"
    TYPE_CHOICES = [
        (TYPE_CARD, "Tarjeta"),
        (TYPE_PAYPAL, "PayPal"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_methods")
    method_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    label = models.CharField(max_length=200, verbose_name="Etiqueta")
    # Stripe fields
    stripe_customer_id = models.CharField(max_length=100, blank=True, default="")
    stripe_payment_method_id = models.CharField(max_length=100, blank=True, default="")
    # PayPal fields
    paypal_email = models.CharField(max_length=254, blank=True, default="")
    paypal_payer_id = models.CharField(max_length=100, blank=True, default="")
    is_default = models.BooleanField(default=False, verbose_name="Predeterminado")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Método de pago guardado"
        verbose_name_plural = "Métodos de pago guardados"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.user.username} – {self.label}"

    def save(self, *args, **kwargs):
        if self.is_default:
            SavedPaymentMethod.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class ShippingAddress(models.Model):
    """Direcciones de entrega de los usuarios"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    full_name = models.CharField(max_length=200, verbose_name="Nombre completo")
    address_line_1 = models.CharField(max_length=250, verbose_name="Dirección")
    address_line_2 = models.CharField(max_length=250, blank=True, verbose_name="Dirección (línea 2)")
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    postal_code = models.CharField(max_length=20, verbose_name="Código postal")
    country = models.CharField(max_length=100, default="España", verbose_name="País")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    is_default = models.BooleanField(default=False, verbose_name="Dirección predeterminada")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dirección de envío"
        verbose_name_plural = "Direcciones de envío"
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.city}"

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.conf import settings

        postal_code = (self.postal_code or "").strip()
        city = (self.city or "").strip()

        if settings.POSTGRES_ENABLED:
            almeria_prefix = "04"
        else:
            from .vars import ALMERIA_POSTAL_CODE_PREFIX
            almeria_prefix = ALMERIA_POSTAL_CODE_PREFIX

        if len(postal_code) != 5 or not postal_code.isdigit() or not postal_code.startswith(almeria_prefix):
            raise ValidationError({
                'postal_code': 'Solo realizamos envíos en la provincia de Almería (código postal 04xxx).'
            })

        if settings.POSTGRES_ENABLED:
            from .vars import ALMERIA_MUNICIPALITIES_DISPLAY
            normalized_municipalities = {
                unicodedata.normalize("NFD", m).encode('ASCII', 'ignore').decode('ASCII')
                .lower().replace("-", " ").replace("  ", " ").strip()
                for m in ALMERIA_MUNICIPALITIES_DISPLAY
            }
            normalized_city = unicodedata.normalize("NFD", city).encode('ASCII', 'ignore').decode('ASCII').lower()
        else:
            from .views import _normalize_location_text
            normalized_city = _normalize_location_text(city)

            from .vars import ALMERIA_MUNICIPALITIES_DISPLAY
            normalized_municipalities = {_normalize_location_text(m) for m in ALMERIA_MUNICIPALITIES_DISPLAY}

        if normalized_city not in normalized_municipalities:
            raise ValidationError({
                'city': 'El pueblo/ciudad debe pertenecer a la provincia de Almería.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_default:
            ShippingAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
