from collections import defaultdict
from django.contrib.contenttypes.models import ContentType
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PasswordResetSerializer, PasswordResetConfirmSerializer,CustomTokenObtainPairSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .models import PasswordResetToken,Empresa,Direccion
from localizacion.models import Departamento, Provincia, Distrito
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from django.http import JsonResponse
from django.conf import settings
from rest_framework.utils import json
from django.middleware.csrf import get_token
from rest_framework import viewsets, permissions
from django.contrib.auth.models import User, Group, Permission
from .serializers import UserSerializer, RoleSerializer, PermissionSerializer, EmpresaSerializer,DireccionSerializer
from localizacion.serializers import  DepartamentoSerializer,ProvinciaSerializer,DistritoSerializer
from rest_framework.permissions import BasePermission
from .permissions import (
    IsAccountsAdmin, CanManageUsers,
    CanManageUsersModule, CanViewUsersModule,
    CanManageRoles, CanViewRoles
)

def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrf_Token': csrf_token})

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Correo enviado con éxito"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if serializer.is_valid():
            # Obtener los datos validados
            user_id = serializer.validated_data['user_id']
            new_password = serializer.validated_data['new_password']
            token = serializer.validated_data['token']

            # Cambiar la contraseña
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()

            #Cambia estado del password
            PasswordResetToken.objects.filter(user_id=user_id).update(active=False)


            return Response({"message": "Contraseña restablecida con éxito."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response_data = serializer.validated_data
        secure = settings.DEBUG is False  # Secure solo cuando está en producción

        # Crear la respuesta
        response = Response(response_data)

        return response

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Obtener el refresh_token de las cookies
        refresh_token = request.COOKIES.get('refresh_token')

        # Si no está en las cookies, intentar obtenerlo de los parámetros de la solicitud
        if not refresh_token:
            print('no se encontro token en las cookies')
            refresh_token = request.data.get('refresh')

        # Validar que se haya encontrado el token
        if not refresh_token:
            print('no se encontro token en la request')
            return JsonResponse({'error': 'Refresh token not found'}, status=400)

        data = request.data.copy()

        data['refresh'] = refresh_token

        # Reemplazar los datos de la solicitud original con la copia mutable
        request._body = json.dumps(data)
        # Llamar al metodo original de TokenRefreshView
        response = super().post(request, *args, **kwargs)
        
        # If successful, add minimal user information to match login response format
        # Roles and permissions are fetched separately via API to avoid large token size
        if response.status_code == 200:
            try:
                from rest_framework_simplejwt.tokens import RefreshToken
                
                # Decode the refresh token to get the user
                refresh = RefreshToken(refresh_token)
                user_id = refresh.get('user_id')
                user = User.objects.get(id=user_id)
                
                # Add minimal user info to response
                # Frontend should fetch full roles/permissions via separate API calls
                response.data['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nombre': user.first_name,
                    'apellido': user.last_name,
                }
                
                profile = getattr(user, 'userprofile', None)
                if profile:
                    response.data['user']['telefono'] = profile.telefono if profile.telefono else None
                    response.data['user']['empresa_id'] = profile.empresa.id if profile.empresa else None
                
                # Don't include full roles and permissions lists to keep response small
                # Frontend fetches these separately via /api/accounts/usuarios/{id}/
                
            except Exception as e:
                print(f"Error adding user info to refresh response: {e}")
                # If there's an error, just return the access token without extra info
                pass
        
        return response

# Permission ViewSet - only admin roles can access
class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    
    def get_permissions(self):
        """
        GET: requiere can_view_roles
        POST/PUT/PATCH/DELETE: requiere can_manage_roles
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated(), CanViewRoles()]
        return [permissions.IsAuthenticated(), CanManageRoles()]
    
    def get_queryset(self):
        """
        Filter permissions to show only functional/modular permissions.
        Excludes default Django table-based permissions (add_, change_, delete_, view_).
        Only returns custom permissions defined in our Permission Meta models.
        
        Functional permission models are configured in settings.FUNCTIONAL_PERMISSION_MODELS
        """
        from django.conf import settings
        from django.apps import apps
        
        # Get configured functional permission models from settings
        functional_model_names = getattr(settings, 'FUNCTIONAL_PERMISSION_MODELS', [])
        
        # Extract model names (lowercase) from full app.Model paths
        model_names = []
        for full_name in functional_model_names:
            try:
                app_label, model_name = full_name.split('.')
                # Get the actual model to ensure it exists
                model = apps.get_model(app_label, model_name)
                model_names.append(model._meta.model_name.lower())
            except (ValueError, LookupError):
                # Skip invalid or non-existent models
                continue
        
        # Filter permissions to only include those from our functional permission models
        queryset = Permission.objects.filter(
            content_type__model__in=model_names
        ).select_related('content_type')
        
        return queryset
    
    @property
    def paginator(self):
        """
        Conditionally disable pagination based on query parameters.
        Use ?pagination=off or ?all=true to get all results without pagination.
        """
        if self.request.query_params.get('pagination') == 'off' or \
           self.request.query_params.get('all') == 'true':
            return None
        return super().paginator

# Role ViewSet - only admin roles can manage
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = RoleSerializer
    
    def get_permissions(self):
        """
        GET: requiere can_view_roles
        POST/PUT/PATCH/DELETE: requiere can_manage_roles
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated(), CanViewRoles()]
        return [permissions.IsAuthenticated(), CanManageRoles()]
    
    def get_queryset(self):
        """Filter roles based on user permissions"""
        return Group.objects.all().prefetch_related('permissions')
    
    @property
    def paginator(self):
        """
        Conditionally disable pagination based on query parameters.
        Use ?pagination=off or ?all=true to get all results without pagination.
        """
        if self.request.query_params.get('pagination') == 'off' or \
           self.request.query_params.get('all') == 'true':
            return None
        return super().paginator

# User ViewSet - only admin roles can manage
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("userprofile").all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        GET: requiere can_view_users
        POST/PUT/PATCH/DELETE: requiere can_manage_users
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated(), CanViewUsersModule()]
        return [permissions.IsAuthenticated(), CanManageUsersModule()]
    
    def get_queryset(self):
        """Filter users based on permissions"""
        user = self.request.user
        
        # System admins see all users (using native Django Groups)
        if user.groups.filter(name='SystemAdmin').exists():
            return User.objects.all().select_related("userprofile").prefetch_related('groups', 'user_permissions')
        
        # Accounts admins see all users (using native Django Groups)
        if user.groups.filter(name='AccountsAdmin').exists():
            return User.objects.all().select_related("userprofile").prefetch_related('groups', 'user_permissions')
        
        # Regular users only see themselves
        return User.objects.filter(id=user.id).select_related("userprofile").prefetch_related('groups', 'user_permissions')
    
    @property
    def paginator(self):
        """
        Conditionally disable pagination based on query parameters.
        Use ?pagination=off or ?all=true to get all results without pagination.
        """
        if self.request.query_params.get('pagination') == 'off' or \
           self.request.query_params.get('all') == 'true':
            return None
        return super().paginator

@api_view(['GET'])
def fetch_content_types(request):
    grouped = defaultdict(list)

    try:
        content_types = ContentType.objects.all().order_by('app_label', 'model')

        for ct in content_types:
            grouped[ct.app_label].append({
                'id': ct.id,
                'model': ct.model,
            })

        response = [
            {'app_label': app_label, 'models': models}
            for app_label, models in grouped.items()
        ]

        return Response(response)

    except Exception as e:
        return Response({'error': str(e)}, status=500)


# Vistas para Departamento, Provincia y Distrito
class DepartamentoListView(generics.ListAPIView):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer

class ProvinciaListView(generics.ListAPIView):
    queryset = Provincia.objects.all()
    serializer_class = ProvinciaSerializer

class DistritoListView(generics.ListAPIView):
    queryset = Distrito.objects.all()
    serializer_class = DistritoSerializer

# Vistas para Empresa y Direccion
class EmpresaListView(generics.ListCreateAPIView):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer

class EmpresaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer


class DireccionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Direccion.objects.all()
    serializer_class = DireccionSerializer

class DireccionListCreateView(generics.ListCreateAPIView):
    queryset = Direccion.objects.all()
    serializer_class = DireccionSerializer


class DireccionesPorEmpresaView(APIView):
    def get(self, request, empresa_id):
        direcciones = Direccion.objects.filter(empresa_id=empresa_id)
        serializer = DireccionSerializer(direcciones, many=True)
        return Response(serializer.data)


# ========================================
# DYNAMIC PERMISSION SYSTEM VIEWSETS
# ========================================

from .models import CustomPermissionCategory, CustomPermission, PermissionChangeAudit
from .serializers import (
    CustomPermissionCategorySerializer,
    CustomPermissionSerializer,
    PermissionChangeAuditSerializer,
    PermissionAssignmentSerializer
)
from rest_framework.decorators import action
from datetime import timedelta
from django.utils import timezone


class CustomPermissionCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar categorías de permisos dinámicos.
    Solo SystemAdmin puede crear/editar/eliminar categorías.
    """
    queryset = CustomPermissionCategory.objects.filter(state=True)
    serializer_class = CustomPermissionCategorySerializer
    
    def get_permissions(self):
        """
        GET: requiere can_view_roles
        POST/PUT/PATCH/DELETE: requiere SystemAdmin
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated(), CanViewRoles()]
        return [permissions.IsAuthenticated(), IsAccountsAdmin()]
    
    def get_queryset(self):
        """Retorna solo categorías activas ordenadas"""
        return CustomPermissionCategory.objects.filter(state=True).order_by('order', 'display_name')
    
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """Obtiene todos los permisos de una categoría"""
        category = self.get_object()
        permissions_qs = category.permissions.filter(state=True)
        serializer = CustomPermissionSerializer(permissions_qs, many=True)
        return Response(serializer.data)


class CustomPermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar permisos dinámicos.
    Solo SystemAdmin puede crear/editar/eliminar permisos.
    """
    queryset = CustomPermission.objects.filter(state=True)
    serializer_class = CustomPermissionSerializer
    
    def get_permissions(self):
        """
        GET: requiere can_view_roles
        POST/PUT/PATCH/DELETE: requiere SystemAdmin
        """
        if self.action in ['list', 'retrieve', 'history', 'hierarchy']:
            return [permissions.IsAuthenticated(), CanViewRoles()]
        return [permissions.IsAuthenticated(), IsAccountsAdmin()]
    
    def get_queryset(self):
        """Retorna solo permisos activos con relaciones pre-cargadas"""
        return CustomPermission.objects.filter(
            state=True
        ).select_related(
            'category', 'parent_permission', 'django_permission'
        ).prefetch_related('child_permissions')
    
    def perform_destroy(self, instance):
        """
        Soft delete del permiso y registra en auditoría.
        Los permisos del sistema no pueden ser eliminados.
        """
        if instance.is_system:
            return Response(
                {'error': 'Los permisos del sistema no pueden ser eliminados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Registrar auditoría antes del soft delete
        from .audit_log import get_client_ip
        PermissionChangeAudit.objects.create(
            permission=instance,
            action='deleted',
            performed_by=self.request.user,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
            reason="Permiso eliminado via API"
        )
        
        # Soft delete
        instance.state = False
        instance.save()
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Obtiene el historial completo de cambios del permiso"""
        permission = self.get_object()
        
        # Obtener historial de django-simple-history
        historical_records = permission.history.all()
        
        # Obtener auditoría específica
        audit_logs = permission.audit_logs.all()
        
        return Response({
            'permission': CustomPermissionSerializer(permission).data,
            'historical_records': [
                {
                    'history_id': h.history_id,
                    'history_date': h.history_date,
                    'history_type': h.get_history_type_display(),
                    'history_user': h.history_user.username if h.history_user else None,
                    'name': h.name,
                    'codename': h.codename,
                    'permission_type': h.permission_type,
                    'action_type': h.action_type,
                }
                for h in historical_records
            ],
            'audit_logs': PermissionChangeAuditSerializer(audit_logs, many=True).data
        })
    
    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """Obtiene la jerarquía completa del permiso (padres e hijos)"""
        permission = self.get_object()
        
        # Obtener todos los ancestros (padres)
        ancestors = []
        current = permission.parent_permission
        while current:
            ancestors.append({
                'id': current.id,
                'name': current.name,
                'codename': current.codename,
                'permission_type': current.permission_type
            })
            current = current.parent_permission
        ancestors.reverse()  # Para mostrar desde la raíz
        
        # Obtener todos los descendientes (hijos)
        def get_children(perm):
            children = []
            for child in perm.child_permissions.filter(state=True):
                children.append({
                    'id': child.id,
                    'name': child.name,
                    'codename': child.codename,
                    'permission_type': child.permission_type,
                    'children': get_children(child)
                })
            return children
        
        descendants = get_children(permission)
        
        return Response({
            'permission': CustomPermissionSerializer(permission).data,
            'ancestors': ancestors,
            'descendants': descendants
        })
    
    @action(detail=False, methods=['post'])
    def assign(self, request):
        """
        Asigna o revoca un permiso a un usuario o grupo.
        Solo SystemAdmin puede ejecutar esta acción.
        """
        # Validar que el usuario sea SystemAdmin
        if not request.user.groups.filter(name='SystemAdmin').exists():
            return Response(
                {'error': 'Solo SystemAdmin puede asignar/revocar permisos'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PermissionAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        permission = serializer.validated_data['permission']
        action_type = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')
        
        target_user = serializer.validated_data.get('user')
        target_group = serializer.validated_data.get('group')
        
        # Obtener el Permission nativo de Django
        django_perm = permission.django_permission
        if not django_perm:
            return Response(
                {'error': 'El permiso no tiene un Permission de Django asociado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Asignar o revocar
        if action_type == 'assign':
            if target_user:
                target_user.user_permissions.add(django_perm)
                message = f"Permiso asignado al usuario {target_user.username}"
            else:
                target_group.permissions.add(django_perm)
                message = f"Permiso asignado al grupo {target_group.name}"
            audit_action = 'assigned'
        else:  # revoke
            if target_user:
                target_user.user_permissions.remove(django_perm)
                message = f"Permiso revocado del usuario {target_user.username}"
            else:
                target_group.permissions.remove(django_perm)
                message = f"Permiso revocado del grupo {target_group.name}"
            audit_action = 'revoked'
        
        # Registrar auditoría
        from .audit_log import get_client_ip
        PermissionChangeAudit.objects.create(
            permission=permission,
            action=audit_action,
            performed_by=request.user,
            target_user=target_user,
            target_group=target_group,
            reason=reason,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        return Response({
            'message': message,
            'permission': CustomPermissionSerializer(permission).data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Crea múltiples permisos en una sola operación.
        Solo SystemAdmin puede ejecutar esta acción.
        Útil para crear set completos de permisos para un nuevo módulo.
        """
        # Validar que el usuario sea SystemAdmin
        if not request.user.groups.filter(name='SystemAdmin').exists():
            return Response(
                {'error': 'Solo SystemAdmin puede crear permisos en lote'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        permissions_data = request.data.get('permissions', [])
        if not permissions_data:
            return Response(
                {'error': 'Debe proporcionar una lista de permisos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_permissions = []
        errors = []
        
        for perm_data in permissions_data:
            serializer = CustomPermissionSerializer(
                data=perm_data,
                context={'request': request}
            )
            if serializer.is_valid():
                permission = serializer.save()
                created_permissions.append(permission)
            else:
                errors.append({
                    'data': perm_data,
                    'errors': serializer.errors
                })
        
        return Response({
            'created': len(created_permissions),
            'failed': len(errors),
            'permissions': CustomPermissionSerializer(created_permissions, many=True).data,
            'errors': errors
        })


class PermissionChangeAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para consultar auditoría de permisos.
    Solo SystemAdmin puede acceder.
    """
    queryset = PermissionChangeAudit.objects.all()
    serializer_class = PermissionChangeAuditSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountsAdmin]
    
    def get_queryset(self):
        """Retorna logs de auditoría con relaciones pre-cargadas"""
        queryset = PermissionChangeAudit.objects.select_related(
            'permission', 'permission__category',
            'performed_by', 'target_user', 'target_group'
        ).order_by('-created_date')
        
        # Filtros opcionales
        permission_id = self.request.query_params.get('permission_id')
        if permission_id:
            queryset = queryset.filter(permission_id=permission_id)
        
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(performed_by_id=user_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtiene los cambios recientes (últimas 24 horas)"""
        since = timezone.now() - timedelta(hours=24)
        recent_logs = self.get_queryset().filter(created_date__gte=since)
        serializer = self.get_serializer(recent_logs, many=True)
        return Response({
            'period': '24 hours',
            'count': recent_logs.count(),
            'logs': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Obtiene todos los cambios realizados por un usuario específico"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'Debe proporcionar user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = self.get_queryset().filter(performed_by_id=user_id)
        serializer = self.get_serializer(logs, many=True)
        return Response({
            'user_id': user_id,
            'count': logs.count(),
            'logs': serializer.data
        })
    
    @property
    def paginator(self):
        """
        Conditionally disable pagination based on query parameters.
        """
        if self.request.query_params.get('pagination') == 'off' or \
           self.request.query_params.get('all') == 'true':
            return None
        return super().paginator