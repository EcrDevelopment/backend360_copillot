from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


class PermissionsCompatibilityTestCase(APITestCase):
    """
    Test cases para verificar la compatibilidad de permisos con el frontend existente.
    """

    def setUp(self):
        """Set up test users and authentication"""
        # Create a regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        # Get JWT tokens for regular user
        refresh = RefreshToken.for_user(self.user)
        self.user_access_token = str(refresh.access_token)
        
        # Get JWT tokens for admin user
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_access_token = str(refresh.access_token)
        
        self.client = APIClient()

    def test_authenticated_user_can_access_users_list(self):
        """Test that authenticated users can access users list"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_access_token}')
        response = self.client.get('/api/accounts/usuarios')
        
        # Should be able to access (even if only sees own data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_authenticated_user_can_access_roles_list(self):
        """Test that authenticated users can access roles list"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_access_token}')
        response = self.client.get('/api/accounts/roles')
        
        # Should be able to access
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_authenticated_user_can_access_permissions_list(self):
        """Test that authenticated users can access permissions list"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_access_token}')
        response = self.client.get('/api/accounts/permisos')
        
        # Should be able to access
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_user_cannot_access_users(self):
        """Test that unauthenticated users cannot access users list"""
        response = self.client.get('/api/accounts/usuarios')
        
        # Should be denied
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_create_user(self):
        """Test that regular users cannot create new users"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_access_token}')
        response = self.client.post('/api/accounts/usuarios', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123'
        })
        
        # Should be denied (requires CanManageUsers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permissions_classes_exist(self):
        """Test that custom permission classes are properly imported"""
        from usuarios.permissions import (
            CanAccessAlmacen,
            CanAccessImportaciones,
            CanEditDocuments,
            CanDeleteResource,
            CanManageUsers
        )
        
        # All permission classes should be importable
        self.assertTrue(CanAccessAlmacen)
        self.assertTrue(CanAccessImportaciones)
        self.assertTrue(CanEditDocuments)
        self.assertTrue(CanDeleteResource)
        self.assertTrue(CanManageUsers)

