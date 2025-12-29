# Solución a Conflictos de Migraciones - Django

## Problema Identificado

Error al ejecutar tests: `MySQLdb.OperationalError: (1060, "Duplicate column name 'fecha_llegada'")`

### Causa Raíz

La columna `fecha_llegada` está siendo agregada dos veces en las migraciones de la app `importaciones`:

1. **0001_initial.py** (línea ~175): Ya incluye `fecha_llegada` en el modelo Despacho
2. **0002_despacho_fecha_llegada.py**: Intenta agregar la misma columna nuevamente

Además, hay múltiples migraciones con números duplicados (0002-0011 tienen 2 archivos cada uno), lo que indica que se crearon migraciones en branches paralelos.

## Solución Implementada

### 1. Migración Duplicada Removida

- **Archivo**: `importaciones/migrations/0002_despacho_fecha_llegada.py`
- **Acción**: Renombrado a `.py.bak` para desactivarlo sin eliminarlo
- **Razón**: La columna ya existe en 0001_initial.py

### 2. Migración de Fix Creada

- **Archivo**: `importaciones/migrations/0036_fix_duplicate_migrations.py`
- **Propósito**: Migración vacía para marcar la resolución del conflicto
- **Contenido**: No ejecuta operaciones, solo documenta la solución

### 3. .gitignore Actualizado

- Agregado `*.py.bak` para no versionar archivos de backup

## Cómo Aplicar la Solución

### Opción 1: Para Tests (Recomendado)

Usar SQLite en memoria para tests evita conflictos con la base de datos de desarrollo:

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
```

### Opción 2: Limpiar Base de Datos de Test

Si prefieres seguir usando MySQL para tests:

```bash
# 1. Eliminar base de datos de test
mysql -u root -p
DROP DATABASE IF EXISTS test_semilla360;
CREATE DATABASE test_semilla360;
exit

# 2. Ejecutar migraciones
python manage.py migrate

# 3. Ejecutar tests
python manage.py test usuarios
```

### Opción 3: Fake Initial (Si hay problemas persistentes)

```bash
# Marcar migraciones como aplicadas sin ejecutarlas
python manage.py migrate --fake-initial

# Luego ejecutar tests
python manage.py test usuarios
```

## Verificación

Para verificar que las migraciones están correctas:

```bash
# Ver estado de migraciones
python manage.py showmigrations importaciones

# Debería mostrar algo como:
# [X] 0001_initial
# [X] 0002_tipodocumento_historicaltipodocumento
# [X] 0003_auto_20250603_1609
# ... (sin 0002_despacho_fecha_llegada)
```

## Prevención de Futuros Conflictos

### Mejores Prácticas

1. **Antes de crear migraciones**:
   ```bash
   git pull origin main
   python manage.py migrate
   python manage.py makemigrations
   ```

2. **Resolver conflictos de migraciones**:
   ```bash
   # Si hay conflictos, crear una migración merge
   python manage.py makemigrations --merge
   ```

3. **Usar settings separados para tests**:
   - `settings.py` - producción/desarrollo
   - `settings_test.py` - tests con SQLite

4. **Coordinar con el equipo**:
   - Comunicar cuando se crean migraciones
   - Revisar migraciones en PRs antes de merge

## Archivos Modificados

- `importaciones/migrations/0036_fix_duplicate_migrations.py` - Nueva migración de fix
- `importaciones/migrations/0002_despacho_fecha_llegada.py.bak` - Backup de migración duplicada
- `.gitignore` - Agregado `*.py.bak`
- `SOLUCION_MIGRACIONES.md` - Esta documentación

## Notas Adicionales

- El archivo `.bak` se mantiene para referencia histórica
- La migración 0036 documenta la solución sin ejecutar cambios
- Los otros conflictos de numeración (0002-0011) ya fueron resueltos por 0013_merge_20250627_0250.py
- La columna `fecha_llegada` en el modelo Despacho permanece intacta

## Tests Relacionados

Después de aplicar la solución, ejecutar:

```bash
# Test específico de usuarios
python manage.py test usuarios

# Test de importaciones
python manage.py test importaciones

# Tests completos
python manage.py test
```
