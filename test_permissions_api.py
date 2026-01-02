#!/usr/bin/env python
"""
Test Script for Dynamic Permissions API
Comprehensive testing of all API endpoints with detailed output.

Usage:
    python test_permissions_api.py
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'semilla360.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from usuarios.models import CustomPermissionCategory, CustomPermission, PermissionChangeAudit

User = get_user_model()

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class PermissionsAPITester:
    def __init__(self):
        self.client = APIClient()
        self.admin_user = None
        self.test_category = None
        self.test_permission = None
        self.test_group = None
        self.test_user = None
        self.results = {'passed': 0, 'failed': 0, 'tests': []}
        
    def print_header(self, text):
        """Print formatted section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    def print_test(self, name, passed, details=""):
        """Print test result"""
        status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if passed else f"{Colors.RED}✗ FAILED{Colors.END}"
        print(f"{status} - {name}")
        if details:
            print(f"  {Colors.YELLOW}{details}{Colors.END}")
        
        self.results['tests'].append({
            'name': name,
            'passed': passed,
            'details': details
        })
        
        if passed:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
    
    def setup_test_data(self):
        """Create test users and authenticate"""
        self.print_header("SETUP - Creating Test Data")
        
        try:
            # Create or get admin user
            self.admin_user, created = User.objects.get_or_create(
                username='test_admin',
                defaults={
                    'email': 'admin@test.com',
                    'first_name': 'Test',
                    'last_name': 'Admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'tipo_usuario': 'SystemAdmin'
                }
            )
            if created:
                self.admin_user.set_password('admin123')
                self.admin_user.save()
            
            self.print_test("Create Admin User", True, f"User: {self.admin_user.username}")
            
            # Create test regular user
            self.test_user, created = User.objects.get_or_create(
                username='test_user',
                defaults={
                    'email': 'user@test.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'tipo_usuario': 'Staff'
                }
            )
            if created:
                self.test_user.set_password('user123')
                self.test_user.save()
            
            self.print_test("Create Regular User", True, f"User: {self.test_user.username}")
            
            # Create test group
            self.test_group, created = Group.objects.get_or_create(name='Test Group')
            self.print_test("Create Test Group", True, f"Group: {self.test_group.name}")
            
            # Authenticate as admin
            self.client.force_authenticate(user=self.admin_user)
            self.print_test("Authenticate as Admin", True, f"Authenticated: {self.admin_user.username}")
            
        except Exception as e:
            self.print_test("Setup Test Data", False, str(e))
            raise
    
    def test_categories_api(self):
        """Test Permission Categories API"""
        self.print_header("TEST 1 - Permission Categories API")
        
        # Test 1.1: List Categories
        try:
            response = self.client.get('/api/accounts/permission-categories/')
            self.print_test(
                "GET /api/accounts/permission-categories",
                response.status_code == 200,
                f"Status: {response.status_code}, Count: {len(response.data.get('results', []))}"
            )
        except Exception as e:
            self.print_test("GET /api/accounts/permission-categories", False, str(e))
        
        # Test 1.2: Create Category
        try:
            category_data = {
                'name': 'test_ventas',
                'display_name': 'Ventas',
                'description': 'Permisos del módulo de ventas',
                'icon': 'shopping-cart',
                'order': 10
            }
            response = self.client.post('/api/accounts/permission-categories/', category_data)
            self.test_category = response.data if response.status_code == 201 else None
            self.print_test(
                "POST /api/accounts/permission-categories (Create)",
                response.status_code == 201,
                f"Status: {response.status_code}, ID: {self.test_category.get('id') if self.test_category else 'N/A'}"
            )
        except Exception as e:
            self.print_test("POST /api/accounts/permission-categories (Create)", False, str(e))
        
        # Test 1.3: Get Specific Category
        if self.test_category:
            try:
                response = self.client.get(f'/api/accounts/permission-categories/{self.test_category["id"]}/')
                self.print_test(
                    "GET /api/accounts/permission-categories/{id}",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Name: {response.data.get('name')}"
                )
            except Exception as e:
                self.print_test("GET /api/accounts/permission-categories/{id}", False, str(e))
        
        # Test 1.4: Update Category
        if self.test_category:
            try:
                update_data = {
                    'display_name': 'Ventas Actualizadas',
                    'description': 'Descripción actualizada'
                }
                response = self.client.patch(
                    f'/api/accounts/permission-categories/{self.test_category["id"]}/',
                    update_data
                )
                self.print_test(
                    "PATCH /api/accounts/permission-categories/{id} (Update)",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Updated: {response.data.get('display_name')}"
                )
            except Exception as e:
                self.print_test("PATCH /api/accounts/permission-categories/{id} (Update)", False, str(e))
    
    def test_permissions_api(self):
        """Test Custom Permissions API"""
        self.print_header("TEST 2 - Custom Permissions API")
        
        # Test 2.1: Create Modular Permission
        if self.test_category:
            try:
                permission_data = {
                    'category': self.test_category['id'],
                    'codename': 'can_manage_sales',
                    'name': 'Puede gestionar ventas',
                    'description': 'Permite crear, editar y eliminar ventas',
                    'permission_type': 'modular',
                    'action_type': 'manage'
                }
                response = self.client.post('/api/accounts/custom-permissions/', permission_data)
                self.test_permission = response.data if response.status_code == 201 else None
                self.print_test(
                    "POST /api/accounts/custom-permissions (Create Modular)",
                    response.status_code == 201,
                    f"Status: {response.status_code}, Codename: {self.test_permission.get('codename') if self.test_permission else 'N/A'}"
                )
            except Exception as e:
                self.print_test("POST /api/accounts/custom-permissions (Create Modular)", False, str(e))
        
        # Test 2.2: Create Granular Permission with Parent
        if self.test_permission:
            try:
                granular_data = {
                    'category': self.test_category['id'],
                    'codename': 'can_create_sales',
                    'name': 'Puede crear ventas',
                    'permission_type': 'granular',
                    'action_type': 'create',
                    'parent_permission': self.test_permission['id']
                }
                response = self.client.post('/api/accounts/custom-permissions/', granular_data)
                self.print_test(
                    "POST /api/accounts/custom-permissions (Create Granular with Parent)",
                    response.status_code == 201,
                    f"Status: {response.status_code}, Codename: {response.data.get('codename')}"
                )
            except Exception as e:
                self.print_test("POST /api/accounts/custom-permissions (Create Granular with Parent)", False, str(e))
        
        # Test 2.3: List Permissions
        try:
            response = self.client.get('/api/accounts/custom-permissions/')
            self.print_test(
                "GET /api/accounts/custom-permissions (List)",
                response.status_code == 200,
                f"Status: {response.status_code}, Count: {len(response.data.get('results', []))}"
            )
        except Exception as e:
            self.print_test("GET /api/accounts/custom-permissions (List)", False, str(e))
        
        # Test 2.4: Get Specific Permission
        if self.test_permission:
            try:
                response = self.client.get(f'/api/accounts/custom-permissions/{self.test_permission["id"]}/')
                self.print_test(
                    "GET /api/accounts/custom-permissions/{id}",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Name: {response.data.get('name')}"
                )
            except Exception as e:
                self.print_test("GET /api/accounts/custom-permissions/{id}", False, str(e))
    
    def test_permission_hierarchy(self):
        """Test Permission Hierarchy Endpoint"""
        self.print_header("TEST 3 - Permission Hierarchy")
        
        if self.test_permission:
            try:
                response = self.client.get(f'/api/accounts/custom-permissions/{self.test_permission["id"]}/hierarchy/')
                self.print_test(
                    "GET /api/accounts/custom-permissions/{id}/hierarchy",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Children: {len(response.data.get('descendants', []))}"
                )
            except Exception as e:
                self.print_test("GET /api/accounts/custom-permissions/{id}/hierarchy", False, str(e))
    
    def test_permission_assignment(self):
        """Test Permission Assignment/Revocation"""
        self.print_header("TEST 4 - Permission Assignment/Revocation")
        
        # Test 4.1: Assign Permission to User
        if self.test_permission and self.test_user:
            try:
                assign_data = {
                    'permission_id': self.test_permission['id'],
                    'user_id': self.test_user.id,
                    'action': 'assign',
                    'reason': 'Test assignment'
                }
                response = self.client.post('/api/accounts/custom-permissions/assign/', assign_data)
                self.print_test(
                    "POST /api/accounts/custom-permissions/assign (User)",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Message: {response.data.get('message', 'N/A')}"
                )
            except Exception as e:
                self.print_test("POST /api/accounts/custom-permissions/assign (User)", False, str(e))
        
        # Test 4.2: Assign Permission to Group
        if self.test_permission and self.test_group:
            try:
                assign_data = {
                    'permission_id': self.test_permission['id'],
                    'group_id': self.test_group.id,
                    'action': 'assign',
                    'reason': 'Test group assignment'
                }
                response = self.client.post('/api/accounts/custom-permissions/assign/', assign_data)
                self.print_test(
                    "POST /api/accounts/custom-permissions/assign (Group)",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Message: {response.data.get('message', 'N/A')}"
                )
            except Exception as e:
                self.print_test("POST /api/accounts/custom-permissions/assign (Group)", False, str(e))
        
        # Test 4.3: Revoke Permission from User
        if self.test_permission and self.test_user:
            try:
                revoke_data = {
                    'permission_id': self.test_permission['id'],
                    'user_id': self.test_user.id,
                    'action': 'revoke',
                    'reason': 'Test revocation'
                }
                response = self.client.post('/api/accounts/custom-permissions/assign/', revoke_data)
                self.print_test(
                    "POST /api/accounts/custom-permissions/assign (Revoke)",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Message: {response.data.get('message', 'N/A')}"
                )
            except Exception as e:
                self.print_test("POST /api/accounts/custom-permissions/assign (Revoke)", False, str(e))
    
    def test_bulk_create(self):
        """Test Bulk Permission Creation"""
        self.print_header("TEST 5 - Bulk Permission Creation")
        
        if self.test_category:
            try:
                bulk_data = {
                    'permissions': [
                        {
                            'category': self.test_category['id'],
                            'codename': 'can_view_sales',
                            'name': 'Puede ver ventas',
                            'permission_type': 'modular',
                            'action_type': 'view'
                        },
                        {
                            'category': self.test_category['id'],
                            'codename': 'can_edit_sales',
                            'name': 'Puede editar ventas',
                            'permission_type': 'granular',
                            'action_type': 'edit'
                        },
                        {
                            'category': self.test_category['id'],
                            'codename': 'can_delete_sales',
                            'name': 'Puede eliminar ventas',
                            'permission_type': 'granular',
                            'action_type': 'delete'
                        }
                    ]
                }
                response = self.client.post('/api/accounts/custom-permissions/bulk_create/', bulk_data)
                self.print_test(
                    "POST /api/accounts/custom-permissions/bulk_create",
                    response.status_code == 201,
                    f"Status: {response.status_code}, Created: {response.data.get('created_count', 0)}"
                )
            except Exception as e:
                self.print_test("POST /api/accounts/custom-permissions/bulk_create", False, str(e))
    
    def test_audit_logs(self):
        """Test Audit Log Endpoints"""
        self.print_header("TEST 6 - Audit Logs")
        
        # Test 6.1: List All Audit Logs
        try:
            response = self.client.get('/api/accounts/permission-audits/')
            self.print_test(
                "GET /api/accounts/permission-audits",
                response.status_code == 200,
                f"Status: {response.status_code}, Count: {len(response.data.get('results', []))}"
            )
        except Exception as e:
            self.print_test("GET /api/accounts/permission-audits", False, str(e))
        
        # Test 6.2: Get Recent Audit Logs (24h)
        try:
            response = self.client.get('/api/accounts/permission-audits/recent/')
            self.print_test(
                "GET /api/accounts/permission-audits/recent",
                response.status_code == 200,
                f"Status: {response.status_code}, Recent: {len(response.data)}"
            )
        except Exception as e:
            self.print_test("GET /api/accounts/permission-audits/recent", False, str(e))
        
        # Test 6.3: Get Audit Logs by User
        if self.test_user:
            try:
                response = self.client.get(f'/api/accounts/permission-audits/by_user/?user_id={self.test_user.id}')
                self.print_test(
                    "GET /api/accounts/permission-audits/by_user",
                    response.status_code == 200,
                    f"Status: {response.status_code}, User Logs: {len(response.data)}"
                )
            except Exception as e:
                self.print_test("GET /api/accounts/permission-audits/by_user", False, str(e))
    
    def test_permission_history(self):
        """Test Permission History Endpoint"""
        self.print_header("TEST 7 - Permission History")
        
        if self.test_permission:
            try:
                response = self.client.get(f'/api/accounts/custom-permissions/{self.test_permission["id"]}/history/')
                self.print_test(
                    "GET /api/accounts/custom-permissions/{id}/history",
                    response.status_code == 200,
                    f"Status: {response.status_code}, History Records: {len(response.data.get('historical_records', []))}"
                )
            except Exception as e:
                self.print_test("GET /api/accounts/custom-permissions/{id}/history", False, str(e))
    
    def test_validation(self):
        """Test API Validation"""
        self.print_header("TEST 8 - Validation Tests")
        
        # Test 8.1: Invalid Codename Format
        if self.test_category:
            try:
                invalid_data = {
                    'category': self.test_category['id'],
                    'codename': 'invalid_codename',  # Doesn't start with 'can_'
                    'name': 'Invalid Permission',
                    'permission_type': 'modular'
                }
                response = self.client.post('/api/accounts/custom-permissions/', invalid_data)
                self.print_test(
                    "POST with Invalid Codename Format",
                    response.status_code == 400,
                    f"Status: {response.status_code}, Correctly rejected"
                )
            except Exception as e:
                self.print_test("POST with Invalid Codename Format", False, str(e))
        
        # Test 8.2: Duplicate Codename
        if self.test_category:
            try:
                duplicate_data = {
                    'category': self.test_category['id'],
                    'codename': 'can_manage_sales',  # Already exists
                    'name': 'Duplicate Permission',
                    'permission_type': 'modular'
                }
                response = self.client.post('/api/accounts/custom-permissions/', duplicate_data)
                self.print_test(
                    "POST with Duplicate Codename",
                    response.status_code == 400,
                    f"Status: {response.status_code}, Correctly rejected"
                )
            except Exception as e:
                self.print_test("POST with Duplicate Codename", False, str(e))
    
    def test_permissions_in_category(self):
        """Test Get Permissions in Category"""
        self.print_header("TEST 9 - Get Permissions in Category")
        
        if self.test_category:
            try:
                response = self.client.get(f'/api/accounts/permission-categories/{self.test_category["id"]}/permissions/')
                self.print_test(
                    "GET /api/accounts/permission-categories/{id}/permissions",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Permissions: {len(response.data)}"
                )
            except Exception as e:
                self.print_test("GET /api/accounts/permission-categories/{id}/permissions", False, str(e))
    
    def cleanup(self):
        """Clean up test data"""
        self.print_header("CLEANUP - Removing Test Data")
        
        try:
            # Delete test permissions (soft delete)
            CustomPermission.objects.filter(
                codename__contains='sales'
            ).update(state=False)
            self.print_test("Delete Test Permissions", True, "Soft deleted")
            
            # Delete test category
            if self.test_category:
                CustomPermissionCategory.objects.filter(
                    id=self.test_category['id']
                ).update(state=False)
            self.print_test("Delete Test Category", True, "Soft deleted")
            
            # Keep test users for future tests (optional)
            # self.admin_user.delete()
            # self.test_user.delete()
            # self.test_group.delete()
            
        except Exception as e:
            self.print_test("Cleanup", False, str(e))
    
    def print_summary(self):
        """Print test results summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.results['passed']}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.results['failed']}{Colors.END}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")
        
        if self.results['failed'] > 0:
            print(f"{Colors.RED}Failed Tests:{Colors.END}")
            for test in self.results['tests']:
                if not test['passed']:
                    print(f"  - {test['name']}: {test['details']}")
        
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}\n")
    
    def run_all_tests(self):
        """Run all test suites"""
        try:
            self.setup_test_data()
            self.test_categories_api()
            self.test_permissions_api()
            self.test_permission_hierarchy()
            self.test_permission_assignment()
            self.test_bulk_create()
            self.test_audit_logs()
            self.test_permission_history()
            self.test_validation()
            self.test_permissions_in_category()
            self.cleanup()
            self.print_summary()
            
        except Exception as e:
            print(f"\n{Colors.RED}Fatal Error: {str(e)}{Colors.END}")
            self.print_summary()
            return False
        
        return self.results['failed'] == 0

def main():
    """Main entry point"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Dynamic Permissions API - Comprehensive Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tester = PermissionsAPITester()
    success = tester.run_all_tests()
    
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
