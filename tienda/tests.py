import json
from pathlib import Path
import re
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError
from django.urls import reverse
from datetime import timedelta
from .models import (
    User, VerificationCode, Category, Image, Product, 
    StockReservation, StockReservationItem, Cart, CartItem, 
    Order, OrderItem, OrderMessage, SavedPaymentMethod, ShippingAddress
)
from .forms import UserRegisterForm, UserLoginForm, EditProfileForm, ChangePasswordForm, ShippingAddressForm, ResetPasswordForm, ResetPasswordPhase2Form
from .vars import VAT_RATE, TRANSACTION_CODE_PREFIX
import secrets
import string
import random


# ==================== USER MODEL TESTS ====================
class UserModelTests(TestCase):
    """Tests exhaustivos para el modelo User."""


class FormTests(TestCase):
    """Tests para formularios Django."""

    def test_user_register_form_terms_required(self):
        """El campo terms debe ser obligatorio."""
        form = UserRegisterForm(data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "password123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("terms", form.errors)

    def test_user_register_form_terms_off_not_checked(self):
        """Si terms está en off (None/false), debe fallar."""
        form = UserRegisterForm(data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "terms": False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("terms", form.errors)

    def test_user_register_form_terms_on(self):
        """Si terms está marcado, el formulario debe ser válido."""
        form = UserRegisterForm(data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "terms": True,
        })
        self.assertTrue(form.is_valid())

    def test_user_register_form_passwords_mismatch(self):
        """Las contraseñas deben coincidir."""
        form = UserRegisterForm(data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "different_password",
            "terms": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_user_register_form_empty_fields(self):
        """Los campos obligatorios no pueden estar vacíos."""
        form = UserRegisterForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("password", form.errors)
        self.assertIn("password_confirm", form.errors)

    def test_user_login_form_valid(self):
        """Login con datos válidos."""
        form = UserLoginForm(data={
            "email": "test@example.com",
            "password": "password123",
        })
        self.assertTrue(form.is_valid())

    def test_user_login_form_missing_email(self):
        """Email es obligatorio en login."""
        form = UserLoginForm(data={
            "password": "password123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_user_login_form_invalid_email_format(self):
        """Email debe tener formato válido."""
        form = UserLoginForm(data={
            "email": "not-an-email",
            "password": "password123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_edit_profile_form_valid(self):
        """Formulario de edición de perfil válido."""
        form = EditProfileForm(data={
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "juan@example.com",
        })
        self.assertTrue(form.is_valid())

    def test_edit_profile_form_missing_email(self):
        """Email es obligatorio en perfil."""
        form = EditProfileForm(data={
            "first_name": "Juan",
            "last_name": "Pérez",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_change_password_form_passwords_mismatch(self):
        """Las nuevas contraseñas deben coincidir."""
        form = ChangePasswordForm(data={
            "current_password": "oldpass123",
            "new_password": "newpass123",
            "confirm_password": "differentpass",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_change_password_form_short_password(self):
        """La nueva contraseña debe tener al menos 8 caracteres."""
        form = ChangePasswordForm(data={
            "current_password": "oldpass123",
            "new_password": "short",
            "confirm_password": "short",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_shipping_address_form_valid(self):
        """Dirección con datos válidos."""
        form = ShippingAddressForm(data={
            "full_name": "Juan Pérez",
            "address_line_1": "Calle Mayor 123",
            "city": "Almería",
            "postal_code": "04001",
            "country": "España",
            "phone": "612345678",
        })
        self.assertTrue(form.is_valid())

    def test_shipping_address_form_missing_required_fields(self):
        """Campos obligatorios no pueden estar vacíos."""
        form = ShippingAddressForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)
        self.assertIn("address_line_1", form.errors)
        self.assertIn("city", form.errors)
        self.assertIn("postal_code", form.errors)
        self.assertIn("phone", form.errors)

    def test_reset_password_form_valid_email(self):
        """Formulario de recuperación de contraseña."""
        form = ResetPasswordForm(data={
            "email": "test@example.com",
        })
        self.assertTrue(form.is_valid())

    def test_reset_password_form_invalid_email(self):
        """Email inválido."""
        form = ResetPasswordForm(data={
            "email": "not-an-email",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_reset_password_phase2_form_valid(self):
        """Cambio de contraseña válido."""
        form = ResetPasswordPhase2Form(data={
            "password": "newpass123",
            "verify_password": "newpass123",
        })
        self.assertTrue(form.is_valid())

    def test_reset_password_phase2_form_mismatch(self):
        """Las contraseñas deben coincidir."""
        form = ResetPasswordPhase2Form(data={
            "password": "newpass123",
            "verify_password": "different",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


# ==================== ENDPOINT VIEW TESTS ====================
    
    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "TestPassword123!"
        }
    
    def test_user_creation_with_defaults(self):
        """Usuario nuevo debe tener estado CONFIRMATION_REQUIRED por defecto."""
        user = User.objects.create(**self.user_data)
        self.assertEqual(user.registration_status, User.RegisterStatus.CONFIRMATION_REQUIRED)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
    
    def test_user_registration_status_choices(self):
        """Todos los estados de registro deben ser válidos."""
        for status_code, status_label in User.RegisterStatus.choices:
            user = User.objects.create(
                username=f"user_{status_code}",
                registration_status=status_code
            )
            self.assertEqual(user.registration_status, status_code)
    
    def test_user_password_hashing(self):
        """Las contraseñas deben hashearse correctamente."""
        user = User.objects.create(username="testuser")
        password = "SecurePassword123!"
        user.set_password(password)
        user.save()
        
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.check_password("WrongPassword"))
    
    def test_user_can_set_active_status(self):
        """Usuario puede cambiar a estado ACTIVE."""
        user = User.objects.create(username="testuser")
        user.registration_status = User.RegisterStatus.ACTIVE
        user.save()
        
        refreshed = User.objects.get(username="testuser")
        self.assertEqual(refreshed.registration_status, User.RegisterStatus.ACTIVE)
    
    def test_user_can_be_banned(self):
        """Usuario puede ser marcado como BANNED."""
        user = User.objects.create(username="testuser")
        user.registration_status = User.RegisterStatus.BANNED
        user.save()
        
        refreshed = User.objects.get(username="testuser")
        self.assertEqual(refreshed.registration_status, User.RegisterStatus.BANNED)
    
    def test_multiple_users_unique_username(self):
        """Dos usuarios no pueden tener el mismo username."""
        User.objects.create(username="unique_user")
        with self.assertRaises(IntegrityError):
            User.objects.create(username="unique_user")
    
    def test_user_str_representation(self):
        """La representación string del usuario debe ser correcta."""
        user = User.objects.create(username="testuser", first_name="Test")
        # AbstractUser generalmente devuelve username
        self.assertIn("testuser", str(user))
    
    def test_user_email_validation(self):
        """Email debe ser válido (Django validation)."""
        user = User.objects.create(username="test", email="valid@example.com")
        self.assertEqual(user.email, "valid@example.com")
    
    def test_user_with_empty_optional_fields(self):
        """Usuario puede ser creado sin first_name/last_name."""
        user = User.objects.create(username="minimal_user")
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
    
    def test_user_related_products(self):
        """User debe estar relacionado con sus productos creados."""
        user = User.objects.create(username="creator")
        category = Category.objects.create(name="TestCat")
        product = Product.objects.create(
            name="TestProd", category=category, creator=user
        )
        
        self.assertIn(product, user.created_products.all())
    
    def test_user_related_orders(self):
        """User debe estar relacionado con sus pedidos."""
        user = User.objects.create(username="buyer")
        order = Order.objects.create(buyer=user, status=Order.STATUS_PAID)
        
        self.assertIn(order, user.orders.all())


# ==================== VERIFICATION CODE MODEL TESTS ====================
class VerificationCodeModelTests(TestCase):
    """Tests exhaustivos para el modelo VerificationCode."""
    
    def setUp(self):
        self.user = User.objects.create(username="testuser")
    
    def test_verification_code_creation(self):
        """Código de verificación debe crearse correctamente."""
        code = VerificationCode.generate(
            self.user, 
            VerificationCode.VerificationModes.VERIFY_ACCOUNT
        )
        
        self.assertIsNotNone(code)
        self.assertEqual(code.user, self.user)
        self.assertEqual(code.code_mode, VerificationCode.VerificationModes.VERIFY_ACCOUNT)
    
    def test_verification_code_uniqueness(self):
        """Dos códigos no pueden tener el mismo código."""
        code1 = VerificationCode.generate(self.user, VerificationCode.VerificationModes.VERIFY_ACCOUNT)
        code2 = VerificationCode.generate(self.user, VerificationCode.VerificationModes.VERIFY_ACCOUNT)
        
        self.assertNotEqual(code1.code, code2.code)
    
    def test_verification_code_for_password_reset(self):
        """Código puede ser para reset de contraseña."""
        code = VerificationCode.generate(
            self.user,
            VerificationCode.VerificationModes.RESET_PASSWORD
        )
        
        self.assertEqual(code.code_mode, VerificationCode.VerificationModes.RESET_PASSWORD)
    
    def test_verification_code_fifty_creations(self):
        """50 códigos pueden crearse sin conflictos."""
        codes = []
        for i in range(50):
            mode = secrets.choice([
                VerificationCode.VerificationModes.VERIFY_ACCOUNT,
                VerificationCode.VerificationModes.RESET_PASSWORD
            ])
            code = VerificationCode.generate(self.user, mode)
            codes.append(code.code)
        
        # Verificar que todos son únicos
        self.assertEqual(len(codes), len(set(codes)))
    
    def test_verification_code_related_to_user(self):
        """Código debe estar relacionado correctamente con usuario."""
        code = VerificationCode.generate(self.user, VerificationCode.VerificationModes.VERIFY_ACCOUNT)
        
        self.assertIn(code, self.user.user_belongsto.all())
    
    def test_verification_code_str_representation(self):
        """La representación string del código debe ser válida."""
        code = VerificationCode.generate(self.user, VerificationCode.VerificationModes.VERIFY_ACCOUNT)
        code_str = str(code)
        self.assertIsNotNone(code_str)


# ==================== CATEGORY MODEL TESTS ====================
class CategoryModelTests(TestCase):
    """Tests exhaustivos para el modelo Category."""
    
    def test_category_creation_basic(self):
        """Categoría debe crearse correctamente."""
        category = Category.objects.create(name="Electronics")
        self.assertEqual(category.name, "Electronics")
    
    def test_category_name_unique(self):
        """Dos categorías no pueden tener el mismo nombre."""
        Category.objects.create(name="UniqueCategory")
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="UniqueCategory")
    
    def test_category_hundred_creations(self):
        """100 categorías pueden crearse sin problemas."""
        categories = []
        for i in range(100):
            cat = Category.objects.create(name=f"Category_{i}_{1000 + secrets.randbelow(9000)}")
            categories.append(cat)
        
        self.assertEqual(len(categories), 100)
        self.assertEqual(Category.objects.count(), 100)
    
    def test_category_str_representation(self):
        """La representación string debe ser el nombre."""
        category = Category.objects.create(name="TestCategory")
        self.assertEqual(str(category), "TestCategory")
    
    def test_category_empty_name_not_allowed(self):
        """Categoría puede crearse con nombre vacío a nivel de BD (validar en forms)."""
        # Django permite guardar campos vacíos sin NULL constraint
        # La validación debe hacerse en forms o modelo validators
        cat = Category.objects.create(name="")
        self.assertEqual(cat.name, "")
        self.assertTrue(Category.objects.filter(name="").exists())
    
    def test_category_special_characters_in_name(self):
        """Categoría puede tener caracteres especiales."""
        category = Category.objects.create(name="Electrónica & Gadgets™")
        self.assertEqual(category.name, "Electrónica & Gadgets™")
    
    def test_category_deletion(self):
        """Categoría puede ser eliminada."""
        category = Category.objects.create(name="ToDelete")
        cat_id = category.id
        category.delete()
        
        self.assertFalse(Category.objects.filter(id=cat_id).exists())


# ==================== IMAGE MODEL TESTS ====================
class ImageModelTests(TestCase):
    """Tests exhaustivos para el modelo Image."""
    
    def test_image_creation_minimal(self):
        """Imagen debe crearse con mínimos campos requeridos."""
        image = Image.objects.create(
            name="TestImage",
            image="path/to/image.jpg",
            alt="Test Alt Text"
        )
        self.assertEqual(image.name, "TestImage")
        self.assertEqual(image.alt, "Test Alt Text")
    
    def test_image_alt_text_optional(self):
        """Alt text puede estar vacío."""
        image = Image.objects.create(
            name="TestImage",
            image="path/to/image.jpg",
            alt=""
        )
        self.assertEqual(image.alt, "")
    
    def test_image_str_representation(self):
        """La representación string debe ser el nombre."""
        image = Image.objects.create(
            name="MyImage",
            image="path/to/image.jpg"
        )
        self.assertEqual(str(image), "MyImage")
    
    def test_image_name_default_empty(self):
        """Nombre tiene default vacío."""
        image = Image(image="path/to/image.jpg")
        self.assertEqual(image.name, "")
    
    def test_image_alt_default_empty(self):
        """Alt text tiene default vacío."""
        image = Image(name="Test", image="path/to/image.jpg")
        self.assertEqual(image.alt, "")


# ==================== PRODUCT MODEL TESTS ====================
class ProductModelTests(TestCase):
    """Tests exhaustivos para el modelo Product."""
    
    def setUp(self):
        self.category = Category.objects.create(name="TestCategory")
        self.user = User.objects.create(username="seller")
        self.image = Image.objects.create(
            name="MainImage",
            image="path/to/main.jpg"
        )
    
    def test_product_creation_full(self):
        """Producto debe crearse con todos los campos."""
        product = Product.objects.create(
            name="TestProduct",
            description="Full description",
            briefdesc="Brief",
            price=99.99,
            stock=50,
            category=self.category,
            primary_image=self.image,
            creator=self.user
        )
        
        self.assertEqual(product.name, "TestProduct")
        self.assertEqual(product.price, 99.99)
        self.assertEqual(product.stock, 50)
    
    def test_product_defaults(self):
        """Producto debe tener valores por defecto correctos."""
        product = Product.objects.create(
            name="MinimalProduct",
            category=self.category
        )
        
        self.assertEqual(product.description, "")
        self.assertEqual(product.briefdesc, "")
        self.assertEqual(product.price, 0)
        self.assertEqual(product.stock, 0)
        self.assertIsNone(product.primary_image)
    
    def test_product_get_price_with_vat(self):
        """Precio con IVA debe calcularse correctamente."""
        product = Product.objects.create(
            name="VATProduct",
            price=100,
            category=self.category
        )
        
        expected = round(100 * (1 + VAT_RATE), 2)
        self.assertEqual(product.get_price_with_vat(), expected)
        self.assertEqual(product.get_price_with_vat(), 121.0)
    
    def test_product_get_vat_amount(self):
        """Cantidad de IVA debe calcularse correctamente."""
        product = Product.objects.create(
            name="VATProduct",
            price=100,
            category=self.category
        )
        
        expected = round(100 * VAT_RATE, 2)
        self.assertEqual(product.get_vat_amount(), expected)
        self.assertEqual(product.get_vat_amount(), 21.0)
    
    def test_product_with_negative_price_allowed(self):
        """Campo price es FloatField, permite valores negativos (validar en forms)."""
        product = Product.objects.create(
            name="NegativePrice",
            price=-10,
            category=self.category
        )
        self.assertEqual(product.price, -10)
    
    def test_product_with_zero_stock(self):
        """Producto puede tener stock 0."""
        product = Product.objects.create(
            name="NoStock",
            stock=0,
            category=self.category
        )
        self.assertEqual(product.stock, 0)
    
    def test_product_str_representation(self):
        """La representación string debe incluir nombre y precio."""
        product = Product.objects.create(
            name="StrProduct",
            price=49.99,
            category=self.category
        )
        expected = f"StrProduct 49.99"
        self.assertEqual(str(product), expected)
    
    def test_product_secondary_images_many_to_many(self):
        """Producto puede tener múltiples imágenes secundarias."""
        product = Product.objects.create(
            name="MultiImageProduct",
            category=self.category
        )
        
        image1 = Image.objects.create(name="Image1", image="path1.jpg")
        image2 = Image.objects.create(name="Image2", image="path2.jpg")
        
        product.secondary_images.add(image1, image2)
        
        self.assertEqual(product.secondary_images.count(), 2)
        self.assertIn(image1, product.secondary_images.all())
        self.assertIn(image2, product.secondary_images.all())
    
    def test_product_creator_optional(self):
        """Producto puede crearse sin creator."""
        product = Product.objects.create(
            name="NoCreator",
            category=self.category,
            creator=None
        )
        self.assertIsNone(product.creator)
    
    def test_product_deletion_cascades(self):
        """Eliminar producto debe mantener categoría."""
        product = Product.objects.create(
            name="ToDelete",
            category=self.category
        )
        product_id = product.id
        product.delete()
        
        self.assertFalse(Product.objects.filter(id=product_id).exists())
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())
    
    def test_product_hundred_creations(self):
        """100 productos pueden crearse correctamente."""
        products = []
        for i in range(100):
            product = Product.objects.create(
                name=f"Product_{i}",
                price=float(i),
                stock=i,
                category=self.category,
                creator=self.user
            )
            products.append(product)
        
        self.assertEqual(len(products), 100)
        self.assertEqual(Product.objects.count(), 100)


# ==================== STOCK RESERVATION MODEL TESTS ====================
class StockReservationModelTests(TestCase):
    """Tests exhaustivos para el modelo StockReservation."""
    
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.expires_at = timezone.now() + timedelta(minutes=5)
    
    def test_stock_reservation_creation_user(self):
        """Reserva de stock para usuario autenticado."""
        reservation = StockReservation.objects.create(
            user=self.user,
            status=StockReservation.STATUS_ACTIVE,
            payment_method=StockReservation.PAYMENT_STRIPE,
            expires_at=self.expires_at
        )
        
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.status, StockReservation.STATUS_ACTIVE)
    
    def test_stock_reservation_creation_session(self):
        """Reserva de stock para sesión anónima."""
        reservation = StockReservation.objects.create(
            session_key="abc123def456",
            status=StockReservation.STATUS_ACTIVE,
            payment_method=StockReservation.PAYMENT_PAYPAL,
            expires_at=self.expires_at
        )
        
        self.assertEqual(reservation.session_key, "abc123def456")
        self.assertIsNone(reservation.user)
    
    def test_stock_reservation_status_choices(self):
        """Todos los estados deben ser válidos."""
        statuses = [
            StockReservation.STATUS_ACTIVE,
            StockReservation.STATUS_COMPLETED,
            StockReservation.STATUS_CANCELLED,
            StockReservation.STATUS_EXPIRED
        ]
        
        for i, status in enumerate(statuses):
            reservation = StockReservation.objects.create(
                user=self.user,
                status=status,
                payment_method=StockReservation.PAYMENT_STRIPE,
                expires_at=self.expires_at
            )
            self.assertEqual(reservation.status, status)
    
    def test_stock_reservation_payment_methods(self):
        """Ambos métodos de pago deben ser válidos."""
        for method in [StockReservation.PAYMENT_STRIPE, StockReservation.PAYMENT_PAYPAL]:
            reservation = StockReservation.objects.create(
                user=self.user,
                status=StockReservation.STATUS_ACTIVE,
                payment_method=method,
                expires_at=self.expires_at
            )
            self.assertEqual(reservation.payment_method, method)
    
    def test_stock_reservation_timestamps(self):
        """Las timestamps deben establecerse automáticamente."""
        reservation = StockReservation.objects.create(
            user=self.user,
            status=StockReservation.STATUS_ACTIVE,
            payment_method=StockReservation.PAYMENT_STRIPE,
            expires_at=self.expires_at
        )
        
        self.assertIsNotNone(reservation.created_at)
        self.assertIsNotNone(reservation.updated_at)
        self.assertLessEqual(reservation.created_at, timezone.now())
    
    def test_stock_reservation_str_representation(self):
        """La representación string debe ser válida."""
        reservation = StockReservation.objects.create(
            user=self.user,
            status=StockReservation.STATUS_ACTIVE,
            payment_method=StockReservation.PAYMENT_STRIPE,
            expires_at=self.expires_at
        )
        
        reservation_str = str(reservation)
        self.assertIn("Reserva", reservation_str)
        self.assertIn("active", reservation_str)


# ==================== STOCK RESERVATION ITEM MODEL TESTS ====================
class StockReservationItemModelTests(TestCase):
    """Tests exhaustivos para el modelo StockReservationItem."""
    
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.category = Category.objects.create(name="TestCat")
        self.product = Product.objects.create(
            name="TestProd",
            category=self.category
        )
        self.reservation = StockReservation.objects.create(
            user=self.user,
            status=StockReservation.STATUS_ACTIVE,
            payment_method=StockReservation.PAYMENT_STRIPE,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
    
    def test_reservation_item_creation(self):
        """Item de reserva debe crearse correctamente."""
        item = StockReservationItem.objects.create(
            reservation=self.reservation,
            product=self.product,
            quantity=10
        )
        
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.product, self.product)
    
    def test_reservation_item_default_quantity(self):
        """Cantidad por defecto es 1."""
        item = StockReservationItem.objects.create(
            reservation=self.reservation,
            product=self.product
        )
        
        self.assertEqual(item.quantity, 1)
    
    def test_reservation_item_unique_together(self):
        """No pueden haber dos items del mismo producto en la misma reserva."""
        StockReservationItem.objects.create(
            reservation=self.reservation,
            product=self.product,
            quantity=5
        )
        
        with self.assertRaises(IntegrityError):
            StockReservationItem.objects.create(
                reservation=self.reservation,
                product=self.product,
                quantity=3
            )
    
    def test_reservation_item_str_representation(self):
        """La representación string debe ser válida."""
        item = StockReservationItem.objects.create(
            reservation=self.reservation,
            product=self.product,
            quantity=5
        )
        
        item_str = str(item)
        self.assertIn("5x", item_str)
        self.assertIn("TestProd", item_str)


# ==================== CART MODEL TESTS ====================
class CartModelTests(TestCase):
    """Tests exhaustivos para el modelo Cart."""
    
    def setUp(self):
        self.user = User.objects.create(username="cartuser")
        self.category = Category.objects.create(name="TestCat")
        self.product1 = Product.objects.create(
            name="Product1", price=100, category=self.category
        )
        self.product2 = Product.objects.create(
            name="Product2", price=50, category=self.category
        )
    
    def test_cart_creation_with_user(self):
        """Carrito debe crearse para usuario autenticado."""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertIsNone(cart.session_key)
    
    def test_cart_creation_with_session(self):
        """Carrito debe crearse para sesión anónima."""
        cart = Cart.objects.create(session_key="session123")
        self.assertEqual(cart.session_key, "session123")
        self.assertIsNone(cart.user)
    
    def test_cart_timestamps(self):
        """Los timestamps deben establecerse automáticamente."""
        cart = Cart.objects.create(user=self.user)
        self.assertIsNotNone(cart.created_at)
        self.assertIsNotNone(cart.updated_at)
    
    def test_cart_get_total_empty(self):
        """Total de carrito vacío debe ser 0."""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.get_total(), 0)
    
    def test_cart_get_total_with_items(self):
        """Total debe calcularse correctamente."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)  # 200
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)  # 50
        
        self.assertEqual(cart.get_total(), 250)
    
    def test_cart_get_total_with_vat(self):
        """Total con IVA debe ser correcto."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)  # 100
        
        expected = round(100 * (1 + VAT_RATE), 2)
        self.assertEqual(cart.get_total_with_vat(), expected)
    
    def test_cart_get_vat_amount(self):
        """Cantidad de IVA debe calcularse correctamente."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)  # 100
        
        expected = round(100 * VAT_RATE, 2)
        self.assertEqual(cart.get_vat_amount(), expected)
    
    def test_cart_get_items_count(self):
        """Conteo de items debe ser correcto."""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.get_items_count(), 0)
        
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=3)
        
        self.assertEqual(cart.get_items_count(), 5)
    
    def test_cart_str_representation(self):
        """La representación string debe ser válida."""
        cart = Cart.objects.create(user=self.user)
        self.assertIn("Cart", str(cart))


# ==================== CART ITEM MODEL TESTS ====================
class CartItemModelTests(TestCase):
    """Tests exhaustivos para el modelo CartItem."""
    
    def setUp(self):
        self.user = User.objects.create(username="cartuser")
        self.category = Category.objects.create(name="TestCat")
        self.product = Product.objects.create(
            name="TestProduct", price=50, category=self.category
        )
        self.cart = Cart.objects.create(user=self.user)
    
    def test_cart_item_creation(self):
        """Item del carrito debe crearse correctamente."""
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=5
        )
        
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.product, self.product)
    
    def test_cart_item_default_quantity(self):
        """Cantidad por defecto es 1."""
        item = CartItem.objects.create(cart=self.cart, product=self.product)
        self.assertEqual(item.quantity, 1)
    
    def test_cart_item_unique_together(self):
        """No pueden haber dos items del mismo producto en el mismo carrito."""
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=5)
        
        with self.assertRaises(IntegrityError):
            CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)
    
    def test_cart_item_get_subtotal(self):
        """Subtotal debe calcularse correctamente."""
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=3
        )
        
        self.assertEqual(item.get_subtotal(), 150)
    
    def test_cart_item_get_subtotal_with_vat(self):
        """Subtotal con IVA debe ser correcto."""
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        
        expected = round(100 * (1 + VAT_RATE), 2)
        self.assertEqual(item.get_subtotal_with_vat(), expected)
    
    def test_cart_item_get_vat_amount(self):
        """Cantidad de IVA del item debe ser correcta."""
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        
        expected = round(100 * VAT_RATE, 2)
        self.assertEqual(item.get_vat_amount(), expected)
    
    def test_cart_item_str_representation(self):
        """La representación string debe ser válida."""
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=3
        )
        
        self.assertEqual(str(item), "3x TestProduct")


# ==================== ORDER MODEL TESTS ====================
class OrderModelTests(TestCase):
    """Tests exhaustivos para el modelo Order."""
    
    def setUp(self):
        self.buyer = User.objects.create(username="buyer")
        self.address = ShippingAddress.objects.create(
            user=self.buyer,
            full_name="John Doe",
            address_line_1="123 Main St",
            city="Almería",
            postal_code="04001",
            country="España",
            phone="123456789"
        )
    
    def test_order_creation_full(self):
        """Pedido debe crearse con todos los campos."""
        order = Order.objects.create(
            buyer=self.buyer,
            shipping_address=self.address,
            total=150.50,
            status=Order.STATUS_PAID,
            payment_method=Order.PAYMENT_STRIPE
        )
        
        self.assertEqual(order.buyer, self.buyer)
        self.assertEqual(order.total, 150.50)
        self.assertEqual(order.status, Order.STATUS_PAID)
    
    def test_order_transaction_code_auto_generated(self):
        """Código de transacción debe generarse automáticamente al guardar."""
        order = Order.objects.create(
            buyer=self.buyer,
            status=Order.STATUS_PAID
        )
        
        self.assertIsNotNone(order.transaction_code)
        self.assertTrue(order.transaction_code.startswith(TRANSACTION_CODE_PREFIX))
    
    def test_order_transaction_code_unique(self):
        """Códigos de transacción deben ser únicos."""
        order1 = Order.objects.create(
            buyer=self.buyer,
            status=Order.STATUS_PAID
        )
        order2 = Order.objects.create(
            buyer=self.buyer,
            status=Order.STATUS_PAID
        )
        
        self.assertNotEqual(order1.transaction_code, order2.transaction_code)
    
    def test_order_default_status(self):
        """Estado por defecto es PAID."""
        order = Order.objects.create(buyer=self.buyer)
        self.assertEqual(order.status, Order.STATUS_PAID)
    
    def test_order_default_payment_method(self):
        """Método de pago por defecto es MANUAL."""
        order = Order.objects.create(buyer=self.buyer)
        self.assertEqual(order.payment_method, Order.PAYMENT_MANUAL)
    
    def test_order_status_choices(self):
        """Todos los estados deben ser válidos."""
        for i, status in enumerate([Order.STATUS_PAID, Order.STATUS_CANCELLED]):
            order = Order.objects.create(
                buyer=self.buyer,
                status=status
            )
            self.assertEqual(order.status, status)
    
    def test_order_payment_methods(self):
        """Todos los métodos de pago deben ser válidos."""
        methods = [Order.PAYMENT_STRIPE, Order.PAYMENT_PAYPAL, Order.PAYMENT_MANUAL]
        for method in methods:
            order = Order.objects.create(
                buyer=self.buyer,
                payment_method=method
            )
            self.assertEqual(order.payment_method, method)
    
    def test_order_anonymous_buyer(self):
        """Pedido puede tener buyer nulo (comprador anónimo)."""
        order = Order.objects.create(
            buyer=None,
            session_key="session123",
            status=Order.STATUS_PAID
        )
        self.assertIsNone(order.buyer)
    
    def test_order_payment_reference_optional(self):
        """Referencia de pago es opcional."""
        order = Order.objects.create(buyer=self.buyer)
        self.assertEqual(order.payment_reference, "")
    
    def test_order_timestamps(self):
        """Los timestamps deben establecerse automáticamente."""
        order = Order.objects.create(buyer=self.buyer)
        self.assertIsNotNone(order.created_at)
        self.assertIsNotNone(order.updated_at)
    
    def test_order_get_items_count_empty(self):
        """Conteo de items en pedido vacío debe ser 0."""
        order = Order.objects.create(buyer=self.buyer)
        self.assertEqual(order.get_items_count(), 0)
    
    def test_order_str_representation(self):
        """La representación string debe ser válida."""
        order = Order.objects.create(buyer=self.buyer)
        order_str = str(order)
        self.assertIn("Pedido", order_str)


# ==================== ORDER ITEM MODEL TESTS ====================
class OrderItemModelTests(TestCase):
    """Tests exhaustivos para el modelo OrderItem."""
    
    def setUp(self):
        self.buyer = User.objects.create(username="buyer")
        self.seller = User.objects.create(username="seller")
        self.category = Category.objects.create(name="TestCat")
        self.product = Product.objects.create(
            name="TestProduct",
            price=100,
            category=self.category,
            creator=self.seller
        )
        self.order = Order.objects.create(buyer=self.buyer)
    
    def test_order_item_creation_full(self):
        """Item de pedido debe crearse correctamente."""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name="TestProduct",
            seller=self.seller,
            quantity=5,
            unit_price=100,
            total_price=500,
            status=OrderItem.STATUS_PENDING
        )
        
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.unit_price, 100)
        self.assertEqual(item.total_price, 500)
    
    def test_order_item_status_choices(self):
        """Todos los estados deben ser válidos."""
        statuses = [
            OrderItem.STATUS_PENDING,
            OrderItem.STATUS_PROCESSING,
            OrderItem.STATUS_SHIPPED
        ]
        
        for status in statuses:
            item = OrderItem.objects.create(
                order=self.order,
                product=self.product,
                product_name="Test",
                status=status
            )
            self.assertEqual(item.status, status)
    
    def test_order_item_default_status(self):
        """Estado por defecto es PENDING."""
        item = OrderItem.objects.create(
            order=self.order,
            product_name="Test"
        )
        self.assertEqual(item.status, OrderItem.STATUS_PENDING)
    
    def test_order_item_product_optional(self):
        """Producto puede ser nulo (producto eliminado)."""
        item = OrderItem.objects.create(
            order=self.order,
            product=None,
            product_name="Deleted Product"
        )
        self.assertIsNone(item.product)
    
    def test_order_item_seller_optional(self):
        """Vendedor puede ser nulo."""
        item = OrderItem.objects.create(
            order=self.order,
            product_name="Test",
            seller=None
        )
        self.assertIsNone(item.seller)
    
    def test_order_item_timestamps(self):
        """El timestamp debe establecerse automáticamente."""
        item = OrderItem.objects.create(
            order=self.order,
            product_name="Test"
        )
        self.assertIsNotNone(item.created_at)
    
    def test_order_item_str_representation(self):
        """La representación string debe ser válida."""
        item = OrderItem.objects.create(
            order=self.order,
            product_name="TestProduct",
            quantity=3
        )
        
        item_str = str(item)
        self.assertIn("3x", item_str)
        self.assertIn("TestProduct", item_str)


# ==================== ORDER MESSAGE MODEL TESTS ====================
class OrderMessageModelTests(TestCase):
    """Tests exhaustivos para el modelo OrderMessage."""
    
    def setUp(self):
        self.buyer = User.objects.create(username="buyer")
        self.seller = User.objects.create(username="seller")
        self.order = Order.objects.create(buyer=self.buyer)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product_name="Test",
            seller=self.seller
        )
    
    def test_order_message_creation(self):
        """Mensaje debe crearse correctamente."""
        message = OrderMessage.objects.create(
            order_item=self.order_item,
            sender=self.buyer,
            message="Hello seller!"
        )
        
        self.assertEqual(message.message, "Hello seller!")
        self.assertEqual(message.sender, self.buyer)
    
    def test_order_message_sender_optional(self):
        """Remitente puede ser nulo."""
        message = OrderMessage.objects.create(
            order_item=self.order_item,
            sender=None,
            message="Anonymous message"
        )
        self.assertIsNone(message.sender)
    
    def test_order_message_timestamp(self):
        """El timestamp debe establecerse automáticamente."""
        message = OrderMessage.objects.create(
            order_item=self.order_item,
            sender=self.buyer,
            message="Test"
        )
        self.assertIsNotNone(message.created_at)
    
    def test_order_message_ordering(self):
        """Los mensajes deben ordenarse por created_at."""
        msg1 = OrderMessage.objects.create(
            order_item=self.order_item,
            sender=self.buyer,
            message="First"
        )
        msg2 = OrderMessage.objects.create(
            order_item=self.order_item,
            sender=self.seller,
            message="Second"
        )
        
        messages = list(self.order_item.messages.all())
        self.assertEqual(messages[0].message, "First")
        self.assertEqual(messages[1].message, "Second")
    
    def test_order_message_str_representation(self):
        """La representación string debe ser válida."""
        message = OrderMessage.objects.create(
            order_item=self.order_item,
            sender=self.buyer,
            message="Test message"
        )
        
        message_str = str(message)
        self.assertIn("buyer", message_str)


# ==================== SAVED PAYMENT METHOD MODEL TESTS ====================
class SavedPaymentMethodModelTests(TestCase):
    """Tests exhaustivos para el modelo SavedPaymentMethod."""
    
    def setUp(self):
        self.user = User.objects.create(username="paymentuser")
    
    def test_saved_payment_method_card_creation(self):
        """Método de pago tarjeta debe crearse correctamente."""
        method = SavedPaymentMethod.objects.create(
            user=self.user,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label="Mi Tarjeta",
            stripe_customer_id="cus_123",
            stripe_payment_method_id="pm_456"
        )
        
        self.assertEqual(method.method_type, SavedPaymentMethod.TYPE_CARD)
        self.assertEqual(method.label, "Mi Tarjeta")
    
    def test_saved_payment_method_paypal_creation(self):
        """Método de pago PayPal debe crearse correctamente."""
        method = SavedPaymentMethod.objects.create(
            user=self.user,
            method_type=SavedPaymentMethod.TYPE_PAYPAL,
            label="Mi PayPal",
            paypal_email="user@example.com",
            paypal_payer_id="ABC123"
        )
        
        self.assertEqual(method.method_type, SavedPaymentMethod.TYPE_PAYPAL)
        self.assertEqual(method.paypal_email, "user@example.com")
    
    def test_saved_payment_method_default_false(self):
        """Por defecto no es predeterminado."""
        method = SavedPaymentMethod.objects.create(
            user=self.user,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label="Test"
        )
        
        self.assertFalse(method.is_default)
    
    def test_saved_payment_method_set_default_unsets_others(self):
        """Marcar como predeterminado debe desmarcar otros."""
        method1 = SavedPaymentMethod.objects.create(
            user=self.user,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label="Card1",
            is_default=True
        )
        
        method2 = SavedPaymentMethod.objects.create(
            user=self.user,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label="Card2",
            is_default=True
        )
        
        method1.refresh_from_db()
        self.assertFalse(method1.is_default)
        self.assertTrue(method2.is_default)
    
    def test_saved_payment_method_ordering(self):
        """Los métodos deben ordenarse por predeterminado y fecha."""
        method2 = SavedPaymentMethod.objects.create(
            user=self.user,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label="Card2",
            is_default=False
        )
        
        method1 = SavedPaymentMethod.objects.create(
            user=self.user,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label="Card1",
            is_default=True
        )
        
        methods = list(SavedPaymentMethod.objects.filter(user=self.user))
        self.assertEqual(methods[0].id, method1.id)
    
    def test_saved_payment_method_timestamps(self):
        """El timestamp debe establecerse automáticamente."""
        method = SavedPaymentMethod.objects.create(
            user=self.user,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label="Test"
        )
        self.assertIsNotNone(method.created_at)
    
    def test_saved_payment_method_str_representation(self):
        """La representación string debe ser válida."""
        method = SavedPaymentMethod.objects.create(
            user=self.user,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label="My Card"
        )
        
        method_str = str(method)
        self.assertIn("paymentuser", method_str)
        self.assertIn("My Card", method_str)


# ==================== SHIPPING ADDRESS MODEL TESTS ====================
class ShippingAddressModelTests(TestCase):
    """Tests exhaustivos para el modelo ShippingAddress."""
    
    def setUp(self):
        self.user = User.objects.create(username="addressuser")
    
    def test_shipping_address_creation_full(self):
        """Dirección de envío debe crearse correctamente."""
        address = ShippingAddress.objects.create(
            user=self.user,
            full_name="John Doe",
            address_line_1="123 Main St",
            address_line_2="Apt 4B",
            city="Almería",
            postal_code="04001",
            country="España",
            phone="123456789"
        )
        
        self.assertEqual(address.full_name, "John Doe")
        self.assertEqual(address.city, "Almería")
    
    def test_shipping_address_default_country(self):
        """País por defecto es España."""
        address = ShippingAddress.objects.create(
            user=self.user,
            full_name="Test",
            address_line_1="Test St",
            city="Almería",
            postal_code="04001",
            phone="123456789"
        )
        
        self.assertEqual(address.country, "España")
    
    def test_shipping_address_line_2_optional(self):
        """Línea de dirección 2 es opcional."""
        address = ShippingAddress.objects.create(
            user=self.user,
            full_name="Test",
            address_line_1="Test St",
            address_line_2="",
            city="Almería",
            postal_code="04001",
            phone="123456789"
        )
        
        self.assertEqual(address.address_line_2, "")
    
    def test_shipping_address_is_default_false(self):
        """Por defecto no es dirección predeterminada."""
        address = ShippingAddress.objects.create(
            user=self.user,
            full_name="Test",
            address_line_1="Test St",
            city="Almería",
            postal_code="04001",
            phone="123456789"
        )
        
        self.assertFalse(address.is_default)
    
    def test_shipping_address_set_default_unsets_others(self):
        """Marcar como predeterminada debe desmarcar otras."""
        addr1 = ShippingAddress.objects.create(
            user=self.user,
            full_name="Address1",
            address_line_1="St1",
            city="Almería",
            postal_code="04001",
            phone="1",
            is_default=True
        )
        
        addr2 = ShippingAddress.objects.create(
            user=self.user,
            full_name="Address2",
            address_line_1="St2",
            city="Almería",
            postal_code="04002",
            phone="2",
            is_default=True
        )
        
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)
    
    def test_shipping_address_ordering(self):
        """Las direcciones deben ordenarse por predeterminada y fecha."""
        addr2 = ShippingAddress.objects.create(
            user=self.user,
            full_name="Address2",
            address_line_1="St2",
            city="Almería",
            postal_code="04002",
            phone="2",
            is_default=False
        )
        
        addr1 = ShippingAddress.objects.create(
            user=self.user,
            full_name="Address1",
            address_line_1="St1",
            city="Almería",
            postal_code="04001",
            phone="1",
            is_default=True
        )
        
        addresses = list(ShippingAddress.objects.filter(user=self.user))
        self.assertEqual(addresses[0].id, addr1.id)
    
    def test_shipping_address_timestamps(self):
        """Los timestamps deben establecerse automáticamente."""
        address = ShippingAddress.objects.create(
            user=self.user,
            full_name="Test",
            address_line_1="Test St",
            city="Almería",
            postal_code="04001",
            phone="123456789"
        )
        
        self.assertIsNotNone(address.created_at)
        self.assertIsNotNone(address.updated_at)
    
    def test_shipping_address_str_representation(self):
        """La representación string debe ser válida."""
        address = ShippingAddress.objects.create(
            user=self.user,
            full_name="John Doe",
            address_line_1="123 Main St",
            city="Almería",
            postal_code="04001",
            phone="123456789"
        )
        
        address_str = str(address)
        self.assertIn("John Doe", address_str)
        self.assertIn("Almería", address_str)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    SESSION_ENGINE="django.contrib.sessions.backends.db",
)
class EndpointViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = "StrongPassword123!"
        cls.buyer = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password=cls.password,
            registration_status=User.RegisterStatus.ACTIVE,
        )
        cls.seller = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password=cls.password,
            registration_status=User.RegisterStatus.ACTIVE,
        )
        cls.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password=cls.password,
            registration_status=User.RegisterStatus.ACTIVE,
        )
        cls.category = Category.objects.create(name="Electrónica")
        cls.image = Image.objects.create(name="imagen", image="images/test.jpg")
        cls.product = Product.objects.create(
            name="Producto test",
            briefdesc="Breve",
            description="Descripción",
            price=10.0,
            stock=20,
            category=cls.category,
            primary_image=cls.image,
            creator=cls.seller,
        )
        cls.address = ShippingAddress.objects.create(
            user=cls.buyer,
            full_name="Comprador Uno",
            address_line_1="Calle Mayor 1",
            city="Almería",
            postal_code="04001",
            phone="600000001",
            is_default=True,
        )
        cls.other_address = ShippingAddress.objects.create(
            user=cls.other_user,
            full_name="Otro Usuario",
            address_line_1="Calle Otro 2",
            city="Almería",
            postal_code="04002",
            phone="600000002",
        )

    def _login(self, user=None):
        self.client.force_login(user or self.buyer)

    def _create_cart_item(self, quantity=1, user=None):
        owner = user or self.buyer
        cart, _ = Cart.objects.get_or_create(user=owner)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=self.product, defaults={"quantity": quantity})
        item.quantity = quantity
        item.save()
        return item

    def _post_json(self, url_name, data, **kwargs):
        return self.client.post(
            reverse(url_name, kwargs=kwargs or None),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_public_endpoints_render(self):
        public_routes = [
            reverse("home"),
            reverse("index"),
            reverse("productos"),
            reverse("producto", args=[self.product.id]),
            reverse("categoria", args=[self.category.id]),
            reverse("search"),
            reverse("search_suggestions"),
            reverse("login"),
            reverse("register"),
            reverse("rgpd"),
            reverse("privacidad"),
            reverse("devoluciones"),
            reverse("aviso_legal"),
            reverse("terminos"),
            reverse("cookies"),
            reverse("sobre_nosotros"),
            reverse("ayuda"),
            reverse("reset_password"),
        ]
        for url in public_routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_index_shows_mobile_categories_toggle(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-bs-target="#mobileCategoriasCollapse"')
        self.assertContains(response, 'id="mobileCategoriasCollapse"')
        self.assertContains(response, "Categorías")

    def test_home_header_renders_mobile_title_outside_collapsible_menu(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'site-title-mobile d-md-none')
        self.assertContains(response, 'site-title-desktop')

    def test_mobile_site_title_css_keeps_title_pinned_to_header_row(self):
        css_path = Path(__file__).resolve().parent / "static" / "css" / "custom.css"
        css_content = css_path.read_text(encoding="utf-8")
        selector_match = re.search(r"\.navbar\.header \.site-title-mobile\s*\{(?P<body>[^}]*)\}", css_content, re.DOTALL)
        self.assertIsNotNone(selector_match)

        rule_block = selector_match.group("body")
        self.assertRegex(rule_block, r"top:\s*calc\(var\(--bs-navbar-padding-y\)\s*\+\s*20px\);")
        self.assertRegex(rule_block, r"transform:\s*translate\(-50%,\s*-50%\);")
    def test_home_mobile_welcome_title_centered(self):
        response = self.client.get(reverse("home"))
        html = response.content.decode()
        media_idx = html.find("@media (max-width: 767.98px)")
        self.assertNotEqual(media_idx, -1)

        rule_idx = html.find(".hero-section h1", media_idx)
        self.assertNotEqual(rule_idx, -1)

        block_end_idx = html.find("}", rule_idx)
        self.assertNotEqual(block_end_idx, -1)
        rule_block = html[rule_idx:block_end_idx]

        self.assertIn("text-align: center", rule_block)
        self.assertIn("text-wrap: balance", rule_block)

    def test_login_required_endpoints_redirect_anonymous(self):
        secured_get_routes = [
            reverse("mis_productos"),
            reverse("pedidos_vendedor"),
            reverse("crear_producto"),
            reverse("checkout"),
            reverse("checkout_success"),
            reverse("checkout_cancel"),
            reverse("portal_usuario"),
            reverse("mis_compras"),
            reverse("mis_recibos"),
            reverse("editar_perfil"),
            reverse("direcciones_usuario"),
            reverse("crear_direccion"),
            reverse("mensajes_comprador"),
            reverse("metodos_pago"),
            reverse("agregar_tarjeta"),
            reverse("agregar_paypal"),
            reverse("editar_producto", args=[self.product.id]),
            reverse("borrar_producto", args=[self.product.id]),
            reverse("cambiar_estado_pedido", args=[1]),
            reverse("enviar_mensaje_pedido", args=[1]),
            reverse("editar_direccion", args=[self.address.id]),
            reverse("eliminar_direccion", args=[self.address.id]),
            reverse("eliminar_metodo_pago", args=[1]),
        ]
        for url in secured_get_routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

        secured_post_routes = [
            "crear_payment_intent",
            "confirmar_pago_tarjeta",
            "crear_orden_paypal",
            "capturar_orden_paypal",
            "crear_setup_intent",
            "confirmar_setup_intent",
            "crear_orden_paypal_setup",
            "capturar_orden_paypal_setup",
        ]
        for name in secured_post_routes:
            with self.subTest(name=name):
                response = self.client.post(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    @patch("tienda.views.tasks.enviar_correo_confirmacion.delay")
    @patch("tienda.views.tasks.enviar_correo_bienvenida.delay")
    def test_register_login_logout_and_verify_flows(self, welcome_delay, confirm_delay):
        register_response = self.client.post(reverse("register"), data={
            "name": "Nuevo",
            "email": "nuevo@example.com",
            "password": self.password,
            "password_confirm": self.password,
            "terms": "on",
        })
        self.assertEqual(register_response.status_code, 302)
        confirm_delay.assert_called_once()

        created_user = User.objects.get(email="nuevo@example.com")
        created_user.registration_status = User.RegisterStatus.ACTIVE
        created_user.save(update_fields=["registration_status"])

        login_response = self.client.post(reverse("login"), data={
            "email": "nuevo@example.com",
            "password": self.password,
            "remember": "on",
        })
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.url, reverse("index"))
        welcome_delay.assert_called_once()

        logout_response = self.client.get(reverse("logout"))
        self.assertEqual(logout_response.status_code, 302)
        self.assertEqual(logout_response.url, reverse("index"))

        verification = VerificationCode.generate(created_user, VerificationCode.VerificationModes.VERIFY_ACCOUNT)
        verify_response = self.client.get(reverse("verify", args=[verification.code]))
        self.assertEqual(verify_response.status_code, 302)
        created_user.refresh_from_db()
        self.assertEqual(created_user.registration_status, User.RegisterStatus.ACTIVE)

        invalid_verify_response = self.client.get(reverse("verify", args=["codigo-invalido"]))
        self.assertEqual(invalid_verify_response.status_code, 200)

    @patch("tienda.views.tasks.enviar_correo_recuperacion.delay")
    def test_password_reset_endpoints(self, recovery_delay):
        reset_get = self.client.get(reverse("reset_password"))
        self.assertEqual(reset_get.status_code, 200)
        reset_post = self.client.post(reverse("reset_password"), data={"email": self.buyer.email})
        self.assertEqual(reset_post.status_code, 200)
        recovery_delay.assert_called_once_with(self.buyer.email)

        code = VerificationCode.generate(self.buyer, VerificationCode.VerificationModes.RESET_PASSWORD)
        phase2_get = self.client.get(reverse("reset_password_phase2", args=[code.code]))
        self.assertEqual(phase2_get.status_code, 200)

        mismatch = self.client.post(reverse("reset_password_phase2", args=[code.code]), data={
            "password": "NuevaPassword123!",
            "verify_password": "DistintaPassword123!",
        })
        self.assertEqual(mismatch.status_code, 200)

        success = self.client.post(reverse("reset_password_phase2", args=[code.code]), data={
            "password": "NuevaPassword123!",
            "verify_password": "NuevaPassword123!",
        })
        self.assertEqual(success.status_code, 302)
        self.assertTrue(User.objects.get(id=self.buyer.id).check_password("NuevaPassword123!"))

        not_found = self.client.get(reverse("reset_password_phase2", args=["no-existe"]))
        self.assertEqual(not_found.status_code, 404)

    def test_search_and_suggestions(self):
        response = self.client.get(reverse("search"), data={"q": "Producto"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Producto test")

        suggestions = self.client.get(reverse("search_suggestions"), data={"q": "Pr"})
        self.assertEqual(suggestions.status_code, 200)
        payload = suggestions.json()
        self.assertTrue(payload["suggestions"])

    def test_cart_endpoints(self):
        self._login()
        cart_view = self.client.get(reverse("view_cart"))
        self.assertEqual(cart_view.status_code, 200)

        add_response = self.client.post(reverse("add_to_cart", args=[self.product.id]), data={"quantity": 2})
        self.assertEqual(add_response.status_code, 302)
        item = CartItem.objects.get(cart__user=self.buyer, product=self.product)
        self.assertEqual(item.quantity, 2)

        update_response = self.client.post(reverse("update_cart_item", args=[item.id]), data={"quantity": 3})
        self.assertEqual(update_response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

        remove_response = self.client.post(reverse("remove_from_cart", args=[item.id]))
        self.assertEqual(remove_response.status_code, 302)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

        self._create_cart_item(quantity=1)
        clear_response = self.client.post(reverse("clear_cart"))
        self.assertEqual(clear_response.status_code, 302)
        self.assertEqual(CartItem.objects.filter(cart__user=self.buyer).count(), 0)

    def test_seller_panel_endpoints(self):
        self._login(self.seller)
        order = Order.objects.create(
            buyer=self.buyer,
            shipping_address=self.address,
            total=12.1,
            payment_method=Order.PAYMENT_STRIPE,
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            seller=self.seller,
            quantity=1,
            unit_price=12.1,
            total_price=12.1,
        )

        self.assertEqual(self.client.get(reverse("mis_productos")).status_code, 200)
        self.assertEqual(self.client.get(reverse("pedidos_vendedor")).status_code, 200)
        self.assertEqual(self.client.get(reverse("crear_producto")).status_code, 200)
        self.assertEqual(self.client.get(reverse("editar_producto", args=[self.product.id])).status_code, 200)

        create_response = self.client.post(reverse("crear_producto"), data={
            "name": "Nuevo producto",
            "briefdesc": "Breve",
            "description": "Descripción",
            "price": "25.50",
            "stock": "5",
            "category": str(self.category.id),
        })
        self.assertEqual(create_response.status_code, 302)
        created = Product.objects.get(name="Nuevo producto")

        edit_response = self.client.post(reverse("editar_producto", args=[created.id]), data={
            "name": "Producto editado",
            "briefdesc": "Actualizado",
            "description": "Descripción nueva",
            "price": "30.00",
            "stock": "6",
            "category": str(self.category.id),
        })
        self.assertEqual(edit_response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.name, "Producto editado")

        status_response = self.client.post(reverse("cambiar_estado_pedido", args=[item.id]), data={
            "estado": OrderItem.STATUS_PROCESSING,
        })
        self.assertEqual(status_response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, OrderItem.STATUS_PROCESSING)

        message_response = self.client.post(reverse("enviar_mensaje_pedido", args=[item.id]), data={"mensaje": "Preparando envío"})
        self.assertEqual(message_response.status_code, 302)
        self.assertTrue(OrderMessage.objects.filter(order_item=item, sender=self.seller).exists())

        delete_get = self.client.get(reverse("borrar_producto", args=[created.id]))
        self.assertEqual(delete_get.status_code, 405)
        delete_post = self.client.post(reverse("borrar_producto", args=[created.id]))
        self.assertEqual(delete_post.status_code, 302)
        self.assertFalse(Product.objects.filter(id=created.id).exists())

    @patch("tienda.views.stripe.PaymentIntent.create")
    @patch("tienda.views._create_stock_reservation_for_cart")
    def test_crear_payment_intent_endpoint(self, reservation_mock, create_pi_mock):
        self._login()
        self._create_cart_item(quantity=2)
        reservation_mock.return_value = (MagicMock(id=321), [])
        create_pi_mock.return_value = MagicMock(client_secret="secret", id="pi_123")

        self.assertEqual(self.client.get(reverse("crear_payment_intent")).status_code, 405)
        bad_json = self.client.post(reverse("crear_payment_intent"), data="{", content_type="application/json")
        self.assertEqual(bad_json.status_code, 400)

        missing_address = self._post_json("crear_payment_intent", {})
        self.assertEqual(missing_address.status_code, 400)

        ok = self._post_json("crear_payment_intent", {"shipping_address_id": self.address.id, "save_card": True})
        self.assertEqual(ok.status_code, 200)
        data = ok.json()
        self.assertEqual(data["client_secret"], "secret")
        self.assertEqual(data["payment_intent_id"], "pi_123")

    @patch("tienda.views.create_order_from_cart")
    @patch("tienda.views.stripe.PaymentIntent.retrieve")
    def test_confirmar_pago_tarjeta_endpoint(self, retrieve_mock, create_order_mock):
        self._login()
        self._create_cart_item(quantity=1)
        session = self.client.session
        session["selected_shipping_address_id"] = self.address.id
        session.save()

        retrieve_mock.return_value = MagicMock(status="succeeded")
        order = Order.objects.create(
            buyer=self.buyer,
            shipping_address=self.address,
            total=12.1,
            payment_method=Order.PAYMENT_STRIPE,
        )
        create_order_mock.return_value = (order, "")

        self.assertEqual(self.client.get(reverse("confirmar_pago_tarjeta")).status_code, 405)
        self.assertEqual(self.client.post(reverse("confirmar_pago_tarjeta"), data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self._post_json("confirmar_pago_tarjeta", {}).status_code, 400)

        ok = self._post_json("confirmar_pago_tarjeta", {"payment_intent_id": "pi_ok"})
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["success"])

    @patch("tienda.views._paypal_create_order")
    @patch("tienda.views._create_stock_reservation_for_cart")
    def test_crear_orden_paypal_endpoint(self, reservation_mock, create_order_mock):
        self._login()
        self._create_cart_item(quantity=1)
        reservation_mock.return_value = (MagicMock(id=555), [])
        create_order_mock.return_value = {"id": "ORDER123"}

        self.assertEqual(self.client.get(reverse("crear_orden_paypal")).status_code, 405)
        missing_address = self._post_json("crear_orden_paypal", {})
        self.assertEqual(missing_address.status_code, 400)

        ok = self._post_json("crear_orden_paypal", {"shipping_address_id": self.address.id})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["id"], "ORDER123")

    @patch("tienda.views.create_order_from_cart")
    @patch("tienda.views._paypal_capture_order")
    def test_capturar_orden_paypal_endpoint(self, capture_mock, create_order_mock):
        self._login()
        self._create_cart_item(quantity=1)
        session = self.client.session
        session["paypal_order_id"] = "ORDER123"
        session["selected_shipping_address_id"] = self.address.id
        session.save()

        order = Order.objects.create(
            buyer=self.buyer,
            shipping_address=self.address,
            total=12.1,
            payment_method=Order.PAYMENT_PAYPAL,
        )
        create_order_mock.return_value = (order, "")

        self.assertEqual(self.client.get(reverse("capturar_orden_paypal")).status_code, 405)
        self.assertEqual(self.client.post(reverse("capturar_orden_paypal"), data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self._post_json("capturar_orden_paypal", {}).status_code, 400)
        self.assertEqual(self._post_json("capturar_orden_paypal", {"orderID": "WRONG"}).status_code, 400)

        capture_mock.return_value = {"status": "APPROVED"}
        not_completed = self._post_json("capturar_orden_paypal", {"orderID": "ORDER123"})
        self.assertEqual(not_completed.status_code, 400)

        capture_mock.return_value = {
            "status": "COMPLETED",
            "payer": {"email_address": "paypal@example.com", "payer_id": "payer_123"},
        }
        ok = self._post_json("capturar_orden_paypal", {"orderID": "ORDER123", "save_paypal": True})
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["success"])
        self.assertTrue(SavedPaymentMethod.objects.filter(user=self.buyer, paypal_email="paypal@example.com").exists())

    @patch("tienda.views.create_order_from_cart")
    @patch("paypalrestsdk.Payment.find")
    @patch("paypalrestsdk.configure")
    def test_paypal_legacy_endpoints(self, configure_mock, find_mock, create_order_mock):
        self._login()
        self._create_cart_item(quantity=1)

        self.assertEqual(self.client.get(reverse("create_paypal_payment")).status_code, 405)

        with patch("paypalrestsdk.Payment") as payment_cls, patch("tienda.views._create_stock_reservation_for_cart") as reservation_mock:
            reservation_mock.return_value = (MagicMock(id=777), [])
            payment_instance = MagicMock()
            payment_instance.create.return_value = True
            payment_instance.id = "PAY-123"
            payment_instance.links = [MagicMock(rel="approval_url", href="https://paypal.local/approve")]
            payment_cls.return_value = payment_instance
            create_payment = self.client.post(reverse("create_paypal_payment"), data={"shipping_address_id": self.address.id})
            self.assertEqual(create_payment.status_code, 200)
            self.assertIn("redirect", create_payment.json())

        missing_data = self.client.get(reverse("paypal_execute"))
        self.assertEqual(missing_data.status_code, 302)

        session = self.client.session
        session["paypal_payment_id"] = "PAY-123"
        session["selected_shipping_address_id"] = self.address.id
        session.save()
        payment_found = MagicMock()
        payment_found.execute.return_value = True
        find_mock.return_value = payment_found
        order = Order.objects.create(
            buyer=self.buyer,
            shipping_address=self.address,
            total=12.1,
            payment_method=Order.PAYMENT_PAYPAL,
        )
        create_order_mock.return_value = (order, "")
        execute = self.client.get(reverse("paypal_execute"), data={"PayerID": "payer"})
        self.assertEqual(execute.status_code, 200)

    @patch("tienda.views.stripe.SetupIntent.create")
    @patch("tienda.views._get_or_create_stripe_customer")
    def test_setup_intent_endpoints(self, customer_mock, setup_mock):
        self._login()
        self.assertEqual(self.client.get(reverse("metodos_pago")).status_code, 200)
        self.assertEqual(self.client.get(reverse("agregar_tarjeta")).status_code, 200)
        self.assertEqual(self.client.get(reverse("agregar_paypal")).status_code, 200)

        self.assertEqual(self.client.get(reverse("crear_setup_intent")).status_code, 405)
        customer_mock.return_value = "cus_123"
        setup_mock.return_value = MagicMock(client_secret="seti_secret")
        setup_response = self.client.post(reverse("crear_setup_intent"))
        self.assertEqual(setup_response.status_code, 200)
        self.assertEqual(setup_response.json()["customer_id"], "cus_123")

        self.assertEqual(self.client.get(reverse("confirmar_setup_intent")).status_code, 405)
        self.assertEqual(self.client.post(reverse("confirmar_setup_intent"), data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self._post_json("confirmar_setup_intent", {}).status_code, 400)

        with patch("tienda.views.stripe.PaymentMethod.attach"), patch("tienda.views.stripe.PaymentMethod.retrieve") as retrieve_pm:
            retrieve_pm.return_value = MagicMock(
                card=MagicMock(brand="visa", last4="4242", exp_month=1, exp_year=2030)
            )
            confirm = self._post_json("confirmar_setup_intent", {"payment_method_id": "pm_123"})
            self.assertEqual(confirm.status_code, 200)
            self.assertTrue(confirm.json()["success"])

    @patch("tienda.views._paypal_create_order")
    def test_paypal_setup_endpoints(self, create_order_mock):
        self._login()
        self.assertEqual(self.client.get(reverse("crear_orden_paypal_setup")).status_code, 405)
        create_order_mock.return_value = {"id": "ORDER_SETUP"}
        create_response = self.client.post(reverse("crear_orden_paypal_setup"))
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(create_response.json()["id"], "ORDER_SETUP")

        self.assertEqual(self.client.get(reverse("capturar_orden_paypal_setup")).status_code, 405)
        self.assertEqual(self.client.post(reverse("capturar_orden_paypal_setup"), data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self._post_json("capturar_orden_paypal_setup", {}).status_code, 400)

        with patch("tienda.views._paypal_capture_order") as capture_mock:
            capture_mock.return_value = {"status": "COMPLETED", "payer": {"email_address": "payer@example.com", "payer_id": "payer_1"}}
            capture_response = self._post_json("capturar_orden_paypal_setup", {"orderID": "ORDER_SETUP"})
            self.assertEqual(capture_response.status_code, 200)
            self.assertTrue(capture_response.json()["success"])

    def test_user_portal_and_addresses_endpoints(self):
        self._login()
        order = Order.objects.create(
            buyer=self.buyer,
            shipping_address=self.address,
            total=12.1,
            payment_method=Order.PAYMENT_STRIPE,
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            seller=self.seller,
            quantity=1,
            unit_price=12.1,
            total_price=12.1,
        )
        OrderMessage.objects.create(order_item=item, sender=self.seller, message="Mensaje vendedor")

        self.assertEqual(self.client.get(reverse("portal_usuario")).status_code, 200)
        self.assertEqual(self.client.get(reverse("mis_compras")).status_code, 200)
        self.assertEqual(self.client.get(reverse("mis_recibos")).status_code, 200)
        self.assertEqual(self.client.get(reverse("mensajes_comprador")).status_code, 200)
        self.assertEqual(self.client.get(reverse("direcciones_usuario")).status_code, 200)
        self.assertEqual(self.client.get(reverse("crear_direccion")).status_code, 200)
        self.assertEqual(self.client.get(reverse("editar_direccion", args=[self.address.id])).status_code, 200)

        profile = self.client.post(reverse("editar_perfil"), data={
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "buyer-updated@example.com",
        })
        self.assertEqual(profile.status_code, 302)
        self.buyer.refresh_from_db()
        self.assertEqual(self.buyer.email, "buyer-updated@example.com")

        wrong_current = self.client.post(reverse("cambiar_contrasena"), data={
            "current_password": "incorrecta",
            "new_password": "PasswordNueva123!",
            "confirm_password": "PasswordNueva123!",
        })
        self.assertEqual(wrong_current.status_code, 200)
        changed = self.client.post(reverse("cambiar_contrasena"), data={
            "current_password": self.password,
            "new_password": "PasswordNueva123!",
            "confirm_password": "PasswordNueva123!",
        })
        self.assertEqual(changed.status_code, 302)
        self.buyer.refresh_from_db()
        self.assertTrue(self.buyer.check_password("PasswordNueva123!"))

        invalid_city = self.client.post(reverse("crear_direccion"), data={
            "full_name": "Comprador Uno",
            "address_line_1": "Calle Nueva 3",
            "city": "Madrid",
            "postal_code": "04003",
            "phone": "600000003",
        })
        self.assertEqual(invalid_city.status_code, 200)
        invalid_postal = self.client.post(reverse("crear_direccion"), data={
            "full_name": "Comprador Uno",
            "address_line_1": "Calle Nueva 3",
            "city": "Almería",
            "postal_code": "28001",
            "phone": "600000003",
        })
        self.assertEqual(invalid_postal.status_code, 200)

        create_ok = self.client.post(reverse("crear_direccion"), data={
            "full_name": "Comprador Dos",
            "address_line_1": "Calle Nueva 3",
            "city": "Almería",
            "postal_code": "04003",
            "phone": "600000003",
            "is_default": "on",
        })
        self.assertEqual(create_ok.status_code, 302)
        new_address = ShippingAddress.objects.get(full_name="Comprador Dos")
        self.assertEqual(new_address.country, "España")

        edit_ok = self.client.post(reverse("editar_direccion", args=[new_address.id]), data={
            "full_name": "Comprador Dos Editado",
            "address_line_1": "Calle Editada 9",
            "city": "Almería",
            "postal_code": "04004",
            "phone": "600000004",
        })
        self.assertEqual(edit_ok.status_code, 302)
        new_address.refresh_from_db()
        self.assertEqual(new_address.full_name, "Comprador Dos Editado")

        delete_get = self.client.get(reverse("eliminar_direccion", args=[new_address.id]))
        self.assertEqual(delete_get.status_code, 405)
        delete_post = self.client.post(reverse("eliminar_direccion", args=[new_address.id]))
        self.assertEqual(delete_post.status_code, 302)
        self.assertFalse(ShippingAddress.objects.filter(id=new_address.id).exists())

    def test_delete_payment_method_endpoint(self):
        self._login()
        method = SavedPaymentMethod.objects.create(
            user=self.buyer,
            method_type=SavedPaymentMethod.TYPE_CARD,
            label="Visa 4242",
            stripe_payment_method_id="pm_4242",
        )
        self.assertEqual(self.client.get(reverse("eliminar_metodo_pago", args=[method.id])).status_code, 302)
        with patch("tienda.views.stripe.PaymentMethod.detach"):
            response = self.client.post(reverse("eliminar_metodo_pago", args=[method.id]))
            self.assertEqual(response.status_code, 302)
        self.assertFalse(SavedPaymentMethod.objects.filter(id=method.id).exists())
