from typing import Optional
from ninja import Router, Schema
from django.db.models import Count
from django.shortcuts import get_object_or_404
from .models import Category, Product

router = Router()

class CategoryOut(Schema):
    id: int
    name: str
    product_count: int

class ImageInfo(Schema):
    url: str
    alt: str

class ProductListOut(Schema):
    id: int
    name: str
    sku: Optional[str] = None
    briefdesc: str
    price: float
    price_with_vat: float
    stock: int
    category_id: int
    category_name: str
    primary_image: Optional[ImageInfo] = None
    average_rating: float
    reviews_count: int

class ProductDetailOut(ProductListOut):
    description: str
    secondary_images: list[ImageInfo]


def _image_info(img, request):
    if not img:
        return None
    return ImageInfo(
        url=request.build_absolute_uri(img.image.url),
        alt=img.alt or img.name,
    )

def _product_to_list_out(p, request):
    return ProductListOut(
        id=p.id,
        name=p.name,
        sku=p.sku,
        briefdesc=p.briefdesc,
        price=p.price,
        price_with_vat=p.get_price_with_vat(),
        stock=p.stock,
        category_id=p.category_id,
        category_name=p.category.name,
        primary_image=_image_info(p.primary_image, request),
        average_rating=p.get_average_rating(),
        reviews_count=p.get_reviews_count(),
    )

def _product_to_detail_out(p, request):
    base = _product_to_list_out(p, request)
    data = base.dict()
    data["description"] = p.description
    data["secondary_images"] = [
        _image_info(img, request) for img in p.secondary_images.all()
    ]
    return ProductDetailOut(**data)


@router.get("/categorias", response=list[CategoryOut])
def listar_categorias(request):
    qs = Category.objects.annotate(product_count=Count("product"))
    return [
        CategoryOut(id=c.id, name=c.name, product_count=c.product_count)
        for c in qs
    ]

@router.get("/productos", response=list[ProductListOut])
def listar_productos(request, categoria_id: Optional[int] = None):
    qs = Product.objects.select_related("category", "primary_image")
    if categoria_id:
        qs = qs.filter(category_id=categoria_id)
    return [_product_to_list_out(p, request) for p in qs]

@router.get("/productos/{product_id}", response=ProductDetailOut)
def detalle_producto(request, product_id: int):
    p = get_object_or_404(
        Product.objects.select_related("category", "primary_image")
        .prefetch_related("secondary_images"),
        id=product_id,
    )
    return _product_to_detail_out(p, request)
