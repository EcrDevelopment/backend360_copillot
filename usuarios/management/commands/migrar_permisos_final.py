from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from usuarios.models import CustomPermission, CustomPermissionCategory


class Command(BaseCommand):
    help = 'Migra permisos legacy a CustomPermission respetando la validación can_'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando migración corregida...")

        # 1. MAPEO BASADO EN TU CSV -> LO QUE ESPERA EL FRONTEND
        # Formato Clave: 'app_label.codename_antiguo' (Lo que viene de Django)
        # Formato Valor: 'categoria_frontend.nuevo_codename' (Lo que definiste en menuConfig)
        RENAME_MAP = {
            # --- USUARIOS (CSV IDs: 305-311, 18-19) ---
            'usuarios.user_listar_usuarios': 'usuarios.can_view_users',
            'usuarios.user_registrar_usuario': 'usuarios.can_create_users',
            'usuarios.user_editar_usuario': 'usuarios.can_edit_users',
            'usuarios.user_eliminar_usuario': 'usuarios.can_delete_users',
            'usuarios.user_asignar_roles': 'usuarios.can_manage_roles',
            'usuarios.user_gestionar_permisos': 'usuarios.can_manage_roles',
            'usuarios.user_ver_perfil': 'usuarios.can_view_users',  # O can_view_profile
            'usuarios.user_editar_perfil': 'usuarios.can_edit_users',
            'usuarios.user_cambiar_password': 'usuarios.can_edit_users',

            # --- ALMACÉN (CSV IDs: 20-31) ---
            'usuarios.almacen_ver_modulo': 'almacen.can_view_warehouse',
            'usuarios.almacen_ver_productos': 'almacen.can_view_warehouse',  # Productos es parte de warehouse
            'usuarios.almacen_ver_stock': 'almacen.can_view_stock',
            'usuarios.almacen_ver_kardex': 'almacen.can_view_stock',
            'usuarios.almacen_gestionar_stock': 'almacen.can_manage_stock',
            'usuarios.almacen_gestionar_movimientos': 'almacen.can_manage_warehouse',
            'usuarios.almacen_registrar_movimientos': 'almacen.can_create_movements',
            'usuarios.almacen_realizar_ajustes': 'almacen.can_manage_stock',
            'usuarios.almacen_generar_reportes': 'almacen.can_view_warehouse_reports',
            'usuarios.almacen_gestionar_productos': 'usuarios.can_manage_product_catalog',  # Catálogo productos

            # --- IMPORTACIONES (CSV IDs: 32-50) ---
            'usuarios.importaciones_ver_modulo': 'importaciones.can_view_importaciones',
            'usuarios.importaciones_ver_fletes_internacionales': 'importaciones.can_view_importaciones',
            'usuarios.importaciones_registrar_flete_internacional': 'importaciones.can_create_importaciones',
            'usuarios.importaciones_editar_flete_internacional': 'importaciones.can_edit_importaciones',
            'usuarios.importaciones_eliminar_flete_internacional': 'importaciones.can_delete_importaciones',
            'usuarios.importaciones_ver_reporte_flete': 'importaciones.can_view_importaciones_reports',
            'usuarios.importaciones_ver_reporte_estibas': 'importaciones.can_view_importaciones_reports',
            'usuarios.importaciones_administrar_documentos_dua': 'importaciones.can_manage_documents',
            'usuarios.importaciones_administrar_expedientes_dua': 'importaciones.can_manage_documents',
            # Mapeos extra para cubrir acciones granulares si las usas
            'usuarios.importaciones_crear_expedientes_dua': 'importaciones.can_create_documents',
            'usuarios.importaciones_editar_expedientes_dua': 'importaciones.can_edit_documents',
            'usuarios.importaciones_descargar_expedientes_dua': 'importaciones.can_view_documents',

            # --- PROVEEDORES (CSV IDs: 60-63) ---
            'usuarios.proveedor_cargar_documentos': 'usuarios.can_upload_documents',
            'usuarios.proveedor_administrar_documentos': 'usuarios.can_manage_own_documents',
            'usuarios.proveedor_ver_documentos_propios': 'usuarios.can_view_own_documents',
            'usuarios.proveedor_descargar_documentos_propios': 'usuarios.can_view_own_documents',

            # --- SISTEMA / TABLAS (CSV IDs: 64-67) ---
            'usuarios.mantenimiento_tabla_tipo_documentos': 'usuarios.can_manage_document_types',
            'usuarios.sistema_gestionar_configuracion': 'usuarios.can_manage_system',
            'usuarios.sistema_ver_logs_auditoria': 'usuarios.can_view_audit_logs',
            'usuarios.sistema_gestionar_respaldos': 'usuarios.can_manage_backups',
        }

        # 2. DEFINIR NOMBRES VISUALES DE CATEGORÍAS
        CATEGORIES_DISPLAY = {
            'usuarios': 'Usuarios y Seguridad',
            'almacen': 'Módulo Almacén',
            'importaciones': 'Módulo Importaciones',
            'proveedores': 'Portal Proveedores',
            'sistema': 'Configuración Sistema'
        }

        # 3. OBTENER PERMISOS
        permissions_in_use = Permission.objects.filter(group__isnull=False).distinct()

        count = 0

        for perm in permissions_in_use:
            # Construir clave única: app_label.codename
            app_label = perm.content_type.app_label
            full_code = f"{app_label}.{perm.codename}"

            # Buscamos el mapeo nuevo
            new_full_code = RENAME_MAP.get(full_code)

            if not new_full_code:
                # Si es un permiso nuevo que ya cumple el formato can_, lo procesamos
                if perm.codename.startswith('can_'):
                    # Intentamos adivinar la categoría del propio nombre si tiene punto (raro en django puro)
                    # O usamos 'sistema' por defecto si no lo reconocemos
                    new_codename = perm.codename
                    cat_key = 'sistema'

                    # Heurística simple para asignar categoría si no está en el mapa
                    if 'user' in perm.codename or 'role' in perm.codename:
                        cat_key = 'usuarios'
                    elif 'warehouse' in perm.codename or 'stock' in perm.codename:
                        cat_key = 'almacen'
                    elif 'import' in perm.codename:
                        cat_key = 'importaciones'
                else:
                    # Si no está en el mapa y no cumple el formato can_, lo ignoramos
                    # self.stdout.write(f"Ignorando: {full_code}")
                    continue
            else:
                # AQUÍ ESTABA EL ERROR: Separamos la categoría del codename
                # new_full_code es 'usuarios.can_view_users'
                # cat_key = 'usuarios'
                # new_codename = 'can_view_users'
                cat_key, new_codename = new_full_code.split('.')

            # Crear Categoría
            cat_display = CATEGORIES_DISPLAY.get(cat_key, cat_key.capitalize())
            category, _ = CustomPermissionCategory.objects.get_or_create(
                name=cat_key,
                defaults={'display_name': cat_display, 'state': True}
            )

            # Crear/Actualizar CustomPermission
            try:
                custom_perm, created = CustomPermission.objects.update_or_create(
                    django_permission=perm,
                    defaults={
                        'codename': new_codename,  # <--- AHORA SÍ: Enviamos solo 'can_view_users'
                        'name': perm.name,
                        'description': f"Migrado de {perm.codename}",
                        'category': category,
                        'permission_type': 'granular',
                        'state': True,
                        'is_system': True
                    }
                )

                status = "Creado" if created else "Actualizado"
                self.stdout.write(f"{status}: {cat_key}.{new_codename}")
                count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error migrando {perm.codename}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f'--------------------------------------'))
        self.stdout.write(self.style.SUCCESS(f'Migración completada con éxito. {count} permisos procesados.'))