from django.contrib import admin
from .models import (
    CustomPermissionCategory,
    CustomPermission,
    PermissionChangeAudit
)


@admin.register(CustomPermissionCategory)
class CustomPermissionCategoryAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'order', 'state', 'created_date']
    list_filter = ['state', 'created_date']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['order', 'display_name']


@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'category', 'permission_type', 'action_type', 'is_system', 'state']
    list_filter = ['category', 'permission_type', 'action_type', 'is_system', 'state']
    search_fields = ['codename', 'name', 'description']
    readonly_fields = ['django_permission', 'created_date', 'modified_date']
    fieldsets = (
        ('Información Básica', {
            'fields': ('category', 'codename', 'name', 'description')
        }),
        ('Clasificación', {
            'fields': ('permission_type', 'action_type', 'parent_permission')
        }),
        ('Sistema', {
            'fields': ('is_system', 'state', 'django_permission')
        }),
        ('Auditoría', {
            'fields': ('created_date', 'modified_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PermissionChangeAudit)
class PermissionChangeAuditAdmin(admin.ModelAdmin):
    list_display = ['permission', 'action', 'performed_by', 'target_user', 'target_group', 'created_date']
    list_filter = ['action', 'created_date']
    search_fields = ['permission__name', 'performed_by__username', 'reason']
    readonly_fields = ['permission', 'action', 'performed_by', 'target_user', 'target_group',
                       'before_value', 'after_value', 'reason', 'ip_address', 'user_agent', 'created_date']

    def has_add_permission(self, request):
        # Los logs de auditoría solo se crean automáticamente
        return False


'''
La ejecucion se efectuo correctamente hice un ajuste con el modulo de almacen ya que esos permisos aun no existian 
pero la idea es que si existan , la implementacion de estos puede servir como prueba, ademas quisiera que continuemos
con los serializer y el API viewsets para poder completar el modulo de permisos personalizados.
finalmente quisiera que se realice pa migracion completa para dejar de usar los permisos anteriores.
'''