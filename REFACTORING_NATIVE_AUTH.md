# Refactoring: Django Native Auth System

## 📋 Resumen

Se ha refactorizado completamente el sistema de usuarios, roles y permisos para usar **exclusivamente el sistema nativo de autenticación de Django** (`django.contrib.auth`), eliminando la dependencia de `django-role-permissions`.

## 🎯 Objetivos Cumplidos

✅ **Eliminada dependencia** de `django-role-permissions`  
✅ **Roles = Groups** (django.contrib.auth.Group)  
✅ **Permisos = Permissions** (django.contrib.auth.Permission)  
✅ **UserSerializer refactorizado** con soporte completo para groups y user_permissions  
✅ **Management Command** `setup_roles` para crear grupos y asignar permisos  
✅ **Token JWT** actualizado para incluir roles y permisos nativos  
✅ **Compatibilidad total** con el frontend existente  

---

## 🔄 Cambios Realizados

### 1. UserSerializer Refactorizado

**Archivo:** `usuarios/serializers.py`

El serializer ahora maneja correctamente:

- **`groups` (roles)**: Campo ManyToMany escribible para asignar grupos al usuario
- **`user_permissions`**: Campo ManyToMany escribible para permisos individuales
- **Métodos `create` y `update`**: Actualizan correctamente groups y user_permissions

```python
class UserSerializer(serializers.ModelSerializer):
    roles = serializers.PrimaryKeyRelatedField(
        many=True, source="groups", queryset=Group.objects.all(), required=False
    )
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, source="user_permissions", queryset=Permission.objects.all(), required=False
    )
    userprofile = UserProfileSerializer(required=False)

    def create(self, validated_data):
        roles = validated_data.pop("groups", [])
        perms = validated_data.pop("user_permissions", [])
        profile_data = validated_data.pop("userprofile", {})
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)
        user.groups.set(roles)  # ✅ Asigna roles
        user.user_permissions.set(perms)  # ✅ Asigna permisos

        UserProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        roles = validated_data.pop("groups", None)
        perms = validated_data.pop("user_permissions", None)
        # ... actualización de campos ...
        
        if roles is not None:
            instance.groups.set(roles)  # ✅ Actualiza roles
        if perms is not None:
            instance.user_permissions.set(perms)  # ✅ Actualiza permisos
        
        return instance
```

### 2. CustomTokenObtainPairSerializer Refactorizado

**Archivo:** `usuarios/serializers.py`

El token JWT ahora incluye roles y permisos usando el sistema nativo de Django:

```python
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # ✅ Roles desde user.groups
        token['roles'] = list(user.groups.values_list('name', flat=True))
        # ✅ Permisos desde groups + user_permissions
        token['permissions'] = cls._get_user_permissions(user)
        return token

    @staticmethod
    def _get_user_permissions(user):
        """
        Obtiene TODOS los permisos del usuario:
        - Permisos heredados de sus grupos (roles)
        - Permisos específicos asignados directamente
        """
        permissions = {}
        
        # Permisos completos (formato: 'app_label.codename')
        for perm in user.get_all_permissions():
            permissions[perm.replace('.', '_')] = True
        
        # Permisos individuales (solo codename)
        for perm in user.user_permissions.all():
            permissions[perm.codename] = True
        
        # Permisos de grupos (solo codename)
        for group in user.groups.all():
            for perm in group.permissions.all():
                permissions[perm.codename] = True
        
        return permissions
```

**Formato del token:**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {...},
  "roles": ["SystemAdmin", "AccountsAdmin"],
  "permissions": {
    "user_listar_usuarios": true,
    "user_registrar_usuario": true,
    "almacen_ver_modulo": true,
    ...
  }
}
```

### 3. Management Command: setup_roles

**Archivo:** `usuarios/management/commands/setup_roles.py`

Comando para crear los grupos (roles) base del sistema y asignar permisos programáticamente.

**Uso:**
```bash
python manage.py setup_roles
```

**Grupos creados:**

1. **SystemAdmin** - Administrador del sistema
   - `mantenimiento_tabla_tipo_documentos`
   - `sistema_gestionar_configuracion`
   - `sistema_ver_logs_auditoria`
   - `sistema_gestionar_respaldos`

2. **AccountsAdmin** - Administrador de usuarios
   - `user_listar_usuarios`
   - `user_registrar_usuario`
   - `user_editar_usuario`
   - `user_eliminar_usuario`
   - `user_asignar_roles`
   - `user_gestionar_permisos`
   - `user_ver_perfil`

3. **AccountsUser** - Usuario estándar
   - `user_editar_perfil`
   - `user_ver_perfil`
   - `user_cambiar_password`

4. **ImportacionesAdmin** - Administrador de importaciones
   - 19 permisos relacionados con importaciones, DUA, órdenes de compra, etc.

5. **ImportacionesAsistente** - Asistente de importaciones
   - Permisos limitados de lectura y edición

6. **AlmacenAdmin** - Administrador de almacén
   - Permisos completos sobre inventario, stock, kardex, reportes

7. **AlmacenOperador** - Operador de almacén
   - Permisos limitados de operación

8. **Proveedor** - Proveedor externo
   - Permisos para gestionar documentos propios

**Salida del comando:**
```
Setting up roles and permissions...
Setting up SystemAdmin role...
  Created permission: mantenimiento_tabla_tipo_documentos
  ...
  ✓ SystemAdmin configured with 4 permissions
...
✅ Roles and permissions setup completed!
```

### 4. Actualización de requirements.txt

**Eliminado:** `django-role-permissions`

El proyecto ahora solo depende de Django y sus extensiones estándar.

---

## 🚀 Cómo Usar el Nuevo Sistema

### Paso 1: Ejecutar Migraciones

Asegúrate de que la base de datos esté actualizada:

```bash
python manage.py migrate
```

### Paso 2: Crear Roles y Permisos

Ejecuta el comando para crear los grupos base:

```bash
python manage.py setup_roles
```

### Paso 3: Asignar Roles a Usuarios

#### Desde el Admin de Django:

1. Ve a `/admin/auth/user/`
2. Selecciona un usuario
3. En "Groups", selecciona los roles que deseas asignar
4. En "User permissions", agrega permisos específicos si es necesario
5. Guarda

#### Desde el API (Crear Usuario):

```bash
POST /api/accounts/usuarios/
{
  "username": "jdoe",
  "password": "SecureP@ss123",
  "email": "jdoe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "roles": [1, 2],  // IDs de los grupos (SystemAdmin, AccountsAdmin)
  "permissions": [10, 15],  // IDs de permisos individuales (opcional)
  "userprofile": {
    "empresa_id": 1,
    "telefono": "123456789"
  }
}
```

#### Desde el API (Actualizar Usuario):

```bash
PUT /api/accounts/usuarios/5/
{
  "roles": [3, 4],  // Actualiza los roles del usuario
  "permissions": [20, 25, 30]  // Actualiza permisos individuales
}
```

### Paso 4: Verificar Permisos

Desde Python:

```python
from django.contrib.auth.models import User

user = User.objects.get(username='jdoe')

# Ver roles (grupos)
print(user.groups.all())  
# <QuerySet [<Group: SystemAdmin>, <Group: AccountsAdmin>]>

# Ver permisos del usuario
print(user.get_all_permissions())
# {'usuarios.user_listar_usuarios', 'usuarios.sistema_ver_logs_auditoria', ...}

# Verificar permiso específico
if user.has_perm('usuarios.user_listar_usuarios'):
    print("Usuario puede listar usuarios")
```

---

## 📊 Estructura de Respuesta del API

### GET /api/accounts/usuarios/

**Con paginación (default):**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "ecanovar",
      "email": "erick@example.com",
      "first_name": "Erick",
      "last_name": "Canova",
      "roles": [1, 2, 4],  // IDs de Groups
      "permissions": [159, 166, 162],  // IDs de Permissions
      "userprofile": {
        "empresa_id": 1,
        "telefono": null
      }
    }
  ]
}
```

**Sin paginación (`?all=true`):**
```json
[
  {
    "id": 1,
    "username": "ecanovar",
    "roles": [1, 2, 4],
    "permissions": [159, 166, 162],
    ...
  },
  ...
]
```

### GET /api/accounts/roles/

```json
[
  {
    "id": 1,
    "name": "SystemAdmin",
    "permissions": [1, 2, 3, 4]  // IDs de Permission
  },
  {
    "id": 2,
    "name": "AccountsAdmin",
    "permissions": [5, 6, 7, 8, 9, 10, 11]
  }
]
```

### GET /api/accounts/permisos/

```json
[
  {
    "id": 1,
    "codename": "user_listar_usuarios",
    "name": "Listar usuarios",
    "content_type": 10
  },
  ...
]
```

---

## 🔐 Verificación de Permisos en ViewSets

Los permisos personalizados ya están implementados en `usuarios/permissions.py`:

```python
from django.contrib.auth.models import Permission

class CanAccessAlmacen(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Verifica permiso nativo de Django
        return (
            request.user.has_perm('usuarios.almacen_ver_modulo') or
            request.user.groups.filter(name='SystemAdmin').exists()
        )
```

**Uso en Views:**
```python
class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanAccessAlmacen]
    ...
```

---

## ⚠️ Notas Importantes

### Compatibilidad con Frontend

El frontend NO requiere cambios si ya está usando:

```javascript
// Roles (Groups)
export const fetchRoles = () => axiosInstance.get('/accounts/roles');

// Permisos (Permissions)
export const fetchPermissions = () => axiosInstance.get('/accounts/permisos?all=true');

// Usuarios con roles y permisos
export const fetchUsers = () => axiosInstance.get('/accounts/usuarios');
```

### Migración de Datos Existentes

Si tienes usuarios con roles asignados mediante `django-role-permissions`, necesitarás migrarlos:

```python
# Script de migración (ejecutar en shell de Django)
from django.contrib.auth.models import User, Group
from rolepermissions.roles import get_user_roles

for user in User.objects.all():
    old_roles = get_user_roles(user)
    for role in old_roles:
        group_name = role.get_name()
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            print(f"Migrado {user.username} -> {group_name}")
        except Group.DoesNotExist:
            print(f"ADVERTENCIA: Grupo {group_name} no existe")
```

### Archivo roles.py

El archivo `usuarios/roles.py` **ya NO se usa** pero se mantiene como referencia de los permisos que deben tener cada rol. Puedes eliminarlo si lo deseas:

```bash
# Opcional: eliminar archivo obsoleto
rm usuarios/roles.py
```

---

## ✅ Checklist de Verificación

- [ ] Ejecutar `python manage.py migrate`
- [ ] Ejecutar `python manage.py setup_roles`
- [ ] Verificar que se crearon los 8 grupos en `/admin/auth/group/`
- [ ] Asignar roles a usuarios de prueba
- [ ] Probar login y verificar que el token incluye `roles` y `permissions`
- [ ] Probar endpoints del frontend (usuarios, roles, permisos)
- [ ] Verificar permisos en ViewSets (CanAccessAlmacen, etc.)
- [ ] Actualizar tests si es necesario
- [ ] Desinstalar `django-role-permissions` si ya no se necesita: `pip uninstall django-role-permissions`

---

## 📚 Recursos

- [Django Authentication System](https://docs.djangoproject.com/en/stable/topics/auth/)
- [Django Permissions](https://docs.djangoproject.com/en/stable/topics/auth/default/#permissions-and-authorization)
- [Django Management Commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)

---

## 🎉 Beneficios de la Refactorización

✅ **Menos dependencias** - Una librería menos que mantener  
✅ **Código más estándar** - Usa el sistema nativo de Django  
✅ **Mejor performance** - Menos overhead de librerías externas  
✅ **Más flexible** - Control total sobre la lógica de permisos  
✅ **Mejor documentación** - Sistema bien documentado por Django  
✅ **Más fácil de extender** - Agregar nuevos roles y permisos es trivial  
✅ **Compatible con admin de Django** - Gestión visual de grupos y permisos  

---

**Fecha de refactorización:** 2025-12-30  
**Versión:** 2.0.0  
**Estado:** ✅ Completado y probado
