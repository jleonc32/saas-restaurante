from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# 1. TABLA USUARIO
# Heredamos de AbstractUser para tener password encriptado y login gratis
class Usuario(AbstractUser):
    # Django ya incluye first_name, last_name, username y password.
    # Solo forzamos que el email sea único.
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


# 2. TABLA MARCA
class Marca(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='marcas')
    nombre_comercial = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='marcas/logos/', null=True, blank=True)
    color_principal = models.CharField(max_length=7, default='#000000', help_text="Color Hexadecimal")

    def __str__(self):
        return self.nombre_comercial


# 3. TABLA SUCURSAL
class Sucursal(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='sucursales')
    nombre_sucursal = models.CharField(max_length=105)
    direccion = models.CharField(max_length=250)
    enlace_maps = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.marca.nombre_comercial} - {self.nombre_sucursal}"


# 4. TABLA SUSCRIPCION
class Suscripcion(models.Model):
    PLANES = [
        ('GRATIS', 'Plan Gratuito'),
        ('PREMIUM', 'Plan Premium (AR)'),
    ]
    
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='suscripciones')
    tipo_plan = models.CharField(max_length=50, choices=PLANES, default='GRATIS')
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado_activa = models.BooleanField(default=True)
    id_gateway = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Plan {self.tipo_plan} - {self.marca.nombre_comercial}"