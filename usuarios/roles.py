# usuarios/roles.py
from rolepermissions.roles import AbstractUserRole

class SystemAdmin(AbstractUserRole):
    """
    Administrador del sistema con acceso completo a configuración y mantenimiento.
    """
    available_permissions = {
        'mantenimiento.tabla_tipo_documentos': True,
        'sistema.gestionar_configuracion': True,
        'sistema.ver_logs_auditoria': True,
        'sistema.gestionar_respaldos': True,
    }

class ImportacionesAdmin(AbstractUserRole):
    """
    Administrador de importaciones con permisos completos sobre el módulo.
    """
    available_permissions = {
        'importaciones.ver_modulo': True,
        'importaciones.ver_fletes_internacionales': True,
        'importaciones.registrar_flete_internacional': True,
        'importaciones.editar_flete_internacional': True,
        'importaciones.eliminar_flete_internacional': True,
        'importaciones.ver_reporte_flete': True,
        'importaciones.ver_reporte_estibas': True,
        'importaciones.administrar_documentos_dua': True,
        'importaciones.administrar_expedientes_dua': True,
        'importaciones.crear_expedientes_dua': True,
        'importaciones.editar_expedientes_dua': True,
        'importaciones.eliminar_expedientes_dua': True,
        'importaciones.descargar_expedientes_dua': True,
        'importaciones.agregar_mes_expedientes_dua': True,
        'importaciones.agregar_empresa_expedientes_dua': True,
        'importaciones.ver_ordenes_compra': True,
        'importaciones.crear_ordenes_compra': True,
        'importaciones.editar_ordenes_compra': True,
        'importaciones.eliminar_ordenes_compra': True,
    }


class ImportacionesAsistente(AbstractUserRole):
    """
    Asistente de importaciones con permisos limitados de lectura y edición.
    """
    available_permissions = {
        'importaciones.ver_modulo': True,
        'importaciones.ver_fletes_internacionales': True,
        'importaciones.administrar_documentos_dua': True,
        'importaciones.administrar_expedientes_dua': True,
        'importaciones.editar_expedientes_dua': True,
        'importaciones.descargar_expedientes_dua': True,
        'importaciones.agregar_mes_expedientes_dua': True,
        'importaciones.agregar_empresa_expedientes_dua': True,
        'importaciones.ver_ordenes_compra': True,
    }

class AccountsAdmin(AbstractUserRole):
    """
    Administrador de usuarios con permisos para gestionar cuentas y perfiles.
    """
    available_permissions = {
        'user.listar_usuarios': True,
        'user.registrar_usuario': True,
        'user.editar_usuario': True,
        'user.eliminar_usuario': True,
        'user.asignar_roles': True,
        'user.gestionar_permisos': True,
        'user.ver_perfil': True,
    }

class AccountsUser(AbstractUserRole):
    """
    Usuario estándar con permisos básicos sobre su propio perfil.
    """
    available_permissions = {
        'user.editar_perfil': True,
        'user.ver_perfil': True,
        'user.cambiar_password': True,
    }

class Proveedor(AbstractUserRole):
    """
    Proveedor externo con permisos limitados para gestionar documentos.
    """
    available_permissions = {
        'proveedor.cargar_documentos': True,
        'proveedor.administrar_documentos': True,
        'proveedor.ver_documentos_propios': True,
        'proveedor.descargar_documentos_propios': True,
    }

class AlmacenAdmin(AbstractUserRole):
    """
    Administrador de almacén con permisos completos sobre inventario.
    """
    available_permissions = {
        'almacen.ver_modulo': True,
        'almacen.gestionar_productos': True,
        'almacen.gestionar_stock': True,
        'almacen.gestionar_movimientos': True,
        'almacen.ver_kardex': True,
        'almacen.generar_reportes': True,
        'almacen.realizar_ajustes': True,
    }

class AlmacenOperador(AbstractUserRole):
    """
    Operador de almacén con permisos limitados de operación.
    """
    available_permissions = {
        'almacen.ver_modulo': True,
        'almacen.ver_productos': True,
        'almacen.ver_stock': True,
        'almacen.registrar_movimientos': True,
        'almacen.ver_kardex': True,
    }