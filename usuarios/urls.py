# usuarios/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView
from . import views
from .views import *

urlpatterns = [
    # Autenticación
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('content_types/', fetch_content_types, name='content_types'),

    # Usuarios
    path('usuarios/', UserViewSet.as_view({'get': 'list', 'post': 'create'}), name='usuarios'),
    path('usuarios/<int:pk>/', UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='usuario-detalle'),

    # Roles
    path('roles/', RoleViewSet.as_view({'get': 'list', 'post': 'create'}), name='roles'),
    path('roles/<int:pk>/', RoleViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='rol-detalle'),

    # Permisos Nativos
    path('permisos/', PermissionViewSet.as_view({'get': 'list', 'post': 'create'}), name='permisos'),
    path('permisos/<int:pk>/', PermissionViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='permiso-detalle'),

    # Empresas
    path('empresas/', EmpresaListView.as_view(), name='empresa-list'),
    path('empresas/<int:pk>/', EmpresaDetailView.as_view(), name='empresa-detail'),

    # Direcciones
    path('direcciones/', DireccionListCreateView.as_view(), name='direccion-list-create'),
    path('direcciones/<int:pk>/', DireccionDetailView.as_view(), name='direccion-detail'),
    path('empresas/<int:empresa_id>/direcciones/', DireccionesPorEmpresaView.as_view(), name='empresa-direcciones'),

    # Localización
    path('departamentos/', DepartamentoListView.as_view(), name='departamento-list'),
    path('provincias/', ProvinciaListView.as_view(), name='provincia-list'),
    path('distritos/', DistritoListView.as_view(), name='distrito-list'),

    # ========================================
    # Dynamic Permission System URLs (CORREGIDAS)
    # ========================================

    # Permission Categories (Agregada la barra / al final)
    path('permission-categories/', CustomPermissionCategoryViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='permission-categories'),

    path('permission-categories/<int:pk>/', CustomPermissionCategoryViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='permission-category-detail'),

    path('permission-categories/<int:pk>/permissions/', CustomPermissionCategoryViewSet.as_view({
        'get': 'permissions'
    }), name='permission-category-permissions'),

    # Custom Permissions (Agregada la barra / al final)
    path('custom-permissions/', CustomPermissionViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='custom-permissions'),

    path('custom-permissions/<int:pk>/', CustomPermissionViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='custom-permission-detail'),

    path('custom-permissions/<int:pk>/history/', CustomPermissionViewSet.as_view({
        'get': 'history'
    }), name='custom-permission-history'),

    path('custom-permissions/<int:pk>/hierarchy/', CustomPermissionViewSet.as_view({
        'get': 'hierarchy'
    }), name='custom-permission-hierarchy'),

    path('custom-permissions/assign/', CustomPermissionViewSet.as_view({
        'post': 'assign'
    }), name='custom-permission-assign'),

    path('custom-permissions/bulk_create/', CustomPermissionViewSet.as_view({
        'post': 'bulk_create'
    }), name='custom-permission-bulk-create'),

    # Permission Audit Logs (Agregada la barra / al final)
    path('permission-audits/', PermissionChangeAuditViewSet.as_view({
        'get': 'list'
    }), name='permission-audits'),

    path('permission-audits/<int:pk>/', PermissionChangeAuditViewSet.as_view({
        'get': 'retrieve'
    }), name='permission-audit-detail'),

    path('permission-audits/recent/', PermissionChangeAuditViewSet.as_view({
        'get': 'recent'
    }), name='permission-audits-recent'),

    path('permission-audits/by_user/', PermissionChangeAuditViewSet.as_view({
        'get': 'by_user'
    }), name='permission-audits-by-user'),
]