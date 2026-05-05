from django.contrib import admin
from .models import Category, Image, Product, Cart, CartItem, Order, OrderItem, OrderMessage, StockReservation, StockReservationItem, User, VerificationCode, SavedPaymentMethod
# Register your models here.

admin.site.register(Category)
admin.site.register(Image)
admin.site.register(User)
admin.site.register(VerificationCode)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'name', 'price', 'stock', 'category', 'creator')
    search_fields = ('name', 'sku', 'creator__username', 'creator__email')
    list_filter = ('category',)
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'get_items_count', 'get_total', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'session_key')
    inlines = [CartItemInline]
    
    def get_items_count(self, obj):
        return obj.get_items_count()
    get_items_count.short_description = 'Productos'
    
    def get_total(self, obj):
        return f"{obj.get_total()} €"
    get_total.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'get_subtotal', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('product__name', 'cart__user__username')
    
    def get_subtotal(self, obj):
        return f"{obj.get_subtotal()} €"
    get_subtotal.short_description = 'Subtotal'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_code', 'buyer', 'total', 'status', 'payment_method', 'payment_reference', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('buyer__username', 'buyer__email', 'payment_reference', 'transaction_code')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'seller', 'quantity', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product_name', 'seller__username', 'order__buyer__username')


@admin.register(OrderMessage)
class OrderMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_item', 'sender', 'message_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('sender__username', 'message', 'order_item__product_name')
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Mensaje'


class StockReservationItemInline(admin.TabularInline):
    model = StockReservationItem
    extra = 0


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'status', 'payment_method', 'expires_at', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'user__email', 'session_key')
    inlines = [StockReservationItemInline]


@admin.register(SavedPaymentMethod)
class SavedPaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'method_type', 'label', 'is_default', 'created_at')
    list_filter = ('method_type', 'is_default', 'created_at')
    search_fields = ('user__username', 'user__email', 'label', 'paypal_email')