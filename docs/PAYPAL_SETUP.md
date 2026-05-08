# Configuración de PayPal

## Pasos para configurar PayPal en el proyecto

### 1. Crear una cuenta de PayPal Developer
- Ve a https://developer.paypal.com/
- Crea una cuenta o inicia sesión con tu cuenta de PayPal

### 2. Acceder al Sandbox
- En el dashboard de PayPal Developer, ve a "Sandbox"
- Aquí encontrarás credenciales de prueba

### 3. Obtener las credenciales
- En la sección "Accounts" del Sandbox, encontrarás:
  - **Business Account** (vendedor)
  - **Personal Account** (comprador de prueba)
- Para cada cuenta, haz clic en "Show" junto a "API Signature" o "API Certificate"
- También puedes usar las credenciales REST API

### 4. Obtener Client ID y Client Secret (REST API)
- En el dashboard, ve a **"Apps & Credentials"**
- Selecciona **Sandbox** (arriba a la derecha)
- Ve a la pestaña **"REST API apps"**
- Haz clic en el app por defecto o crea uno nuevo
- Verás:
  - **Client ID** (tu PAYPAL_CLIENT_ID)
  - **Secret** (tu PAYPAL_CLIENT_SECRET)

### 5. Actualizar settings.py
Edita el archivo `proyecto/settings.py` y reemplaza:

```python
PAYPAL_CLIENT_ID = 'YOUR_PAYPAL_CLIENT_ID'
PAYPAL_CLIENT_SECRET = 'YOUR_PAYPAL_CLIENT_SECRET'
PAYPAL_MODE = 'sandbox'  # Cambiar a 'live' en producción
```

Con tus valores reales del Sandbox.

### 6. Instalar el SDK de PayPal
```bash
uv add paypalrestsdk
```

### 7. Usar cuentas de prueba para transacciones
En Sandbox puedes usar las cuentas de prueba:
- **Email de vendedor**: El que aparece en el Business Account
- **Email de comprador**: El que aparece en el Personal Account

Ambas cuentas tienen saldo de prueba disponible.

## Pasar a Producción

Para usar PayPal en producción:

1. Cambia `PAYPAL_MODE = 'live'` en settings.py
2. Reemplaza `PAYPAL_CLIENT_ID` y `PAYPAL_CLIENT_SECRET` con las credenciales reales (no de Sandbox)
3. Obten tus credenciales reales en https://www.paypal.com/cgi-bin/customerprofileweb?cmd=_profile-api-signature

## Métodos de Pago Disponibles

Actualmente el proyecto soporta:
- **Stripe** 💳
- **PayPal** 🅿️

Ambos métodos están disponibles en la página de checkout.

## Notas de Seguridad

- NUNCA commits las credenciales reales en git
- Usa variables de entorno en producción
- Mantén tus claves secretas privadas
- El modo Sandbox es solo para pruebas

## Testear PayPal

1. Ve a la página de Checkout
2. Haz clic en "Pagar con PayPal"
3. Se abrirá PayPal Sandbox
4. Usa las credenciales de la cuenta de prueba (Personal Account)
5. Completa el pago simulado
6. Serás redirigido a la página de éxito
