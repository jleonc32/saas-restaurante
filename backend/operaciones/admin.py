from django.contrib import admin
from .models import DisponibilidadSucursal, Mesa, Pedido, DetallePedido

class MesaAdmin(admin.ModelAdmin):
    reandoly_fields= ('qr_token',)
    list_display = ('identificador', 'sucursal', 'qr_token', 'esta_activa')

admin.site.register(DisponibilidadSucursal)
admin.site.register(Mesa, MesaAdmin)
admin.site.register(Pedido)
admin.site.register(DetallePedido)