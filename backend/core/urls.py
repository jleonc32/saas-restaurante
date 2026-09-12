from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from menu.views import menu_digital

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esta es la URL mágica. Captura el UUID del QR y se lo pasa a la vista
    path('menu/<uuid:qr_token>/', menu_digital, name='menu_digital'),
]

# Esto solo se usa en desarrollo local para poder ver las fotos y archivos 3D
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
    