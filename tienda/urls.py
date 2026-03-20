from django.urls import path
from . import views
urlpatterns = [
    path("", views.index, name="index"),
    path("productos/", views.index, name="productos"),
    path("producto/<int:id>", views.producto, name="producto"),
    path("categoria/<int:id>", views.categoria, name="categoria"),
    path("buscar/", views.search, name="search"),
    path("api/sugerencias/", views.search_suggestions, name="search_suggestions"),
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),
    # Sección de vendedor
    path("venta/", views.mis_productos, name="mis_productos"),
    path("venta/pedidos/", views.pedidos_vendedor, name="pedidos_vendedor"),
    path("venta/pedidos/<int:item_id>/cambiar-estado/", views.cambiar_estado_pedido, name="cambiar_estado_pedido"),
    path("venta/pedidos/<int:item_id>/enviar-mensaje/", views.enviar_mensaje_pedido, name="enviar_mensaje_pedido"),
    path("venta/crear-producto/", views.crear_producto, name="crear_producto"),
    path("venta/editar-producto/<int:id>/", views.editar_producto, name="editar_producto"),
    path("venta/borrar-producto/<int:id>/", views.borrar_producto, name="borrar_producto"),
    # Carrito
    path("cart/", views.view_cart, name="view_cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart_item, name="update_cart_item"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/clear/", views.clear_cart, name="clear_cart"),
    path("checkout/", views.checkout, name="checkout"),
    # Stripe
    path("config/", views.stripe_config, name="stripe_config"),
    path("create-checkout-session/", views.create_checkout_session, name="create_checkout_session"),
    path("checkout/success/", views.checkout_success, name="checkout_success"),
    path("checkout/cancel/", views.checkout_cancel, name="checkout_cancel"),
    # PayPal
    path("paypal/create-payment/", views.create_paypal_payment, name="create_paypal_payment"),
    path("paypal/execute/", views.paypal_execute, name="paypal_execute"),
    # Portal de usuario
    path("usuario/", views.portal_usuario, name="portal_usuario"),
    path("usuario/compras/", views.mis_compras, name="mis_compras"),
    path("usuario/recibos/", views.mis_recibos, name="mis_recibos"),
    path("usuario/perfil/", views.editar_perfil, name="editar_perfil"),
    path("usuario/perfil/cambiar-contrasena/", views.cambiar_contrasena, name="cambiar_contrasena"),
    path("usuario/direcciones/", views.direcciones_usuario, name="direcciones_usuario"),
    path("usuario/direcciones/crear/", views.crear_direccion, name="crear_direccion"),
    path("usuario/direcciones/<int:id>/editar/", views.editar_direccion, name="editar_direccion"),
    path("usuario/direcciones/<int:id>/eliminar/", views.eliminar_direccion, name="eliminar_direccion"),
    path("usuario/mensajes/", views.mensajes_comprador, name="mensajes_comprador"),
    path("verify/<str:code>", views.verify, name="verify"),
    path("rgpd", views.rgpd, name="rgpd")
]
