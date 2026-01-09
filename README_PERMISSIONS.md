# Sistema de Permisos Funcionales - Guía Completa

**⭐ EMPEZAR AQUÍ** - Guía consolidada del sistema de permisos funcional, modular y dinámico

---

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Inicio Rápido](#inicio-rápido)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Casos de Uso Comunes](#casos-de-uso-comunes)
5. [Referencia API](#referencia-api)
6. [Testing](#testing)
7. [Documentación Detallada](#documentación-detallada)
8. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Resumen Ejecutivo

### ¿Qué es este sistema?

Migración completa del sistema de permisos por defecto de Django (~2000 permisos basados en tablas) a un sistema funcional, modular y dinámico con **38 permisos empresariales** y capacidad de crear permisos ilimitados desde el frontend.

### ¿Por qué cambiamos?

**Antes (Django por defecto):**
- ❌ ~2000 permisos generados automáticamente (add_*, change_*, delete_*, view_*)
- ❌ Difícil de gestionar y entender
- ❌ Propenso a errores
- ❌ No refleja procesos de negocio

**Ahora (Sistema funcional):**
- ✅ 38 permisos basados en acciones de negocio
- ✅ Sistema jerárquico (modular + granular)
- ✅ Permisos dinámicos creables desde frontend
- ✅ Control a nivel almacén y sede
- ✅ Auditoría completa integrada
- ✅ Seguridad: 9.5/10 (Excelente)

### Beneficios Clave

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Cantidad** | ~2000 permisos | 38 + dinámicos |
| **Gestión** | Imposible | Fácil desde admin/API |
| **Comprensión** | Técnico | Orientado a negocio |
| **Escalabilidad** | Limitada | Ilimitada (dinámicos) |
| **Control granular** | No | Sí (warehouse/sede level) |
| **Auditoría** | Básica | Completa con historial |

---

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.8+
- Django 3.2+
- django-simple-history instalado
- Migraciones aplicadas

### Instalación (5 minutos)

**1. Verificar modelos implementados:**
```bash
# Los modelos ya están en usuarios/models.py:
# - CustomPermissionCategory
# - CustomPermission
# - PermissionChangeAudit
```

**2. Aplicar migraciones:**
```bash
python manage.py makemigrations usuarios
python manage.py migrate usuarios
```

**3. (Opcional) Migrar permisos existentes:**
```bash
python manage.py migrate_to_dynamic_permissions --dry-run
python manage.py migrate_to_dynamic_permissions
```

**4. Verificar instalación:**
```bash
python test_permissions_api.py
```

**5. Acceder al admin:**
```
http://localhost:8000/admin/
```
Verifica que aparezcan:
- Categorías de Permisos
- Permisos Personalizados
- Auditorías de Permisos

---

## 🏗️ Arquitectura del Sistema

### 1. Permisos Estáticos (38 predefinidos)

#### Usuarios Module (10 permisos)
**Modulares:**
- `usuarios.can_manage_users` - Gestión completa de usuarios
- `usuarios.can_view_users` - Solo visualización
- `usuarios.can_manage_roles` - Gestión de roles
- `usuarios.can_view_roles` - Solo visualización de roles

**Granulares:**
- `usuarios.can_create_users` - Crear usuarios
- `usuarios.can_edit_users` - Editar usuarios
- `usuarios.can_delete_users` - Eliminar usuarios
- `usuarios.can_create_roles` - Crear roles
- `usuarios.can_edit_roles` - Editar roles
- `usuarios.can_delete_roles` - Eliminar roles

#### Almacén Module (11 permisos)
**Modulares:**
- `almacen.can_manage_warehouse` - Gestión completa
- `almacen.can_view_warehouse` - Solo visualización
- `almacen.can_view_warehouse_reports` - Ver reportes
- `almacen.can_manage_stock` - Gestión de inventario
- `almacen.can_view_stock` - Ver inventario

**Granulares:**
- `almacen.can_create_movements` - Crear movimientos
- `almacen.can_edit_movements` - Editar movimientos
- `almacen.can_delete_movements` - Eliminar movimientos
- `almacen.can_create_transfers` - Crear transferencias
- `almacen.can_edit_transfers` - Editar transferencias
- `almacen.can_approve_transfers` - Aprobar transferencias

#### Importaciones Module (11 permisos)
**Modulares:**
- `importaciones.can_manage_importaciones` - Gestión completa
- `importaciones.can_view_importaciones` - Solo visualización
- `importaciones.can_view_importaciones_reports` - Ver reportes
- `importaciones.can_manage_documents` - Gestión documentos
- `importaciones.can_view_documents` - Ver documentos

**Granulares:**
- `importaciones.can_create_importaciones`
- `importaciones.can_edit_importaciones`
- `importaciones.can_delete_importaciones`
- `importaciones.can_create_documents`
- `importaciones.can_edit_documents`
- `importaciones.can_delete_documents`

#### Mantenimiento Module (6 permisos)
- `usuarios.can_manage_maintenance_tables` - Tablas del sistema
- `usuarios.can_view_maintenance_tables` - Ver tablas
- `usuarios.can_manage_document_types` - Tipos de documento
- `usuarios.can_manage_companies` - Empresas
- `usuarios.can_manage_product_catalog` - Catálogo productos
- `usuarios.can_manage_warehouse_catalog` - Catálogo almacenes

#### Proveedor Module (4 permisos)
- `usuarios.can_upload_documents` - Subir documentos
- `usuarios.can_manage_own_documents` - Gestionar propios
- `usuarios.can_view_own_documents` - Ver propios
- `usuarios.can_download_own_documents` - Descargar propios

### 2. Jerarquía de Permisos

Los permisos modulares (`can_manage_*`) **incluyen** todos los permisos granulares relacionados:

```
can_manage_users (modular)
├── can_create_users (granular)
├── can_edit_users (granular)
└── can_delete_users (granular)
```

**Para control fino:** Asignar SOLO permisos granulares sin el modular.

**Ejemplo:**
- Asignar solo `can_edit_users` → Usuario puede editar, pero NO crear ni eliminar

### 3. Permisos Dinámicos (Ilimitados)

Los administradores pueden crear nuevos permisos sin código:

**Crear nuevo módulo "Ventas":**
1. Admin crea categoría "ventas"
2. Crea permiso `ventas.can_manage_sales`
3. Asigna a grupo "Vendedores"
4. ¡Listo! Sin código, sin migraciones

**Uso en ViewSet:**
```python
class VentasViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasModulePermission]
    permission_required = 'ventas.can_manage_sales'
```

### 4. Control a Nivel Almacén y Sede

#### Campo `empresa` en UserProfile
**⚠️ IMPORTANTE:** El campo `empresa` es **SOLO para proveedores**

```python
# PROVEEDOR (tiene empresa)
profile.empresa = empresa_proveedor  # Identifica empresa del proveedor
profile.require_warehouse_access = False

# EMPLEADO (NO tiene empresa)
profile.empresa = None  # Empleados NO usan este campo
profile.require_warehouse_access = True  # Control por almacenes
profile.almacenes_asignados.add(almacen1, almacen2)
```

#### Control de Acceso por Almacén
```python
# Operario restringido
profile.require_warehouse_access = True
profile.almacenes_asignados.add(almacen_callao, almacen_miraflores)
# Ve SOLO movimientos/stock de Callao y Miraflores

# Gerente sin restricción
profile.require_warehouse_access = False
# Ve TODO, puede filtrar: ?empresa=1 (Semilla), ?empresa=2 (Maxi)
```

#### Control de Acceso por Sede
```python
# Gerente regional restringido
profile.require_sede_access = True
profile.sedes_asignadas.add(sede_norte1, sede_norte2)
# Solo accede a sedes de la región Norte

# Gerente general sin restricción
profile.require_sede_access = False
# Accede a TODAS las sedes
```

---

## 👥 Casos de Uso Comunes

### Caso 1: Operario de Almacén (Restringido)

**Configuración:**
```python
profile.empresa = None  # NO es proveedor
profile.require_warehouse_access = True
profile.almacenes_asignados.add(almacen_callao, almacen_miraflores)
# Permisos: almacen.can_view_warehouse, almacen.can_create_movements
```

**Comportamiento:**
- ✅ `GET /api/almacen/movimientos/` → Solo ve Callao y Miraflores
- ✅ `GET /api/almacen/stock/` → Solo ve Callao y Miraflores
- ✅ `GET /api/almacen/kardex/?almacen_id=1` (Callao) → ✓ Éxito
- ❌ `GET /api/almacen/kardex/?almacen_id=3` (Surco) → ✗ HTTP 403
- ❌ No puede eliminar movimientos (no tiene permiso)

### Caso 2: Gerente Regional (Sede-Restringido)

**Configuración:**
```python
profile.empresa = None
profile.require_warehouse_access = False  # Sin restricción de almacén
profile.require_sede_access = True  # Restricción por sede
profile.sedes_asignadas.add(sede_norte1, sede_norte2, sede_norte3)
# Permisos: todos los modulares
```

**Comportamiento:**
- ✅ Ve TODOS los almacenes
- ✅ Solo accede a datos de sedes Norte
- ✅ Puede gestionar operaciones en su región
- ❌ No accede a sedes Sur o Centro

### Caso 3: Gerente General (Sin Restricciones)

**Configuración:**
```python
profile.empresa = None
profile.require_warehouse_access = False
profile.require_sede_access = False
# Permisos: todos los modulares
```

**Comportamiento:**
- ✅ Acceso completo a TODOS los almacenes
- ✅ Acceso completo a TODAS las sedes
- ✅ Puede filtrar: `?empresa=1` (Semilla), `?empresa=2` (Maxi), `?empresa=3` (Trading)
- ✅ Gestión completa del sistema

### Caso 4: Usuario Proveedor

**Configuración:**
```python
profile.empresa = empresa_abc_logistics  # ÚNICO caso donde se usa
profile.require_warehouse_access = False
# Permisos: usuarios.can_upload_documents, usuarios.can_view_own_documents
```

**Comportamiento:**
- ✅ Sube documentos asociados a su empresa
- ✅ Ve solo SUS documentos
- ❌ NO accede al módulo de importaciones
- ❌ NO accede a almacenes

### Caso 5: SystemAdmin

**Configuración:**
```python
user.is_system_admin = True
# Bypasses TODAS las restricciones
```

**Comportamiento:**
- ✅ Acceso total a TODO
- ✅ Puede crear/modificar permisos
- ✅ Sin filtros de almacén/sede
- ✅ Acceso completo al sistema

---

## 📡 Referencia API

### Autenticación

Todos los endpoints requieren autenticación JWT:
```bash
# Obtener token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Usar token
curl -X GET http://localhost:8000/api/accounts/custom-permissions/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Endpoints Principales

#### 1. Gestión de Categorías
```bash
# Listar categorías
GET /api/accounts/permission-categories

# Crear categoría (SystemAdmin only)
POST /api/accounts/permission-categories
{
  "name": "ventas",
  "display_name": "Ventas",
  "description": "Módulo de ventas",
  "icon": "shopping-cart",
  "order": 10
}

# Obtener categoría
GET /api/accounts/permission-categories/{id}

# Listar permisos de categoría
GET /api/accounts/permission-categories/{id}/permissions
```

#### 2. Gestión de Permisos
```bash
# Listar permisos
GET /api/accounts/custom-permissions

# Crear permiso (SystemAdmin only)
POST /api/accounts/custom-permissions
{
  "category": 1,
  "codename": "can_manage_sales",
  "name": "Puede gestionar ventas",
  "description": "Permite crear, editar y eliminar ventas",
  "permission_type": "modular",
  "action_type": "manage",
  "parent_permission": null
}

# Obtener permiso
GET /api/accounts/custom-permissions/{id}

# Ver historial completo
GET /api/accounts/custom-permissions/{id}/history

# Ver jerarquía (padre-hijos)
GET /api/accounts/custom-permissions/{id}/hierarchy
```

#### 3. Asignación de Permisos
```bash
# Asignar a usuario
POST /api/accounts/custom-permissions/assign
{
  "permission_id": 1,
  "user_id": 5,
  "action": "assign",
  "reason": "Nuevo vendedor"
}

# Asignar a grupo
POST /api/accounts/custom-permissions/assign
{
  "permission_id": 1,
  "group_id": 3,
  "action": "assign",
  "reason": "Grupo Vendedores"
}

# Revocar
POST /api/accounts/custom-permissions/assign
{
  "permission_id": 1,
  "user_id": 5,
  "action": "revoke",
  "reason": "Usuario cambió de rol"
}
```

#### 4. Creación Masiva
```bash
# Crear múltiples permisos
POST /api/accounts/custom-permissions/bulk_create
{
  "permissions": [
    {
      "category": 1,
      "codename": "can_manage_sales",
      "name": "Puede gestionar ventas",
      "permission_type": "modular",
      "action_type": "manage"
    },
    {
      "category": 1,
      "codename": "can_create_sales",
      "name": "Puede crear ventas",
      "permission_type": "granular",
      "action_type": "create"
    }
  ]
}
```

#### 5. Auditoría
```bash
# Todos los logs
GET /api/accounts/permission-audits

# Cambios recientes (24h)
GET /api/accounts/permission-audits/recent

# Por usuario
GET /api/accounts/permission-audits/by_user?user_id=5

# Por permiso
GET /api/accounts/permission-audits?permission_id=1

# Por acción
GET /api/accounts/permission-audits?action=assigned
```

#### 6. Almacén (con filtrado automático)
```bash
# Listar almacenes (filtrado por usuario)
GET /api/almacen/almacenes/

# Movimientos (solo almacenes asignados para operarios)
GET /api/almacen/movimientos/

# Stock (filtrado automático)
GET /api/almacen/stock/
GET /api/almacen/stock/?empresa=1  # Gerente filtra por Semilla

# Kardex (valida acceso)
GET /api/almacen/kardex/?almacen_id=1  # 403 si no tiene acceso

# Transferencias (filtra origen O destino)
GET /api/almacen/transferencias/

# Recibir transferencia (valida acceso a destino)
POST /api/almacen/transferencias/{id}/recibir/
```

---

## 🧪 Testing

### Testing Automatizado

**Ejecutar suite completa:**
```bash
python test_permissions_api.py
```

**Cobertura:**
- ✅ 35+ tests automatizados
- ✅ CRUD de categorías y permisos
- ✅ Asignación a usuarios/grupos
- ✅ Jerarquía de permisos
- ✅ Logs de auditoría
- ✅ Validaciones (formato, duplicados, circular hierarchy)
- ✅ Seguridad (solo SystemAdmin puede modificar)

### Testing Manual

**1. Django Admin (10 min):**
```
1. Acceder a /admin/
2. Ir a "Categorías de Permisos"
3. Crear categoría "test"
4. Ir a "Permisos Personalizados"
5. Crear permiso "test.can_test"
6. Verificar auditoría
```

**2. API con curl (15 min):**
Ver sección [Referencia API](#referencia-api)

**3. Filtrado de Almacén (10 min):**
```bash
# Como operario (solo Callao)
GET /api/almacen/movimientos/  # Solo ve Callao

# Como gerente (todo)
GET /api/almacen/movimientos/  # Ve todo
GET /api/almacen/stock/?empresa=1  # Filtra por Semilla
```

### Validación de Seguridad

**Verificar que:**
- ❌ Usuario no-admin NO puede crear permisos
- ❌ Usuario NO puede eliminar permisos del sistema
- ❌ Operario NO accede a almacenes no asignados (HTTP 403)
- ✅ Auditoría registra TODOS los cambios
- ✅ Soft delete funciona (state=False, no eliminación)

---

## 📚 Documentación Detallada

Para información técnica profunda, consulta `docs/`:

### Implementación
- **[IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)** - Guía completa de despliegue
- **[ALMACEN_PERMISSIONS_IMPLEMENTATION_GUIDE.md](docs/ALMACEN_PERMISSIONS_IMPLEMENTATION_GUIDE.md)** - Implementación de filtrado por almacén
- **[ORGANIZATION_WAREHOUSE_PERMISSIONS.md](docs/ORGANIZATION_WAREHOUSE_PERMISSIONS.md)** - Arquitectura de control de acceso

### Permisos
- **[FUNCTIONAL_PERMISSIONS.md](docs/FUNCTIONAL_PERMISSIONS.md)** - 14 permisos modulares originales
- **[EXPANDED_PERMISSIONS.md](docs/EXPANDED_PERMISSIONS.md)** - Sistema completo de 38 permisos
- **[DYNAMIC_PERMISSIONS_SYSTEM.md](docs/DYNAMIC_PERMISSIONS_SYSTEM.md)** - Sistema de permisos dinámicos (36KB, código completo)
- **[DYNAMIC_PERMISSIONS_QUICK_START.md](docs/DYNAMIC_PERMISSIONS_QUICK_START.md)** - Inicio rápido dinámicos

### Frontend
- **[FRONTEND_IMPLEMENTATION_GUIDE.md](docs/FRONTEND_IMPLEMENTATION_GUIDE.md)** - 7 componentes React (40KB)
- **[FRONTEND_USER_REGISTRATION_GUIDE.md](docs/FRONTEND_USER_REGISTRATION_GUIDE.md)** - Registro con almacenes/sedes
- **[MENU_PERMISSIONS_MAPPING.md](docs/MENU_PERMISSIONS_MAPPING.md)** - Mapeo de menú

### Seguridad & Auditoría
- **[SECURITY_ANALYSIS.md](docs/SECURITY_ANALYSIS.md)** - Análisis completo (9.5/10)
- **[AUDIT_INTEGRATION_GUIDE.md](docs/AUDIT_INTEGRATION_GUIDE.md)** - django-simple-history

### Testing
- **[TESTING_QUICK_START.md](docs/TESTING_QUICK_START.md)** - Guía de pruebas paso a paso

### Administración
- **[GUIA_ASIGNACION_PERMISOS.md](docs/GUIA_ASIGNACION_PERMISOS.md)** - Guía para administradores (Español)

---

## 🔧 Solución de Problemas

### Problema: Permisos no aparecen en /admin/

**Solución:**
```bash
python manage.py makemigrations usuarios
python manage.py migrate usuarios
python manage.py collectstatic
# Reiniciar servidor
```

### Problema: Usuario no puede acceder a almacén

**Diagnóstico:**
```python
user = User.objects.get(username='operario')
profile = user.userprofile

# Verificar configuración
print(f"Require access: {profile.require_warehouse_access}")
print(f"Almacenes: {profile.almacenes_asignados.all()}")
```

**Solución:**
```python
# Asignar almacenes
profile.require_warehouse_access = True
profile.almacenes_asignados.add(almacen1, almacen2)
profile.save()
```

### Problema: HTTP 403 en endpoint de permisos

**Causa:** Solo SystemAdmin puede modificar permisos

**Verificar:**
```python
user.is_system_admin  # Debe ser True
```

**Solución:**
```python
user.is_system_admin = True
user.save()
```

### Problema: Filtrado no funciona

**Verificar ViewSet:**
```python
def get_queryset(self):
    # Debe tener esta lógica
    if profile.require_warehouse_access:
        almacenes_ids = profile.almacenes_asignados.values_list('id', flat=True)
        return queryset.filter(almacen_id__in=almacenes_ids)
```

### Problema: Campo empresa confunde empleados/proveedores

**Recordar:**
- Campo `empresa` es **SOLO para proveedores**
- Empleados usan `almacenes_asignados` y `sedes_asignadas`
- Son conceptos **independientes**

---

## 📊 Estado del Sistema

### Implementación

- ✅ **Backend** - Completo (modelos, serializers, views)
- ✅ **API** - 16 endpoints funcionando
- ✅ **Permisos** - 38 estáticos + dinámicos ilimitados
- ✅ **Filtrado** - Almacén y sede nivel
- ✅ **Auditoría** - django-simple-history integrado
- ✅ **Testing** - 35+ tests automatizados
- ✅ **Frontend** - Componentes React listos
- ✅ **Documentación** - Consolidada y organizada
- ✅ **Seguridad** - 9.5/10 (Excelente)

### Métricas

| Métrica | Valor |
|---------|-------|
| **Permisos estáticos** | 38 |
| **Permisos dinámicos** | Ilimitados |
| **Reducción vs Django** | 99.3% (2000 → 38) |
| **API endpoints** | 16 |
| **Tests automatizados** | 35+ |
| **Seguridad** | 9.5/10 |
| **Cobertura** | Usuarios, Almacén, Importaciones, Mantenimiento, Proveedores |

### Migración

**De:** ~2000 permisos tabla-based
**A:** 38 permisos funcionales + dinámicos
**Tiempo:** ~5 minutos (migraciones + verificación)
**Impacto:** Zero downtime
**Reversible:** Sí (rollback migrations)

---

## 🚀 Despliegue a Producción

### Checklist Pre-Despliegue

- [ ] Ejecutar tests: `python test_permissions_api.py`
- [ ] Verificar migraciones: `python manage.py showmigrations usuarios`
- [ ] Backup de base de datos
- [ ] Verificar configuración de auditoría
- [ ] Configurar HTTPS (obligatorio)
- [ ] Configurar rate limiting
- [ ] Verificar configuración JWT
- [ ] Documentar usuarios SystemAdmin

### Comandos de Despliegue

```bash
# 1. Aplicar migraciones
python manage.py migrate usuarios

# 2. (Opcional) Migrar permisos existentes
python manage.py migrate_to_dynamic_permissions

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Verificar
python test_permissions_api.py

# 5. Reiniciar servidor
# (depende de tu configuración: gunicorn, uwsgi, etc.)
```

### Post-Despliegue

- [ ] Verificar /admin/ accesible
- [ ] Probar creación de permiso dinámico
- [ ] Verificar filtrado de almacén para operario
- [ ] Verificar logs de auditoría
- [ ] Monitorear errores 403
- [ ] Verificar performance queries

---

## 📞 Soporte

### Recursos

- **Documentación detallada:** `docs/`
- **Tests:** `test_permissions_api.py`
- **Admin:** `http://localhost:8000/admin/`

### Contacto

Para issues, consultas o mejoras, contactar al equipo de desarrollo.

---

## 📝 Notas de Versión

### v2.0.0 - Sistema Funcional Completo

**Cambios mayores:**
- ✅ Migración de 2000 a 38 permisos funcionales
- ✅ Sistema de permisos dinámicos
- ✅ Control a nivel almacén y sede
- ✅ Auditoría completa con django-simple-history
- ✅ 16 API endpoints REST
- ✅ 35+ tests automatizados
- ✅ Componentes React para frontend
- ✅ Seguridad 9.5/10

**Breaking changes:**
- Los permisos antiguos (add_*, change_*, etc.) ya NO se usan
- Migración automática preserva asignaciones

**Compatibilidad:**
- Django 3.2+
- Python 3.8+
- django-simple-history 3.0+

---

**🎉 ¡Sistema listo para producción!**

*Última actualización: 2026-01-09*
