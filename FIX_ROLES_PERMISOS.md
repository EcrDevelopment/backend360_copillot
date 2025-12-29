# Fix: Sistema de Roles y Permisos - Solución Correcta

## Problema Original

El sistema de roles y permisos implementado en PR #1 era correcto y necesario, pero causaba errores al intentar listar usuarios, roles y permisos desde el frontend porque **todas** las operaciones (incluyendo GET) requerían el permiso `CanManageUsers`.

### Errores Reportados
- ❌ Listar usuarios daba error 403
- ❌ Listar roles daba error 403
- ❌ Listar permisos daba error 403
- ❌ Frontend no podía mostrar información de usuarios/roles

## Solución Implementada

### ✅ Lo que NO se hizo (intentos incorrectos anteriores)
- ❌ NO se relajaron los permisos de módulos
- ❌ NO se dio acceso abierto a almacén/importaciones
- ❌ NO se eliminaron los permisos granulares

### ✅ Lo que SÍ se hizo (solución correcta)

**Cambio en `usuarios/views.py`:**

Se modificaron los ViewSets para diferenciar entre operaciones de lectura (GET) y escritura (POST/PUT/DELETE):

```python
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        GET operations: cualquier usuario autenticado
        POST/PUT/DELETE: requiere CanManageUsers
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), CanManageUsers()]
    
    def get_queryset(self):
        # Los usuarios regulares solo ven sus propios datos
        # Los admins ven todos los datos
        ...
```

Lo mismo se aplicó a `RoleViewSet` y `PermissionViewSet`.

## Sistema de Permisos Mantenido

### Permisos Granulares (sin cambios)

El sistema original de permisos granulares se mantiene intacto:

**Módulos:**
- `CanAccessAlmacen` - Requiere `almacen.ver_modulo` o rol `system_admin`
- `CanAccessImportaciones` - Requiere `importaciones.ver_modulo` o rol `system_admin`
- `CanEditDocuments` - Requiere permisos específicos de documentos
- `CanDeleteResource` - Requiere roles de administrador

**Gestión de Usuarios:**
- `CanManageUsers` - Requiere roles `system_admin` o `accounts_admin`
- Solo usuarios con este permiso pueden crear/editar/eliminar usuarios

### Roles Disponibles

Los roles definidos en `usuarios/roles.py` permanecen sin cambios:

1. **SystemAdmin** - Acceso completo al sistema
2. **AccountsAdmin** - Gestión de usuarios y roles
3. **ImportacionesAdmin** - Acceso completo a importaciones
4. **ImportacionesAsistente** - Acceso limitado a importaciones
5. **AlmacenAdmin** - Acceso completo a almacén
6. **AlmacenOperador** - Acceso limitado a almacén
7. **Proveedor** - Acceso limitado a documentos propios

## Beneficios de la Solución

### ✅ Seguridad Mantenida
- Los permisos granulares siguen activos
- Los módulos requieren roles específicos
- Las operaciones administrativas están protegidas
- Solo admins pueden gestionar usuarios/roles

### ✅ Funcionalidad Restaurada
- El frontend puede listar usuarios para mostrar información
- El frontend puede listar roles para asignar a usuarios
- El frontend puede listar permisos para configuración
- Los usuarios ven solo sus propios datos (filtrado en get_queryset)

### ✅ Buenas Prácticas
- Separación clara entre lectura y escritura
- Principio de mínimo privilegio aplicado
- Filtrado de datos a nivel de queryset
- Sin comprometer la seguridad del sistema

## Asignación de Roles y Permisos

### Cómo Asignar Roles a Usuarios

Los administradores con permiso `CanManageUsers` pueden asignar roles:

**Desde el Admin de Django:**
```python
from django.contrib.auth.models import User
from rolepermissions.roles import assign_role

user = User.objects.get(username='usuario')
assign_role(user, 'importaciones_admin')
```

**Desde el API:**
```
PUT /api/accounts/usuarios/{id}/
{
    "roles": [1, 2, 3],  // IDs de grupos/roles
    "permissions": [4, 5, 6]  // IDs de permisos específicos
}
```

### Permisos Granulares por Usuario

El sistema permite asignar permisos individuales a usuarios además de roles:

1. **Por Rol**: El usuario hereda todos los permisos del rol
2. **Individual**: Se pueden agregar permisos específicos al usuario

## Próximas Mejoras Recomendadas

### 1. Interfaz de Administración Mejorada
- Crear vista en frontend para asignar roles fácilmente
- Mostrar permisos disponibles por módulo
- Interfaz para ver qué usuarios tienen qué roles

### 2. Organización de Permisos por Módulos
- Agrupar permisos en la UI por módulo
- Facilitar la asignación de permisos completos de un módulo

### 3. Audit Trail Mejorado
- Registrar cambios de roles y permisos
- Historial de quién asignó qué rol a quién

### 4. Validación de Permisos
- Alertas cuando un usuario intenta acceder sin permisos
- Logs de intentos de acceso denegados

## Verificación

Para verificar que el sistema funciona correctamente:

### Test 1: Usuario Regular
```bash
# Login como usuario regular
# Intentar: GET /api/accounts/usuarios/
# Resultado esperado: 200 OK, solo ve su propio usuario

# Intentar: POST /api/accounts/usuarios/
# Resultado esperado: 403 Forbidden
```

### Test 2: Administrador
```bash
# Login como admin con CanManageUsers
# Intentar: GET /api/accounts/usuarios/
# Resultado esperado: 200 OK, ve todos los usuarios

# Intentar: POST /api/accounts/usuarios/
# Resultado esperado: 201 Created
```

### Test 3: Módulos
```bash
# Login como usuario sin rol de almacén
# Intentar: GET /api/almacen/productos/
# Resultado esperado: 403 Forbidden

# Login como usuario con rol almacen_admin
# Intentar: GET /api/almacen/productos/
# Resultado esperado: 200 OK
```

## Conclusión

La solución mantiene el sistema de permisos granulares original mientras permite que el frontend funcione correctamente. Los cambios fueron mínimos y quirúrgicos:

- ✅ 1 archivo modificado: `usuarios/views.py`
- ✅ 3 ViewSets actualizados con `get_permissions()`
- ✅ Permisos granulares mantenidos
- ✅ Seguridad preservada
- ✅ Funcionalidad restaurada

**Commit:** `fc5e903` - Fix: Revert to granular permissions, allow GET for authenticated users
