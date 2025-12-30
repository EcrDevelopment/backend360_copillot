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
from .permissions import IsAccountsAdmin, CanManageUsers

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
        
        # If successful, add user information to match login response format
        if response.status_code == 200:
            try:
                from rest_framework_simplejwt.tokens import RefreshToken
                from .serializers import CustomTokenObtainPairSerializer
                
                # Decode the refresh token to get the user
                refresh = RefreshToken(refresh_token)
                user_id = refresh.get('user_id')
                user = User.objects.get(id=user_id)
                
                # Add user info, roles, and permissions to response
                response.data['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nombre': user.first_name,
                    'apellido': user.last_name,
                    'profile_id': None,
                    'empresa_id': None
                }
                
                profile = getattr(user, 'userprofile', None)
                if profile:
                    response.data['user']['telefono'] = profile.telefono if profile.telefono else None
                    response.data['user']['empresa_id'] = profile.empresa.id if profile.empresa else None
                
                response.data['roles'] = list(user.groups.values_list('name', flat=True))
                response.data['permissions'] = CustomTokenObtainPairSerializer._get_user_permissions(user)
                
            except Exception as e:
                print(f"Error adding user info to refresh response: {e}")
                # If there's an error, just return the access token without extra info
                pass
        
        return response

# Permission ViewSet - only admin roles can access
class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        Allows GET for authenticated users (needed for frontend to display options).
        Requires CanManageUsers for create/update/delete operations.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), CanManageUsers()]
    
    def get_queryset(self):
        """Filter permissions to show only relevant ones"""
        return Permission.objects.all().select_related('content_type')
    
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
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        Allows GET for authenticated users (needed for frontend to display user roles).
        Requires CanManageUsers for create/update/delete operations.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), CanManageUsers()]
    
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
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        Allows GET for authenticated users (users can view their own profile and admins can view all).
        Requires CanManageUsers for create/update/delete operations.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), CanManageUsers()]
    
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