# Guía Rápida: Implementación del Sistema Dinámico

## Pasos de Implementación

### Paso 1: Crear los Modelos (Backend)

Agregar a `usuarios/models.py`:
- `CustomPermissionCategory` - Para organizar permisos por módulo
- `CustomPermission` - Para almacenar permisos personalizados

### Paso 2: Crear Migraciones

```bash
python manage.py makemigrations usuarios
python manage.py migrate usuarios
```

### Paso 3: Poblar Permisos Existentes

```bash
python manage.py migrate_to_dynamic_permissions
```

Este comando migrará los 38 permisos actuales al sistema dinámico.

### Paso 4: Configurar URLs

Agregar a `usuarios/urls.py`:
```python
router.register(r'custom-permissions', CustomPermissionViewSet)
router.register(r'permission-categories', CustomPermissionCategoryViewSet)
```

### Paso 5: Implementar UI Frontend

Crear página de administración en:
`/admin/permissions`

Solo accesible para SystemAdmin.

## Flujo de Creación de Permisos

### Para Administrador:

1. **Acceder a** `/admin/permissions`
2. **Click** "Nuevo Permiso"
3. **Completar formulario**:
   - Categoría: (ej: ventas, finanzas, etc.)
   - Código: `can_manage_sales`
   - Nombre: "Puede gestionar ventas"
   - Tipo: Modular o Granular
   - Acción: Gestionar, Ver, Crear, Editar, etc.
4. **Guardar**

El permiso estará inmediatamente disponible para asignar a usuarios/grupos.

### Automáticamente:

- Se crea en `django.contrib.auth.models.Permission`
- Aparece en `/api/accounts/permisos`
- Se puede asignar a usuarios y grupos
- Se valida en ViewSets con `HasModulePermission`

## Ejemplo de Uso

### Crear Nuevo Módulo "Ventas"

1. **Crear Categoría**:
   ```json
   POST /api/accounts/permission-categories/
   {
     "name": "ventas",
     "display_name": "Ventas",
     "description": "Módulo de ventas",
     "order": 10
   }
   ```

2. **Crear Permisos**:
   ```json
   POST /api/accounts/custom-permissions/
   {
     "category": 1,  // ID de categoría "ventas"
     "codename": "can_manage_sales",
     "name": "Puede gestionar ventas",
     "permission_type": "modular",
     "action_type": "manage",
     "is_active": true
   }
   ```

3. **Crear Permisos Granulares**:
   ```json
   POST /api/accounts/custom-permissions/
   {
     "category": 1,
     "codename": "can_create_sales",
     "name": "Puede crear ventas",
     "permission_type": "granular",
     "action_type": "create",
     "parent_permission": 5,  // ID de can_manage_sales
     "is_active": true
   }
   ```

4. **Asignar a Grupo**:
   ```json
   POST /api/accounts/custom-permissions/assign/
   {
     "permission_ids": [5, 6, 7],
     "group_ids": [3],
     "action": "add"
   }
   ```

5. **Usar en ViewSet**:
   ```python
   class VentasViewSet(viewsets.ModelViewSet):
       permission_classes = [IsAuthenticated, HasModulePermission]
       permission_required = 'ventas.can_manage_sales'
   ```

## Ventajas

✅ **Sin Desarrollo**: Crear permisos sin programar  
✅ **Flexible**: Adaptarse a cambios de negocio rápidamente  
✅ **Auditable**: Saber quién creó cada permiso  
✅ **Escalable**: Crecer con nuevos módulos sin límite  
✅ **Compatible**: Usa Django nativo internamente  

## Seguridad

🔒 Solo SystemAdmin puede crear/editar permisos  
🔒 Permisos del sistema protegidos contra eliminación  
🔒 Validación de formato y duplicados  
🔒 Auditoría automática de cambios  

## Soporte

Ver documentación completa en:
- `DYNAMIC_PERMISSIONS_SYSTEM.md` - Sistema completo
- `EXPANDED_PERMISSIONS.md` - Permisos actuales

---

**Listo para implementar**: Los modelos y código están en `DYNAMIC_PERMISSIONS_SYSTEM.md`
