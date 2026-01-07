from django.core.management.base import BaseCommand
from usuarios.models import CustomPermission, CustomPermissionCategory

class Command(BaseCommand):
    help = 'Corrige las categorías de los permisos basándose en el prefijo del codename'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando corrección de categorías...")

        # 1. Definir o recuperar las categorías correctas
        cat_importaciones, _ = CustomPermissionCategory.objects.get_or_create(
            name='importaciones', defaults={'display_name': 'Módulo Importaciones', 'state': True, 'order': 1}
        )
        cat_almacen, _ = CustomPermissionCategory.objects.get_or_create(
            name='almacen', defaults={'display_name': 'Módulo Almacén', 'state': True, 'order': 2}
        )
        cat_usuarios, _ = CustomPermissionCategory.objects.get_or_create(
            name='usuarios', defaults={'display_name': 'Usuarios y Seguridad', 'state': True, 'order': 3}
        )
        cat_proveedores, _ = CustomPermissionCategory.objects.get_or_create(
            name='proveedores', defaults={'display_name': 'Portal Proveedores', 'state': True, 'order': 4}
        )
        cat_sistema, _ = CustomPermissionCategory.objects.get_or_create(
            name='sistema', defaults={'display_name': 'Configuración Sistema', 'state': True, 'order': 5}
        )

        # 2. Obtener todos los CustomPermissions
        permissions = CustomPermission.objects.all()
        count = 0

        for p in permissions:
            # Miramos el codename ORIGINAL de Django para saber de qué trata
            # Ej: 'importaciones_ver_modulo', 'almacen_ver_stock'
            original_code = p.django_permission.codename

            new_category = None

            # 3. Lógica de detección por prefijo
            if original_code.startswith('importaciones_'):
                new_category = cat_importaciones

            elif original_code.startswith('almacen_'):
                new_category = cat_almacen

            elif original_code.startswith('proveedor_'):
                new_category = cat_proveedores

            elif original_code.startswith('user_') or 'role' in original_code or 'can_manage_users' in original_code:
                new_category = cat_usuarios

            elif original_code.startswith('mantenimiento_') or original_code.startswith('sistema_'):
                new_category = cat_sistema

            # 4. Aplicar corrección si se encontró una categoría mejor
            if new_category and p.category != new_category:
                p.category = new_category
                p.save()
                self.stdout.write(f"Corregido: {original_code} -> {new_category.display_name}")
                count += 1

        self.stdout.write(self.style.SUCCESS(f'-----------------------------------'))
        self.stdout.write(self.style.SUCCESS(f'Corrección finalizada. {count} permisos re-categorizados.'))