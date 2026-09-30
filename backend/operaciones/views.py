from django.shortcuts import render, get_object_or_404, redirect
from .models import Mesa, DisponibilidadSucursal, Pedido, DetallePedido
from gestion.models import Sucursal
import json
from django.http import JsonResponse, HttpResponse
from menu.models import Plato
from django.db.models import Count, Q
from django.template.loader import get_template
from xhtml2pdf import pisa


def panel_mesas(request, sucursal_id):
    # 1. Buscamos la sucursal específica
    sucursal = get_object_or_404(Sucursal, id=sucursal_id)
    
    # 2. Traemos las mesas, pero le "anotamos" cuántos pedidos activos tienen
    mesas = Mesa.objects.filter(sucursal=sucursal, esta_activa=True).annotate(
        cuentas_abiertas=Count(
            'pedidos', 
            # Filtramos para contar solo los pedidos que NO están pagados
            filter=Q(pedidos__estado__in=['RECIBIDO', 'PREPARACION', 'LISTO', 'ENTREGADO'])
        )
    ).order_by('identificador')
    
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
                estado='RECIBIDO'
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

def ver_cuentas_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    
    # Buscamos los pedidos de esta mesa que sigan activos
    pedidos_activos = Pedido.objects.filter(
        mesa=mesa,
        estado__in=['RECIBIDO', 'PREPARACION', 'LISTO', 'ENTREGADO']
    ).order_by('fecha_creacion')
    
    context = {
        'mesa': mesa,
        'pedidos': pedidos_activos,
    }
    return render(request, 'operaciones/ver_cuentas_mesa.html', context)

def detalle_cuenta(request, pedido_id):
    # Buscamos el pedido específico
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Traemos todos los platos que pertenecen a esta cuenta
    detalles = pedido.detalles.all()
    
    context = {
        'pedido': pedido,
        'detalles': detalles,
        'mesa': pedido.mesa,
    }
    return render(request, 'operaciones/detalle_cuenta.html', context)

def cobrar_pedido(request, pedido_id):
    if request.method == 'POST':
        # 1. Buscamos el pedido
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # 2. Le cambiamos el estado a PAGADO
        pedido.estado = 'PAGADO'
        pedido.save()
        
        # 3. Redirigimos al mesero de vuelta al mapa de mesas de su sucursal
        return redirect('panel_mesas', sucursal_id=pedido.mesa.sucursal.id)
        
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})

def imprimir_ticket(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    detalles = pedido.detalles.all()

    # 1. Cargamos nuestro diseño de ticket
    template = get_template('operaciones/ticket_pdf.html')
    context = {
        'pedido': pedido,
        'detalles': detalles,
        'mesa': pedido.mesa,
    }
    html = template.render(context)

    # 2. Configuramos la respuesta para que el navegador sepa que es un PDF
    response = HttpResponse(content_type='application/pdf')
    # Usamos 'inline' para que el PDF se abra en una pestaña nueva listo para imprimir
    response['Content-Disposition'] = f'inline; filename="ticket_{pedido.id}.pdf"'

    # 3. La magia de xhtml2pdf convirtiendo todo
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Hubo un error al generar el PDF', status=500)

    return response

def pantalla_cocina(request, sucursal_id):
    sucursal = get_object_or_404(Sucursal, id=sucursal_id)
    
    # Traemos solo los pedidos que la cocina necesita ver y los ordenamos por el más antiguo primero
    pedidos = Pedido.objects.filter(
        mesa__sucursal=sucursal,
        estado__in=['RECIBIDO', 'PREPARACION']
    ).order_by('fecha_creacion')
    
    context = {
        'sucursal': sucursal,
        'pedidos': pedidos,
    }
    return render(request, 'operaciones/pantalla_cocina.html', context)

def actualizar_estado_pedido(request, pedido_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')
            
            pedido = get_object_or_404(Pedido, id=pedido_id)
            pedido.estado = nuevo_estado
            pedido.save()
            
            return JsonResponse({'status': 'success', 'nuevo_estado': pedido.estado})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)})
            
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})

def entregar_pedido(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)
        # Cambiamos el estado confirmando que llegó a la mesa
        pedido.estado = 'ENTREGADO'
        pedido.save()
        
        # Lo devolvemos a la misma pantalla de gestión de esa mesa
        return redirect('ver_cuentas_mesa', mesa_id=pedido.mesa.id)
        
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})