from django.contrib import admin
from .models import Usuario, Marca, Sucursal, Suscripcion

# Registramos nuestros modelos para que aparezcan en el panel
admin.site.register(Usuario)
admin.site.register(Marca)
admin.site.register(Sucursal)
admin.site.register(Suscripcion)