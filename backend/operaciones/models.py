import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings # Para importar tu modelo de Usuario personalizado

# Importamos los modelos de las otras apps
from gestion.models import Sucursal
from menu.models import Plato

# 1. TABLA PUENTE: DISPONIBILIDAD SUCURSAL (Inventario local)
class DisponibilidadSucursal(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='inventario')
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name='disponibilidad')
    
    estado_activo = models.BooleanField(
        default=True, 
        help_text="¿Este plato se está vendiendo en esta sucursal hoy?"
    )
    precio_local = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio específico para esta sucursal (puede variar de la base)"
    )

    def __str__(self):
        return f"{self.sucursal.nombre_sucursal} - {self.plato.nombre}"

    class Meta:
        verbose_name = "Disponibilidad en Sucursal"
        verbose_name_plural = "Disponibilidad en Sucursales"
        unique_together = ('sucursal', 'plato') # Evita que un plato se duplique en la misma sucursal


# 2. TABLA MESA
class Mesa(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='mesas')
    identificador = models.CharField(max_length=50, help_text="Ej: Mesa 5, VIP 1, Terraza")
    qr_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    esta_activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sucursal.nombre_sucursal} - {self.identificador}"

    class Meta:
        unique_together = ('sucursal', 'identificador')


# 3. TABLA PEDIDO (La orden general)
class Pedido(models.Model):
    ESTADOS = [
        ('RECIBIDO', 'Recibido'),
        ('PREPARACION', 'En Preparación'),
        ('LISTO', 'Listo para entregar'),
        ('ENTREGADO', 'Entregado'),
        ('PAGADO', 'Pagado'),
    ]

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='pedidos')
    
    # Apuntamos al usuario (que en este caso actuará como el Mesero)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='pedidos_tomados')
    
    estado = models.CharField(max_length=50, choices=ESTADOS, default='RECIBIDO')
    esta_activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    total_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Pedido #{self.id} - {self.mesa}"


# 4. TABLA DETALLE PEDIDO (Los platos dentro de la orden)
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    
    # ¡Clave! Apuntamos a DisponibilidadSucursal, no a Plato directamente
    disponibilidad = models.ForeignKey(DisponibilidadSucursal, on_delete=models.RESTRICT)
    
    cantidad = models.PositiveIntegerField(default=1)
    notas_clientes = models.TextField(blank=True, help_text="Ej: Sin cebolla, extra salsa")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad}x {self.disponibilidad.plato.nombre} (Pedido #{self.pedido.id})"