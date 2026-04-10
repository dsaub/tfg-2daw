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
    # Stripe Payment Intents (nuevo sistema)
    path("checkout/crear-payment-intent/", views.crear_payment_intent, name="crear_payment_intent"),
    path("checkout/confirmar-pago-tarjeta/", views.confirmar_pago_tarjeta, name="confirmar_pago_tarjeta"),
    path("checkout/success/", views.checkout_success, name="checkout_success"),
    path("checkout/cancel/", views.checkout_cancel, name="checkout_cancel"),
    # PayPal Orders API (nuevo sistema)
    path("paypal/crear-orden/", views.crear_orden_paypal, name="crear_orden_paypal"),
    path("paypal/capturar-orden/", views.capturar_orden_paypal, name="capturar_orden_paypal"),
    # PayPal (legacy - mantenido por compatibilidad)
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
    # Métodos de pago del usuario
    path("usuario/metodos-pago/", views.metodos_pago, name="metodos_pago"),
    path("usuario/metodos-pago/agregar-tarjeta/", views.agregar_tarjeta, name="agregar_tarjeta"),
    path("usuario/metodos-pago/agregar-tarjeta/crear-setup-intent/", views.crear_setup_intent, name="crear_setup_intent"),
    path("usuario/metodos-pago/agregar-tarjeta/confirmar/", views.confirmar_setup_intent, name="confirmar_setup_intent"),
    path("usuario/metodos-pago/<int:id>/eliminar/", views.eliminar_metodo_pago, name="eliminar_metodo_pago"),
    path("usuario/metodos-pago/agregar-paypal/", views.agregar_paypal, name="agregar_paypal"),
    path("usuario/metodos-pago/agregar-paypal/crear-orden/", views.crear_orden_paypal_setup, name="crear_orden_paypal_setup"),
    path("usuario/metodos-pago/agregar-paypal/capturar/", views.capturar_orden_paypal_setup, name="capturar_orden_paypal_setup"),
    path("verify/<str:code>", views.verify, name="verify"),
    path("rgpd", views.rgpd, name="rgpd"),
    path("reset-password", views.reset_password, name="reset_password"),
    path("reset-password-phase2/<str:code>", views.reset_password_phase2, name="reset_password_phase2")
]
