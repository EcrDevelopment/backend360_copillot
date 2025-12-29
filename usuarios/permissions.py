# usuarios/permissions.py
"""
Custom permission classes for role-based access control.
These classes provide granular permission checking for different user roles.
"""
from rest_framework.permissions import BasePermission
from rolepermissions.checkers import has_role, has_permission


class IsSystemAdmin(BasePermission):
    """
    Permite acceso solo a usuarios con rol SystemAdmin.
    """
    message = "Debe tener permisos de administrador del sistema."

    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and has_role(request.user, 'system_admin')
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
            and has_role(request.user, 'accounts_admin')
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
            and has_role(request.user, 'importaciones_admin')
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
            and has_role(request.user, 'almacen_admin')
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
            has_role(request.user, 'system_admin') 
            or has_role(request.user, 'accounts_admin')
        )


class CanAccessImportaciones(BasePermission):
    """
    Permite acceso al módulo de importaciones.
    Por defecto, cualquier usuario autenticado tiene acceso de lectura.
    """
    message = "No tiene permisos para acceder al módulo de importaciones."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Permitir acceso a cualquier usuario autenticado
        # Los permisos específicos se verificarán en operaciones individuales
        return True


class CanAccessAlmacen(BasePermission):
    """
    Permite acceso al módulo de almacén.
    Por defecto, cualquier usuario autenticado tiene acceso de lectura.
    """
    message = "No tiene permisos para acceder al módulo de almacén."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Permitir acceso a cualquier usuario autenticado
        # Los permisos específicos se verificarán en operaciones individuales
        return True


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
        if has_role(request.user, 'system_admin') or has_role(request.user, 'accounts_admin'):
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
    Por defecto, permite a usuarios autenticados editar documentos.
    """
    message = "No tiene permisos para editar documentos."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Permitir acceso a usuarios autenticados
        # Los permisos específicos pueden ser verificados a nivel de objeto si es necesario
        return True


class CanDeleteResource(BasePermission):
    """
    Permite eliminar recursos a usuarios autenticados.
    En producción, esto podría ser más restrictivo según las necesidades del negocio.
    """
    message = "No tiene permisos para eliminar recursos."

    def has_permission(self, request, view):
        if request.method != 'DELETE':
            return True
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Permitir a usuarios autenticados eliminar recursos
        # Esto puede ser más restrictivo en el futuro si se requiere
        return True


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
            has_permission(request.user, self.permission_required)
            or has_role(request.user, 'system_admin')
        )
