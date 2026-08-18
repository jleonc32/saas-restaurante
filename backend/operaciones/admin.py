from django.contrib import admin
from .models import DisponibilidadSucursal, Mesa, Pedido, DetallePedido

admin.site.register(DisponibilidadSucursal)
admin.site.register(Mesa)
admin.site.register(Pedido)
admin.site.register(DetallePedido)