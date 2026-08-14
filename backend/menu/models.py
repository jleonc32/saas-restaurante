from django.db import models
# Importamos el modelo Marca desde la app gestion para poder relacionarlo
from gestion.models import Marca

# 1. TABLA CATEGORIA
class Categoria(models.Model):
    # Relación 1 a N: Una Marca tiene muchas Categorías
    marca = models.ForeignKey(
        Marca, 
        on_delete=models.CASCADE, 
        related_name='categorias'
    )
    nombre = models.CharField(max_length=150)
    orden = models.PositiveSmallIntegerField(
        default=0, 
        help_text="Define el orden en el que aparecerá en el menú (ej. 1, 2, 3...)"
    )

    def __str__(self):
        return f"{self.marca.nombre_comercial} - {self.nombre}"

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['orden'] # Esto asegura que Django siempre las devuelva ordenadas


# 2. TABLA PLATO
class Plato(models.Model):
    # Relación 1 a N: Una Categoría tiene muchos Platos
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.CASCADE, 
        related_name='platos'
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=300, blank=True)
    
    # max_digits=10 y decimal_places=2 equivale exactamente a tu DecimalField(10,2)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Archivos multimedia
    imagen_foto = models.ImageField(
        upload_to='platos/fotos/', 
        null=True, 
        blank=True
    )
    archivo_ar_3d = models.FileField(
        upload_to='platos/ar_models/', 
        null=True, 
        blank=True,
        help_text="Sube aquí el archivo .gltf o .usdz para la Realidad Aumentada"
    )

    def __str__(self):
        return self.nombre
