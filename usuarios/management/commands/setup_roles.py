"""
Management command to setup initial roles (Groups) and assign permissions.
This replaces the django-role-permissions library functionality.

Usage: python manage.py setup_roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


class Command(BaseCommand):
    help = 'Create base groups (roles) and assign permissions to them'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up roles and permissions...'))
        
        with transaction.atomic():
            self._setup_system_admin()
            self._setup_accounts_admin()
            self._setup_accounts_user()
            self._setup_importaciones_admin()
            self._setup_importaciones_asistente()
            self._setup_almacen_admin()
            self._setup_almacen_operador()
            self._setup_proveedor()
        
        self.stdout.write(self.style.SUCCESS('✅ Roles and permissions setup completed!'))

    def _get_or_create_permission(self, codename, name, content_type=None):
        """Helper to get or create a custom permission"""
        if content_type is None:
            # Use a generic content type for custom permissions
            content_type, _ = ContentType.objects.get_or_create(
                app_label='usuarios',
                model='custompe

rmission'
            )
        
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                'name': name,
                'content_type': content_type
            }
        )
        
        if created:
            self.stdout.write(f'  Created permission: {codename}')
        
        return permission

    def _setup_system_admin(self):
        """Setup SystemAdmin role with full system access"""
        self.stdout.write('Setting up SystemAdmin role...')
        group, created = Group.objects.get_or_create(name='SystemAdmin')
        
        permissions = [
            ('mantenimiento_tabla_tipo_documentos', 'Gestionar tabla de tipos de documentos'),
            ('sistema_gestionar_configuracion', 'Gestionar configuración del sistema'),
            ('sistema_ver_logs_auditoria', 'Ver logs de auditoría'),
            ('sistema_gestionar_respaldos', 'Gestionar respaldos del sistema'),
        ]
        
        perm_objects = []
        for codename, name in permissions:
            perm_objects.append(self._get_or_create_permission(codename, name))
        
        group.permissions.set(perm_objects)
        self.stdout.write(self.style.SUCCESS(f'  ✓ SystemAdmin configured with {len(perm_objects)} permissions'))

    def _setup_accounts_admin(self):
        """Setup AccountsAdmin role for user management"""
        self.stdout.write('Setting up AccountsAdmin role...')
        group, created = Group.objects.get_or_create(name='AccountsAdmin')
        
        permissions = [
            ('user_listar_usuarios', 'Listar usuarios'),
            ('user_registrar_usuario', 'Registrar usuario'),
            ('user_editar_usuario', 'Editar usuario'),
            ('user_eliminar_usuario', 'Eliminar usuario'),
            ('user_asignar_roles', 'Asignar roles'),
            ('user_gestionar_permisos', 'Gestionar permisos'),
            ('user_ver_perfil', 'Ver perfil'),
        ]
        
        perm_objects = []
        for codename, name in permissions:
            perm_objects.append(self._get_or_create_permission(codename, name))
        
        group.permissions.set(perm_objects)
        self.stdout.write(self.style.SUCCESS(f'  ✓ AccountsAdmin configured with {len(perm_objects)} permissions'))

    def _setup_accounts_user(self):
        """Setup AccountsUser role for standard users"""
        self.stdout.write('Setting up AccountsUser role...')
        group, created = Group.objects.get_or_create(name='AccountsUser')
        
        permissions = [
            ('user_editar_perfil', 'Editar perfil propio'),
            ('user_ver_perfil', 'Ver perfil propio'),
            ('user_cambiar_password', 'Cambiar contraseña'),
        ]
        
        perm_objects = []
        for codename, name in permissions:
            perm_objects.append(self._get_or_create_permission(codename, name))
        
        group.permissions.set(perm_objects)
        self.stdout.write(self.style.SUCCESS(f'  ✓ AccountsUser configured with {len(perm_objects)} permissions'))

    def _setup_importaciones_admin(self):
        """Setup ImportacionesAdmin role"""
        self.stdout.write('Setting up ImportacionesAdmin role...')
        group, created = Group.objects.get_or_create(name='ImportacionesAdmin')
        
        permissions = [
            ('importaciones_ver_modulo', 'Ver módulo de importaciones'),
            ('importaciones_ver_fletes_internacionales', 'Ver fletes internacionales'),
            ('importaciones_registrar_flete_internacional', 'Registrar flete internacional'),
            ('importaciones_editar_flete_internacional', 'Editar flete internacional'),
            ('importaciones_eliminar_flete_internacional', 'Eliminar flete internacional'),
            ('importaciones_ver_reporte_flete', 'Ver reporte de fletes'),
            ('importaciones_ver_reporte_estibas', 'Ver reporte de estibas'),
            ('importaciones_administrar_documentos_dua', 'Administrar documentos DUA'),
            ('importaciones_administrar_expedientes_dua', 'Administrar expedientes DUA'),
            ('importaciones_crear_expedientes_dua', 'Crear expedientes DUA'),
            ('importaciones_editar_expedientes_dua', 'Editar expedientes DUA'),
            ('importaciones_eliminar_expedientes_dua', 'Eliminar expedientes DUA'),
            ('importaciones_descargar_expedientes_dua', 'Descargar expedientes DUA'),
            ('importaciones_agregar_mes_expedientes_dua', 'Agregar mes a expedientes DUA'),
            ('importaciones_agregar_empresa_expedientes_dua', 'Agregar empresa a expedientes DUA'),
            ('importaciones_ver_ordenes_compra', 'Ver órdenes de compra'),
            ('importaciones_crear_ordenes_compra', 'Crear órdenes de compra'),
            ('importaciones_editar_ordenes_compra', 'Editar órdenes de compra'),
            ('importaciones_eliminar_ordenes_compra', 'Eliminar órdenes de compra'),
        ]
        
        perm_objects = []
        for codename, name in permissions:
            perm_objects.append(self._get_or_create_permission(codename, name))
        
        group.permissions.set(perm_objects)
        self.stdout.write(self.style.SUCCESS(f'  ✓ ImportacionesAdmin configured with {len(perm_objects)} permissions'))

    def _setup_importaciones_asistente(self):
        """Setup ImportacionesAsistente role"""
        self.stdout.write('Setting up ImportacionesAsistente role...')
        group, created = Group.objects.get_or_create(name='ImportacionesAsistente')
        
        permissions = [
            ('importaciones_ver_modulo', 'Ver módulo de importaciones'),
            ('importaciones_ver_fletes_internacionales', 'Ver fletes internacionales'),
            ('importaciones_administrar_documentos_dua', 'Administrar documentos DUA'),
            ('importaciones_administrar_expedientes_dua', 'Administrar expedientes DUA'),
            ('importaciones_editar_expedientes_dua', 'Editar expedientes DUA'),
            ('importaciones_descargar_expedientes_dua', 'Descargar expedientes DUA'),
            ('importaciones_agregar_mes_expedientes_dua', 'Agregar mes a expedientes DUA'),
            ('importaciones_agregar_empresa_expedientes_dua', 'Agregar empresa a expedientes DUA'),
            ('importaciones_ver_ordenes_compra', 'Ver órdenes de compra'),
        ]
        
        perm_objects = []
        for codename, name in permissions:
            perm_objects.append(self._get_or_create_permission(codename, name))
        
        group.permissions.set(perm_objects)
        self.stdout.write(self.style.SUCCESS(f'  ✓ ImportacionesAsistente configured with {len(perm_objects)} permissions'))

    def _setup_almacen_admin(self):
        """Setup AlmacenAdmin role"""
        self.stdout.write('Setting up AlmacenAdmin role...')
        group, created = Group.objects.get_or_create(name='AlmacenAdmin')
        
        permissions = [
            ('almacen_ver_modulo', 'Ver módulo de almacén'),
            ('almacen_gestionar_productos', 'Gestionar productos'),
            ('almacen_gestionar_stock', 'Gestionar stock'),
            ('almacen_gestionar_movimientos', 'Gestionar movimientos'),
            ('almacen_ver_kardex', 'Ver kardex'),
            ('almacen_generar_reportes', 'Generar reportes'),
            ('almacen_realizar_ajustes', 'Realizar ajustes de inventario'),
        ]
        
        perm_objects = []
        for codename, name in permissions:
            perm_objects.append(self._get_or_create_permission(codename, name))
        
        group.permissions.set(perm_objects)
        self.stdout.write(self.style.SUCCESS(f'  ✓ AlmacenAdmin configured with {len(perm_objects)} permissions'))

    def _setup_almacen_operador(self):
        """Setup AlmacenOperador role"""
        self.stdout.write('Setting up AlmacenOperador role...')
        group, created = Group.objects.get_or_create(name='AlmacenOperador')
        
        permissions = [
            ('almacen_ver_modulo', 'Ver módulo de almacén'),
            ('almacen_ver_productos', 'Ver productos'),
            ('almacen_ver_stock', 'Ver stock'),
            ('almacen_registrar_movimientos', 'Registrar movimientos'),
            ('almacen_ver_kardex', 'Ver kardex'),
        ]
        
        perm_objects = []
        for codename, name in permissions:
            perm_objects.append(self._get_or_create_permission(codename, name))
        
        group.permissions.set(perm_objects)
        self.stdout.write(self.style.SUCCESS(f'  ✓ AlmacenOperador configured with {len(perm_objects)} permissions'))

    def _setup_proveedor(self):
        """Setup Proveedor role"""
        self.stdout.write('Setting up Proveedor role...')
        group, created = Group.objects.get_or_create(name='Proveedor')
        
        permissions = [
            ('proveedor_cargar_documentos', 'Cargar documentos'),
            ('proveedor_administrar_documentos', 'Administrar documentos'),
            ('proveedor_ver_documentos_propios', 'Ver documentos propios'),
            ('proveedor_descargar_documentos_propios', 'Descargar documentos propios'),
        ]
        
        perm_objects = []
        for codename, name in permissions:
            perm_objects.append(self._get_or_create_permission(codename, name))
        
        group.permissions.set(perm_objects)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Proveedor configured with {len(perm_objects)} permissions'))
