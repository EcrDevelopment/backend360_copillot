# Mapeo de Permisos: Legacy → Funcionales

## Análisis del Menu Actual

Este documento analiza el `frontend-menu-config.js` actual y proporciona el mapeo exacto hacia los nuevos permisos funcionales.

## Mapeo Completo de Permisos

### Módulo: Importaciones

| Permiso Actual (Legacy) | Permiso Funcional (Nuevo) | Item del Menu | Acción |
|------------------------|---------------------------|---------------|--------|
| `importaciones` | `importaciones.can_view_importaciones` | Importaciones (padre) | Ver módulo |
| `importaciones.ver_fletes_internacionales` | `importaciones.can_view_importaciones` | Listado Fletes | Ver listado |
| `importaciones.registrar_flete_internacional` | `importaciones.can_manage_importaciones` | Fletes Extranjeros | Crear/Editar |
| `importaciones.ver_reporte_estibas` | `importaciones.can_view_importaciones_reports` | Reporte Estiba | Ver reportes |
| `importaciones.administrar_documentos_dua` | `importaciones.can_manage_documents` | Documentos Prov. | Gestionar docs |
| `importaciones.administrar_expedientes_dua` | `importaciones.can_manage_documents` | Archivos DUA | Gestionar expedientes |
| `null` (Ticket Senasa) | `importaciones.can_view_importaciones` | Ticket Senasa | Consulta general |

### Módulo: Proveedores

| Permiso Actual (Legacy) | Permiso Funcional (Nuevo) | Item del Menu | Acción |
|------------------------|---------------------------|---------------|--------|
| `proveedor.cargar_documentos` | `importaciones.can_manage_documents` | Cargar Documentos DUA | Subir docs |
| `proveedor.administrar_documentos` | `importaciones.can_manage_documents` | Gestión de docs. | Administrar docs |

**Nota**: Los permisos de proveedor se integran con `importaciones.can_manage_documents` ya que son parte del flujo de documentos de importación.

### Módulo: Tablas (Mantenimiento)

| Permiso Actual (Legacy) | Permiso Funcional (Nuevo) | Item del Menu | Acción |
|------------------------|---------------------------|---------------|--------|
| `mantenimiento.tabla_tipo_documentos` | `usuarios.can_manage_roles` | Tablas (padre) | Administración |
| `mantenimiento.tabla_tipo_documentos` | `usuarios.can_manage_roles` | Tabla Tipo Doc. | CRUD tipos doc |
| `null` (Empresas) | `usuarios.can_view_users` | Tabla Empresas | Ver/Gestionar |
| `null` (Productos) | `almacen.can_manage_warehouse` | Tabla Productos | CRUD productos |
| `null` (Almacenes) | `almacen.can_manage_warehouse` | Tabla Almacenes | CRUD almacenes |
| `null` (Tipo Estibaje) | `almacen.can_manage_warehouse` | Tipo Estibaje | CRUD tipos |

**Nota**: Las tablas de mantenimiento se distribuyen según el módulo al que pertenecen.

### Módulo: Almacén

| Permiso Actual (Legacy) | Permiso Funcional (Nuevo) | Item del Menu | Acción |
|------------------------|---------------------------|---------------|--------|
| `null` (módulo) | `almacen.can_view_warehouse` | Almacén (padre) | Ver módulo |
| `null` (Ingresos/Salidas) | `almacen.can_manage_warehouse` | Ingresos/Salidas | Registrar movimientos |
| `null` (Lector QR) | `almacen.can_view_warehouse` | Lector QR | Consulta rápida |
| `null` (Stock) | `almacen.can_view_stock` | Stock | Ver inventario |
| `null` (Transferencias) | `almacen.can_manage_stock` | Transferencias | Gestionar transferencias |
| `null` (Consulta Guía) | `almacen.can_view_warehouse` | Consulta Guía | Consulta general |

### Módulo: Usuarios

| Permiso Actual (Legacy) | Permiso Funcional (Nuevo) | Item del Menu | Acción |
|------------------------|---------------------------|---------------|--------|
| `null` (módulo) | `usuarios.can_view_users` | Usuarios (padre) | Ver módulo |
| `user.listar_usuarios` | `usuarios.can_view_users` | Usuarios | Ver listado |
| `user.listar_usuarios` | `usuarios.can_view_roles` | Roles | Ver roles |
| `user.listar_usuarios` | `usuarios.can_view_roles` | Permisos | Ver permisos |

**Nota**: Para gestionar (crear/editar/eliminar) se requiere `usuarios.can_manage_users` y `usuarios.can_manage_roles` respectivamente.

## Menu Config Actualizado

```javascript
/*
Menu actualizado con permisos funcionales del backend
- Se usan los 14 permisos funcionales en lugar de ~2000 permisos de tabla
- Un permiso puede controlar múltiples opciones del menú
- Permisos más claros y fáciles de gestionar
*/

const menuConfig = [
  {
    key: '1',
    icon: <HomeOutlined />,
    label: 'Inicio',
    to: '/',
    permission: null, // Público
  },
  {
    key: 'sub1',
    icon: <GoContainer />,
    label: 'Importaciones',
    permission: 'importaciones.can_view_importaciones', // ✅ Nuevo permiso funcional
    children: [
      { 
        key: '3', 
        label: 'Listado Fletes', 
        to: '/importaciones/ver_fletes_internacionales', 
        permission: 'importaciones.can_view_importaciones' // ✅ Ver importaciones
      },
      { 
        key: '4', 
        label: 'Reporte Estiba', 
        to: '/importaciones/reporte-estiba', 
        permission: 'importaciones.can_view_importaciones_reports' // ✅ Ver reportes
      },
      { 
        key: '5', 
        label: 'Documentos Prov.', 
        to: '/importaciones/gestion_documentos', 
        permission: 'importaciones.can_manage_documents' // ✅ Gestionar docs
      },
      { 
        key: '6', 
        label: 'Archivos DUA', 
        to: '/importaciones/listado-archivos-dua', 
        permission: 'importaciones.can_manage_documents' // ✅ Gestionar docs
      },
      { 
        key: '7', 
        label: 'Ticket Senasa', 
        to: '/consulta-ticket-senasa', 
        permission: 'importaciones.can_view_importaciones' // ✅ Consulta general
      },
    ],
  },
  {
    key: 'sub2',
    icon: <AiOutlineTruck />,
    label: 'Proveedores',
    permission: 'importaciones.can_view_documents', // ✅ Ver documentos
    children: [
      { 
        key: '8', 
        label: 'Cargar Documentos DUA', 
        to: '/proveedores/carga_docs_dua', 
        permission: 'importaciones.can_manage_documents' // ✅ Subir docs
      },
      { 
        key: '9', 
        label: 'Gestión de docs.', 
        to: '/proveedores/gestion_de_documentos', 
        permission: 'importaciones.can_manage_documents' // ✅ Gestionar docs
      },
    ],
  },
  {
    key: 'sub3',
    icon: <MdOutlineTableView />,
    label: 'Tablas',
    permission: 'usuarios.can_manage_roles', // ✅ Administración de tablas
    children: [
      { 
        key: '10', 
        label: 'Tabla Tipo Doc.', 
        to: '/tipos_documentos', 
        permission: 'usuarios.can_manage_roles' // ✅ Gestionar catálogos
      },
      { 
        key: '11', 
        label: 'Tabla Empresas', 
        to: '/miscelanea/empresas', 
        permission: 'usuarios.can_view_users' // ✅ Ver empresas
      },
      { 
        key: '12', 
        label: 'Tabla Productos', 
        to: '/miscelanea/productos', 
        permission: 'almacen.can_manage_warehouse' // ✅ Gestionar productos
      },
      { 
        key: '13', 
        label: 'Tabla Almacenes', 
        to: '/miscelanea/almacenes', 
        permission: 'almacen.can_manage_warehouse' // ✅ Gestionar almacenes
      },
      { 
        key: '14', 
        label: 'Tipo Estibaje', 
        to: '/tipo_estiba', 
        permission: 'almacen.can_manage_warehouse' // ✅ Gestionar tipos
      },
    ],
  },
  {
    key: 'sub4',
    icon: <BiStore />,
    label: 'Almacen',
    permission: 'almacen.can_view_warehouse', // ✅ Ver módulo de almacén
    children: [
      { 
        key: '15', 
        label: 'Ingresos/Salidas', 
        to: '/almacen/movimientos', 
        permission: 'almacen.can_manage_warehouse' // ✅ Registrar movimientos
      },
      { 
        key: '16', 
        label: 'Lector QR', 
        to: '/almacen/lectorQr', 
        permission: 'almacen.can_view_warehouse' // ✅ Consulta rápida
      },
      { 
        key: '17', 
        label: 'Stock', 
        to: '/almacen/stock', 
        permission: 'almacen.can_view_stock' // ✅ Ver inventario
      },
      { 
        key: '18', 
        label: 'Transferencias', 
        to: '/almacen/transferencias', 
        permission: 'almacen.can_manage_stock' // ✅ Gestionar transferencias
      },
      { 
        key: '19', 
        label: 'Consulta Guía', 
        to: '/consulta-guia', 
        permission: 'almacen.can_view_warehouse' // ✅ Consulta general
      },
    ]
  },
  {
    key: 'sub5',
    icon: <MdLock />,
    label: 'Usuarios',
    permission: 'usuarios.can_view_users', // ✅ Ver módulo de usuarios
    children: [
      { 
        key: '20', 
        label: 'Usuarios', 
        to: '/usuarios', 
        permission: 'usuarios.can_view_users' // ✅ Ver usuarios
      },
      { 
        key: '21', 
        label: 'Roles', 
        to: '/roles', 
        permission: 'usuarios.can_view_roles' // ✅ Ver roles
      },
      { 
        key: '22', 
        label: 'Permisos', 
        to: '/permisos', 
        permission: 'usuarios.can_view_roles' // ✅ Ver permisos
      },
    ],
  },
];
```

## Resumen de Cambios

### Antes (Permisos Legacy)
- ~15 permisos diferentes en el menú
- Muchos items con `permission: null`
- Permisos granulares por acción específica
- Difícil de mantener

### Después (Permisos Funcionales)
- **14 permisos funcionales** en total
- Todos los items tienen permisos asignados
- Permisos agrupados por módulo y acción
- Fácil de mantener y escalar

## Ventajas del Nuevo Sistema

### 1. Menos Permisos, Más Control
- **Antes**: `importaciones.ver_fletes_internacionales`, `importaciones.registrar_flete_internacional`, etc. (muchos permisos)
- **Ahora**: `importaciones.can_view_importaciones`, `importaciones.can_manage_importaciones` (2 permisos)

### 2. Jerarquía Clara
- `can_manage_*` incluye `can_view_*`
- Si un usuario puede gestionar, automáticamente puede ver

### 3. Agrupación Lógica
- Todos los permisos de almacén empiezan con `almacen.*`
- Todos los permisos de usuarios empiezan con `usuarios.*`
- Todos los permisos de importaciones empiezan con `importaciones.*`

### 4. Escalabilidad
- Agregar nuevas opciones al menú es más fácil
- Los permisos existentes cubren la mayoría de casos
- Solo se crean nuevos permisos para funcionalidades completamente nuevas

## Items Pendientes de Desarrollo

Los siguientes items actualmente tienen `permission: null`. Se sugiere asignarles permisos:

### Alta Prioridad
1. **Almacén completo** → Ya mapeado a permisos funcionales
2. **Tablas de mantenimiento** → Ya mapeado a permisos funcionales

### Media Prioridad
3. **Ticket Senasa** → `importaciones.can_view_importaciones` (consulta pública o requiere permiso básico)

### Notas
- **Inicio** puede quedarse sin permiso (público para usuarios autenticados)
- **Lector QR** podría ser público o requerir `almacen.can_view_warehouse`

## Migración Gradual

### Opción 1: Migración Inmediata (Recomendada)
Reemplazar todos los permisos a la vez con el nuevo `menuConfig`.

**Ventajas**:
- Cambio limpio
- Todos usan el mismo sistema
- Más fácil de mantener

**Desventajas**:
- Requiere actualizar permisos de usuarios/grupos

### Opción 2: Soporte Dual Temporal
Soportar ambos sistemas de permisos durante un periodo de transición.

```javascript
// Función helper para transición
const checkPermission = (user, legacyPerm, functionalPerm) => {
  // Verificar si tiene el permiso funcional nuevo
  if (user.permissions.includes(functionalPerm)) {
    return true;
  }
  
  // Fallback: verificar permiso legacy
  if (legacyPerm && user.permissions.includes(legacyPerm)) {
    return true;
  }
  
  return false;
};
```

## Código de Integración

Ver `FRONTEND_INTEGRATION.md` para:
- Funciones de validación de permisos
- Filtrado dinámico del menú
- Cache de permisos
- Ejemplos con React
- Tests unitarios

## Próximos Pasos

1. ✅ **Revisar mapeo** - Verificar que todos los permisos estén correctamente asignados
2. ⬜ **Actualizar menuConfig** - Implementar el nuevo menuConfig en el frontend
3. ⬜ **Crear/Actualizar grupos** - Asignar permisos funcionales a grupos en Django admin
4. ⬜ **Probar con usuarios reales** - Verificar que el filtrado del menú funcione correctamente
5. ⬜ **Documentar cambios** - Comunicar a equipo sobre nuevos permisos

---

**Fecha de Análisis**: 2025-12-31  
**Versión**: 1.0
