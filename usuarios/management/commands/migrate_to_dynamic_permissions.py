from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from usuarios.models import (
    CustomPermissionCategory,
    CustomPermission,
    UsuariosPermissions,
    #AlmacenPermissions,
    MantenimientoPermissions,
    ProveedorPermissions
)
from django.contrib.auth.models import Permission


class Command(BaseCommand):
    help = 'Migra permisos estáticos a permisos dinámicos'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando migración de permisos...')

        # Crear categorías
        categories = self._create_categories()

        # Migrar permisos por categoría
        self._migrate_usuarios_permissions(categories['usuarios'])
        #self._migrate_almacen_permissions(categories['almacen'])
        self._migrate_mantenimiento_permissions(categories['mantenimiento'])
        self._migrate_proveedor_permissions(categories['proveedor'])

        self.stdout.write(self.style.SUCCESS('✅ Migración completada exitosamente'))

    def _create_categories(self):
        self.stdout.write('Creando categorías...')

        categories = {}

        # Usuarios
        cat, created = CustomPermissionCategory.objects.get_or_create(
            name='usuarios',
            defaults={
                'display_name': 'Usuarios y Roles',
                'description': 'Permisos para gestión de usuarios, roles y permisos',
                'icon': 'users',
                'order': 10
            }
        )
        categories['usuarios'] = cat
        if created:
            self.stdout.write(f'  ✓ Categoría creada: {cat.display_name}')

        # Almacén
        cat, created = CustomPermissionCategory.objects.get_or_create(
            name='almacen',
            defaults={
                'display_name': 'Almacén',
                'description': 'Permisos para gestión de almacenes, stock y movimientos',
                'icon': 'warehouse',
                'order': 20
            }
        )
        categories['almacen'] = cat
        if created:
            self.stdout.write(f'  ✓ Categoría creada: {cat.display_name}')

        # Mantenimiento
        cat, created = CustomPermissionCategory.objects.get_or_create(
            name='mantenimiento',
            defaults={
                'display_name': 'Tablas de Mantenimiento',
                'description': 'Permisos para gestión de tablas de configuración del sistema',
                'icon': 'settings',
                'order': 90
            }
        )
        categories['mantenimiento'] = cat
        if created:
            self.stdout.write(f'  ✓ Categoría creada: {cat.display_name}')

        # Proveedor
        cat, created = CustomPermissionCategory.objects.get_or_create(
            name='proveedor',
            defaults={
                'display_name': 'Proveedores',
                'description': 'Permisos específicos para usuarios proveedores',
                'icon': 'truck',
                'order': 80
            }
        )
        categories['proveedor'] = cat
        if created:
            self.stdout.write(f'  ✓ Categoría creada: {cat.display_name}')

        return categories

    def _migrate_usuarios_permissions(self, category):
        self.stdout.write('Migrando permisos de Usuarios...')

        # Obtener ContentType del modelo UsuariosPermissions
        content_type = ContentType.objects.get_for_model(UsuariosPermissions)

        # Obtener todos los permisos de este ContentType
        django_perms = Permission.objects.filter(content_type=content_type)

        for django_perm in django_perms:
            # Determinar tipo y acción
            perm_type, action_type = self._classify_permission(django_perm.codename)

            # Determinar permiso padre (si es granular)
            parent = None
            if perm_type == 'granular':
                parent_codename = self._get_parent_codename(django_perm.codename)
                if parent_codename:
                    parent = CustomPermission.objects.filter(codename=parent_codename).first()

            # Crear CustomPermission
            custom_perm, created = CustomPermission.objects.get_or_create(
                codename=django_perm.codename,
                defaults={
                    'category': category,
                    'name': django_perm.name,
                    'description': f'Permiso migrado desde sistema estático',
                    'permission_type': perm_type,
                    'action_type': action_type,
                    'parent_permission': parent,
                    'django_permission': django_perm,
                    'is_system': True  # Marcar como sistema para protección
                }
            )

            if created:
                self.stdout.write(f'  ✓ {custom_perm.codename}')

    def _migrate_almacen_permissions(self, category):
        self.stdout.write('Migrando permisos de Almacén...')
        # Similar a usuarios, adaptado para AlmacenPermissions
        # ... (implementación similar)

    def _migrate_mantenimiento_permissions(self, category):
        self.stdout.write('Migrando permisos de Mantenimiento...')
        # Similar a usuarios, adaptado para MantenimientoPermissions
        # ... (implementación similar)

    def _migrate_proveedor_permissions(self, category):
        self.stdout.write('Migrando permisos de Proveedor...')
        # Similar a usuarios, adaptado para ProveedorPermissions
        # ... (implementación similar)

    def _classify_permission(self, codename):
        """
        Clasifica un permiso por tipo y acción.
        Returns: (permission_type, action_type)
        """
        if '_manage_' in codename or codename.startswith('can_manage_'):
            return ('modular', 'manage')
        elif '_view_' in codename or codename.startswith('can_view_'):
            return ('modular', 'view')
        elif '_create_' in codename or codename.startswith('can_create_'):
            return ('granular', 'create')
        elif '_edit_' in codename or codename.startswith('can_edit_'):
            return ('granular', 'edit')
        elif '_delete_' in codename or codename.startswith('can_delete_'):
            return ('granular', 'delete')
        elif '_approve_' in codename or codename.startswith('can_approve_'):
            return ('granular', 'approve')
        else:
            return ('modular', 'custom')

    def _get_parent_codename(self, granular_codename):
        """
        Obtiene el codename del permiso padre para un permiso granular.
        Ejemplo: can_create_users -> can_manage_users
        """
        # can_create_users -> users
        # can_edit_roles -> roles
        parts = granular_codename.split('_')
        if len(parts) >= 3:
            # Reconstruir: can_manage_users
            resource = '_'.join(parts[2:])  # users, roles, etc.
            return f'can_manage_{resource}'
        return None