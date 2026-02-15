from .models import Cart

def cart_context(request):
    """Context processor para hacer el carrito disponible en todas las plantillas"""
    cart_count = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_items_count()
        except Cart.DoesNotExist:
            cart_count = 0
    elif request.session.session_key:
        try:
            cart = Cart.objects.get(session_key=request.session.session_key)
            cart_count = cart.get_items_count()
        except Cart.DoesNotExist:
            cart_count = 0
    
    return {
        'cart_count': cart_count
    }
