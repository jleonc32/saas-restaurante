from django.shortcuts import render, get_object_or_404
from .models import Mesa, DisponibilidadSucursal, Pedido, DetallePedido
from gestion.models import Sucursal
import json
from django.http import JsonResponse
from menu.models import Plato

def panel_mesas(request, sucursal_id):
    # 1. Buscamos la sucursal específica donde está trabajando el mesero
    sucursal = get_object_or_404(Sucursal, id=sucursal_id)
    
    # 2. Traemos todas las mesas que estén activas, ordenadas por nombre
    mesas = Mesa.objects.filter(sucursal=sucursal, esta_activa=True).order_by('identificador')
    
    context = {
        'sucursal' : sucursal,
        'mesas' : mesas,
    }

    return render(request, 'operaciones/panel_mesas.html', context)

def tomar_pedido(request, mesa_id):
    
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    
    menu_disponible = DisponibilidadSucursal.objects.filter(
        sucursal=mesa.sucursal,
        estado_activo=True
    ).select_related('plato', 'plato__categoria')
    
    context = {
        'mesa' : mesa,
        'menu_disponible' : menu_disponible,
    }
    
    return render(request, 'operaciones/tomar_pedido.html', context)

def procesar_pedido(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mesa_id = data['mesa_id']
            items = data['items']
            total = data['total']
            
            mesa = Mesa.objects.get(id=mesa_id)
            
            # CORRECCIÓN 1: Usamos 'total_estimado' y 'PAGADO' (en mayúsculas como en tu modelo)
            nuevo_pedido = Pedido.objects.create(
                mesa=mesa,
                total_estimado=total,
                estado='PAGADO'
            )

            for item in items:
                # CORRECCIÓN 2: Buscamos la Disponibilidad específica de esa sucursal, no el Plato suelto
                disponibilidad = DisponibilidadSucursal.objects.get(
                    plato__id=item['id'],
                    sucursal=mesa.sucursal
                )
                
                # CORRECCIÓN 3: Usamos 'disponibilidad' y 'subtotal' calculando cantidad * precio
                subtotal_item = float(item['precio']) * int(item['cantidad'])
                
                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    disponibilidad=disponibilidad,
                    cantidad=item['cantidad'],
                    subtotal=subtotal_item
                )
                
            return JsonResponse({'status': 'success', 'mensaje': 'Pedido cobrado y guardado con éxito'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)})
    
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})