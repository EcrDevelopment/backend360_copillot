# usuarios/permissions.py
"""
Custom permission classes for role-based access control.
These classes provide granular permission checking for different user roles.
"""
from rest_framework.permissions import BasePermission
#from rolepermissions.checkers import has_role, has_permission


class IsSystemAdmin(BasePermission):
    """
    Permite acceso solo a usuarios con rol SystemAdmin.
    """
    message = "Debe tener permisos de administrador del sistema."

    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.groups.filter(name='SystemAdmin').exists()
        )


class IsAccountsAdmin(BasePermission):
    """
    Permite acceso solo a usuarios con rol AccountsAdmin.
    """
    message = "Debe tener permisos de administrador de usuarios."

    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.groups.filter(name= 'accounts_admin').exists()
        )


class IsImportacionesAdmin(BasePermission):
    """
    Permite acceso solo a usuarios con rol ImportacionesAdmin.
    """
    message = "Debe tener permisos de administrador de importaciones."

    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            #and has_role(request.user, 'importaciones_admin')
            and request.user.groups.filter(name='importaciones_admin').exists()
        )


class IsAlmacenAdmin(BasePermission):
    """
    Permite acceso solo a usuarios con rol AlmacenAdmin.
    """
    message = "Debe tener permisos de administrador de almacén."

    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            #and has_role(request.user, 'almacen_admin')
            and request.user.groups.filter(name='almacen_admin').exists()
        )


class CanManageUsers(BasePermission):
    """
    Permite acceso a usuarios que pueden gestionar otros usuarios.
    """
    message = "No tiene permisos para gestionar usuarios."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # SystemAdmin y AccountsAdmin pueden gestionar usuarios
        return (
            request.user.groups.filter(name='SystemAdmin').exists()
            #or has_role(request.user, 'accounts_admin')
            and request.user.groups.filter(name='accounts_admin').exists()
        )


class CanAccessImportaciones(BasePermission):
    """
    Permite acceso al módulo de importaciones.
    """
    message = "No tiene permisos para acceder al módulo de importaciones."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return (
            request.user.has_perm('usuarios.importaciones_ver_modulo')
            or request.user.groups.filter(name='SystemAdmin').exists()
        )


class CanAccessAlmacen(BasePermission):
    """
    Permite acceso al módulo de almacén.
    """
    message = "No tiene permisos para acceder al módulo de almacén."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return (
            #has_permission(request.user, 'almacen.ver_modulo')
            request.user.groups.filter(name='ialmacen.ver_modulo').exists()
            or request.user.groups.filter(name='SystemAdmin').exists()
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Permite acceso al propietario del objeto o a administradores.
    Debe ser usado con has_object_permission.
    """
    message = "Solo puede acceder a sus propios datos."

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Administradores tienen acceso completo
        if request.user.groups.filter(name='SystemAdmin').exists() or  request.user.groups.filter(name='accounts_admin').exists():
            return True
        
        # Verificar si el objeto tiene un campo 'user' o 'usuario'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class ReadOnly(BasePermission):
    """
    Permite solo operaciones de lectura (GET, HEAD, OPTIONS).
    """
    message = "Solo tiene permisos de lectura."

    def has_permission(self, request, view):
        return request.method in ['GET', 'HEAD', 'OPTIONS']


class CanEditDocuments(BasePermission):
    """
    Permite edición de documentos según los permisos del usuario.
    """
    message = "No tiene permisos para editar documentos."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Solo lectura para métodos GET
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Para crear/editar/eliminar, verificar permisos específicos
        return (
            #has_permission(request.user, 'importaciones.administrar_documentos_dua')
            request.user.has_perm('importaciones.administrar_documentos_dua')
            #or has_permission(request.user, 'proveedor.administrar_documentos')
            or request.user.has_perm('proveedor.administrar_documentos')
            or request.user.groups.filter(name='SystemAdmin').exists()
        )


class CanDeleteResource(BasePermission):
    """
    Permite eliminar recursos solo a administradores.
    """
    message = "No tiene permisos para eliminar recursos."

    def has_permission(self, request, view):
        if request.method != 'DELETE':
            return True
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Solo administradores pueden eliminar
        return (
            request.user.groups.filter(name='SystemAdmin').exists()
            or request.user.groups.filter(name='accounts_admin').exists()
            or request.user.groups.filter(name= 'importaciones_admin').exists()
            or request.user.groups.filter(name='almacen_admin').exists()
        )


class HasModulePermission(BasePermission):
    """
    Custom permission class to check functional/modular permissions.
    Can be used directly by setting permission_required on the class,
    or by subclassing and defining permission_required.
    
    Usage examples:
    1. As a base class:
        class CanManageWarehouse(HasModulePermission):
            permission_required = 'almacen.can_manage_warehouse'
    
    2. Directly in ViewSet:
        permission_classes = [HasModulePermission]
        permission_required = 'almacen.can_manage_warehouse'
    
    3. With multiple permissions (OR logic - user needs ANY one):
        permission_required = ['almacen.can_manage_warehouse', 'almacen.can_view_warehouse']
        
        IMPORTANT: Multiple permissions use OR logic (any match grants access).
        If you need ALL permissions, use multiple permission classes instead:
        permission_classes = [CanManageWarehouse, CanViewWarehouse]
    
    Note: The view's permission_required attribute takes precedence over the 
    permission class's permission_required. This allows flexible permission 
    assignment but should be used consistently within your codebase.
    """
    permission_required = None
    message = "No tiene los permisos requeridos para esta acción."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # SystemAdmin always has access
        if request.user.groups.filter(name='SystemAdmin').exists():
            return True
        
        # Get permission_required from view if not set on permission class
        # Note: View's permission_required takes precedence for flexibility
        permission = self.permission_required or getattr(view, 'permission_required', None)
        
        if not permission:
            return False
        
        # Support multiple permissions (OR logic - user needs any one of them)
        # For AND logic, use multiple permission classes instead
        if isinstance(permission, (list, tuple)):
            return any(request.user.has_perm(perm) for perm in permission)
        
        # Single permission check
        return request.user.has_perm(permission)


# ========================================
# Functional Permission Classes for Modules
# ========================================

# --- Usuarios Module ---
class CanManageUsersModule(HasModulePermission):
    """Permite gestionar usuarios (crear, editar, eliminar)"""
    permission_required = 'usuarios.can_manage_users'
    message = "No tiene permisos para gestionar usuarios."


class CanViewUsersModule(HasModulePermission):
    """Permite ver usuarios"""
    permission_required = 'usuarios.can_view_users'
    message = "No tiene permisos para ver usuarios."


class CanManageRoles(HasModulePermission):
    """Permite gestionar roles y permisos"""
    permission_required = 'usuarios.can_manage_roles'
    message = "No tiene permisos para gestionar roles y permisos."


class CanViewRoles(HasModulePermission):
    """Permite ver roles y permisos"""
    permission_required = 'usuarios.can_view_roles'
    message = "No tiene permisos para ver roles y permisos."


# --- Almacen Module ---
class CanManageWarehouse(HasModulePermission):
    """Permite gestionar almacén (guías, detalles, kardex, movimientos)"""
    permission_required = 'almacen.can_manage_warehouse'
    message = "No tiene permisos para gestionar el almacén."


class CanViewWarehouse(HasModulePermission):
    """Permite ver información de almacén"""
    permission_required = 'almacen.can_view_warehouse'
    message = "No tiene permisos para ver información del almacén."


class CanViewWarehouseReports(HasModulePermission):
    """Permite ver reportes de almacén"""
    permission_required = 'almacen.can_view_warehouse_reports'
    message = "No tiene permisos para ver reportes del almacén."


class CanManageStock(HasModulePermission):
    """Permite gestionar stock y transferencias"""
    permission_required = 'almacen.can_manage_stock'
    message = "No tiene permisos para gestionar stock."


class CanViewStock(HasModulePermission):
    """Permite ver stock"""
    permission_required = 'almacen.can_view_stock'
    message = "No tiene permisos para ver stock."


# --- Importaciones Module ---
class CanManageImportaciones(HasModulePermission):
    """Permite gestionar importaciones (DUA, declaraciones, proveedores)"""
    permission_required = 'importaciones.can_manage_importaciones'
    message = "No tiene permisos para gestionar importaciones."


class CanViewImportaciones(HasModulePermission):
    """Permite ver información de importaciones"""
    permission_required = 'importaciones.can_view_importaciones'
    message = "No tiene permisos para ver información de importaciones."


class CanViewImportacionesReports(HasModulePermission):
    """Permite ver reportes de importaciones"""
    permission_required = 'importaciones.can_view_importaciones_reports'
    message = "No tiene permisos para ver reportes de importaciones."


class CanManageDocuments(HasModulePermission):
    """Permite gestionar documentos de importaciones"""
    permission_required = 'importaciones.can_manage_documents'
    message = "No tiene permisos para gestionar documentos."


class CanViewDocuments(HasModulePermission):
    """Permite ver documentos de importaciones"""
    permission_required = 'importaciones.can_view_documents'
    message = "No tiene permisos para ver documentos."
