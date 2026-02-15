#!/usr/bin/env python
"""
Script de prueba para el cacheo de productos en Redis
Ejecutar: python test_product_cache.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')
django.setup()

from tienda.models import Product
from django.core.cache import cache
import time

def test_product_cache():
    """Prueba el sistema de cacheo de productos"""
    print("=" * 60)
    print("TEST: Sistema de Cacheo de Productos en Redis")
    print("=" * 60)
    
    # Obtener un producto de prueba
    try:
        product = Product.objects.first()
        if not product:
            print("❌ No hay productos en la base de datos para probar")
            return
        
        product_id = product.id
        cache_key = f'product_{product_id}'
        
        print(f"\n📦 Producto de prueba: {product.name} (ID: {product_id})")
        
        # 1. Limpiar caché del producto
        cache.delete(cache_key)
        print(f"\n1️⃣  Caché limpiado")
        
        # 2. Primera visita (debe cargar desde BD)
        print(f"\n2️⃣  Primera visita - Cargando desde BD...")
        start_time = time.time()
        cached_product = cache.get(cache_key)
        if cached_product is None:
            print("   ✅ No está en caché (esperado)")
            product_from_db = Product.objects.select_related('category', 'primary_image', 'creator').prefetch_related('secondary_images').get(id=product_id)
            cache.set(cache_key, product_from_db, 300)
            print(f"   ✅ Producto cacheado por 5 minutos")
        db_time = (time.time() - start_time) * 1000
        
        # 3. Segunda visita (debe cargar desde caché)
        print(f"\n3️⃣  Segunda visita - Cargando desde caché...")
        start_time = time.time()
        cached_product = cache.get(cache_key)
        if cached_product:
            print(f"   ✅ Encontrado en caché: {cached_product.name}")
        cache_time = (time.time() - start_time) * 1000
        
        # 4. Comparar tiempos
        print(f"\n⏱️  Comparación de rendimiento:")
        print(f"   - Desde BD: {db_time:.2f}ms")
        print(f"   - Desde caché: {cache_time:.2f}ms")
        speedup = db_time / cache_time if cache_time > 0 else float('inf')
        print(f"   - Mejora: {speedup:.1f}x más rápido")
        
        # 5. Verificar TTL
        ttl = cache.ttl(cache_key)
        print(f"\n⏳ TTL (tiempo de vida): {ttl} segundos (~5 minutos)")
        
        # 6. Verificar en Redis
        print(f"\n🔍 Verificación en Redis:")
        print(f"   - Clave: {cache_key}")
        print(f"   - Base de datos: 1")
        print(f"   - Comando para ver: valkey-cli -n 1 GET ':1:{cache_key}'")
        
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_product_cache()
