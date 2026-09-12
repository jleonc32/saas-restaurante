from django.shortcuts import render, get_object_or_404
from operaciones.models import Mesa, DisponibilidadSucursal

def menu_digital(request, qr_token):
    # 1. Buscamos la mesa usando el token único del QR. 
    # Si el token no existe, Django mostrará un error 404 automático.
    mesa = get_object_or_404(Mesa, qr_token=qr_token, esta_activa=True)
    sucursal = mesa.sucursal
    marca = sucursal.marca
    
    # 2. Buscamos los platos activos SOLO de esta sucursal
    # select_related hace que la consulta a la base de datos sea ultra rápida
    platos_disponibles = DisponibilidadSucursal.objects.filter(
        sucursal=sucursal, 
        estado_activo=True
    ).select_related('plato', 'plato__categoria')
    
    # 3. Organizamos los platos por categoría para que el HTML los dibuje fácil
    menu_organizado = {}
    for item in platos_disponibles:
        categoria = item.plato.categoria
        if categoria not in menu_organizado:
            menu_organizado[categoria] = []
        menu_organizado[categoria].append(item)
        
    context = {
        'mesa' : mesa,
        'sucursal' : sucursal,
        'marca' : marca,
        'menu_organizado' : menu_organizado,
    }
        
    return render(request, 'menu/menu_digital.html', context)    


# Create your views here.
