from ninja import NinjaAPI
from .models import Product
api = NinjaAPI()

@api.get("/hola")
def hola(request):
    return {"mensaje": "¡Hola Mundo!"}

@api.get("/products")
def products(request):
    productos = Product.objects.all()
    return [dict(producto) for producto in productos]