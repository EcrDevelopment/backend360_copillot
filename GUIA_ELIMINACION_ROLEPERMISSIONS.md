# Guía Completa: Eliminación de rolepermissions

## 📋 Resumen Ejecutivo

Esta guía detalla todos los archivos que contienen referencias a `django-role-permissions` y el orden prioritario para eliminarlas completamente del proyecto.

---

## ✅ Estado Actual (Commits ya realizados)

### Archivos YA Migrados a Sistema Nativo Django:

1. **`usuarios/serializers.py`** ✅ (Commit `421ed36`)
   - Eliminados imports no usados
   - `CustomTokenObtainPairSerializer` usa `user.groups` y `user.get_all_permissions()`

2. **`usuarios/views.py`** ✅ (Commit `fda672b`)
   - Eliminado `from rolepermissions.checkers import has_role`
   - Usa `user.groups.filter(name='SystemAdmin').exists()`

3. **`requirements.txt`** ✅ (Commit `413c432`)
   - Removida línea `django-role-permissions`

---

## 🔴 PRIORIDAD CRÍTICA - Archivos que DEBEN modificarse

### 1. **`usuarios/permissions.py`** - PRIORIDAD MÁXIMA ⚠️

**Estado:** ❌ Usa rolepermissions extensivamente  
**Líneas afectadas:** 7, 20, 34, 48, 62, 78, 79, 94, 95, 111, 127, 128, 167, 168, 188-191, 211, 212

**Imports a eliminar:**
```python
from rolepermissions.checkers import has_role, has_permission
```

**Funciones a reemplazar:**
- `has_role(request.user, 'system_admin')` → `request.user.groups.filter(name='SystemAdmin').exists()`
- `has_permission(request.user, 'importaciones.ver_modulo')` → `request.user.has_perm('usuarios.importaciones_ver_modulo')`

**Clases afectadas:**
- `IsSystemAdmin`
- `IsAccountsAdmin`
- `IsImportacionesAdmin`
- `IsAlmacenAdmin`
- `CanManageUsers`
- `CanAccessImportaciones`
- `CanAccessAlmacen`
- `IsOwnerOrAdmin`
- `CanEditDocuments`
- `CanDeleteResource`
- `HasModulePermission`

**Solución:** Refactorizar cada clase para usar:
```python
# En lugar de has_role
request.user.groups.filter(name='SystemAdmin').exists()

# En lugar de has_permission
request.user.has_perm('usuarios.permission_codename')
```

---

### 2. **`usuarios/roles.py`** - PRIORIDAD ALTA ⚠️

**Estado:** ❌ Define roles usando AbstractUserRole de rolepermissions  
**Líneas afectadas:** 2, y todas las clases (SystemAdmin, ImportacionesAdmin, etc.)

**Import a eliminar:**
```python
from rolepermissions.roles import AbstractUserRole
```

**Solución:**
- **OPCIÓN A (RECOMENDADA):** Eliminar completamente este archivo
  - Los grupos ya se crean en `setup_roles.py`
  - Este archivo ya NO es necesario con sistema nativo Django
  
- **OPCIÓN B:** Mantenerlo como documentación
  - Comentar todo el código
  - Agregar nota que indica que ahora se usa `setup_roles.py`

**Acción:** ❌ **ELIMINAR ARCHIVO** `usuarios/roles.py`

---

### 3. **`SECURITY_SETTINGS.py`** - PRIORIDAD MEDIA

**Estado:** ❌ Contiene configuración de rolepermissions  
**Líneas afectadas:** Líneas con ROLEPERMISSIONS_MODULE y ROLEPERMISSIONS_REGISTER_ADMIN

**Settings a eliminar:**
```python
ROLEPERMISSIONS_MODULE = 'usuarios.roles'
ROLEPERMISSIONS_REGISTER_ADMIN = True
```

**Solución:** Eliminar estas 2 líneas del archivo

---

## 🟡 PRIORIDAD BAJA - Archivos de documentación/migración

### 4. **`migrate_to_native_auth.py`** - MANTENER TEMPORALMENTE

**Estado:** ⚠️ Script de migración (contiene imports de rolepermissions para propósito de migración)  
**Líneas afectadas:** 1, y referencias en prints

**Acción:**
- ✅ **MANTENER** temporalmente para usuarios que necesiten migrar
- Agregar comentario indicando que es solo para migración única
- Después de ejecutar en producción, puede eliminarse

---

### 5. **Archivos de Documentación** - ACTUALIZAR

**Archivos:**
- `FIX_ROLES_PERMISOS.md`
- `REFACTORING_NATIVE_AUTH.md`
- `RESUMEN_MEJORAS.md`

**Acción:**
- ✅ Actualizar ejemplos para mostrar sistema nativo Django
- Mantener sección "antes/después" para referencia histórica

---

## 📋 Plan de Acción Ordenado por Prioridad

### Fase 1: Eliminación de Código Activo (CRÍTICO)

1. **Step 1:** Refactorizar `usuarios/permissions.py`
   - Reemplazar todos los `has_role` con `user.groups.filter(name='...').exists()`
   - Reemplazar todos los `has_permission` con `user.has_perm('...')`
   - Eliminar imports de rolepermissions

2. **Step 2:** Eliminar `usuarios/roles.py`
   - Ya no se necesita con sistema nativo
   - Los grupos se crean en `setup_roles.py`

3. **Step 3:** Actualizar `SECURITY_SETTINGS.py`
   - Eliminar `ROLEPERMISSIONS_MODULE`
   - Eliminar `ROLEPERMISSIONS_REGISTER_ADMIN`

### Fase 2: Limpieza de INSTALLED_APPS

4. **Step 4:** Verificar y remover de settings
   - Buscar `'rolepermissions'` en INSTALLED_APPS
   - Eliminarlo si existe

### Fase 3: Limpieza de Documentación (OPCIONAL)

5. **Step 5:** Actualizar documentación
   - Actualizar ejemplos en archivos .md
   - Mantener referencia histórica si se desea

---

## 🔍 Comandos de Verificación

### Verificar que no quedan referencias:

```bash
# Buscar en archivos Python
grep -r "rolepermissions" --include="*.py" . | grep -v "migrate_to_native_auth.py"

# Buscar en configuración
grep -r "ROLEPERMISSIONS" --include="*.py" .

# Verificar imports específicos
grep -r "from rolepermissions" --include="*.py" .
grep -r "import rolepermissions" --include="*.py" .
```

### Después de los cambios, estos comandos NO deben retornar resultados (excepto migrate_to_native_auth.py).

---

## 📝 Mapeo de Conversiones

### Conversión de has_role:

```python
# ANTES (rolepermissions)
has_role(request.user, 'system_admin')
has_role(request.user, 'accounts_admin')
has_role(request.user, 'importaciones_admin')
has_role(request.user, 'almacen_admin')

# DESPUÉS (Django nativo)
request.user.groups.filter(name='SystemAdmin').exists()
request.user.groups.filter(name='AccountsAdmin').exists()
request.user.groups.filter(name='ImportacionesAdmin').exists()
request.user.groups.filter(name='AlmacenAdmin').exists()
```

### Conversión de has_permission:

```python
# ANTES (rolepermissions)
has_permission(request.user, 'importaciones.ver_modulo')
has_permission(request.user, 'almacen.ver_modulo')

# DESPUÉS (Django nativo)
request.user.has_perm('usuarios.importaciones_ver_modulo')
request.user.has_perm('usuarios.almacen_ver_modulo')
```

**NOTA:** Los permisos en Django usan el formato: `app_label.codename`

---

## ⚡ Resumen de Prioridades

| Prioridad | Archivo | Acción | Estado |
|-----------|---------|--------|--------|
| 🔴 CRÍTICA | `usuarios/permissions.py` | Refactorizar | ❌ Pendiente |
| 🔴 CRÍTICA | `usuarios/roles.py` | Eliminar | ❌ Pendiente |
| 🟡 MEDIA | `SECURITY_SETTINGS.py` | Eliminar 2 líneas | ❌ Pendiente |
| 🟢 BAJA | `migrate_to_native_auth.py` | Mantener temporalmente | ✅ OK |
| 🟢 BAJA | Documentación (.md files) | Actualizar ejemplos | ⚠️ Opcional |

---

## ✅ Checklist Final

Después de completar todos los cambios, verificar:

- [ ] `usuarios/permissions.py` no tiene imports de rolepermissions
- [ ] `usuarios/roles.py` ha sido eliminado
- [ ] `SECURITY_SETTINGS.py` no tiene ROLEPERMISSIONS_*
- [ ] `grep -r "from rolepermissions" --include="*.py" .` solo retorna migrate_to_native_auth.py
- [ ] Ejecutar `python manage.py check` sin errores
- [ ] Ejecutar tests: `python manage.py test usuarios`
- [ ] Verificar login y permisos en el sistema

---

## 📚 Documentos de Referencia

- **REFACTORING_NATIVE_AUTH.md** - Guía completa del refactoring
- **migrate_to_native_auth.py** - Script de migración de datos
- **setup_roles.py** - Comando para crear grupos y permisos

---

**Autor:** GitHub Copilot  
**Fecha:** 2025-12-30  
**Versión:** 1.0
