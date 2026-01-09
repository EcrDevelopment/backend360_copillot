# Guía Rápida: Asignación de Permisos Funcionales

## Para Administradores

Esta guía explica cómo asignar los nuevos permisos funcionales a usuarios y grupos en el sistema.

## ¿Qué cambió?

### Antes
- ~2000 permisos técnicos por tabla (add_producto, change_producto, delete_producto, view_producto, etc.)
- Difícil de gestionar y propenso a errores

### Ahora
- ~15 permisos funcionales basados en acciones de negocio
- Nombres claros y descriptivos
- Más fácil de entender y asignar

## Lista de Permisos Funcionales

### Módulo de Usuarios
| Permiso | Descripción | ¿Para quién? |
|---------|-------------|--------------|
| `can_manage_users` | Crear, editar, eliminar usuarios | Administradores de Usuarios |
| `can_view_users` | Ver listado y detalles de usuarios | Cualquier usuario autenticado |
| `can_manage_roles` | Crear y modificar roles y permisos | Administradores del Sistema |
| `can_view_roles` | Ver roles y permisos disponibles | Administradores de Usuarios |

### Módulo de Almacén
| Permiso | Descripción | ¿Para quién? |
|---------|-------------|--------------|
| `can_manage_warehouse` | Gestionar guías, productos, almacenes, kardex | Jefe de Almacén, Asistentes |
| `can_view_warehouse` | Ver información de almacén | Cualquier usuario que necesite consultar |
| `can_view_warehouse_reports` | Acceder a reportes de almacén | Gerentes, Contadores |
| `can_manage_stock` | Gestionar stock y transferencias | Almaceneros |
| `can_view_stock` | Ver niveles de stock | Ventas, Logística |

### Módulo de Importaciones
| Permiso | Descripción | ¿Para quién? |
|---------|-------------|--------------|
| `can_manage_importaciones` | Gestionar DUA, declaraciones, proveedores | Jefe de Importaciones |
| `can_view_importaciones` | Ver información de importaciones | Asistentes, Consultores |
| `can_view_importaciones_reports` | Ver reportes de importaciones | Gerencia, Finanzas |
| `can_manage_documents` | Subir y editar documentos | Asistentes de Importaciones |
| `can_view_documents` | Ver y descargar documentos | Usuarios autorizados |

## Cómo Asignar Permisos

### Opción 1: Desde el Admin de Django (Recomendado)

#### Paso 1: Crear o Editar un Grupo
1. Ingresar al Admin de Django: `https://tu-dominio.com/admin/`
2. Ir a **Autenticación y autorización** → **Grupos**
3. Click en **Agregar grupo** o seleccionar un grupo existente

#### Paso 2: Asignar Permisos al Grupo
1. En el campo **Nombre**, ingresar el nombre del rol (ej: "Almaceneros")
2. En **Permisos disponibles**, buscar los permisos funcionales:
   - Se identifican por el texto en español descriptivo
   - Ejemplo: "Puede gestionar almacén (guías, detalles, kardex, movimientos)"
3. Seleccionar los permisos apropiados y moverlos a **Permisos elegidos**
4. Click en **Guardar**

#### Paso 3: Asignar Usuarios al Grupo
1. Ir a **Autenticación y autorización** → **Usuarios**
2. Seleccionar el usuario
3. En la sección **Permisos**, encontrar **Grupos**
4. Mover el grupo a **Grupos elegidos**
5. Click en **Guardar**

### Opción 2: Desde la API (Interfaz de Usuario)

#### Endpoint: GET /api/accounts/permisos
```bash
# Obtener lista de permisos funcionales disponibles
curl -H "Authorization: Bearer TOKEN" \
  https://tu-dominio.com/api/accounts/permisos?all=true
```

#### Endpoint: GET /api/accounts/roles
```bash
# Obtener lista de roles/grupos
curl -H "Authorization: Bearer TOKEN" \
  https://tu-dominio.com/api/accounts/roles
```

#### Endpoint: PUT /api/accounts/roles/{id}
```bash
# Actualizar permisos de un rol
curl -X PUT \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Almaceneros","permissions":[103,104,105]}' \
  https://tu-dominio.com/api/accounts/roles/5
```

## Ejemplos de Configuración por Rol

### Ejemplo 1: Almacenero
**Responsabilidades**: Registrar movimientos, gestionar stock, transferencias

**Permisos asignados**:
- ✅ `can_manage_warehouse` - Para registrar guías y movimientos
- ✅ `can_manage_stock` - Para hacer transferencias
- ✅ `can_view_warehouse` - Para consultar información

### Ejemplo 2: Vendedor
**Responsabilidades**: Consultar stock disponible, ver productos

**Permisos asignados**:
- ✅ `can_view_warehouse` - Para ver productos
- ✅ `can_view_stock` - Para consultar disponibilidad

### Ejemplo 3: Asistente de Importaciones
**Responsabilidades**: Registrar DUA, subir documentos, consultar información

**Permisos asignados**:
- ✅ `can_manage_importaciones` - Para registrar DUA y declaraciones
- ✅ `can_manage_documents` - Para subir documentos
- ✅ `can_view_importaciones` - Para consultar información

### Ejemplo 4: Gerente
**Responsabilidades**: Ver reportes, consultar información de todos los módulos

**Permisos asignados**:
- ✅ `can_view_warehouse_reports` - Reportes de almacén
- ✅ `can_view_importaciones_reports` - Reportes de importaciones
- ✅ `can_view_warehouse` - Información de almacén
- ✅ `can_view_importaciones` - Información de importaciones
- ✅ `can_view_stock` - Ver stock

### Ejemplo 5: Administrador de Usuarios
**Responsabilidades**: Crear usuarios, asignar permisos, gestionar roles

**Permisos asignados**:
- ✅ `can_manage_users` - Crear y editar usuarios
- ✅ `can_manage_roles` - Crear y modificar roles
- ✅ `can_view_users` - Ver usuarios
- ✅ `can_view_roles` - Ver roles

## Permisos Especiales

### SystemAdmin (Superusuario)
- **Acceso automático** a todas las funcionalidades
- No necesita permisos específicos asignados
- Útil para:
  - Configuración inicial del sistema
  - Soporte técnico
  - Administradores principales

### Permisos Individuales vs Grupos
- **Recomendado**: Usar **Grupos** para asignar permisos por rol
- **Evitar**: Asignar permisos directamente a usuarios individuales
- **Ventaja**: Más fácil de mantener y escalar

## Buenas Prácticas

### 1. Principio de Menor Privilegio
- Asignar solo los permisos necesarios para realizar el trabajo
- No dar permisos de "gestión" si solo necesitan "ver"

### 2. Usar Grupos en lugar de Permisos Directos
- Crear grupos por rol (Almaceneros, Vendedores, etc.)
- Asignar permisos al grupo, no a usuarios individuales
- Facilita la gestión cuando hay rotación de personal

### 3. Documentar los Roles
- Mantener una lista de qué permisos tiene cada rol
- Revisar periódicamente si los permisos siguen siendo apropiados

### 4. Revisar Periódicamente
- Auditar permisos cada 3-6 meses
- Remover permisos de usuarios inactivos
- Ajustar permisos según cambios en responsabilidades

### 5. Testing de Permisos
- Después de asignar permisos, verificar que el usuario puede:
  - Acceder a las funciones necesarias
  - No puede acceder a funciones restringidas

## Solución de Problemas

### Problema: Usuario no puede acceder a una funcionalidad

**Verificar**:
1. ¿El usuario está autenticado?
2. ¿El usuario pertenece a un grupo con el permiso apropiado?
3. ¿El permiso funcional está asignado al grupo?

**Solución**:
```python
# En Django shell
from django.contrib.auth.models import User
user = User.objects.get(username='juan')

# Verificar permisos del usuario
print(user.get_all_permissions())

# Verificar grupos del usuario
print(user.groups.all())

# Verificar si tiene un permiso específico
print(user.has_perm('almacen.can_view_warehouse'))
```

### Problema: Permisos no aparecen en la lista

**Solución**: Ejecutar las migraciones
```bash
python manage.py migrate usuarios
python manage.py migrate almacen
python manage.py migrate importaciones
```

### Problema: Usuario tiene permisos pero sigue sin acceso

**Verificar**:
1. ¿El ViewSet está usando la clase de permiso correcta?
2. ¿El nombre del permiso coincide exactamente?
3. ¿Hay cache de sesión? Pedir al usuario que cierre sesión y vuelva a ingresar

## Contacto y Soporte

Para soporte adicional:
- **Email**: sistemas@grupolasemilla.com
- **Documentación completa**: Ver `FUNCTIONAL_PERMISSIONS.md`
- **Equipo de desarrollo**: Backend360 Development Team

---

**Última actualización**: 2025-12-30  
**Versión**: 1.0
