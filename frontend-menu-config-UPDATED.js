/*
Menu actualizado con permisos funcionales del backend (Sistema de Permisos Funcionales)

CAMBIOS PRINCIPALES:
- Se usan los 14 permisos funcionales en lugar de ~2000 permisos de tabla
- Un permiso puede controlar múltiples opciones del menú
- Permisos más claros y fáciles de gestionar
- Todos los items tienen permisos asignados (sin null)

PERMISOS FUNCIONALES DISPONIBLES:
- usuarios.can_manage_users - Gestionar usuarios (crear, editar, eliminar)
- usuarios.can_view_users - Ver usuarios
- usuarios.can_manage_roles - Gestionar roles y permisos
- usuarios.can_view_roles - Ver roles y permisos
- almacen.can_manage_warehouse - Gestionar almacén (guías, productos, kardex, movimientos)
- almacen.can_view_warehouse - Ver información de almacén
- almacen.can_view_warehouse_reports - Ver reportes de almacén
- almacen.can_manage_stock - Gestionar stock y transferencias
- almacen.can_view_stock - Ver stock
- importaciones.can_manage_importaciones - Gestionar importaciones (DUA, declaraciones, proveedores)
- importaciones.can_view_importaciones - Ver información de importaciones
- importaciones.can_view_importaciones_reports - Ver reportes de importaciones
- importaciones.can_manage_documents - Gestionar documentos de importaciones
- importaciones.can_view_documents - Ver documentos de importaciones

DOCUMENTACIÓN:
- Ver MENU_PERMISSIONS_MAPPING.md para el mapeo completo de permisos legacy → funcionales
- Ver FRONTEND_INTEGRATION.md para ejemplos de código de integración
*/


/*
Esta menu que me sugieres si bien es cierto acota mucho mejor los permisos y los hace mas funcionales, sin embargo
por ejemplo en la seccion de proveedores comparte lo mismo que en la seccion importaciones, lo que hace que si a un usuario
de tipo proveedor le doy el permiso de ver importaciones, automaticamente pueda ver las opciones de importaciones cosa que no
deberia ocurrir. Por otro lado, en la seccion de usuarios, si bien es cierto que se puede acotar mas los permisos, en este caso
se esta manejando un permiso general para administrar usuarios, roles y permisos ya que en la mayoria de los casos
el usuario que tiene acceso a esta seccion es un administrador general que puede hacer todo.

por otro lado en la seccion de tablas estan dando permisos para gestionar usuarios me parece cosa que no deberia
suceder tampoco ya que no tiene nada que ver. Esta seccion de tablas es una especie de seccion de mantenimiento del sistema
donde se manejan tablas que son usadas en varios modulos del sistema como tipos de documentos, empresas, productos,
almacenes y tipos de estibaje. Por lo tanto el permiso deberia ser mas general para gestionar estas tablas de mantenimiento
y no permisos especificos de usuarios. o en todo caso permisos especificos para cada tabla pero no relacionados con usuarios.

y ya que es una tabla de este tipo podria ser un permiso general como "miscelanea.can_manage_tables" o algo similar. aunque
preferiria que sea un permiso mas especifico para cada tabla pero no relacionado con usuarios.
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
    permission: 'importaciones.can_view_importaciones', // ✅ Permiso funcional para ver módulo
    children: [
      { 
        key: '3', 
        label: 'Listado Fletes', 
        to: '/importaciones/ver_fletes_internacionales', 
        permission: 'importaciones.can_view_importaciones' // Ver importaciones
      },
      // Comentado - en desarrollo
      //{ 
      //  key: '4-dev', 
      //  label: 'Fletes Extranjeros', 
      //  to: '/importaciones/registrar_flete_internacional', 
      //  permission: 'importaciones.can_manage_importaciones' // Crear/editar fletes
      //},
      { 
        key: '4', 
        label: 'Reporte Estiba', 
        to: '/importaciones/reporte-estiba', 
        permission: 'importaciones.can_view_importaciones_reports' // Ver reportes
      },
      { 
        key: '5', 
        label: 'Documentos Prov.', 
        to: '/importaciones/gestion_documentos', 
        permission: 'importaciones.can_manage_documents' // Gestionar documentos
      },
      { 
        key: '6', 
        label: 'Archivos DUA', 
        to: '/importaciones/listado-archivos-dua', 
        permission: 'importaciones.can_manage_documents' // Gestionar expedientes
      },
      { 
        key: '7', 
        label: 'Ticket Senasa', 
        to: '/consulta-ticket-senasa', 
        permission: 'importaciones.can_view_importaciones' // Consulta general
      },
    ],
  },
  {
    key: 'sub2',
    icon: <AiOutlineTruck />,
    label: 'Proveedores',
    permission: 'importaciones.can_view_documents', // Ver documentos (lectura básica)
    children: [
      { 
        key: '8', 
        label: 'Cargar Documentos DUA', 
        to: '/proveedores/carga_docs_dua', 
        permission: 'importaciones.can_manage_documents' // Subir documentos
      },
      { 
        key: '9', 
        label: 'Gestión de docs.', 
        to: '/proveedores/gestion_de_documentos', 
        permission: 'importaciones.can_manage_documents' // Administrar documentos
      },
    ],
  },

  {
    key: 'sub3',
    icon: <MdOutlineTableView />,
    label: 'Tablas',
    permission: 'usuarios.can_manage_roles', // Gestión de tablas de mantenimiento
    children: [
      { 
        key: '10', 
        label: 'Tabla Tipo Doc.', 
        to: '/tipos_documentos', 
        permission: 'usuarios.can_manage_roles' // Gestionar catálogos del sistema
      },
      { 
        key: '11', 
        label: 'Tabla Empresas', 
        to: '/miscelanea/empresas', 
        permission: 'usuarios.can_view_users' // Ver/gestionar empresas
      },
      { 
        key: '12', 
        label: 'Tabla Productos', 
        to: '/miscelanea/productos', 
        permission: 'almacen.can_manage_warehouse' // CRUD productos
      },
      { 
        key: '13', 
        label: 'Tabla Almacenes', 
        to: '/miscelanea/almacenes', 
        permission: 'almacen.can_manage_warehouse' // CRUD almacenes
      },
      { 
        key: '14', 
        label: 'Tipo Estibaje', 
        to: '/tipo_estiba', 
        permission: 'almacen.can_manage_warehouse' // Gestionar tipos de estibaje
      },
    ],
  },

   {
    key: 'sub4',
    icon: <BiStore />,
    label: 'Almacen',
    permission: 'almacen.can_view_warehouse', // Ver módulo de almacén
    children: [
      { 
        key: '15', 
        label: 'Ingresos/Salidas', 
        to: '/almacen/movimientos', 
        permission: 'almacen.can_manage_warehouse' // Registrar movimientos
      },
      { 
        key: '16', 
        label: 'Lector QR', 
        to: '/almacen/lectorQr', 
        permission: 'almacen.can_view_warehouse' // Consulta rápida
      },
      { 
        key: '17', 
        label: 'Stock', 
        to: '/almacen/stock', 
        permission: 'almacen.can_view_stock' // Ver inventario
      },
      { 
        key: '18', 
        label: 'Transferencias', 
        to: '/almacen/transferencias', 
        permission: 'almacen.can_manage_stock' // Gestionar transferencias
      },
      { 
        key: '19', 
        label: 'Consulta Guía', 
        to: '/consulta-guia', 
        permission: 'almacen.can_view_warehouse' // Consulta general
      },
    ]
  },

  {
    key: 'sub5',
    icon: <MdLock />,
    label: 'Usuarios',
    permission: 'usuarios.can_view_users', // Ver módulo de usuarios
    children: [
      { 
        key: '20', 
        label: 'Usuarios', 
        to: '/usuarios', 
        permission: 'usuarios.can_view_users' // Ver lista de usuarios
      },
      { 
        key: '21', 
        label: 'Roles', 
        to: '/roles', 
        permission: 'usuarios.can_view_roles' // Ver roles del sistema
      },
      { 
        key: '22', 
        label: 'Permisos', 
        to: '/permisos', 
        permission: 'usuarios.can_view_roles' // Ver permisos disponibles
      },
    ],
  },
];

/*
NOTAS DE IMPLEMENTACIÓN:

1. JERARQUÍA DE PERMISOS:
   - Si un usuario tiene 'can_manage_*', automáticamente tiene 'can_view_*'
   - Ejemplo: can_manage_warehouse incluye can_view_warehouse

2. VALIDACIÓN EN FRONTEND:
   - Usar la función hasPermission() del archivo FRONTEND_INTEGRATION.md
   - Filtrar el menú dinámicamente según permisos del usuario
   - Cache los permisos para mejor rendimiento

3. ROLES ESPECIALES:
   - SystemAdmin: Acceso automático a todo (no requiere permisos específicos)
   - Superuser: Acceso automático a todo

4. MIGRACIÓN:
   - Usuarios con permisos legacy deben actualizarse a permisos funcionales
   - Ver MENU_PERMISSIONS_MAPPING.md para el mapeo completo
   - Usar Django admin para asignar permisos a grupos

5. TESTING:
   - Probar cada opción del menú con diferentes roles
   - Verificar que el filtrado funcione correctamente
   - Validar que no aparezcan opciones sin permiso

Para más información:
- MENU_PERMISSIONS_MAPPING.md - Mapeo de permisos legacy → funcionales
- FRONTEND_INTEGRATION.md - Código de integración y ejemplos
- FUNCTIONAL_PERMISSIONS.md - Documentación técnica completa
*/

export default menuConfig;
