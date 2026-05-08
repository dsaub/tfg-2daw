# Solución de Problemas - PayPal

## Si ves "Error al procesar el pago con PayPal"

### Paso 1: Abre la Consola del Navegador
1. Presiona **F12** o **Cmd+Option+I** (Mac)
2. Ve a la pestaña **Console**

### Paso 2: Busca el mensaje de error
Cuando hagas clic en "Pagar con PayPal", deberías ver en la consola:
- `CSRF Token encontrado: Sí`
- `Response status: 200`
- `Response data: {"redirect": "https://www.sandbox.paypal.com/..."}`
- `Redirigiendo a: https://www.sandbox.paypal.com/...`

### Paso 3: Interpreta los errores

#### Error: "CSRF Token encontrado: No"
**Solución:**
- El formulario no tiene token CSRF
- Asegúrate de que `{% csrf_token %}` esté en el template checkout.html
- Recarga la página (Ctrl+Shift+R)

#### Error: "Response status: 403"
**Causa:** Error de CSRF token o permisos
**Solución:**
- Verifica que estés logueado
- Limpia cookies: Settings > Clear browsing data > Cookies
- Recarga la página

#### Error: "Response status: 500"
**Causa:** Error en el servidor
**Solución:**
- Ve a la terminal donde corre Django
- Busca el mensaje de error (stack trace en rojo)
- Verifica que `PAYPAL_CLIENT_ID` y `PAYPAL_CLIENT_SECRET` estén correctos en settings.py

#### Error: "Error inesperado al procesar el pago"
**Solución:**
- Mira en la consola qué dice exactamente
- Copia el error completo
- Revisa los logs de Django en la terminal

### Paso 4: Verifica el Backend

En la terminal donde corre Django, deberías ver:
```
[00/Month/2026 12:00:00] "POST /tienda/paypal/create-payment/ HTTP/1.1" 200 123
```

Si ves un error (4xx o 5xx), el problema está en el servidor.

### Paso 5: Test Manual

Ejecuta en la terminal:
```bash
cd /home/daniel/projects/proyecto/proyecto2/proyecto
.venv/bin/python test_paypal.py
```

Si todo está bien, deberías ver:
```
✓ paypalrestsdk importado correctamente
✓ Configuración de PayPal aplicada
✓ Pago creado exitosamente
```

## Checklist de Configuración

- [ ] `uv add paypalrestsdk` (verificar con: `uv pip list | grep paypal`)
- [ ] `PAYPAL_CLIENT_ID` en settings.py (no vacío)
- [ ] `PAYPAL_CLIENT_SECRET` en settings.py (no vacío)
- [ ] `PAYPAL_MODE = 'sandbox'` en settings.py
- [ ] `{% csrf_token %}` en checkout.html
- [ ] El usuario está autenticado (login requerido)
- [ ] El carrito tiene items

## Credenciales de Prueba

Si necesitas nuevas credenciales:
1. Ve a https://sandbox.paypal.com/
2. Login con tu cuenta
3. Ve a Dashboard > Apps & Credentials
4. Copia Client ID y Secret
5. Actualiza en settings.py
6. Recarga la página

## Logs Útiles

Para ver más detalles, edita `/tienda/views.py` y busca la función `create_paypal_payment`:
- Ya tiene `print()` para loguear errores
- Verás los mensajes en la terminal de Django

## Contacto con PayPal

Si todo lo anterior no funciona:
- El problema puede ser con las credenciales de PayPal
- Verifica que sean del **SANDBOX** (no production)
- Intenta regenerar las credenciales en paypal.com
