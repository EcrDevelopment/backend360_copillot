from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from usuarios.models import CustomPermission


class Command(BaseCommand):
    help = 'Actualiza los codenames de auth_permission para que coincidan con CustomPermission'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando alineación de permisos nativos de Django...")

        # Obtenemos todos los permisos custom activos
        custom_perms = CustomPermission.objects.filter(state=True).select_related('django_permission')

        updated_count = 0

        for cp in custom_perms:
            django_perm = cp.django_permission

            # Si el permiso nativo tiene un nombre diferente al nuevo estándar
            if django_perm and django_perm.codename != cp.codename:
                old_name = django_perm.codename

                # ACTUALIZAMOS EL PERMISO NATIVO
                django_perm.codename = cp.codename
                django_perm.save()

                self.stdout.write(f"Actualizado: {old_name} -> {cp.codename}")
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Proceso terminado. Se actualizaron {updated_count} permisos.'))
        self.stdout.write(self.style.WARNING('NOTA: Debes reiniciar el servidor para limpiar la caché de permisos.'))