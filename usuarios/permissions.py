# usuarios/permissions.py
"""
Custom permission classes for role-based access control.
These classes provide granular permission checking for different user roles.

NOTA DE COMPATIBILIDAD:
Las clases CanAccessAlmacen, CanAccessImportaciones, CanEditDocuments y CanDeleteResource
han sido modificadas para permitir acceso a usuarios autenticados por defecto.
Esto mantiene compatibilidad con el frontend existente.

Para mayor seguridad en producción, considere:
1. Implementar permisos a nivel de objeto en las vistas
2. Asignar roles específicos a usuarios
3. Configurar filtrado de datos por usuario
4. Monitorear logs de auditoría regularmente
"""
from rest_framework.permissions import BasePermission
from rolepermissions.checkers import has_role, has_permission
import logging

# Logger para auditoría de permisos
# Logs: INFO (accesos), WARNING (modificaciones/eliminaciones)
# IMPORTANTE: Los logs contienen IDs de usuario para cumplimiento de privacidad
permissions_logger = logging.getLogger('audit')


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
    
    NOTA: Para mayor seguridad, implemente filtrado de datos a nivel de vista
    o asigne roles específicos a usuarios que necesiten acceso completo.
    """
    message = "No tiene permisos para acceder al módulo de importaciones."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Log de acceso para auditoría (usando ID por privacidad)
        permissions_logger.info(
            f"Acceso al módulo de importaciones - UserID: {request.user.id}, "
            f"Método: {request.method}, Vista: {view.__class__.__name__}"
        )
        
        # Permitir acceso a cualquier usuario autenticado
        # Los permisos específicos se verificarán en operaciones individuales
        return True


class CanAccessAlmacen(BasePermission):
    """
    Permite acceso al módulo de almacén.
    Por defecto, cualquier usuario autenticado tiene acceso de lectura.
    
    NOTA: Para mayor seguridad, implemente filtrado de datos a nivel de vista
    o asigne roles específicos a usuarios que necesiten acceso completo.
    """
    message = "No tiene permisos para acceder al módulo de almacén."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Log de acceso para auditoría (usando ID por privacidad)
        permissions_logger.info(
            f"Acceso al módulo de almacén - UserID: {request.user.id}, "
            f"Método: {request.method}, Vista: {view.__class__.__name__}"
        )
        
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
    
    NOTA: Para mayor seguridad, implemente verificación de propiedad de documentos
    a nivel de vista o requiera roles específicos para edición.
    """
    message = "No tiene permisos para editar documentos."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Log de operaciones de edición para auditoría (usando ID por privacidad)
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            permissions_logger.warning(
                f"Operación de edición de documentos - UserID: {request.user.id}, "
                f"Método: {request.method}, Vista: {view.__class__.__name__}"
            )
        
        # Permitir acceso a usuarios autenticados
        # Los permisos específicos pueden ser verificados a nivel de objeto si es necesario
        return True


class CanDeleteResource(BasePermission):
    """
    Permite eliminar recursos a usuarios autenticados.
    En producción, esto podría ser más restrictivo según las necesidades del negocio.
    
    ADVERTENCIA: Las operaciones de eliminación son críticas.
    Para mayor seguridad, considere:
    1. Implementar soft deletes en lugar de hard deletes
    2. Requerir roles de administrador para eliminación
    3. Implementar confirmación de dos factores para eliminaciones
    """
    message = "No tiene permisos para eliminar recursos."

    def has_permission(self, request, view):
        if request.method != 'DELETE':
            return True
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Log crítico de operaciones de eliminación (usando ID por privacidad)
        permissions_logger.warning(
            f"⚠️ OPERACIÓN DELETE - UserID: {request.user.id}, "
            f"Vista: {view.__class__.__name__}, "
            f"Path: {request.path}"
        )
        
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
