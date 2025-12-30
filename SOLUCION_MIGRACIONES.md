# Solución Definitiva - Conflictos de Migraciones

## 🔴 Error Actual

```
django.db.migrations.exceptions.InconsistentMigrationHistory: 
Migration importaciones.0005_alter_ordencompradespacho_options_and_more 
is applied before its dependency importaciones.0005_merge_branches
```

## 📋 Explicación

Tu base de datos ya tiene migraciones aplicadas. Cuando intenté reorganizar el grafo de migraciones, Django detectó una inconsistencia entre:
- Lo que está en la tabla `django_migrations` de tu BD
- Lo que las migraciones actuales esperan

## ✅ SOLUCIÓN (Elige UNA opción)

### Opción 1: Fake Migration ⭐ RECOMENDADA

Esta es la más simple y segura. Solo actualiza el tracking sin tocar el schema:

```bash
# 1. Ver qué migraciones están aplicadas
python manage.py showmigrations importaciones

# 2. Sincronizar hasta 0036 (marca como aplicadas sin ejecutar)
python manage.py migrate importaciones 0036 --fake

# 3. Aplicar nuevas migraciones (0037 en adelante)
python manage.py migrate importaciones

# 4. Verificar
python manage.py test usuarios
python manage.py test importaciones
```

**¿Por qué funciona?**
- `--fake` le dice a Django "estas migraciones ya están aplicadas"
- No modifica el schema de la base de datos
- Solo actualiza la tabla `django_migrations`

### Opción 2: SQLite para Tests

Si solo tienes problemas con tests, usa SQLite:

```python
# En settings.py o crear settings_test.py
import sys

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
```

Luego ejecuta los tests normalmente:
```bash
python manage.py test
```

**Ventajas:**
- Tests más rápidos
- Sin conflictos de migraciones
- No afecta tu base de datos de desarrollo

### Opción 3: Reset de Base de Datos de Test

⚠️ Solo si las opciones anteriores no funcionan:

```bash
# Conectarse a MySQL
mysql -u root -p

# Eliminar y recrear
DROP DATABASE IF EXISTS test_semilla360;
CREATE DATABASE test_semilla360;
exit

# Aplicar todas las migraciones desde cero
python manage.py migrate

# Ejecutar tests
python manage.py test
```

## 🔍 Verificación

Después de aplicar cualquier opción:

```bash
# Ver estado de migraciones
python manage.py showmigrations importaciones

# Debe mostrar:
# [X] 0001_initial
# [X] 0002_tipodocumento_historicaltipodocumento
# [X] 0003_auto_20250603_1609
# [X] 0003_gastosextra
# ... etc (todas con [X])

# Ejecutar tests
python manage.py test usuarios
python manage.py test importaciones
```

## 📚 Archivos Relacionados

- `importaciones/migrations/0037_fix_inconsistent_history.py` - Esta solución documentada
- `importaciones/migrations/0036_fix_duplicate_migrations.py` - Fix anterior de columna duplicada
- `FIX_ROLES_PERMISOS.md` - Documentación de permisos

## ❓ Preguntas Frecuentes

**P: ¿El flag --fake es seguro?**
R: Sí, solo actualiza el tracking. No modifica tablas, columnas ni datos.

**P: ¿Qué pasa si uso la Opción 1 y sigo teniendo errores?**
R: Prueba la Opción 2 (SQLite) que aísla completamente el problema.

**P: ¿Por qué ocurrió esto?**
R: Las migraciones fueron creadas en branches paralelos y aplicadas en diferente orden.

**P: ¿La columna fecha_llegada existe?**
R: Sí, existe desde `0001_initial.py`. No se necesita agregar.

## 🎯 Resumen Ejecutivo

```bash
# Comando más simple (Opción 1):
python manage.py migrate importaciones 0036 --fake && python manage.py migrate importaciones && python manage.py test
```

## 📞 Si Nada Funciona

Comparte el output de estos comandos:

```bash
python manage.py showmigrations importaciones
python manage.py dbshell
> SELECT * FROM django_migrations WHERE app='importaciones' ORDER BY id;
> DESCRIBE importaciones_despacho;
> exit
```
