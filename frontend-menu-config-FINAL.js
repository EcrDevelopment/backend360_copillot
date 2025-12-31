/*
Menu actualizado con sistema de permisos EXPANDIDO (Modular + Granular)

CAMBIOS PRINCIPALES vs versión anterior:
1. ✅ Proveedores ahora usa permisos separados (usuarios.can_upload_documents) - NO comparte con Importaciones
2. ✅ Tablas usa permisos de Mantenimiento (usuarios.can_manage_maintenance_tables) - NO permisos de usuarios
3. ✅ Permisos granulares disponibles para control específico dentro de cada módulo
4. ✅ Total: 38 permisos funcionales (14 modulares + 24 granulares)

ESTRUCTURA DE PERMISOS:
- Permisos MODULARES (alto nivel): can_manage_*, can_view_* - Control de acceso al módulo
- Permisos GRANULARES (acciones): can_create_*, can_edit_*, can_delete_* - Control de botones/acciones específicas

JERARQUÍA:
- can_manage_* incluye automáticamente can_view_*, can_create_*, can_edit_*, can_delete_*
- Para control fino, usar solo permisos granulares sin el modular

EJEMPLO USO FRONTEND:
const canEditUser = user.permissions.includes('usuarios.can_manage_users') || 
                    user.permissions.includes('usuarios.can_edit_users');
                    
{canEditUser && <Button onClick={handleEdit}>Editar</Button>}

DOCUMENTACIÓN COMPLETA:
- EXPANDED_PERMISSIONS.md - Sistema expandido con 38 permisos
- MENU_PERMISSIONS_MAPPING.md - Mapeo de permisos legacy
- FRONTEND_INTEGRATION.md - Ejemplos de integración
*/

const menuConfig = [
  {
    key: '1',
    icon: <HomeOutlined />,
    label: 'Inicio',
    to: '/',
    permission: null, // Público para todos los usuarios autenticados
  },
  
  {
    key: 'sub1',
    icon: <GoContainer />,
    label: 'Importaciones',
    permission: 'importaciones.can_view_importaciones', // ✅ Permiso modular para ver módulo
    children: [
      { 
        key: '3', 
        label: 'Listado Fletes', 
        to: '/importaciones/ver_fletes_internacionales', 
        permission: 'importaciones.can_view_importaciones', // Ver importaciones
        // Nota: Para crear/editar fletes usar: importaciones.can_create_importaciones / can_edit_importaciones
      },
      { 
        key: '4', 
        label: 'Reporte Estiba', 
        to: '/importaciones/reporte-estiba', 
        permission: 'importaciones.can_view_importaciones_reports', // Ver reportes
      },
      { 
        key: '5', 
        label: 'Documentos Prov.', 
        to: '/importaciones/gestion_documentos', 
        permission: 'importaciones.can_manage_documents', // Gestionar documentos (amplio)
        // Nota: Para control granular usar: can_create_documents, can_edit_documents, can_delete_documents
      },
      { 
        key: '6', 
        label: 'Archivos DUA', 
        to: '/importaciones/listado-archivos-dua', 
        permission: 'importaciones.can_manage_documents', // Gestionar expedientes
      },
      { 
        key: '7', 
        label: 'Ticket Senasa', 
        to: '/consulta-ticket-senasa', 
        permission: 'importaciones.can_view_importaciones', // Consulta general
      },
    ],
  },
  
  {
    key: 'sub2',
    icon: <AiOutlineTruck />,
    label: 'Proveedores',
    permission: 'usuarios.can_view_own_documents', // ✅ NUEVO: Permisos específicos de proveedor (separado de importaciones)
    children: [
      { 
        key: '8', 
        label: 'Cargar Documentos DUA', 
        to: '/proveedores/carga_docs_dua', 
        permission: 'usuarios.can_upload_documents', // ✅ Subir documentos (solo proveedor)
      },
      { 
        key: '9', 
        label: 'Gestión de docs.', 
        to: '/proveedores/gestion_de_documentos', 
        permission: 'usuarios.can_manage_own_documents', // ✅ Gestionar SOLO sus propios docs
      },
    ],
  },

  {
    key: 'sub3',
    icon: <MdOutlineTableView />,
    label: 'Tablas',
    permission: 'usuarios.can_view_maintenance_tables', // ✅ NUEVO: Permisos de mantenimiento (NO usuarios)
    children: [
      { 
        key: '10', 
        label: 'Tabla Tipo Doc.', 
        to: '/tipos_documentos', 
        permission: 'usuarios.can_manage_document_types', // ✅ Específico para tipos de documentos
      },
      { 
        key: '11', 
        label: 'Tabla Empresas', 
        to: '/miscelanea/empresas', 
        permission: 'usuarios.can_manage_companies', // ✅ Específico para empresas
      },
      { 
        key: '12', 
        label: 'Tabla Productos', 
        to: '/miscelanea/productos', 
        permission: 'usuarios.can_manage_product_catalog', // ✅ Específico para catálogo de productos
      },
      { 
        key: '13', 
        label: 'Tabla Almacenes', 
        to: '/miscelanea/almacenes', 
        permission: 'usuarios.can_manage_warehouse_catalog', // ✅ Específico para catálogo de almacenes
      },
      { 
        key: '14', 
        label: 'Tipo Estibaje', 
        to: '/tipo_estiba', 
        permission: 'usuarios.can_manage_stowage_types', // ✅ Específico para tipos de estibaje
      },
    ],
  },

  {
    key: 'sub4',
    icon: <BiStore />,
    label: 'Almacen',
    permission: 'almacen.can_view_warehouse', // ✅ Permiso modular para ver módulo
    children: [
      { 
        key: '15', 
        label: 'Ingresos/Salidas', 
        to: '/almacen/movimientos', 
        permission: 'almacen.can_view_warehouse', // Ver movimientos
        // Nota: Botones internos usan: can_create_movements, can_edit_movements, can_delete_movements
      },
      { 
        key: '16', 
        label: 'Lector QR', 
        to: '/almacen/lectorQr', 
        permission: 'almacen.can_view_warehouse', // Consulta rápida
      },
      { 
        key: '17', 
        label: 'Stock', 
        to: '/almacen/stock', 
        permission: 'almacen.can_view_stock', // Ver inventario
      },
      { 
        key: '18', 
        label: 'Transferencias', 
        to: '/almacen/transferencias', 
        permission: 'almacen.can_view_stock', // Ver transferencias
        // Nota: Botones internos usan: can_create_transfers, can_edit_transfers, can_approve_transfers
      },
      { 
        key: '19', 
        label: 'Consulta Guía', 
        to: '/consulta-guia', 
        permission: 'almacen.can_view_warehouse', // Consulta general
      },
    ]
  },

  {
    key: 'sub5',
    icon: <MdLock />,
    label: 'Usuarios',
    permission: 'usuarios.can_view_users', // ✅ Permiso modular para ver módulo
    children: [
      { 
        key: '20', 
        label: 'Usuarios', 
        to: '/usuarios', 
        permission: 'usuarios.can_view_users', // Ver lista de usuarios
        // Nota: Botones internos usan: can_create_users, can_edit_users, can_delete_users
      },
      { 
        key: '21', 
        label: 'Roles', 
        to: '/roles', 
        permission: 'usuarios.can_view_roles', // Ver roles del sistema
        // Nota: Botones internos usan: can_create_roles, can_edit_roles, can_delete_roles
      },
      { 
        key: '22', 
        label: 'Permisos', 
        to: '/permisos', 
        permission: 'usuarios.can_view_roles', // Ver permisos disponibles
      },
    ],
  },
];

/*
═══════════════════════════════════════════════════════════════════════════════
GUÍA DE USO DE PERMISOS GRANULARES EN VISTAS
═══════════════════════════════════════════════════════════════════════════════

EJEMPLO 1: Página de Usuarios con Botones Condicionales
────────────────────────────────────────────────────────────────────────────────
import React from 'react';
import { Button, Table } from 'antd';

const UsuariosPage = ({ user }) => {
  // Verificar permisos granulares
  const canCreate = user.permissions.includes('usuarios.can_manage_users') || 
                    user.permissions.includes('usuarios.can_create_users');
  
  const canEdit = user.permissions.includes('usuarios.can_manage_users') || 
                  user.permissions.includes('usuarios.can_edit_users');
  
  const canDelete = user.permissions.includes('usuarios.can_manage_users') || 
                    user.permissions.includes('usuarios.can_delete_users');

  return (
    <div>
      {canCreate && (
        <Button type="primary" onClick={handleCreate}>
          Nuevo Usuario
        </Button>
      )}
      
      <Table
        dataSource={usuarios}
        columns={[
          { title: 'Nombre', dataIndex: 'nombre' },
          {
            title: 'Acciones',
            render: (_, record) => (
              <>
                {canEdit && <Button onClick={() => handleEdit(record)}>Editar</Button>}
                {canDelete && <Button danger onClick={() => handleDelete(record)}>Eliminar</Button>}
              </>
            )
          }
        ]}
      />
    </div>
  );
};

EJEMPLO 2: Página de Almacén con Permisos Granulares
────────────────────────────────────────────────────────────────────────────────
const MovimientosPage = ({ user }) => {
  const canCreateMovement = user.permissions.includes('almacen.can_manage_warehouse') || 
                            user.permissions.includes('almacen.can_create_movements');
  
  const canEditMovement = user.permissions.includes('almacen.can_manage_warehouse') || 
                          user.permissions.includes('almacen.can_edit_movements');
  
  const canDeleteMovement = user.permissions.includes('almacen.can_manage_warehouse') || 
                            user.permissions.includes('almacen.can_delete_movements');

  return (
    <div>
      {canCreateMovement && (
        <Button onClick={handleNewMovement}>Registrar Ingreso/Salida</Button>
      )}
      
      <MovimientosList 
        onEdit={canEditMovement ? handleEdit : null}
        onDelete={canDeleteMovement ? handleDelete : null}
      />
    </div>
  );
};

EJEMPLO 3: Función Helper Reutilizable
────────────────────────────────────────────────────────────────────────────────
// utils/permissions.js
export const checkPermission = (userPermissions, requiredPermissions) => {
  if (!Array.isArray(requiredPermissions)) {
    requiredPermissions = [requiredPermissions];
  }
  
  return requiredPermissions.some(perm => userPermissions.includes(perm));
};

export const checkAnyPermission = (userPermissions, permissionsList) => {
  return permissionsList.some(perms => checkPermission(userPermissions, perms));
};

// Uso:
const canEdit = checkAnyPermission(user.permissions, [
  'usuarios.can_manage_users',
  'usuarios.can_edit_users'
]);

═══════════════════════════════════════════════════════════════════════════════
CASOS DE USO ESPECÍFICOS
═══════════════════════════════════════════════════════════════════════════════

CASO 1: Almacenero que solo registra ingresos/salidas
──────────────────────────────────────────────────────
Permisos asignados:
  ✓ almacen.can_view_warehouse (puede ver el módulo y listados)
  ✓ almacen.can_create_movements (puede registrar movimientos)
  ✗ almacen.can_edit_movements (NO puede editar)
  ✗ almacen.can_delete_movements (NO puede eliminar)

Resultado en UI:
  - Ve el menú "Almacén" y sub-opciones
  - En "Ingresos/Salidas" ve el botón "Registrar"
  - NO ve botones "Editar" ni "Eliminar" en la lista

CASO 2: Usuario Proveedor externo
──────────────────────────────────
Permisos asignados:
  ✓ usuarios.can_upload_documents (puede subir docs)
  ✓ usuarios.can_view_own_documents (puede ver sus docs)
  ✗ importaciones.can_view_importaciones (NO ve módulo Importaciones)

Resultado en UI:
  - Ve solo el menú "Proveedores"
  - NO ve menú "Importaciones"
  - Solo accede a sus propios documentos

CASO 3: Gerente de Importaciones
─────────────────────────────────
Permisos asignados:
  ✓ importaciones.can_view_importaciones (ve todo)
  ✓ importaciones.can_create_importaciones (puede crear)
  ✓ importaciones.can_edit_importaciones (puede editar)
  ✗ importaciones.can_delete_importaciones (NO puede eliminar)

Resultado en UI:
  - Ve menú completo de Importaciones
  - Puede crear y editar importaciones
  - NO ve botón "Eliminar" (solo admin puede eliminar)

CASO 4: Encargado de Mantenimiento
───────────────────────────────────
Permisos asignados:
  ✓ usuarios.can_manage_maintenance_tables (acceso completo a tablas)
  ✗ usuarios.can_manage_users (NO gestiona usuarios)
  ✗ almacen.can_manage_warehouse (NO gestiona almacén)

Resultado en UI:
  - Ve solo menú "Tablas"
  - Puede editar todas las tablas de mantenimiento
  - NO ve menús "Usuarios" ni "Almacén"

═══════════════════════════════════════════════════════════════════════════════
NOTAS IMPORTANTES
═══════════════════════════════════════════════════════════════════════════════

1. JERARQUÍA DE PERMISOS:
   - Permisos modulares (can_manage_*) incluyen TODOS los permisos granulares
   - Si das can_manage_users, automáticamente tiene can_create/edit/delete_users
   - Para restricción específica, dar SOLO permisos granulares (sin el modular)

2. PROVEEDORES SEPARADOS:
   - Los permisos usuarios.can_*_own_documents son RESTRICTIVOS
   - Solo acceden a SUS PROPIOS documentos
   - NO comparten permisos con importaciones.can_* (que es para staff)

3. TABLAS DE MANTENIMIENTO:
   - Separadas de permisos de usuarios
   - Usar usuarios.can_manage_*_catalog para tablas específicas
   - O usuarios.can_manage_maintenance_tables para acceso completo

4. BACKEND DEBE VALIDAR:
   - El frontend solo oculta opciones
   - El backend DEBE verificar permisos en cada endpoint
   - Ver HasModulePermission en usuarios/permissions.py

Para documentación completa ver: EXPANDED_PERMISSIONS.md
*/

export default menuConfig;
