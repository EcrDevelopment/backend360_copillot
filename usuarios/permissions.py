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
    Clase base para verificar permisos específicos de módulo.
    Debe ser heredada y especificar el permission_required.
    """
    permission_required = None
    message = "No tiene los permisos requeridos."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if not self.permission_required:
            return False
        
        return (
            request.user, self.permission_required
            or request.user.groups.filter(name='SystemAdmin').exists()
        )
