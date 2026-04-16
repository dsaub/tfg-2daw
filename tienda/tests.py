from django.test import TestCase
from .models import *
import string, random
class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create(
            username="elordenador",
            first_name="Hello",
            last_name="World",
            email="a@a.a"
        )
        User.objects.create(
            username="roader",
            first_name="RODOR",
            last_name="goll",
            email="b@b.b"
        )
    def test_users_should_not_be_verified(self):
        elordenador = User.objects.get(username="elordenador")
        roader = User.objects.get(username="roader")

        self.assertEqual(elordenador.registration_status, User.RegisterStatus.CONFIRMATION_REQUIRED)
        self.assertEqual(elordenador.registration_status, User.RegisterStatus.CONFIRMATION_REQUIRED)
    def test_users_can_set_and_verify_password(self):
        usernames = ["elordenador", "roader"]
        for username in usernames:
            user = User.objects.get(username=username)

            password = "".join(random.choices(string.digits, k=16))

            user.set_password(password)
            self.assertTrue(user.check_password(password), "Log-in should work!!")

class VerificationCodeTests(TestCase):
    # First create a user
    def setUp(self):
        self.user = User.objects.create(
            username = "test_user_01"
        )
    def test_able_to_create_fifty_codes(self):

        for i in range(50):
            modes = [VerificationCode.VerificationModes.VERIFY_ACCOUNT, VerificationCode.VerificationModes.RESET_PASSWORD]
            code = VerificationCode.generate(self.user, random.choice(modes))

class CategoryTests(TestCase):
    def setUp(self):
        self.lista = []
    def test_able_to_create_a_hundred_categories(self):
        for i in range(100):
            cat_name = "test_{}_{}".format(i, "".join(random.choices(string.digits, k=3)))
            category = Category.objects.create(name=cat_name)
            self.lista.append(cat_name)
    def test_category_have_that_name(self):
        for i in self.lista:
            self.assertTrue(Category.objects.filter(name=i).exists(), "Category does NOT exist")

class ProductTests(TestCase):
    def setUp(self):
        self.categorias = []
        self.products = []
        for i in range(5):
            cat_name = "test_{}_{}".format(i, "".join(random.choices(string.digits, k=3)))
            category = Category.objects.create(name=cat_name)
            self.categorias.append(cat_name)
        self.user = User.objects.create(username="product_test_user")
    
    def test_able_to_create_a_hundred_products(self):
        for i in range(100):
            cat = random.choice(self.categorias)
            categoria = Category.objects.filter(name=cat).first()

            prod_name = "product_{}{}".format(i, "".join(random.choices(string.digits, k=3)))
            prod_description = "".join(random.choices(string.ascii_letters, k=255))
            prod_briefdesc = "".join(random.choices(string.ascii_letters, k=50))
            prod_price = random.randint(1,1000)
            prod_stock = random.randint(1,100)
            creator = self.user.username

            product = Product.objects.create(
                name = prod_name,
                description = prod_description,
                briefdesc = prod_briefdesc,
                price = prod_price,
                stock = prod_stock,
                category = categoria,
                creator = self.user
            )

            diction = {
                "name": prod_name,
                "description": prod_description,
                "briefdesc": prod_briefdesc,
                "price": prod_price,
                "stock": prod_stock,
                "creator": creator
            }

            self.products.append(diction)
    def test_verify_products(self):
        for prod in self.products:
            producto = Product.objects.filter(name=prod["name"])
            self.assertTrue(producto.exists(), "Product DOES NOT EXIST")

            producto = producto.first()
            self.assertEqual(producto.name, prod["name"], "product name {} does not match".format(producto.name))
            self.assertEqual(producto.description, prod["description"], "product {} description does not match".format(producto.name))
            self.assertEqual(producto.briefdesc, prod["briefdesc"], "product {} brief description does not match".format(producto.name))
            self.assertEqual(producto.price, prod["price"], "product {} price does not match ({} != {})".format(producto.name, producto.price, prod["price"]))
            self.assertEqual(producto.stock, prod["stock"], "product {} stock does not match".format(producto.name))
            self.assertEqual(producto.creator.username, prod["creator"], "product {} owner does not match".format(producto.name))