"""
Custom permission classes for role-based access control.
These classes provide granular permission checking for different user roles.
"""
from rest_framework.permissions import BasePermission

# =============================================================================
# 1. PERMISOS LEGACY (Basados en Grupos/Roles Fijos)
# Nota: Se mantiene compatibilidad con grupos antiguos y se asegura acceso a Superuser.
# =============================================================================

class IsSystemAdmin(BasePermission):
    message = "Debe tener permisos de administrador del sistema."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser or
                request.user.groups.filter(name='SystemAdmin').exists()
            )
        )

class IsAccountsAdmin(BasePermission):
    message = "Debe tener permisos de administrador de usuarios."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser or
                request.user.groups.filter(name='SystemAdmin').exists() or
                request.user.groups.filter(name='accounts_admin').exists() or
                request.user.groups.filter(name='AccountsAdmin').exists()
            )
        )

class IsImportacionesAdmin(BasePermission):
    message = "Debe tener permisos de administrador de importaciones."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser or
                request.user.groups.filter(name='SystemAdmin').exists() or
                request.user.groups.filter(name='importaciones_admin').exists()
            )
        )

class IsAlmacenAdmin(BasePermission):
    message = "Debe tener permisos de administrador de almacén."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser or
                request.user.groups.filter(name='SystemAdmin').exists() or
                request.user.groups.filter(name='almacen_admin').exists()
            )
        )

class CanManageUsers(BasePermission):
    message = "No tiene permisos para gestionar usuarios."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return (
            request.user.is_superuser or
            request.user.groups.filter(name='SystemAdmin').exists() or
            request.user.groups.filter(name='accounts_admin').exists()
        )

class CanAccessImportaciones(BasePermission):
    message = "No tiene permisos para acceder al módulo de importaciones."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return (
            request.user.is_superuser or
            request.user.groups.filter(name='SystemAdmin').exists() or
            request.user.has_perm('usuarios.importaciones_ver_modulo')
        )

class CanAccessAlmacen(BasePermission):
    message = "No tiene permisos para acceder al módulo de almacén."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return (
            request.user.is_superuser or
            request.user.groups.filter(name='SystemAdmin').exists() or
            # CORREGIDO: Decía 'ialmacen' (typo) y verificaba nombre de grupo en vez de permiso
            # Si usas permisos modernos, debería ser has_perm. Si es legacy grupo, está bien filter.
            request.user.groups.filter(name='almacen_admin').exists()
        )

class IsOwnerOrAdmin(BasePermission):
    message = "Solo puede acceder a sus propios datos."

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if (request.user.is_superuser or
            request.user.groups.filter(name='SystemAdmin').exists() or
            request.user.groups.filter(name='accounts_admin').exists()):
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        return False

class ReadOnly(BasePermission):
    message = "Solo tiene permisos de lectura."
    def has_permission(self, request, view):
        return request.method in ['GET', 'HEAD', 'OPTIONS']

class CanEditDocuments(BasePermission):
    message = "No tiene permisos para editar documentos."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        return (
            request.user.is_superuser or
            request.user.groups.filter(name='SystemAdmin').exists() or
            request.user.has_perm('importaciones.administrar_documentos_dua') or
            request.user.has_perm('proveedor.administrar_documentos')
        )

class CanDeleteResource(BasePermission):
    message = "No tiene permisos para eliminar recursos."

    def has_permission(self, request, view):
        if request.method != 'DELETE':
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        return (
            request.user.is_superuser or
            request.user.groups.filter(name='SystemAdmin').exists() or
            request.user.groups.filter(name='accounts_admin').exists() or
            request.user.groups.filter(name='importaciones_admin').exists() or
            request.user.groups.filter(name='almacen_admin').exists()
        )


# =============================================================================
# 2. PERMISOS MODULARES MODERNOS (Sistema Dinámico)
# =============================================================================

class HasModulePermission(BasePermission):
    """
    Clase base para el sistema de permisos dinámicos.
    Mejorada para manejar desajustes entre Nombre de Categoría y App Label de Django.
    """
    permission_required = None
    message = "No tiene los permisos requeridos para esta acción."

    def has_permission(self, request, view):

        if not (request.user and request.user.is_authenticated):
            return False

        # 1. ACCESO TOTAL: Superusuario o SystemAdmin
        if request.user.is_superuser or request.user.groups.filter(name='SystemAdmin').exists():
            return True

        # 2. Obtener el permiso requerido
        permission = self.permission_required or getattr(view, 'permission_required', None)

        if not permission:
            return False

        # Normalizamos a lista para manejar múltiples permisos
        perms_to_check = permission if isinstance(permission, (list, tuple)) else [permission]

        for perm_str in perms_to_check:
            # A. Intento Directo (Ej: 'almacen.can_view_warehouse')
            if request.user.has_perm(perm_str):
                return True

            # B. Intento con App 'usuarios' (Fix de Migración)
            # Si el permiso se llama 'almacen.can_view', probamos 'usuarios.can_view'
            if '.' in perm_str:
                codename = perm_str.split('.')[-1]
                if request.user.has_perm(f'usuarios.{codename}'):
                    return True

                # C. Intento con App 'auth' (Por si acaso)
                if request.user.has_perm(f'auth.{codename}'):
                    return True

        return False


# ========================================
# Definición de Clases Funcionales
# NOTA: Los strings deben coincidir con 'app_label.codename' en la BD
# ========================================

# --- Usuarios & Sistema ---
class CanManageUsersModule(HasModulePermission):
    permission_required = 'usuarios.can_manage_users'
    message = "No tiene permisos para gestionar usuarios."

class CanViewUsersModule(HasModulePermission):
    permission_required = 'usuarios.can_view_users'
    message = "No tiene permisos para ver usuarios."

class CanManageRoles(HasModulePermission):
    permission_required = 'usuarios.can_manage_roles'
    message = "No tiene permisos para gestionar roles."

class CanViewRoles(HasModulePermission):
    permission_required = 'usuarios.can_view_roles'
    message = "No tiene permisos para ver roles."

class CanManageSystem(HasModulePermission):
    permission_required = 'usuarios.can_manage_system' # O 'sistema.can_manage_system' según tu BD
    message = "No tiene permisos de configuración del sistema."

# --- Almacén ---
class CanManageWarehouse(HasModulePermission):
    permission_required = 'almacen.can_manage_warehouse'
    message = "No tiene permisos para gestionar el almacén."

class CanViewWarehouse(HasModulePermission):
    permission_required = 'almacen.can_view_warehouse'
    message = "No tiene permisos para ver información del almacén."

class CanViewWarehouseReports(HasModulePermission):
    permission_required = 'almacen.can_view_warehouse_reports'
    message = "No tiene permisos para ver reportes del almacén."

class CanManageStock(HasModulePermission):
    permission_required = 'almacen.can_manage_stock'
    message = "No tiene permisos para gestionar stock."

class CanViewStock(HasModulePermission):
    permission_required = 'almacen.can_view_stock'
    message = "No tiene permisos para ver stock."

# --- Importaciones ---
class CanManageImportaciones(HasModulePermission):
    permission_required = 'importaciones.can_manage_importaciones'
    message = "No tiene permisos para gestionar importaciones."

class CanViewImportaciones(HasModulePermission):
    permission_required = 'importaciones.can_view_importaciones'
    message = "No tiene permisos para ver información de importaciones."

class CanViewImportacionesReports(HasModulePermission):
    permission_required = 'importaciones.can_view_importaciones_reports'
    message = "No tiene permisos para ver reportes de importaciones."

class CanManageDocuments(HasModulePermission):
    permission_required = 'importaciones.can_manage_documents'
    message = "No tiene permisos para gestionar documentos."

class CanViewDocuments(HasModulePermission):
    permission_required = 'importaciones.can_view_documents'
    message = "No tiene permisos para ver documentos."