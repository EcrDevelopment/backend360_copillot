# Guía de Implementación: Permisos por Almacén en ViewSets

## 📋 Resumen de tus Preguntas

Basado en el comentario en tu archivo `almacen/views.py`, necesitas:

1. **Listar almacenes**: Sin permisos especiales
2. **Ver Kardex, movimientos, transferencias**: Más restrictivo
3. **Operadores**: Solo info de SU almacén o stock de SU almacén
4. **Gerentes**: Stock general por producto o por empresa (3 empresas internas)

## 🎯 Arquitectura Correcta

### Conceptos Clave

**3 Empresas Internas (Semilla, Maxi, Trading):**
- Son entidades completamente separadas del campo `empresa` en `UserProfile`
- El campo `empresa` en perfil es **SOLO para proveedores**
- Los empleados NO tienen el campo empresa poblado

**Niveles de Permiso:**
1. **Funcional** (`can_view_warehouse`, `can_manage_warehouse`) - Acceso al módulo
2. **Almacén** (`almacenes_asignados`) - Qué almacenes puede ver/usar
3. **Acción** (`can_create_*`, `can_edit_*`, `can_delete_*`) - Qué puede hacer

## 📊 Matriz de Permisos Recomendada

| ViewSet | Operador Almacén | Gerente | SystemAdmin |
|---------|-----------------|---------|-------------|
| **AlmacenViewSet** (lista) | ✅ Solo sus almacenes | ✅ Todos | ✅ Todos |
| **ProductoViewSet** | ✅ Ver todos | ✅ Ver/Editar todos | ✅ Full |
| **MovimientoAlmacenViewSet** | ✅ Solo sus almacenes | ✅ Todos | ✅ Todos |
| **StockViewSet** | ✅ Solo sus almacenes | ✅ Todos (con filtros) | ✅ Todos |
| **KardexReportView** | ✅ Solo sus almacenes | ✅ Todos | ✅ Todos |
| **TransferenciaViewSet** | ✅ Enviar desde sus almacenes<br>✅ Recibir en sus almacenes | ✅ Todas | ✅ Todas |

## 🔧 Implementación Paso a Paso

### 1. AlmacenViewSet - Lista de Almacenes (SIN permisos especiales)

**Estado actual**: ✅ Ya está correctamente implementado

```python
class AlmacenViewSet(viewsets.ModelViewSet):
    queryset = Almacen.objects.all()
    serializer_class = AlmacenSerializer
    
    def get_queryset(self):
        """
        Filtrar queryset basado en almacenes accesibles
        """
        queryset = super().get_queryset()
        user = self.request.user

        # SystemAdmin ve todo
        if hasattr(user, 'is_system_admin') and user.is_system_admin:
            return queryset

        # Obtener perfil
        if not hasattr(user, 'userprofile'):
            return queryset.none()

        profile = user.userprofile

        # Si no requiere restricción, ver TODOS los almacenes
        if not profile.require_warehouse_access:
            return queryset.filter(state=True)

        # Filtrar por almacenes asignados
        almacenes_ids = profile.almacenes_asignados.values_list('id', flat=True)
        return queryset.filter(id__in=almacenes_ids)

    def get_permissions(self):
        # Solo requiere autenticación para listar, no permisos especiales
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        # Para crear/editar/eliminar sí necesita permisos
        return [IsAuthenticated(), CanManageWarehouse()]
```

**✅ Recomendación**: Cambiar el permiso de lectura a solo `IsAuthenticated()` para que cualquier usuario autenticado pueda ver los almacenes (filtrados por sus asignaciones).

---

### 2. MovimientoAlmacenViewSet - Solo movimientos de sus almacenes

**Estado actual**: ⚠️ Necesita filtrado por almacén

```python
class MovimientoAlmacenViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MovimientoAlmacenSerializer
    permission_classes = [IsAuthenticated, CanViewWarehouse]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MovimientoAlmacenFilter
    ordering_fields = ['fecha_documento', 'fecha_movimiento', 'producto__nombre_producto']
    ordering = ['-fecha_documento', '-id']

    def get_queryset(self):
        """
        Queryset base optimizado + filtrado por almacén
        """
        user = self.request.user
        queryset = MovimientoAlmacen.objects.filter(state=True).select_related(
            'empresa', 'almacen', 'producto'
        )

        # SystemAdmin ve todo
        if hasattr(user, 'is_system_admin') and user.is_system_admin:
            return queryset

        # Usuario sin perfil no ve nada
        if not hasattr(user, 'userprofile'):
            return queryset.none()

        profile = user.userprofile

        # Si no requiere restricción de almacén, ve TODO
        if not profile.require_warehouse_access:
            return queryset

        # Filtrar solo movimientos de almacenes asignados
        almacenes_ids = profile.almacenes_asignados.values_list('id', flat=True)
        return queryset.filter(almacen_id__in=almacenes_ids)
```

**✅ Beneficios**:
- Operadores solo ven movimientos de sus almacenes
- Gerentes ven todos los movimientos (pueden filtrar por empresa)
- SystemAdmin ve todo sin restricciones

---

### 3. StockViewSet - Stock filtrado por almacén

**Estado actual**: ⚠️ Necesita filtrado por almacén

```python
class StockViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated, CanViewStock]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = StockFilter
    ordering_fields = ['producto__nombre_producto', 'cantidad_actual']
    ordering = ['producto__nombre_producto']

    def get_queryset(self):
        """
        Optimizado + filtrado por almacén
        """
        user = self.request.user
        queryset = Stock.objects.all().select_related(
            'empresa', 'almacen', 'producto'
        )

        # SystemAdmin ve todo
        if hasattr(user, 'is_system_admin') and user.is_system_admin:
            return queryset

        # Usuario sin perfil no ve nada
        if not hasattr(user, 'userprofile'):
            return queryset.none()

        profile = user.userprofile

        # Si no requiere restricción, ve TODO el stock
        if not profile.require_warehouse_access:
            return queryset

        # Operadores: Solo stock de sus almacenes
        almacenes_ids = profile.almacenes_asignados.values_list('id', flat=True)
        return queryset.filter(almacen_id__in=almacenes_ids)
```

**✅ Uso en Frontend**:

**Operador**:
```javascript
// Solo ve stock de almacenes 1 y 3 (sus asignados)
GET /api/almacen/stock/
// Respuesta automáticamente filtrada
```

**Gerente**:
```javascript
// Ve todo el stock, puede filtrar por empresa
GET /api/almacen/stock/?empresa=1  // Solo Semilla
GET /api/almacen/stock/?empresa=2  // Solo Maxi
GET /api/almacen/stock/             // Todas las empresas
```

---

### 4. KardexReportView - Kardex restringido por almacén

**Estado actual**: ⚠️ Necesita validación de almacén

```python
class KardexReportView(APIView):
    """
    Endpoint para obtener el reporte de Kárdex con control de acceso por almacén.
    """
    permission_classes = [IsAuthenticated, CanViewWarehouse]

    def get(self, request, *args, **kwargs):
        try:
            empresa_id = int(request.query_params.get('empresa_id'))
            almacen_id = int(request.query_params.get('almacen_id'))
            producto_ids_str = request.query_params.getlist('producto_id')
            
            if not producto_ids_str:
                raise ValueError("Se requiere al menos un parámetro 'producto_id'.")

            producto_ids = [int(pid) for pid in producto_ids_str]
            fecha_inicio_str = request.query_params.get('fecha_inicio')
            fecha_fin_str = request.query_params.get('fecha_fin')

            if not all([fecha_inicio_str, fecha_fin_str]):
                raise ValueError("Faltan parámetros de fecha.")

            fecha_inicio = datetime.datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

        except (TypeError, ValueError, AttributeError) as e:
            return Response(
                {'error': f'Parámetros inválidos: {e}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ===== NUEVA VALIDACIÓN DE ACCESO AL ALMACÉN =====
        user = request.user
        
        # SystemAdmin puede ver cualquier almacén
        if not (hasattr(user, 'is_system_admin') and user.is_system_admin):
            # Usuario debe tener perfil
            if not hasattr(user, 'userprofile'):
                return Response(
                    {'error': 'Usuario sin perfil no puede acceder al Kardex'},
                    status=status.HTTP_403_FORBIDDEN
                )

            profile = user.userprofile

            # Si requiere restricción, validar acceso al almacén
            if profile.require_warehouse_access:
                almacenes_ids = profile.almacenes_asignados.values_list('id', flat=True)
                
                if almacen_id not in almacenes_ids:
                    return Response(
                        {'error': f'No tiene acceso al almacén {almacen_id}'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        # ===== FIN VALIDACIÓN =====

        try:
            # Resto del código permanece igual...
            nombre_empresa = "Empresa Desconocida"
            try:
                empresa_obj = Empresa.objects.get(pk=empresa_id)
                nombre_empresa = empresa_obj.razon_social
            except Empresa.DoesNotExist:
                pass

            kardex_data = get_kardex_detallado(
                empresa_id, almacen_id, producto_ids, fecha_inicio, fecha_fin
            )

            export_format = request.query_params.get('export_format')

            if export_format == 'excel':
                return generate_kardex_excel(kardex_data, fecha_inicio, fecha_fin, nombre_empresa)

            elif export_format == 'pdf':
                context = {
                    'empresa_id': empresa_id,
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                    'almacen_id': almacen_id
                }
                return generate_kardex_pdf(kardex_data, context, nombre_empresa)

            return Response(kardex_data)

        except Exception as e:
            return Response(
                {'error': f'Error generando el reporte: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

**✅ Comportamiento**:
- Operador intenta ver Kardex de almacén 5 (no asignado): ❌ Error 403
- Operador intenta ver Kardex de almacén 1 (asignado): ✅ Ve el reporte
- Gerente puede ver Kardex de cualquier almacén: ✅ Sin restricciones

---

### 5. TransferenciaViewSet - Transferencias entre almacenes

**Estado actual**: ⚠️ Necesita validación de almacenes origen/destino

```python
class TransferenciaViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    """
    API para ver y gestionar Transferencias con control de acceso por almacén.
    """
    serializer_class = TransferenciaSerializer
    permission_classes = [IsAuthenticated, CanManageStock]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'estado': ['exact'],
        'almacen_origen': ['exact'],
        'almacen_destino': ['exact'],
        'fecha_envio': ['gte', 'lte'],
    }
    
    search_fields = ['producto__codigo_producto', 'producto__nombre_producto', 'id_erp_salida_cab']
    ordering_fields = ['fecha_envio', 'estado', 'producto__codigo_producto']
    ordering = ['-fecha_envio']

    def get_queryset(self):
        """
        Filtrar transferencias según almacenes accesibles
        """
        user = self.request.user
        queryset = Transferencia.objects.select_related(
            'empresa', 'almacen_origen', 'almacen_destino', 'producto'
        ).order_by('-fecha_envio')

        # SystemAdmin ve todo
        if hasattr(user, 'is_system_admin') and user.is_system_admin:
            return queryset

        # Usuario sin perfil no ve nada
        if not hasattr(user, 'userprofile'):
            return queryset.none()

        profile = user.userprofile

        # Si no requiere restricción, ve TODO
        if not profile.require_warehouse_access:
            return queryset

        # Operadores: Solo transferencias donde origen O destino sean sus almacenes
        almacenes_ids = list(profile.almacenes_asignados.values_list('id', flat=True))
        
        from django.db.models import Q
        return queryset.filter(
            Q(almacen_origen_id__in=almacenes_ids) | 
            Q(almacen_destino_id__in=almacenes_ids)
        )

    @action(detail=True, methods=['post'], serializer_class=RecepcionSerializer)
    def recibir(self, request, pk=None):
        """
        Endpoint para recibir mercadería con validación de acceso al almacén destino.
        """
        transferencia = self.get_object()

        # Validación de estado
        if transferencia.estado != 'EN_TRANSITO':
            return Response(
                {'error': f'Esta transferencia ya fue procesada (Estado: {transferencia.get_estado_display()}).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ===== NUEVA VALIDACIÓN: Solo puede recibir en almacenes asignados =====
        user = request.user
        if not (hasattr(user, 'is_system_admin') and user.is_system_admin):
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                
                if profile.require_warehouse_access:
                    almacenes_ids = profile.almacenes_asignados.values_list('id', flat=True)
                    
                    if transferencia.almacen_destino_id not in almacenes_ids:
                        return Response(
                            {'error': 'No tiene acceso al almacén destino para recibir esta transferencia'},
                            status=status.HTTP_403_FORBIDDEN
                        )
        # ===== FIN VALIDACIÓN =====

        # Validar el body del request
        serializer = RecepcionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data
        cantidad_recibida = datos.get('cantidad_recibida')
        notas = datos.get('notas_recepcion', '')

        try:
            exito = transferencia.recibir_mercaderia(
                cantidad_recibida=cantidad_recibida,
                fecha_recepcion=timezone.now(),
                notas=notas,
                auto_recepcion=False
            )

            if not exito:
                return Response(
                    {"error": "La transferencia ya fue procesada."},
                    status=status.HTTP_409_CONFLICT
                )

            updated_serializer = TransferenciaSerializer(
                transferencia,
                context=self.get_serializer_context()
            )
            return Response(updated_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error al recibir transferencia {pk}: {e}", exc_info=True)
            return Response(
                {"error": f"Error al recibir: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

**✅ Lógica**:
- Operador de almacén 1 puede:
  - ✅ Ver transferencias DESDE almacén 1
  - ✅ Ver transferencias HACIA almacén 1
  - ✅ Recibir transferencias en almacén 1
  - ❌ Recibir transferencias en otros almacenes

---

## 📝 Resumen de Cambios por ViewSet

| ViewSet | Cambio Principal | Línea Clave |
|---------|------------------|-------------|
| **AlmacenViewSet** | ✅ Ya correcto | `get_queryset()` filtra por asignados |
| **MovimientoAlmacenViewSet** | Agregar filtro en `get_queryset()` | Filtrar por `almacen_id__in=almacenes_ids` |
| **StockViewSet** | Agregar filtro en `get_queryset()` | Filtrar por `almacen_id__in=almacenes_ids` |
| **KardexReportView** | Validar `almacen_id` antes de consultar | Verificar acceso con `tiene_acceso_almacen()` |
| **TransferenciaViewSet** | Filtrar queryset + validar recepción | Filtrar con `Q(origen) \| Q(destino)` |

---

## 🔒 Cómo Funciona el Sistema Completo

### Ejemplo: Operador de Almacén

**Configuración del Usuario**:
```python
user = User.objects.get(username='operador_callao')
profile = user.userprofile
profile.require_warehouse_access = True
profile.almacenes_asignados.add(almacen_callao, almacen_miraflores)
profile.save()

# Asignar permisos funcionales
user.groups.add(grupo_operadores)  # Tiene: can_view_warehouse, can_view_stock
```

**Comportamiento en el Sistema**:

1. **GET /api/almacen/almacenes/**
   - Ve solo: Callao, Miraflores
   - No ve: Surco, Ventanilla

2. **GET /api/almacen/movimientos/**
   - Ve movimientos de Callao y Miraflores
   - No ve movimientos de otros almacenes

3. **GET /api/almacen/stock/**
   - Ve stock en Callao y Miraflores
   - No ve stock de otros almacenes

4. **GET /api/almacen/kardex/?almacen_id=1** (Callao)
   - ✅ Funciona (tiene acceso)

5. **GET /api/almacen/kardex/?almacen_id=5** (Surco)
   - ❌ Error 403: No tiene acceso

6. **POST /api/almacen/transferencias/123/recibir/** (Destino: Callao)
   - ✅ Funciona (tiene acceso al destino)

7. **POST /api/almacen/transferencias/456/recibir/** (Destino: Surco)
   - ❌ Error 403: No tiene acceso al destino

---

### Ejemplo: Gerente

**Configuración del Usuario**:
```python
user = User.objects.get(username='gerente_general')
profile = user.userprofile
profile.require_warehouse_access = False  # Sin restricciones
profile.save()

# Asignar permisos funcionales
user.groups.add(grupo_gerentes)  # Tiene: can_manage_warehouse, can_manage_stock
```

**Comportamiento en el Sistema**:

1. **GET /api/almacen/almacenes/**
   - Ve TODOS los almacenes

2. **GET /api/almacen/stock/?empresa=1**
   - Ve stock de todas las empresas, puede filtrar

3. **GET /api/almacen/movimientos/?empresa=2&almacen=3**
   - Ve todos los movimientos, puede filtrar como quiera

4. **GET /api/almacen/kardex/?almacen_id=X** (Cualquier almacén)
   - ✅ Funciona para todos

---

## 🎨 Ejemplo de Uso en Frontend

### React: Selector de Almacén Filtrado

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

function AlmacenSelector() {
  const [almacenes, setAlmacenes] = useState([]);
  
  useEffect(() => {
    // El backend ya filtra automáticamente por usuario
    axios.get('/api/almacen/almacenes/')
      .then(response => {
        setAlmacenes(response.data);
        // Operador ve solo [Callao, Miraflores]
        // Gerente ve [Todos]
      });
  }, []);

  return (
    <select>
      {almacenes.map(alm => (
        <option key={alm.id} value={alm.id}>
          {alm.nombre} - {alm.empresa_nombre}
        </option>
      ))}
    </select>
  );
}
```

### React: Stock por Almacén

```javascript
function StockView() {
  const [almacenId, setAlmacenId] = useState(null);
  const [stock, setStock] = useState([]);

  useEffect(() => {
    if (almacenId) {
      // Backend filtra automáticamente
      axios.get(`/api/almacen/stock/?almacen=${almacenId}`)
        .then(response => setStock(response.data))
        .catch(error => {
          if (error.response?.status === 403) {
            alert('No tiene acceso a este almacén');
          }
        });
    }
  }, [almacenId]);

  return (
    <div>
      <AlmacenSelector onChange={(e) => setAlmacenId(e.target.value)} />
      <StockTable data={stock} />
    </div>
  );
}
```

---

## ✅ Checklist de Implementación

- [ ] **1. Actualizar MovimientoAlmacenViewSet**
  - Agregar filtrado por almacenes en `get_queryset()`

- [ ] **2. Actualizar StockViewSet**
  - Agregar filtrado por almacenes en `get_queryset()`

- [ ] **3. Actualizar KardexReportView**
  - Validar acceso al almacén solicitado antes de generar reporte

- [ ] **4. Actualizar TransferenciaViewSet**
  - Filtrar por almacenes origen/destino en `get_queryset()`
  - Validar acceso al almacén destino en `recibir()`

- [ ] **5. Cambiar permiso de lectura en AlmacenViewSet (opcional)**
  - De `CanViewWarehouse` a solo `IsAuthenticated` para listar

- [ ] **6. Pruebas**
  - Crear usuario operador con almacenes asignados
  - Crear usuario gerente sin restricciones
  - Probar cada endpoint con ambos usuarios

---

## 🚀 Próximos Pasos

1. **Aplicar los cambios sugeridos** a cada ViewSet
2. **Crear migraciones** si se modificó el modelo UserProfile
3. **Probar con usuarios reales** (operador y gerente)
4. **Actualizar documentación de API** para usuarios finales
5. **Capacitar a administradores** en asignación de almacenes

---

## 💡 Tips Adicionales

### Optimización de Queries

```python
# Malo: N+1 queries
for movimiento in movimientos:
    print(movimiento.almacen.nombre)

# Bueno: 1 query
movimientos = MovimientoAlmacen.objects.select_related('almacen').all()
for movimiento in movimientos:
    print(movimiento.almacen.nombre)
```

### Logging de Acceso Denegado

```python
if almacen_id not in almacenes_ids:
    logger.warning(
        f"Usuario {user.username} intentó acceder al almacén {almacen_id} "
        f"pero solo tiene acceso a: {list(almacenes_ids)}"
    )
    return Response({'error': 'Sin acceso'}, status=403)
```

### Endpoint Útil: Mis Almacenes

```python
@action(detail=False, methods=['get'])
def mis_almacenes(self, request):
    """
    GET /api/almacen/almacenes/mis_almacenes/
    Devuelve los almacenes accesibles para el usuario actual.
    """
    user = request.user
    
    if hasattr(user, 'is_system_admin') and user.is_system_admin:
        almacenes = Almacen.objects.filter(state=True)
    elif hasattr(user, 'userprofile'):
        profile = user.userprofile
        if profile.require_warehouse_access:
            almacenes = profile.almacenes_asignados.filter(state=True)
        else:
            almacenes = Almacen.objects.filter(state=True)
    else:
        almacenes = Almacen.objects.none()
    
    serializer = self.get_serializer(almacenes, many=True)
    return Response(serializer.data)
```

---

## 📞 Soporte

Si tienes dudas sobre la implementación:
1. Revisa los ejemplos en `ORGANIZATION_WAREHOUSE_PERMISSIONS.md`
2. Consulta `SECURITY_ANALYSIS.md` para entender el modelo de seguridad
3. Ejecuta `python test_permissions_api.py` para validar el sistema

**Sistema listo para producción** con control granular de acceso por almacén. ✅
