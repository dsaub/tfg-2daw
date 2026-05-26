from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinLengthValidator, MaxLengthValidator
from .models import Category
from .constants import *
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']




def validate_image_file(value):
    ext = value.name.split('.')[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(f'Tipo de archivo no permitido. Allowed: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}')
    if hasattr(value, 'content_type') and value.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(f'Tipo MIME no permitido. Allowed: {", ".join(ALLOWED_MIME_TYPES)}')


class ProductForm(forms.Form): 
    name = forms.CharField(
        label="Nombre del Producto", 
        max_length=200,
        required = True,
        widget=forms.TextInput(
            attrs = {
                'class': 'form-control',
                'placeholder': 'Ej: iPhone 15 Pro Max'
            }
        )
    )
    briefdesc = forms.CharField(
        label="Descripción Breve", 
        max_length=250,
        required = True,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control',
                'placeholder': 'Una descripción corta para mostrar en las tarjetas de producto'
            }
        )
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "5", "class": "form-control"}), 
        max_length=5000, 
        label="Descripción completa",
        required = True
    )
    price = forms.FloatField(
        label="Precio (en €)",
        required = True,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control',
                'placeholder': '15.99'
            }
        )
    )
    stock = forms.IntegerField(
        label="Stock Disponible",
        required = True,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control'
            }
        )
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Categoría",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    primary_image = forms.ImageField(
        label="Imagen Principal",
        required = False,
        validators=[validate_image_file],
        widget = forms.ClearableFileInput(
            attrs = {
                'class': 'form-control',
                'accept': IMAGE_TYPE
            }
        )
    )


class ProductEditForm(forms.Form):
    name = forms.CharField(
        label="Nombre del Producto",
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: iPhone 15 Pro Max'})
    )
    briefdesc = forms.CharField(
        label="Descripción Breve",
        max_length=250,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Una descripción corta'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": "5", "class": "form-control"}),
        max_length=5000,
        label="Descripción completa",
        required=True
    )
    price = forms.FloatField(
        label="Precio (en €)",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '15.99'})
    )
    stock = forms.IntegerField(
        label="Stock Disponible",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Categoría",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    primary_image = forms.ImageField(
        label="Imagen Principal (opcional)",
        required=False,
        validators=[validate_image_file],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )


class SecondaryImageForm(forms.Form):
    image = forms.ImageField(
        label="Seleccionar Imagen",
        required = True,
        validators=[validate_image_file],
        widget = forms.ClearableFileInput(
            attrs = {
                'class': 'form-control',
                'accept': IMAGE_TYPE
            }
        )
    )
    alt = forms.CharField(
        label="Texto Alternativo",
        max_length=255,
        required = False,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control',
                'placeholder': 'Descripción opcional de la imagen'
            }
        )
    )


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        label = "Correo Electrónico",
        max_length=255,
        required = True,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control',
                'placeholder': 'Correo Electronico de tu cuenta...'
            }
        )
    )
    password = forms.CharField(
        label="Contraseña",
        max_length = 255,
        required = True,
        widget = forms.PasswordInput(
            attrs = {
                'class': 'form-control',
                'placeholder': 'Contraseña del usuario'
            }
        )
    )
    remember = forms.BooleanField(
        required = False,
        label = "Recuerdame",
        widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )   


class UserRegisterForm(forms.Form):
    name = forms.CharField(
        label = "Nombre Completo",
        max_length = 255,
        required = True,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control'
            }
        )
    )
    email = forms.EmailField(
        label = EMAIL_FORMNAME,
        max_length = 255,
        required = True,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control'
            }
        )
    )
    password = forms.CharField(
        label = "Contraseña",
        max_length = 255,
        min_length = 8,
        required = True,
        validators=[MinLengthValidator(8)],
        widget = forms.PasswordInput(
            attrs = {
                'class': 'form-control'
            }
        )
    )
    password_confirm = forms.CharField(
        label = "Verificar Contraseña",
        max_length = 255,
        min_length = 8,
        required = True,
        validators=[MinLengthValidator(8)],
        widget = forms.PasswordInput(
            attrs = {
                'class': 'form-control'
            }
        )
    )
    terms = forms.BooleanField(
        required = True,
        label = "Acepto los terminos y condiciones",
        widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise ValidationError(INCORRECT_PASSWORDS)


class EditProfileForm(forms.Form):
    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label=EMAIL_FORMNAME,
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label="Contraseña Actual",
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password = forms.CharField(
        label="Nueva Contraseña",
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        label="Confirmar Nueva Contraseña",
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError(INCORRECT_PASSWORDS)
        if new_password and len(new_password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")


class ShippingAddressForm(forms.Form):
    full_name = forms.CharField(
        label="Nombre Completo",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan Pérez García'})
    )
    address_line_1 = forms.CharField(
        label="Dirección",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle Mayor 123'})
    )
    address_line_2 = forms.CharField(
        label="Dirección (línea 2)",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Piso, puerta, etc.'})
    )
    city = forms.CharField(
        label="Población",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Almería'})
    )
    postal_code = forms.CharField(
        label="Código Postal",
        max_length=5,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '04001'})
    )
    country = forms.CharField(
        label="País",
        max_length=100,
        required=False,
        initial="España",
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    phone = forms.CharField(
        label="Teléfono",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '612 345 678'})
    )
    is_default = forms.BooleanField(
        label="Establecer como dirección predeterminada",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ResetPasswordForm(forms.Form):
    email = forms.EmailField(
        label=EMAIL_FORMNAME,
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@email.com'})
    )


class ResetPasswordPhase2Form(forms.Form):
    password = forms.CharField(
        label="Nueva Contraseña",
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    verify_password = forms.CharField(
        label="Confirmar Contraseña",
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        verify_password = cleaned_data.get("verify_password")
        if password and verify_password and password != verify_password:
            raise ValidationError(INCORRECT_PASSWORDS)


class ReviewForm(forms.Form):
    rating = forms.IntegerField(
        label="Puntuación",
        required=True,
        min_value=1,
        max_value=5,
        widget=forms.HiddenInput()
    )
    title = forms.CharField(
        label="Título",
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Título de tu valoración'
        })
    )
    content = forms.CharField(
        label="Descripción",
        max_length=2000,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Comparte tu experiencia con este producto...'
        })
    )