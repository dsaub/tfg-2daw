#!/usr/bin/env python
"""
Script para testear la configuración de PayPal
Ejecutar: python test_paypal.py
"""
import os
import sys
import django

def main() -> None:
    # Configurar Django solo cuando se ejecuta script manualmente.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
    sys.path.insert(0, os.path.dirname(__file__))
    django.setup()

    from django.conf import settings

    print("=" * 60)
    print("TEST DE CONFIGURACIÓN DE PAYPAL")
    print("=" * 60)

    # Verificar configuración
    print("\n1. Verificando configuración en settings.py:")
    print(f"   PAYPAL_MODE: {settings.PAYPAL_MODE}")
    print(f"   PAYPAL_CLIENT_ID: {settings.PAYPAL_CLIENT_ID[:20]}..." if settings.PAYPAL_CLIENT_ID else "   ❌ NO CONFIGURADO")
    print(f"   PAYPAL_CLIENT_SECRET: {settings.PAYPAL_CLIENT_SECRET[:20]}..." if settings.PAYPAL_CLIENT_SECRET else "   ❌ NO CONFIGURADO")

    # Intentar importar paypalrestsdk
    print("\n2. Verificando SDK de PayPal:")
    try:
        import paypalrestsdk
        print("   ✓ paypalrestsdk importado correctamente")
        print(f"   Versión: {paypalrestsdk.__version__ if hasattr(paypalrestsdk, '__version__') else 'Desconocida'}")
    except ImportError as e:
        print(f"   ❌ Error: {e}")
        print("   SOLUCIÓN: uv add paypalrestsdk")
        sys.exit(1)

    # Intentar conectar a PayPal
    print("\n3. Probando conexión a PayPal:")
    try:
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })
        print("   ✓ Configuración de PayPal aplicada")

        # Intentar crear un pago de prueba
        print("\n4. Creando pago de prueba:")
        test_payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": "http://localhost:8000/test-return",
                "cancel_url": "http://localhost:8000/test-cancel"
            },
            "transactions": [
                {
                    "amount": {
                        "total": "10.00",
                        "currency": "EUR",
                        "details": {
                            "subtotal": "10.00",
                            "tax": "0",
                            "shipping": "0"
                        }
                    },
                    "description": "Pago de prueba",
                    "item_list": {
                        "items": [
                            {
                                "name": "Test Item",
                                "sku": "test_1",
                                "price": "10.00",
                                "currency": "EUR",
                                "quantity": 1
                            }
                        ]
                    }
                }
            ]
        })

        if test_payment.create():
            print("   ✓ Pago creado exitosamente")
            print(f"   Payment ID: {test_payment.id}")
            for link in test_payment.links:
                if link.rel == "approval_url":
                    print(f"   URL de aprobación: {link.href}")
        else:
            print("   ❌ Error al crear el pago:")
            if hasattr(test_payment, 'error') and test_payment.error:
                print(f"   {test_payment.error}")

    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("TEST COMPLETADO")
    print("=" * 60)


if __name__ == '__main__':
    main()
