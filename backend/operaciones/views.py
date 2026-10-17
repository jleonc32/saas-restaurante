from django.shortcuts import render, get_object_or_404, redirect
from .models import Mesa, DisponibilidadSucursal, Pedido, DetallePedido, PerfilEmpleado
from gestion.models import Sucursal
import json
from django.http import JsonResponse, HttpResponse
from menu.models import Plato
from django.db.models import Count, Q
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.db.models import Sum, Count
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

# Esta función crea un decorador personalizado para verificar el rol
def rol_requerido(*roles_permitidos):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # Si no ha iniciado sesión o no tiene perfil, lo mandamos al login
            if not request.user.is_authenticated or not hasattr(request.user, 'perfil'):
                return redirect('login')
            # Si su rol no está en la lista de permitidos, le bloqueamos el paso
            if request.user.perfil.rol not in roles_permitidos:
                raise PermissionDenied 
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
User = get_user_model() # Trae tu modelo de usuario personalizado de forma segura

@rol_requerido('MESERO', 'GERENTE')
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

@rol_requerido('MESERO', 'GERENTE')
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

@rol_requerido('MESERO', 'GERENTE')
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

@rol_requerido('MESERO', 'GERENTE')
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

@rol_requerido('MESERO', 'GERENTE')
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

@rol_requerido('MESERO', 'GERENTE')
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

@rol_requerido('MESERO', 'GERENTE')
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

@rol_requerido('CHEF', 'GERENTE')
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

@rol_requerido('CHEF', 'GERENTE')
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

@rol_requerido('MESERO', 'GERENTE')
def entregar_pedido(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)
        # Cambiamos el estado confirmando que llegó a la mesa
        pedido.estado = 'ENTREGADO'
        pedido.save()
        
        # Lo devolvemos a la misma pantalla de gestión de esa mesa
        return redirect('ver_cuentas_mesa', mesa_id=pedido.mesa.id)
        
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'})

@rol_requerido('GERENTE')
def dashboard_gerencia(request, sucursal_id):
    sucursal = get_object_or_404(Sucursal, id=sucursal_id)
    
    pedidos_pagados = Pedido.objects.filter(
        mesa__sucursal=sucursal, 
        estado='PAGADO'
    )
    
    ingresos_totales = pedidos_pagados.aggregate(total=Sum('total_estimado'))['total'] or 0
    cantidad_ventas = pedidos_pagados.count()
    
    # NUEVO: Calculamos el ticket promedio directamente en el servidor (Python)
    ticket_promedio = (ingresos_totales / cantidad_ventas) if cantidad_ventas > 0 else 0
    
    platos_top = DetallePedido.objects.filter(
        pedido__in=pedidos_pagados
    ).values(
        'disponibilidad__plato__nombre'
    ).annotate(
        cantidad_vendida=Sum('cantidad')
    ).order_by('-cantidad_vendida')[:5]

    context = {
        'sucursal': sucursal,
        'ingresos_totales': ingresos_totales,
        'cantidad_ventas': cantidad_ventas,
        'ticket_promedio': ticket_promedio,  # Pasamos el valor ya calculado
        'platos_top': platos_top,
    }
    
    return render(request, 'operaciones/dashboard.html', context)


def login_empleado(request):
    # Si el usuario ya inició sesión, no le mostramos el login de nuevo, lo redirigimos
    if request.user.is_authenticated and hasattr(request.user, 'perfil'):
        rol = request.user.perfil.rol
        sucursal_id = request.user.perfil.sucursal.id
        if rol == 'MESERO': return redirect('panel_mesas', sucursal_id=sucursal_id)
        if rol == 'CHEF': return redirect('pantalla_cocina', sucursal_id=sucursal_id)
        if rol == 'GERENTE': return redirect('dashboard_gerencia', sucursal_id=sucursal_id)

    # Si apenas va a iniciar sesión
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            
            # Verificamos qué rol tiene para mandarlo a su pantalla
            if hasattr(usuario, 'perfil'):
                rol = usuario.perfil.rol
                sucursal_id = usuario.perfil.sucursal.id
                
                if rol == 'MESERO':
                    return redirect('panel_mesas', sucursal_id=sucursal_id)
                elif rol == 'CHEF':
                    return redirect('pantalla_cocina', sucursal_id=sucursal_id)
                elif rol == 'GERENTE':
                    return redirect('dashboard_gerencia', sucursal_id=sucursal_id)
            
            # Si es un superusuario sin perfil, lo mandamos al panel de admin
            return redirect('/admin/')
    else:
        form = AuthenticationForm()

    return render(request, 'operaciones/login.html', {'form': form})

def logout_empleado(request):
    logout(request) # Cierra la sesión en Django
    return redirect('login') # Lo devuelve al semáforo inicial


@rol_requerido('GERENTE')
def gestion_empleados(request, sucursal_id):
    sucursal = get_object_or_404(Sucursal, id=sucursal_id)
    error = None
    exito = None

    if request.method == 'POST':
        # Capturamos todos los campos del nuevo formulario
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol = request.POST.get('rol')
        email = request.POST.get('email')
        cedula = request.POST.get('cedula')
        telefono = request.POST.get('telefono')

        # 1. Validamos que el usuario no exista
        if User.objects.filter(username=username).exists():
            error = "Ese nombre de usuario ya está en uso."
        # 2. Validamos que el correo no esté repetido en la base de datos
        elif User.objects.filter(email=email).exists():
            error = "Ese correo electrónico ya está registrado."
        else:
            try:
                # 3. Creamos el usuario con su correo real
                nuevo_user = User.objects.create_user(
                    username=username, 
                    email=email, 
                    password=password
                )
                
                # 4. Creamos el perfil guardando la cédula y el teléfono
                PerfilEmpleado.objects.create(
                    usuario=nuevo_user, 
                    rol=rol, 
                    sucursal=sucursal,
                    cedula=cedula,
                    telefono=telefono
                )
                exito = f"Empleado '{username}' agregado correctamente."
            except Exception as e:
                error = f"Error al guardar: {str(e)}"

    empleados = PerfilEmpleado.objects.filter(sucursal=sucursal).order_by('rol')
    
    context = {
        'sucursal': sucursal,
        'empleados': empleados,
        'error': error,
        'exito': exito
    }
    return render(request, 'operaciones/gestion_empleados.html', context)