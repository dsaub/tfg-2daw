# Documentación de `tienda/views.py`

Este directorio contiene la documentación de cada función definida en `tienda/views.py`.

---

## 🔧 Funciones auxiliares y helpers

### Helpers privados de localización y validación

| Función | Descripción |
|---------|-------------|
| [`_normalize_location_text`](./_normalize_location_text.md) | Normaliza texto de localidad (quita acentos, símbolos, pasa a minúsculas). |
| [`_is_almeria_postal_code`](./_is_almeria_postal_code.md) | Valida que un código postal pertenezca a Almería (`04xxx`). |
| [`_is_almeria_city`](./_is_almeria_city.md) | Comprueba si un municipio pertenece a la provincia de Almería. |
| [`_address_form_context`](./_address_form_context.md) | Construye el contexto de template para formularios de dirección. |

### Helpers privados de petición

| Función | Descripción |
|---------|-------------|
| [`_get_client_ip`](./_get_client_ip.md) | Obtiene la IP real del cliente (soporta proxy con `X-Forwarded-For`). |

### Helpers públicos de precio

| Función | Descripción |
|---------|-------------|
| [`get_price_with_vat_decimal`](./get_price_with_vat_decimal.md) | Calcula el precio con IVA aplicado, redondeado a 2 decimales. |

---

## 🛒 Carrito de compra

| Función | Descripción |
|---------|-------------|
| [`get_or_create_cart`](./get_or_create_cart.md) | Obtiene o crea el carrito del usuario/sesión actual. |
| [`add_to_cart`](./add_to_cart.md) | Agrega un producto al carrito. |
| [`view_cart`](./view_cart.md) | Muestra el contenido del carrito. |
| [`update_cart_item`](./update_cart_item.md) | Actualiza la cantidad de un ítem del carrito. |
| [`remove_from_cart`](./remove_from_cart.md) | Elimina un ítem del carrito. |
| [`clear_cart`](./clear_cart.md) | Vacía el carrito completo. |

---

## 📦 Reservas de stock

| Función | Descripción |
|---------|-------------|
| [`_get_or_create_session_key`](./_get_or_create_session_key.md) | Garantiza que la sesión tiene una clave activa. |
| [`_get_reservation_owner_filters`](./_get_reservation_owner_filters.md) | Filtros ORM para identificar al propietario de una reserva. |
| [`_release_expired_stock_reservations`](./_release_expired_stock_reservations.md) | Marca como expiradas las reservas caducadas. |
| [`_clear_stock_reservation_session`](./_clear_stock_reservation_session.md) | Elimina los datos de reserva de la sesión HTTP. |
| [`_cancel_active_stock_reservations_for_request`](./_cancel_active_stock_reservations_for_request.md) | Cancela las reservas activas del usuario/sesión actual. |
| [`_get_reserved_quantities_by_product`](./_get_reserved_quantities_by_product.md) | Calcula la cantidad reservada activamente por producto. |
| [`_get_active_reservation_ids_for_request`](./_get_active_reservation_ids_for_request.md) | Devuelve los IDs de reservas activas del usuario/sesión. |
| [`_get_available_stock_by_product`](./_get_available_stock_by_product.md) | Calcula el stock disponible real (total menos reservado). |
| [`_get_cart_stock_issues`](./_get_cart_stock_issues.md) | Detecta conflictos de stock en los ítems del carrito. |
| [`_build_stock_issue_message`](./_build_stock_issue_message.md) | Construye el mensaje de error para un conflicto de stock. |
| [`_create_stock_reservation_for_cart`](./_create_stock_reservation_for_cart.md) | Crea atómicamente una reserva de stock para el carrito. |
| [`_get_session_stock_reservation`](./_get_session_stock_reservation.md) | Recupera la reserva de stock activa desde la sesión. |

---

## 💳 Pedidos y checkout

| Función | Descripción |
|---------|-------------|
| [`_get_selected_shipping_address`](./_get_selected_shipping_address.md) | Obtiene y valida la dirección de envío seleccionada. |
| [`create_order_from_cart`](./create_order_from_cart.md) | Crea el pedido, descuenta stock y vacía el carrito. |
| [`checkout`](./checkout.md) | Página de checkout con resumen de carrito y direcciones. |
| [`checkout_success`](./checkout_success.md) | Página de confirmación de pago exitoso (Stripe). |
| [`checkout_cancel`](./checkout_cancel.md) | Página de cancelación de pago. |

---

## 💳 Pago con Stripe

| Función | Descripción |
|---------|-------------|
| [`stripe_config`](./stripe_config.md) | Expone la clave pública de Stripe al frontend. |
| [`create_checkout_session`](./create_checkout_session.md) | Crea una sesión de pago en Stripe Checkout. |

---

## 🅿️ Pago con PayPal

| Función | Descripción |
|---------|-------------|
| [`create_paypal_payment`](./create_paypal_payment.md) | Crea un pago en PayPal y devuelve la URL de aprobación. |
| [`paypal_execute`](./paypal_execute.md) | Confirma y ejecuta el pago de PayPal tras la aprobación. |

---

## 🏪 Panel de vendedor

| Función | Descripción |
|---------|-------------|
| [`mis_productos`](./mis_productos.md) | Lista de productos del vendedor autenticado. |
| [`pedidos_vendedor`](./pedidos_vendedor.md) | Lista de pedidos asignados al vendedor. |
| [`cambiar_estado_pedido`](./cambiar_estado_pedido.md) | Cambia el estado de un ítem de pedido. |
| [`enviar_mensaje_pedido`](./enviar_mensaje_pedido.md) | Envía un mensaje al comprador sobre un pedido. |
| [`crear_producto`](./crear_producto.md) | Formulario para crear un nuevo producto. |
| [`editar_producto`](./editar_producto.md) | Formulario para editar un producto existente. |
| [`borrar_producto`](./borrar_producto.md) | Elimina un producto del vendedor. |

---

## 👤 Portal de usuario

| Función | Descripción |
|---------|-------------|
| [`portal_usuario`](./portal_usuario.md) | Dashboard del portal de usuario. |
| [`mis_compras`](./mis_compras.md) | Historial de compras del usuario. |
| [`mis_recibos`](./mis_recibos.md) | Lista de recibos / pedidos pagados. |
| [`editar_perfil`](./editar_perfil.md) | Edita el perfil del usuario. |
| [`cambiar_contrasena`](./cambiar_contrasena.md) | Cambia la contraseña del usuario. |
| [`mensajes_comprador`](./mensajes_comprador.md) | Mensajes de vendedores al comprador. |

---

## 📍 Direcciones de envío

| Función | Descripción |
|---------|-------------|
| [`direcciones_usuario`](./direcciones_usuario.md) | Lista las direcciones del usuario. |
| [`crear_direccion`](./crear_direccion.md) | Crea una nueva dirección de entrega. |
| [`editar_direccion`](./editar_direccion.md) | Edita una dirección existente. |
| [`eliminar_direccion`](./eliminar_direccion.md) | Elimina una dirección. |

---

## 🔍 Búsqueda

| Función | Descripción |
|---------|-------------|
| [`search`](./search.md) | Búsqueda de productos por nombre y descripción. |
| [`search_suggestions`](./search_suggestions.md) | API AJAX de sugerencias para el autocompletado. |

---

## 🏷️ Catálogo público

| Función | Descripción |
|---------|-------------|
| [`home`](./home.md) | Página de inicio con productos destacados. |
| [`index`](./index.md) | Catálogo paginado de productos. |
| [`producto`](./producto.md) | Detalle de un producto (con caché Redis). |
| [`categoria`](./categoria.md) | Catálogo filtrado por categoría. |

---

## 🔐 Autenticación y cuentas

| Función | Descripción |
|---------|-------------|
| [`login`](./login.md) | Inicio de sesión. |
| [`register`](./register.md) | Registro de nuevo usuario. |
| [`logout`](./logout.md) | Cierre de sesión. |
| [`verify`](./verify.md) | Verificación de cuenta por email. |
| [`reset_password`](./reset_password.md) | Solicitud de restablecimiento de contraseña. |
| [`reset_password_phase2`](./reset_password_phase2.md) | Segunda fase: establecer la nueva contraseña. |

---

## 📄 Páginas estáticas y utilidades

| Función | Descripción |
|---------|-------------|
| [`rgpd`](./rgpd.md) | Página de política de privacidad / RGPD. |
| [`send_test_email`](./send_test_email.md) | Vista de prueba para envío de correo (solo desarrollo). |
