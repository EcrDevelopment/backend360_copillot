from rest_framework import permissions
from django.core.exceptions import PermissionDenied


class HasWarehouseAccess(permissions.BasePermission):
    """
    Permiso que verifica si el usuario tiene acceso al almacén especificado.

    Uso en ViewSet:
        permission_classes = [IsAuthenticated, HasWarehouseAccess]

    En la vista debe existir:
        - self.get_warehouse() que devuelva el almacén
        - O request.data['almacen_id']
        - O kwargs['almacen_pk']
    """
    message = "No tiene acceso a este almacén"

    def has_permission(self, request, view):
        # SystemAdmin siempre tiene acceso
        if hasattr(request.user, 'is_system_admin') and request.user.is_system_admin:
            return True

        # Usuario debe estar autenticado
        if not request.user.is_authenticated:
            return False

        # Usuario debe tener perfil
        if not hasattr(request.user, 'userprofile'):
            return False

        profile = request.user.userprofile

        # Si no requiere restricción, dar acceso
        if not profile.require_warehouse_access:
            return True

        # Para listados, permitir (filtraremos después)
        if request.method == 'GET' and not view.kwargs.get('pk'):
            return True

        # Para otros métodos, verificar almacén específico
        return True  # Verificación detallada en has_object_permission

    def has_object_permission(self, request, view, obj):
        # SystemAdmin siempre tiene acceso
        if hasattr(request.user, 'is_system_admin') and request.user.is_system_admin:
            return True

        profile = request.user.userprofile

        # Si no requiere restricción, dar acceso
        if not profile.require_warehouse_access:
            return True

        # Obtener el almacén del objeto
        almacen = None
        if hasattr(obj, 'almacen'):
            almacen = obj.almacen
        elif hasattr(obj, 'almacen_id'):
            almacen = obj.almacen
        elif obj.__class__.__name__ == 'Almacen':
            almacen = obj

        if not almacen:
            # No se pudo determinar el almacén, denegar por seguridad
            return False

        # Verificar acceso
        return profile.tiene_acceso_almacen(almacen)


class HasSedeAccess(permissions.BasePermission):
    """
    Permiso que verifica si el usuario tiene acceso a la sede especificada.
    """
    message = "No tiene acceso a esta sede"

    def has_permission(self, request, view):
        # SystemAdmin siempre tiene acceso
        if hasattr(request.user, 'is_system_admin') and request.user.is_system_admin:
            return True

        if not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'userprofile'):
            return False

        profile = request.user.userprofile

        # Si no requiere restricción, dar acceso
        if not profile.require_sede_access:
            return True

        # Para listados, permitir (filtraremos después)
        if request.method == 'GET' and not view.kwargs.get('pk'):
            return True

        return True  # Verificación detallada en has_object_permission

    def has_object_permission(self, request, view, obj):
        # SystemAdmin siempre tiene acceso
        if hasattr(request.user, 'is_system_admin') and request.user.is_system_admin:
            return True

        profile = request.user.userprofile

        # Si no requiere restricción, dar acceso
        if not profile.require_sede_access:
            return True

        # Obtener la sede del objeto
        sede = None
        if hasattr(obj, 'sede'):
            sede = obj.sede
        elif hasattr(obj, 'direccion'):
            sede = obj.direccion
        elif obj.__class__.__name__ == 'Direccion':
            sede = obj

        if not sede:
            return False

        # Verificar acceso
        return profile.tiene_acceso_sede(sede)