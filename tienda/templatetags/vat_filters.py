from django import template
from tienda.vars import VAT_RATE

register = template.Library()

@register.filter
def add_vat(value):
    """Agrega IVA (21%) al precio"""
    try:
        price = float(value)
        return round(price * (1 + VAT_RATE), 2)
    except (ValueError, TypeError):
        return value

@register.filter
def vat_amount(value):
    """Retorna solo el monto del IVA"""
    try:
        price = float(value)
        return round(price * VAT_RATE, 2)
    except (ValueError, TypeError):
        return value

@register.filter
def format_price(value):
    """Formatea el precio con 2 decimales"""
    try:
        price = float(value)
        return f"{price:.2f}"
    except (ValueError, TypeError):
        return value
