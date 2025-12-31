const menuConfig = [
  {
    key: '1',
    icon: <HomeOutlined />,
    label: 'Inicio',
    to: '/',
    permission: null,
  },
  {
    key: 'sub1',
    icon: <GoContainer />,
    label: 'Importaciones',
    permission: 'importaciones',
    children: [
      { key: '3', label: 'Listado Fletes', to: '/importaciones/ver_fletes_internacionales', permission: 'importaciones.ver_fletes_internacionales' },
      //{ key: '4', label: 'Fletes Extranjeros', to: '/importaciones/registrar_flete_internacional', permission: 'importaciones.registrar_flete_internacional' },
      { key: '4', label: 'Reporte Estiba', to: '/importaciones/reporte-estiba', permission: 'importaciones.ver_reporte_estibas' },
      { key: '5', label: 'Documentos Prov.', to: '/importaciones/gestion_documentos', permission: 'importaciones.administrar_documentos_dua' },
      { key: '6', label: 'Archivos DUA', to: '/importaciones/listado-archivos-dua', permission: 'importaciones.administrar_expedientes_dua' },
      { key: '7', label: 'Ticket Senasa', to: '/consulta-ticket-senasa', permission: null },
    ],
  },
  {
    key: 'sub2',
    icon: <AiOutlineTruck />,
    label: 'Proveedores',
    permission: null,
    children: [
      { key: '8', label: 'Cargar Documentos DUA', to: '/proveedores/carga_docs_dua', permission: 'proveedor.cargar_documentos' },
      { key: '9', label: 'Gestión de docs.', to: '/proveedores/gestion_de_documentos', permission: 'proveedor.administrar_documentos' },
    ],
  },

  {
    key: 'sub3',
    icon: <MdOutlineTableView />,
    label: 'Tablas',
    permission: 'mantenimiento.tabla_tipo_documentos',
    children: [
      { key: '10', label: 'Tabla Tipo Doc.', to: '/tipos_documentos', permission: 'mantenimiento.tabla_tipo_documentos' },
      { key: '11', label: 'Tabla Empresas', to: '/miscelanea/empresas', permission: null },
      { key: '12', label: 'Tabla Productos', to: '/miscelanea/productos', permission: null },
      { key: '13', label: 'Tabla Almacenes', to: '/miscelanea/almacenes', permission: null },
      { key: '14', label: 'Tipo Estibaje', to: '/tipo_estiba', permission: null },
    ],
  },

   {
    key: 'sub4',
    icon: <BiStore />,
    label: 'Almacen',
    permission: null,
    children: [
      { key: '15', label: 'Ingresos/Salidas', to: '/almacen/movimientos', permission: null },
      { key: '16', label: 'Lector QR', to: '/almacen/lectorQr', permission: null },
      { key: '17', label: 'Stock', to: '/almacen/stock', permission: null },
      { key: '18', label: 'Transferencias', to: '/almacen/transferencias', permission: null },
      { key: '19', label: 'Consulta Guía', to: '/consulta-guia', permission: null },
    ]
  },

  {
    key: 'sub5',
    icon: <MdLock />,
    label: 'Usuarios',
    permission: null,
    children: [
      { key: '20', label: 'Usuarios', to: '/usuarios', permission: 'user.listar_usuarios' },
      { key: '21', label: 'Roles', to: '/roles', permission: 'user.listar_usuarios' },
      { key: '22', label: 'Permisos', to: '/permisos', permission: 'user.listar_usuarios' },



    ],
  },

];