# Consideraciones de Seguridad - Permisos Flexibles

## Resumen

Los permisos se han relajado para mantener compatibilidad con el frontend existente. Este documento describe las implicaciones de seguridad y las recomendaciones para mitigarlas.

## Permisos Modificados

### 1. CanAccessImportaciones
**Estado**: Permite acceso a cualquier usuario autenticado

**Riesgo**: Usuarios autenticados pueden acceder a datos de importaciones
**Mitigación**:
- ✅ Logging de todos los accesos al módulo
- ⚠️ Considerar filtrado de datos por usuario en las vistas
- 📋 Asignar roles específicos cuando se necesite mayor control

### 2. CanAccessAlmacen
**Estado**: Permite acceso a cualquier usuario autenticado

**Riesgo**: Usuarios autenticados pueden ver datos de inventario
**Mitigación**:
- ✅ Logging de todos los accesos al módulo
- ⚠️ Considerar filtrado de datos por almacén/empresa
- 📋 Implementar vistas que limiten datos según contexto del usuario

### 3. CanEditDocuments
**Estado**: Permite edición a cualquier usuario autenticado

**Riesgo**: Usuarios pueden modificar documentos sin verificación de propiedad
**Mitigación**:
- ✅ Logging (WARNING level) de operaciones POST/PUT/PATCH/DELETE
- ⚠️ Implementar verificación de propiedad a nivel de vista
- 📋 Usar has_object_permission en vistas críticas
- 💡 Considerar versionado de documentos para auditoría

### 4. CanDeleteResource
**Estado**: Permite eliminación a cualquier usuario autenticado

**Riesgo**: Mayor riesgo - usuarios pueden eliminar recursos
**Mitigación Implementada**:
- ✅ Logging crítico (WARNING level) con emoji ⚠️ de todas las operaciones DELETE
- ✅ Incluye usuario, vista y path en el log

**Mitigaciones Recomendadas**:
- 🔴 **PRIORIDAD ALTA**: Implementar soft deletes en lugar de hard deletes
- 🔴 **PRIORIDAD ALTA**: Considerar revertir este permiso a admin-only
- 📋 Implementar confirmación de dos factores para eliminaciones críticas
- 💡 Agregar tabla de respaldo antes de eliminar

## Sistema de Logging

Todos los permisos modificados incluyen logging para auditoría:

### Niveles de Log
- **INFO**: Accesos a módulos (CanAccessImportaciones, CanAccessAlmacen)
- **WARNING**: Operaciones de edición y eliminación (CanEditDocuments, CanDeleteResource)

### Información Registrada
- Nombre de usuario
- Método HTTP
- Nombre de la vista
- Path (para DELETE)

### Ubicación de Logs
- `logs/audit.log` - Log principal de auditoría
- Configurado en LOGGING settings de Django

## Seguridad Mantenida

✅ **Autenticación JWT**: Todos los endpoints requieren token válido
✅ **Auditoría Completa**: Middleware AuditMiddleware registra operaciones
✅ **Rate Limiting**: Protección contra fuerza bruta activa
✅ **Headers de Seguridad**: SecurityHeadersMiddleware activo
✅ **Operaciones Administrativas**: UserViewSet/RoleViewSet/PermissionViewSet protegidos

## Recomendaciones Inmediatas

### Para Desarrollo
1. ✅ Monitorear logs regularmente
2. ⚠️ Revisar operaciones DELETE sospechosas
3. 📋 Documentar qué usuarios necesitan qué permisos

### Para Producción

#### Prioridad Alta 🔴
1. **Implementar Soft Deletes**
   ```python
   class BaseModel(models.Model):
       deleted_at = models.DateTimeField(null=True, blank=True)
       
       def soft_delete(self):
           self.deleted_at = timezone.now()
           self.save()
   ```

2. **Restringir CanDeleteResource**
   ```python
   # Revertir a admin-only
   return (
       has_role(request.user, 'system_admin')
       or has_role(request.user, 'accounts_admin')
   )
   ```

#### Prioridad Media ⚠️
1. **Filtrado de Datos por Usuario**
   ```python
   def get_queryset(self):
       queryset = super().get_queryset()
       if not has_role(self.request.user, 'system_admin'):
           queryset = queryset.filter(empresa=self.request.user.empresa)
       return queryset
   ```

2. **Verificación de Propiedad de Documentos**
   ```python
   def has_object_permission(self, request, view, obj):
       return obj.created_by == request.user or has_role(request.user, 'admin')
   ```

#### Prioridad Baja 📋
1. **Asignación de Roles**: Asignar roles específicos a usuarios
2. **Documentación**: Documentar requisitos de permisos por funcionalidad
3. **Capacitación**: Entrenar usuarios en prácticas de seguridad

## Monitoreo

### Comandos Útiles

```bash
# Ver accesos recientes al módulo de almacén
grep "módulo de almacén" logs/audit.log | tail -n 20

# Ver operaciones DELETE recientes
grep "OPERACIÓN DELETE" logs/audit.log | tail -n 20

# Ver actividad de un usuario específico
grep "Usuario: username" logs/audit.log | tail -n 50

# Monitoreo en tiempo real
tail -f logs/audit.log | grep -E "DELETE|EDIT"
```

### Alertas Recomendadas

Configure alertas para:
- Más de 10 operaciones DELETE por usuario por día
- Operaciones DELETE fuera de horario laboral
- Acceso desde IPs desconocidas
- Intentos de acceso denegado repetidos

## Plan de Transición a Permisos Granulares

Si en el futuro se necesita mayor seguridad:

### Fase 1: Preparación (1-2 semanas)
1. Identificar roles de usuario necesarios
2. Documentar qué permisos necesita cada rol
3. Crear script de asignación de roles
4. Comunicar cambios al equipo

### Fase 2: Asignación (1 semana)
1. Asignar roles a usuarios existentes
2. Verificar que usuarios tienen acceso apropiado
3. Monitorear logs por problemas

### Fase 3: Activación (1 día)
1. Modificar permisos para requerir roles
2. Desplegar cambios
3. Monitorear errores
4. Resolver issues rápidamente

### Fase 4: Validación (1 semana)
1. Verificar que todo funciona
2. Recolectar feedback de usuarios
3. Ajustar permisos según necesidad

## Contacto

Para preguntas o preocupaciones de seguridad:
1. Revisar logs en `logs/audit.log`
2. Revisar este documento para mitigaciones
3. Contactar al equipo de desarrollo

## Conclusión

Los permisos actuales priorizan **funcionalidad y compatibilidad** sobre seguridad granular. Esto es apropiado para desarrollo y testing, pero debe ser evaluado para producción.

**Recomendación**: Mantener configuración actual para desarrollo, pero planear implementación de permisos granulares antes de despliegue en producción.
