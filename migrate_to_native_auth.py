"""
Script de migración para transicionar de django-role-permissions a Django nativo.
Este script migra los roles existentes a Groups de Django.

ADVERTENCIA: Ejecutar SOLO UNA VEZ después de instalar el nuevo código.

Uso:
    python manage.py shell < migrate_to_native_auth.py
"""

from django.contrib.auth.models import User, Group

print("=" * 60)
print("Migración de django-role-permissions a Django nativo")
print("=" * 60)

try:
    from rolepermissions.roles import get_user_roles
    HAS_OLD_LIBRARY = True
except ImportError:
    HAS_OLD_LIBRARY = False
    print("⚠️  django-role-permissions no está instalado.")
    print("   Si ya desinstalaste la librería, este script no es necesario.")
    print("   Solo asegúrate de ejecutar: python manage.py setup_roles")
    exit(0)

print("\n📋 Paso 1: Verificando grupos existentes...")
existing_groups = Group.objects.all()
if existing_groups.exists():
    print(f"   Encontrados {existing_groups.count()} grupos:")
    for group in existing_groups:
        print(f"   - {group.name}")
else:
    print("   ⚠️  No hay grupos creados. Ejecuta primero:")
    print("   python manage.py setup_roles")
    exit(1)

print("\n📋 Paso 2: Migrando usuarios...")
migrated_count = 0
error_count = 0

for user in User.objects.all():
    try:
        old_roles = get_user_roles(user)
        
        if not old_roles:
            print(f"   ⏭️  {user.username}: Sin roles antiguos")
            continue
        
        for role in old_roles:
            role_name = role.get_name()
            
            try:
                group = Group.objects.get(name=role_name)
                user.groups.add(group)
                print(f"   ✅ {user.username} -> {role_name}")
                migrated_count += 1
            except Group.DoesNotExist:
                print(f"   ❌ {user.username}: Grupo '{role_name}' no existe")
                error_count += 1
                
    except Exception as e:
        print(f"   ❌ Error migrando {user.username}: {str(e)}")
        error_count += 1

print("\n" + "=" * 60)
print(f"✅ Migración completada!")
print(f"   - Usuarios migrados: {migrated_count}")
print(f"   - Errores: {error_count}")
print("=" * 60)

print("\n📝 Próximos pasos:")
print("1. Verificar que los usuarios tienen los grupos correctos en /admin/")
print("2. Probar login y verificar el token JWT")
print("3. Desinstalar django-role-permissions:")
print("   pip uninstall django-role-permissions")
print("4. Remover 'rolepermissions' de INSTALLED_APPS en settings.py")
print("5. Opcional: Eliminar el archivo usuarios/roles.py (ya no se usa)")
