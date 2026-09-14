from django.contrib import admin
from django.utils.html import format_html #nuevo para poder inyectar HTML (la imagen) en el panel
from .models import DisponibilidadSucursal, Mesa, Pedido, DetallePedido

class MesaAdmin(admin.ModelAdmin):
    readonly_fields= ('qr_token', 'qr_imagen', 'ver_qr_grande')
    list_display = ('identificador', 'sucursal', 'ver_qr_pequeno', 'esta_activa')
    
    #funcion para mostrar un QR pequeñito en la lista general
    def ver_qr_pequeno(self, obj):
        if obj.qr_imagen:
            return format_html('<img src="{}" width="40" height="40" />', obj.qr_imagen.url)
        return "-"
    ver_qr_pequeno.short_description = "Código QR"
    
    #funcion para mostrar el QR grande al entrar a editar la mesa
    def ver_qr_grande(self, obj):
        if obj.qr_imagen:
            return format_html('<img src="{}" width="200" height="200" />', obj.qr_imagen.url)
        return "-"
    ver_qr_grande.short_description = "Vista Previa QR"

admin.site.register(DisponibilidadSucursal)
admin.site.register(Mesa, MesaAdmin)
admin.site.register(Pedido)
admin.site.register(DetallePedido)