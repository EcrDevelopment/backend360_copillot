# Sistema de Permisos Expandido: Modular + Granular

## Resumen de Cambios

En respuesta a los comentarios del usuario, se ha expandido el sistema de permisos funcionales para incluir:

1. **Permisos Modulares** (alto nivel) - Control de acceso al módulo completo
2. **Permisos Granulares** (acciones específicas) - Control de acciones individuales (crear, editar, eliminar)
3. **Nuevo Módulo: Mantenimiento** - Permisos para tablas de configuración del sistema
4. **Nuevo Módulo: Proveedor** - Permisos separados de Importaciones para usuarios tipo proveedor

## Total de Permisos

**Antes**: 14 permisos funcionales
**Ahora**: 38 permisos funcionales

### Distribución:
- **Usuarios**: 10 permisos (4 modulares + 6 granulares)
- **Almacén**: 11 permisos (5 modulares + 6 granulares)
- **Importaciones**: 11 permisos (5 modulares + 6 granulares)
- **Mantenimiento**: 6 permisos (2 modulares + 5 específicos)
- **Proveedor**: 4 permisos (acceso limitado a documentos propios)

## Listado Completo de Permisos

### 1. Módulo de Usuarios (10 permisos)

#### Modulares
| Permiso | Descripción | Incluye |
|---------|-------------|---------|
| `usuarios.can_manage_users` | Gestionar usuarios completo | create, edit, delete, view |
| `usuarios.can_view_users` | Ver usuarios | Solo lectura |
| `usuarios.can_manage_roles` | Gestionar roles y permisos | create, edit, delete roles |
| `usuarios.can_view_roles` | Ver roles | Solo lectura |

#### Granulares
| Permiso | Descripción | Uso |
|---------|-------------|-----|
| `usuarios.can_create_users` | Crear usuarios | Botón "Nuevo Usuario" |
| `usuarios.can_edit_users` | Editar usuarios | Botón "Editar" en listado |
| `usuarios.can_delete_users` | Eliminar usuarios | Botón "Eliminar" |
| `usuarios.can_create_roles` | Crear roles | Botón "Nuevo Rol" |
| `usuarios.can_edit_roles` | Editar roles | Botón "Editar Rol" |
| `usuarios.can_delete_roles` | Eliminar roles | Botón "Eliminar Rol" |

### 2. Módulo de Almacén (11 permisos)

#### Modulares
| Permiso | Descripción | Incluye |
|---------|-------------|---------|
| `almacen.can_manage_warehouse` | Gestionar almacén completo | Movimientos, guías, kardex |
| `almacen.can_view_warehouse` | Ver almacén | Solo lectura |
| `almacen.can_view_warehouse_reports` | Ver reportes | Acceso a reportes |
| `almacen.can_manage_stock` | Gestionar stock | Transferencias, ajustes |
| `almacen.can_view_stock` | Ver stock | Consulta de inventario |

#### Granulares
| Permiso | Descripción | Uso |
|---------|-------------|-----|
| `almacen.can_create_movements` | Crear movimientos | Registrar ingresos/salidas |
| `almacen.can_edit_movements` | Editar movimientos | Modificar movimientos |
| `almacen.can_delete_movements` | Eliminar movimientos | Anular movimientos |
| `almacen.can_create_transfers` | Crear transferencias | Nueva transferencia |
| `almacen.can_edit_transfers` | Editar transferencias | Modificar transferencia |
| `almacen.can_approve_transfers` | Aprobar transferencias | Autorizar transferencia |

### 3. Módulo de Importaciones (11 permisos)

#### Modulares
| Permiso | Descripción | Incluye |
|---------|-------------|---------|
| `importaciones.can_manage_importaciones` | Gestionar importaciones | DUA, declaraciones |
| `importaciones.can_view_importaciones` | Ver importaciones | Solo lectura |
| `importaciones.can_view_importaciones_reports` | Ver reportes | Acceso a reportes |
| `importaciones.can_manage_documents` | Gestionar documentos | Admin documentos |
| `importaciones.can_view_documents` | Ver documentos | Solo lectura |

#### Granulares
| Permiso | Descripción | Uso |
|---------|-------------|-----|
| `importaciones.can_create_importaciones` | Crear importaciones | Nueva importación |
| `importaciones.can_edit_importaciones` | Editar importaciones | Modificar datos |
| `importaciones.can_delete_importaciones` | Eliminar importaciones | Anular importación |
| `importaciones.can_create_documents` | Crear/subir documentos | Upload documentos |
| `importaciones.can_edit_documents` | Editar documentos | Modificar metadatos |
| `importaciones.can_delete_documents` | Eliminar documentos | Borrar documentos |

### 4. Módulo de Mantenimiento (6 permisos) **NUEVO**

#### Modulares
| Permiso | Descripción | Incluye |
|---------|-------------|---------|
| `usuarios.can_manage_maintenance_tables` | Gestionar todas las tablas | Acceso completo a mantenimiento |
| `usuarios.can_view_maintenance_tables` | Ver tablas | Solo lectura |

#### Específicos por Tabla
| Permiso | Descripción | Tabla |
|---------|-------------|-------|
| `usuarios.can_manage_document_types` | Gestionar tipos de documentos | Tabla Tipo Doc. |
| `usuarios.can_manage_companies` | Gestionar empresas | Tabla Empresas |
| `usuarios.can_manage_product_catalog` | Gestionar catálogo de productos | Tabla Productos |
| `usuarios.can_manage_warehouse_catalog` | Gestionar catálogo de almacenes | Tabla Almacenes |
| `usuarios.can_manage_stowage_types` | Gestionar tipos de estibaje | Tipo Estibaje |

### 5. Módulo de Proveedor (4 permisos) **NUEVO**

| Permiso | Descripción | Uso |
|---------|-------------|-----|
| `usuarios.can_upload_documents` | Cargar documentos DUA | Upload docs |
| `usuarios.can_manage_own_documents` | Gestionar documentos propios | CRUD propios |
| `usuarios.can_view_own_documents` | Ver documentos propios | Lista propia |
| `usuarios.can_download_own_documents` | Descargar documentos propios | Download propios |

**Nota**: Los permisos de proveedor son restrictivos - solo acceso a sus propios documentos.

## Jerarquía de Permisos

### Regla General
Los permisos modulares (`can_manage_*`) **incluyen** todos los permisos granulares correspondientes.

```
can_manage_users (modular)
  ├── can_view_users
  ├── can_create_users
  ├── can_edit_users
  └── can_delete_users
```

### Implementación en Frontend

```javascript
// Verificar permiso modular O granular
const canEditUser = user.permissions.includes('usuarios.can_manage_users') || 
                    user.permissions.includes('usuarios.can_edit_users');

// Mostrar botón solo si tiene permiso
{canEditUser && <Button>Editar</Button>}
```

### Implementación en Backend

```python
# En ViewSet - usar permiso modular para acceso general
class UserViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated(), CanViewUsersModule()]
        # Para create/update/delete, verificar permiso específico
        elif self.action == 'create':
            return [IsAuthenticated(), HasModulePermission()]
        # ...

# En la vista, definir permiso requerido
permission_required = 'usuarios.can_create_users'
```

## Configuración en settings.py

```python
FUNCTIONAL_PERMISSION_MODELS = [
    'usuarios.UsuariosPermissions',
    'usuarios.MantenimientoPermissions',
    'usuarios.ProveedorPermissions',
    'almacen.AlmacenPermissions',
    'importaciones.ImportacionesPermissions',
]
```

## Casos de Uso

### Caso 1: Administrador General
**Necesidad**: Acceso completo a todo

**Solución**: Grupo "SystemAdmin" o asignar todos los permisos modulares:
- `usuarios.can_manage_users`
- `usuarios.can_manage_roles`
- `usuarios.can_manage_maintenance_tables`
- `almacen.can_manage_warehouse`
- `almacen.can_manage_stock`
- `importaciones.can_manage_importaciones`
- `importaciones.can_manage_documents`

### Caso 2: Almacenero
**Necesidad**: Registrar movimientos y ver stock, pero no eliminar

**Solución**: Permisos granulares específicos:
- `almacen.can_view_warehouse` (ver listados)
- `almacen.can_create_movements` (registrar ingresos/salidas)
- `almacen.can_view_stock` (consultar inventario)

**NO dar**:
- ❌ `almacen.can_manage_warehouse` (muy amplio)
- ❌ `almacen.can_delete_movements` (no debe eliminar)

### Caso 3: Usuario Proveedor
**Necesidad**: Solo subir y ver sus propios documentos

**Solución**: Permisos de proveedor:
- `usuarios.can_upload_documents`
- `usuarios.can_view_own_documents`
- `usuarios.can_download_own_documents`

**NO dar**:
- ❌ `importaciones.can_view_importaciones` (vería todas las importaciones)
- ❌ `importaciones.can_manage_documents` (vería/editaría docs de otros)

### Caso 4: Gerente de Importaciones
**Necesidad**: Ver todo de importaciones, crear/editar, pero no eliminar

**Solución**: Mezcla de modulares y granulares:
- `importaciones.can_view_importaciones` (ver todo)
- `importaciones.can_create_importaciones` (crear)
- `importaciones.can_edit_importaciones` (editar)
- `importaciones.can_view_importaciones_reports` (reportes)
- `importaciones.can_view_documents` (ver docs)

**NO dar**:
- ❌ `importaciones.can_delete_importaciones` (no debe eliminar)
- ❌ `importaciones.can_delete_documents` (no debe borrar docs)

### Caso 5: Encargado de Mantenimiento
**Necesidad**: Gestionar solo tablas de configuración

**Solución**: Permisos de mantenimiento:
- `usuarios.can_manage_maintenance_tables` (acceso general)
- O permisos específicos por tabla si requiere control granular

**NO dar**:
- ❌ `usuarios.can_manage_users` (no debe gestionar usuarios)
- ❌ `almacen.can_manage_warehouse` (no debe gestionar almacén)

## Ventajas del Sistema Expandido

### 1. Flexibilidad Total
- Permisos amplios para admins (`can_manage_*`)
- Permisos específicos para roles limitados (`can_create_*`, `can_edit_*`)

### 2. Seguridad Mejorada
- Control fino sobre eliminación de datos
- Separación de proveedores de staff interno
- Aislamiento de tablas de mantenimiento

### 3. Fácil de Escalar
- Agregar nuevo permiso granular sin afectar existentes
- Jerarquía clara: modular > granular

### 4. Mejor UX
- Botones/acciones se muestran según permisos específicos
- Mensajes de error más claros ("No tiene permiso para eliminar")

## Migración desde Sistema Anterior

```python
# Mapeo de permisos legacy → nuevos permisos

LEGACY_TO_FUNCTIONAL_MAP = {
    # Usuarios
    'user.registrar_usuario': ['usuarios.can_manage_users', 'usuarios.can_create_users'],
    'user.editar_usuario': ['usuarios.can_manage_users', 'usuarios.can_edit_users'],
    'user.eliminar_usuario': ['usuarios.can_manage_users', 'usuarios.can_delete_users'],
    
    # Almacén
    'almacen.gestionar_productos': ['almacen.can_manage_warehouse'],
    'almacen.gestionar_movimientos': ['almacen.can_manage_warehouse', 'almacen.can_create_movements'],
    
    # Importaciones
    'importaciones.administrar_documentos_dua': ['importaciones.can_manage_documents'],
    
    # Proveedor
    'proveedor.cargar_documentos': ['usuarios.can_upload_documents'],
    'proveedor.administrar_documentos': ['usuarios.can_manage_own_documents'],
    
    # Mantenimiento
    'mantenimiento.tabla_tipo_documentos': ['usuarios.can_manage_maintenance_tables'],
}
```

## Archivos Modificados

1. `usuarios/models.py` - Agregado MantenimientoPermissions y ProveedorPermissions, expandido UsuariosPermissions
2. `almacen/models.py` - Expandido AlmacenPermissions con permisos granulares
3. `importaciones/models.py` - Expandido ImportacionesPermissions con permisos granulares

## Próximos Pasos

1. ✅ Crear migraciones para nuevos permisos
2. ⬜ Actualizar menu config con nuevos permisos
3. ⬜ Crear grupos de ejemplo con permisos asignados
4. ⬜ Actualizar ViewSets para usar permisos granulares
5. ⬜ Documentar ejemplos de uso en frontend

---

**Fecha**: 2025-12-31  
**Versión**: 2.0 (Expandido)
