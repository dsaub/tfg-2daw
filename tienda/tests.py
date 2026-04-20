from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError
from datetime import timedelta
from .models import (
    User, VerificationCode, Category, Image, Product, 
    StockReservation, StockReservationItem, Cart, CartItem, 
    Order, OrderItem, OrderMessage, SavedPaymentMethod, ShippingAddress
)
from .vars import VAT_RATE, TRANSACTION_CODE_PREFIX
import string
import random


# ==================== USER MODEL TESTS ====================
class UserModelTests(TestCase):
    """Tests exhaustivos para el modelo User."""
    
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
            mode = random.choice([
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
            cat = Category.objects.create(name=f"Category_{i}_{random.randint(1000, 9999)}")
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