# Solución Completa a Conflictos de Migraciones - Django

## Problema Identificado

Error al ejecutar tests: `MySQLdb.OperationalError: (1060, "Duplicate column name 'fecha_llegada'")`

### Causa Raíz

El proyecto tenía múltiples ramas de migraciones paralelas (0003-0011 cada una con 2 archivos) causadas por desarrollo en branches de Git separados. El problema principal:

1. **Columna duplicada**: `fecha_llegada` ya existía en `0001_initial.py` pero `0002_despacho_fecha_llegada.py` intentaba agregarla nuevamente
2. **Referencias rotas**: `0003_gastosextra.py` dependía de la migración duplicada `0002_despacho_fecha_llegada`
3. **Ramas paralelas**: Múltiples migraciones con el mismo número (0003-0011)

## Solución Implementada

### 1. Eliminación de Migración Duplicada

- **Archivo**: `importaciones/migrations/0002_despacho_fecha_llegada.py`
- **Acción**: Eliminado completamente
- **Razón**: La columna `fecha_llegada` ya existe en `0001_initial.py`

### 2. Corrección de Dependencias

**`0003_gastosextra.py`**:
- **Antes**: Dependía de `0002_despacho_fecha_llegada` (eliminado)
- **Ahora**: Depende de `0002_tipodocumento_historicaltipodocumento`

### 3. Creación de Migración Merge

**`0005_merge_branches.py`** (nuevo):
- Merge las dos ramas de `0004`:
  - `0004_documento_content_type_documento_object_id_and_more.py`
  - `0004_rename_decripcion_gastosextra_descripcion.py`

### 4. Actualización de Dependencias Posteriores

**`0005_alter_ordencompradespacho_options_and_more.py`**:
- **Antes**: Dependía de `0004_rename_decripcion_gastosextra_descripcion`
- **Ahora**: Depende de `0005_merge_branches`

**`0005_remove_documento_declaracion_and_more.py`**:
- **Antes**: Dependía de `0004_documento_content_type_documento_object_id_and_more`
- **Ahora**: Depende de `0005_merge_branches`

### 5. Documentación del Fix

**`0036_fix_duplicate_migrations.py`** (actualizado):
- Documenta toda la solución
- Sin operaciones de base de datos (solo documentación)

## Estructura de Migraciones Corregida

```
0001_initial.py (incluye fecha_llegada en Despacho)
  └─ 0002_tipodocumento_historicaltipodocumento.py
       ├─ 0003_auto_20250603_1609.py
       │    └─ 0004_documento_content_type...py
       │         └─ 0005_merge_branches.py (MERGE)
       │              ├─ 0005_alter_ordencompradespacho...py
       │              └─ 0005_remove_documento_declaracion...py
       │                   └─ 0006... (continúa)
       │
       └─ 0003_gastosextra.py (CORREGIDO)
            └─ 0004_rename_decripcion...py
                 └─ 0005_merge_branches.py (MERGE)
                      (continúa arriba)

... más merges en 0013_merge_20250627_0250.py
... hasta 0036_fix_duplicate_migrations.py
```

## Cómo Aplicar la Solución

### Opción 1: Usar SQLite para Tests (Recomendado)

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

Luego ejecutar:
```bash
python manage.py test usuarios
python manage.py test importaciones
```

### Opción 2: Limpiar y Recrear Base de Datos MySQL

```bash
# 1. Eliminar base de datos de test
mysql -u root -p
DROP DATABASE IF EXISTS test_semilla360;
CREATE DATABASE test_semilla360;
exit

# 2. Aplicar migraciones desde cero
python manage.py migrate

# 3. Ejecutar tests
python manage.py test usuarios
python manage.py test importaciones
```

### Opción 3: Fake Migrations (Si la DB ya tiene los cambios)

```bash
# Si tu base de datos ya tiene todas las tablas/columnas correctas
python manage.py migrate importaciones --fake

# Ejecutar tests
python manage.py test
```

## Archivos Modificados

1. **Eliminado**: `importaciones/migrations/0002_despacho_fecha_llegada.py`
2. **Modificado**: `importaciones/migrations/0003_gastosextra.py` - Dependency corregida
3. **Nuevo**: `importaciones/migrations/0005_merge_branches.py` - Merge de ramas 0004
4. **Modificado**: `importaciones/migrations/0005_alter_ordencompradespacho_options_and_more.py` - Dependency actualizada
5. **Modificado**: `importaciones/migrations/0005_remove_documento_declaracion_and_more.py` - Dependency actualizada
6. **Modificado**: `importaciones/migrations/0036_fix_duplicate_migrations.py` - Documentación actualizada
7. **Modificado**: `.gitignore` - Agregado `*.py.bak`
8. **Modificado**: `SOLUCION_MIGRACIONES.md` - Esta documentación actualizada

## Verificación

Para verificar que las migraciones están correctas:

```bash
# Ver el grafo de migraciones
python manage.py showmigrations importaciones --plan

# Debería mostrar una secuencia lineal sin duplicados
# [X] importaciones.0001_initial
# [X] importaciones.0002_tipodocumento_historicaltipodocumento
# [X] importaciones.0003_auto_20250603_1609
# [X] importaciones.0003_gastosextra
# [X] importaciones.0004_documento_content_type...
# [X] importaciones.0004_rename_decripcion...
# [X] importaciones.0005_merge_branches
# ... etc
```

## Prevención de Futuros Conflictos

### Mejores Prácticas

1. **Sincronizar antes de crear migraciones**:
   ```bash
   git pull origin main
   python manage.py migrate
   python manage.py makemigrations
   ```

2. **Resolver conflictos inmediatamente**:
   ```bash
   # Si detectas migraciones paralelas
   python manage.py makemigrations --merge
   ```

3. **Usar settings separados para tests**:
   ```python
   # settings_test.py
   from .settings import *
   
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': ':memory:',
       }
   }
   ```

4. **Ejecutar tests con**:
   ```bash
   python manage.py test --settings=semilla360.settings_test
   ```

## Tests Después del Fix

Ejecutar para verificar que todo funciona:

```bash
# Tests de usuarios (permisos)
python manage.py test usuarios

# Tests de importaciones (migraciones corregidas)
python manage.py test importaciones

# Tests completos
python manage.py test
```

## Resumen

✅ **Migración duplicada eliminada**: `0002_despacho_fecha_llegada.py`
✅ **Dependencias corregidas**: `0003_gastosextra.py` actualizado
✅ **Merge creado**: `0005_merge_branches.py` une ramas paralelas
✅ **Dependencias actualizadas**: Dos migraciones `0005` ahora dependen del merge
✅ **Documentación completa**: Toda la solución documentada en código
✅ **Sin operaciones de DB**: Todos los cambios ya están en migraciones existentes

El sistema ahora tiene una estructura de migraciones limpia y sin conflictos.
