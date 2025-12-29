# Cambios de Compatibilidad - Sistema de Roles y Permisos

## Resumen de Cambios

Se han realizado modificaciones al sistema de roles y permisos para mantener la compatibilidad con el frontend existente y evitar interrupciones en el funcionamiento de los módulos.

## Problema Identificado

El sistema de roles y permisos anterior era demasiado restrictivo y requería que los usuarios tuvieran roles específicos asignados para acceder a los módulos, lo cual rompió la funcionalidad existente del frontend.

## Solución Implementada

### 1. Permisos de Acceso a Módulos Más Flexibles

Se modificaron las siguientes clases de permisos para permitir acceso a cualquier usuario autenticado:

#### `CanAccessImportaciones`
- **Antes**: Requería permiso `importaciones.ver_modulo` o rol `system_admin`
- **Ahora**: Permite acceso a cualquier usuario autenticado
- **Razón**: El frontend necesita acceder a datos de importaciones para usuarios regulares

#### `CanAccessAlmacen`
- **Antes**: Requería permiso `almacen.ver_modulo` o rol `system_admin`
- **Ahora**: Permite acceso a cualquier usuario autenticado
- **Razón**: El frontend necesita acceder a datos de almacén para usuarios regulares

#### `CanEditDocuments`
- **Antes**: Requería permisos específicos de edición de documentos
- **Ahora**: Permite edición a cualquier usuario autenticado
- **Razón**: Los usuarios necesitan poder cargar y editar documentos sin configuración adicional de roles

#### `CanDeleteResource`
- **Antes**: Solo permitía a usuarios con roles de administrador
- **Ahora**: Permite a cualquier usuario autenticado eliminar recursos
- **Razón**: Mantener compatibilidad con el comportamiento anterior

### 2. ViewSets de Usuario con Permisos Diferenciados

Se actualizaron los siguientes ViewSets para permitir lectura a todos los usuarios autenticados, pero mantener restricciones en operaciones de escritura:

#### `UserViewSet`
- **GET (list, retrieve)**: Todos los usuarios autenticados
  - Los usuarios regulares solo ven su propia información
  - Los administradores ven todos los usuarios
- **POST, PUT, PATCH, DELETE**: Requiere `CanManageUsers` (SystemAdmin o AccountsAdmin)

#### `RoleViewSet`
- **GET (list, retrieve)**: Todos los usuarios autenticados
- **POST, PUT, PATCH, DELETE**: Requiere `CanManageUsers`

#### `PermissionViewSet`
- **GET (list, retrieve)**: Todos los usuarios autenticados
- **POST, PUT, PATCH, DELETE**: Requiere `CanManageUsers`

## Compatibilidad con Frontend

### Endpoints Afectados

Los siguientes endpoints ahora son accesibles para usuarios autenticados:

1. **Módulo de Almacén** (`/api/almacen/*`)
   - Todos los endpoints que usan `CanAccessAlmacen`
   - Ejemplos: productos, stock, movimientos, kardex

2. **Módulo de Importaciones** (`/api/importaciones/*`)
   - Todos los endpoints que usan `CanAccessImportaciones`
   - Ejemplos: órdenes de compra, despachos, declaraciones, documentos

3. **Módulo de Usuarios** (`/api/accounts/*`)
   - GET endpoints para usuarios, roles y permisos
   - POST/PUT/DELETE solo para administradores

## Seguridad

### Medidas de Seguridad Mantenidas

1. **Autenticación Requerida**: Todos los endpoints requieren autenticación JWT
2. **Filtrado de Datos**: Los usuarios regulares solo ven sus propios datos en UserViewSet
3. **Operaciones Administrativas**: Las operaciones de creación, actualización y eliminación de usuarios/roles/permisos siguen protegidas
4. **Auditoría**: El sistema de auditoría sigue registrando todas las operaciones

### Consideraciones para Producción

Si se requiere mayor seguridad en producción, se pueden:

1. **Reactivar Permisos Granulares**: Modificar las clases de permisos para requerir roles específicos
2. **Configurar Roles**: Asignar roles apropiados a todos los usuarios
3. **Permisos por Objeto**: Implementar verificaciones a nivel de objeto en lugar de a nivel de vista

## Migración de Usuarios Existentes

No se requiere migración de datos. Los usuarios existentes podrán:

- ✅ Acceder a los módulos de almacén e importaciones
- ✅ Ver su propia información de usuario
- ✅ Editar y eliminar recursos según sea necesario
- ✅ Cargar y administrar documentos

Los administradores pueden opcionalmente asignar roles específicos para habilitar funcionalidades avanzadas en el futuro.

## Próximos Pasos Recomendados

1. **Probar el Frontend**: Verificar que todas las funcionalidades del frontend funcionen correctamente
2. **Asignar Roles Gradualmente**: Comenzar a asignar roles a usuarios para preparar la implementación de permisos granulares
3. **Monitorear Logs**: Revisar los logs de auditoría para identificar patrones de uso
4. **Documentar Requisitos**: Documentar qué operaciones deberían ser restringidas en el futuro

## Archivos Modificados

- `usuarios/permissions.py`: Clases de permisos actualizadas
- `usuarios/views.py`: ViewSets con permisos diferenciados

## Soporte

Para cualquier problema o pregunta sobre estos cambios, revisar:
- Este documento (`CAMBIOS_COMPATIBILIDAD.md`)
- `SECURITY_PERMISSIONS.md` para documentación detallada del sistema de permisos
- Logs de auditoría en `logs/audit.log`
