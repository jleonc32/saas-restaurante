from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from menu.views import menu_digital
from operaciones.views import panel_mesas, tomar_pedido, procesar_pedido, ver_cuentas_mesa, detalle_cuenta, cobrar_pedido, imprimir_ticket, pantalla_cocina, actualizar_estado_pedido, entregar_pedido
urlpatterns = [
    path('admin/', admin.site.urls),
    # Esta es la URL mágica. Captura el UUID del QR y se lo pasa a la vista
    path('menu/<uuid:qr_token>/', menu_digital, name='menu_digital'),
    path('mesero/<int:sucursal_id>/', panel_mesas, name='panel_mesas'),
    path('mesero/mesa/<int:mesa_id>/', tomar_pedido, name='tomar_pedido'),
    path('mesero/procesar-pedido/', procesar_pedido, name='procesar_pedido'),
    path('mesero/mesa/<int:mesa_id>/cuentas/', ver_cuentas_mesa, name='ver_cuentas_mesa'),
    # NUEVA RUTA: Para ver y cobrar una cuenta específica
    path('mesero/cuenta/<int:pedido_id>/', detalle_cuenta, name='detalle_cuenta'),
    # NUEVA RUTA: La acción invisible que procesa el pago
    path('mesero/cuenta/<int:pedido_id>/cobrar/', cobrar_pedido, name='cobrar_pedido'),
    # NUEVA RUTA: Generador del PDF
    path('mesero/cuenta/<int:pedido_id>/ticket/', imprimir_ticket, name='imprimir_ticket'),
    # RUTAS DE LA COCINA
    path('cocina/<int:sucursal_id>/', pantalla_cocina, name='pantalla_cocina'),
    path('cocina/actualizar-estado/<int:pedido_id>/', actualizar_estado_pedido, name='actualizar_estado_pedido'),
    path('mesero/cuenta/<int:pedido_id>/entregar/', entregar_pedido, name='entregar_pedido'),
]

# Esto solo se usa en desarrollo local para poder ver las fotos y archivos 3D
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
    