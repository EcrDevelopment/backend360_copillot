# Sistema de Permisos Funcionales / Modulares

## Descripción General

Este documento describe el nuevo sistema de permisos funcionales implementado en el proyecto backend360_copillot. El sistema migra desde permisos basados en tablas de Django (add_model, change_model, etc.) hacia permisos basados en **acciones de negocio** o **módulos funcionales**.

## Problema Resuelto

### Antes (Permisos por Tabla)
- Django generaba automáticamente 4 permisos por cada modelo (add, change, delete, view)
- Con muchas tablas, la lista de permisos se volvía gigante e inmanejable (~2000 permisos)
- Asignar permisos tabla por tabla era propenso a errores humanos
- La interfaz de usuario mostraba una lista abrumadora de permisos técnicos

### Después (Permisos Funcionales)
- Permisos de alto nivel basados en acciones de negocio
- Lista reducida y manejable (~15 permisos funcionales)
- Más fácil de entender para usuarios no técnicos
- Un solo permiso puede dar acceso a múltiples ViewSets relacionados
- Interfaz de usuario limpia y clara

## Arquitectura

### 1. Modelos Meta de Permisos

Se crearon modelos Meta (managed=False) en cada app principal para definir permisos personalizados:

#### **usuarios/models.py** - UsuariosPermissions
```python
class UsuariosPermissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('can_manage_users', 'Puede gestionar usuarios (crear, editar, eliminar)'),
            ('can_view_users', 'Puede ver usuarios'),
            ('can_manage_roles', 'Puede gestionar roles y permisos'),
            ('can_view_roles', 'Puede ver roles y permisos'),
        ]
```

#### **almacen/models.py** - AlmacenPermissions
```python
class AlmacenPermissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('can_manage_warehouse', 'Puede gestionar almacén (guías, detalles, kardex, movimientos)'),
            ('can_view_warehouse', 'Puede ver información de almacén'),
            ('can_view_warehouse_reports', 'Puede ver reportes de almacén'),
            ('can_manage_stock', 'Puede gestionar stock y transferencias'),
            ('can_view_stock', 'Puede ver stock'),
        ]
```

#### **importaciones/models.py** - ImportacionesPermissions
```python
class ImportacionesPermissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('can_manage_importaciones', 'Puede gestionar importaciones (DUA, declaraciones, proveedores)'),
            ('can_view_importaciones', 'Puede ver información de importaciones'),
            ('can_view_importaciones_reports', 'Puede ver reportes de importaciones'),
            ('can_manage_documents', 'Puede gestionar documentos de importaciones'),
            ('can_view_documents', 'Puede ver documentos de importaciones'),
        ]
```

### 2. Clase Base de Permisos Personalizada

**usuarios/permissions.py** - `HasModulePermission`

```python
class HasModulePermission(BasePermission):
    """
    Clase base para verificar permisos funcionales/modulares.
    
    Uso:
    1. Como clase base:
        class CanManageWarehouse(HasModulePermission):
            permission_required = 'almacen.can_manage_warehouse'
    
    2. Directamente en ViewSet:
        permission_classes = [HasModulePermission]
        permission_required = 'almacen.can_manage_warehouse'
    
    3. Con múltiples permisos (cualquier coincidencia):
        permission_required = ['almacen.can_manage_warehouse', 'almacen.can_view_warehouse']
    """
    permission_required = None
    message = "No tiene los permisos requeridos para esta acción."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # SystemAdmin siempre tiene acceso
        if request.user.groups.filter(name='SystemAdmin').exists():
            return True
        
        # Obtener permission_required de la vista si no está definido en la clase
        permission = self.permission_required or getattr(view, 'permission_required', None)
        
        if not permission:
            return False
        
        # Soporte para múltiples permisos (el usuario necesita cualquiera de ellos)
        if isinstance(permission, (list, tuple)):
            return any(request.user.has_perm(perm) for perm in permission)
        
        # Verificación de un solo permiso
        return request.user.has_perm(permission)
```

### 3. Clases de Permisos Específicas

Se crearon clases de permiso específicas para cada módulo en **usuarios/permissions.py**:

#### Módulo de Usuarios
- `CanManageUsersModule` - Gestionar usuarios
- `CanViewUsersModule` - Ver usuarios
- `CanManageRoles` - Gestionar roles y permisos
- `CanViewRoles` - Ver roles y permisos

#### Módulo de Almacén
- `CanManageWarehouse` - Gestionar almacén
- `CanViewWarehouse` - Ver información de almacén
- `CanViewWarehouseReports` - Ver reportes
- `CanManageStock` - Gestionar stock y transferencias
- `CanViewStock` - Ver stock

#### Módulo de Importaciones
- `CanManageImportaciones` - Gestionar importaciones
- `CanViewImportaciones` - Ver importaciones
- `CanViewImportacionesReports` - Ver reportes
- `CanManageDocuments` - Gestionar documentos
- `CanViewDocuments` - Ver documentos

## Uso en ViewSets

### Ejemplo 1: Permisos Diferentes por Acción

```python
class AlmacenViewSet(viewsets.ModelViewSet):
    queryset = Almacen.objects.all()
    serializer_class = AlmacenSerializer
    
    def get_permissions(self):
        """
        GET: requiere can_view_warehouse
        POST/PUT/PATCH/DELETE: requiere can_manage_warehouse
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated(), CanViewWarehouse()]
        return [IsAuthenticated(), CanManageWarehouse()]
```

### Ejemplo 2: Un Permiso para Múltiples ViewSets

El permiso `can_manage_warehouse` da acceso a:
- GremisionCabViewSet (modificar guías)
- AlmacenViewSet (gestionar almacenes)
- ProductoViewSet (gestionar productos)
- MovimientoAlmacenViewSet (ver movimientos)

```python
class GremisionCabViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, CanManageWarehouse]
    # ...

class AlmacenViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageWarehouse]
    # ...

class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageWarehouse]
    # ...
```

### Ejemplo 3: Solo Lectura

```python
class MovimientoAlmacenViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MovimientoAlmacenSerializer
    permission_classes = [IsAuthenticated, CanViewWarehouse]
    # ...
```

## Endpoint de Permisos

El endpoint `/api/accounts/permisos` ahora retorna **solo permisos funcionales**, no los 2000+ permisos de tabla.

### Implementación

```python
class PermissionViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        """
        Filtra para mostrar solo permisos funcionales/modulares.
        """
        functional_models = [
            'usuariospermissions',
            'almacenpermissions',
            'importacionespermissions'
        ]
        
        queryset = Permission.objects.filter(
            content_type__model__in=functional_models
        ).select_related('content_type')
        
        return queryset
```

### Respuesta de Ejemplo

```json
[
  {
    "id": 101,
    "codename": "can_manage_users",
    "name": "Puede gestionar usuarios (crear, editar, eliminar)",
    "content_type": 25
  },
  {
    "id": 102,
    "codename": "can_view_users",
    "name": "Puede ver usuarios",
    "content_type": 25
  },
  {
    "id": 103,
    "codename": "can_manage_warehouse",
    "name": "Puede gestionar almacén (guías, detalles, kardex, movimientos)",
    "content_type": 26
  },
  // ... más permisos funcionales
]
```

## Migraciones

### Ejecutar Migraciones

```bash
python manage.py migrate usuarios
python manage.py migrate almacen
python manage.py migrate importaciones
```

Las migraciones crean los permisos funcionales en la tabla `auth_permission` de Django.

### Archivos de Migración Generados

- `usuarios/migrations/0009_usuariospermissions.py`
- `almacen/migrations/0006_almacenpermissions.py`
- `importaciones/migrations/0038_importacionespermissions.py`

## Asignación de Permisos

### Opción 1: A través del Admin de Django

1. Ir a Django Admin → Groups
2. Crear o editar un grupo (ej: "Almaceneros")
3. Seleccionar permisos funcionales:
   - `almacen | Permiso de Almacén | can_view_warehouse`
   - `almacen | Permiso de Almacén | can_manage_stock`
4. Asignar usuarios a ese grupo

### Opción 2: Programáticamente

```python
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from almacen.models import AlmacenPermissions

# Obtener o crear grupo
almaceneros, created = Group.objects.get_or_create(name='Almaceneros')

# Obtener content type del modelo de permisos
ct = ContentType.objects.get_for_model(AlmacenPermissions)

# Obtener permisos funcionales
can_view = Permission.objects.get(content_type=ct, codename='can_view_warehouse')
can_manage = Permission.objects.get(content_type=ct, codename='can_manage_warehouse')

# Asignar permisos al grupo
almaceneros.permissions.add(can_view, can_manage)

# Asignar usuario al grupo
user = User.objects.get(username='juan')
user.groups.add(almaceneros)
```

### Opción 3: API REST (Frontend)

```javascript
// GET: Obtener permisos disponibles
fetch('/api/accounts/permisos?all=true')
  .then(res => res.json())
  .then(permissions => console.log(permissions));

// PUT: Actualizar permisos de un grupo
fetch('/api/accounts/roles/5', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Almaceneros',
    permissions: [103, 104, 105] // IDs de permisos funcionales
  })
});
```

## Ventajas del Nuevo Sistema

1. **Simplicidad**: ~15 permisos funcionales vs ~2000 permisos de tabla
2. **Claridad**: Nombres descriptivos basados en acciones de negocio
3. **Menos Errores**: Menos opciones = menos oportunidad de error humano
4. **Mantenibilidad**: Agregar nuevos permisos es más sencillo
5. **Flexibilidad**: Un permiso puede controlar múltiples ViewSets
6. **Compatibilidad**: Usa el sistema nativo de Django (Groups y Permissions)
7. **Escalabilidad**: Fácil agregar nuevos módulos y permisos

## Agregar Nuevos Permisos

### Paso 1: Definir en el Modelo Meta

```python
# nueva_app/models.py
class NuevaAppPermissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('can_manage_feature', 'Puede gestionar feature X'),
            ('can_view_feature', 'Puede ver feature X'),
        ]
```

### Paso 2: Crear Clase de Permiso

```python
# usuarios/permissions.py
class CanManageFeature(HasModulePermission):
    permission_required = 'nueva_app.can_manage_feature'
    message = "No tiene permisos para gestionar esta funcionalidad."
```

### Paso 3: Usar en ViewSet

```python
# nueva_app/views.py
from usuarios.permissions import CanManageFeature

class FeatureViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageFeature]
    # ...
```

### Paso 4: Crear Migración

```bash
python manage.py makemigrations nueva_app
python manage.py migrate nueva_app
```

## Compatibilidad con Código Existente

- El sistema es compatible con grupos y permisos existentes
- Los permisos antiguos siguen funcionando
- Se puede migrar gradualmente ViewSet por ViewSet
- El grupo `SystemAdmin` tiene acceso automático a todo

## Testing

### Test de Permisos

```python
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from almacen.models import AlmacenPermissions

class PermissionsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password')
        ct = ContentType.objects.get_for_model(AlmacenPermissions)
        self.permission = Permission.objects.get(
            content_type=ct,
            codename='can_view_warehouse'
        )
    
    def test_user_has_permission(self):
        self.user.user_permissions.add(self.permission)
        self.assertTrue(self.user.has_perm('almacen.can_view_warehouse'))
    
    def test_user_without_permission(self):
        self.assertFalse(self.user.has_perm('almacen.can_view_warehouse'))
```

## Troubleshooting

### Problema: Permisos no aparecen después de migrar

**Solución**: Ejecutar las migraciones:
```bash
python manage.py migrate
```

### Problema: Usuario no tiene acceso a ViewSet

**Solución**: Verificar que el usuario tenga el permiso funcional correcto:
```python
user.has_perm('almacen.can_view_warehouse')  # Debe retornar True
```

### Problema: Endpoint de permisos retorna lista vacía

**Solución**: Verificar que las migraciones se hayan ejecutado correctamente:
```bash
python manage.py showmigrations usuarios almacen importaciones
```

## Referencias

- [Django Permissions Documentation](https://docs.djangoproject.com/en/stable/topics/auth/default/#permissions-and-authorization)
- [Django Rest Framework Permissions](https://www.django-rest-framework.org/api-guide/permissions/)

## Resumen de Cambios

### Archivos Modificados
- `usuarios/models.py` - Agregado UsuariosPermissions
- `almacen/models.py` - Agregado AlmacenPermissions
- `importaciones/models.py` - Agregado ImportacionesPermissions
- `usuarios/permissions.py` - Agregado HasModulePermission y clases específicas
- `usuarios/views.py` - Actualizado PermissionViewSet, RoleViewSet, UserViewSet
- `almacen/views.py` - Actualizados todos los ViewSets
- `importaciones/views.py` - Actualizadas importaciones
- `semilla360/settings.py` - Removido rolepermissions, agregado almacen a INSTALLED_APPS

### Migraciones Creadas
- `usuarios/migrations/0009_usuariospermissions.py`
- `almacen/migrations/0006_almacenpermissions.py`
- `importaciones/migrations/0038_importacionespermissions.py`

---

**Autor**: Backend360 Development Team  
**Fecha**: 2025-12-30  
**Versión**: 1.0
