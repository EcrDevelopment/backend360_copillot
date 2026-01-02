from django.contrib.auth.models import User, Group, Permission
from django.db import models
from datetime import timedelta
from django.utils import timezone
from base.models import BaseModel
from localizacion.models import Departamento, Distrito, Provincia


class Empresa(BaseModel):
    nombre = models.CharField(max_length=255)
    direccion = models.TextField(blank=True, null=True)
    ruc = models.CharField(max_length=11, unique=True)  # RUC u otro identificador único de la empresa

    class Meta:
        db_table = 'empresa_perfil'

    def __str__(self):
        return self.nombre

    def tiene_direcciones(self):
        return self.direcciones.exists()

class Direccion(BaseModel):
    empresa = models.ForeignKey(Empresa, related_name='direcciones', on_delete=models.CASCADE)
    direccion = models.TextField(max_length=2500)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE)
    distrito = models.ForeignKey(Distrito, on_delete=models.CASCADE)

    class Meta:
        db_table = 'direccion'

    def __str__(self):
        return f"{self.direccion} - {self.distrito.name}, {self.provincia.name}, {self.departamento.name}"



class UserProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    telefono = models.CharField(max_length=20, null=True, blank=True)
    empresa = models.ForeignKey(Empresa, related_name='empresa', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'perfil'

    def __str__(self):
        return f"Perfil de {self.user.username}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField( editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    active=models.BooleanField(default=True)

    def is_expired(self):
        #el token expira en 15 minutos
        return not self.active or timezone.now() > self.created_at + timedelta(minutes=15)

    class Meta:
        db_table = 'password_reset_token'

    def __str__(self):
        return str(self.token)


class UsuariosPermissions(models.Model):
    """
    Meta modelo para definir permisos funcionales del módulo de Usuarios.
    Este modelo no crea una tabla en la base de datos (managed=False).
    Solo se usa para registrar permisos personalizados de alto nivel.
    
    Incluye permisos modulares Y granulares para control específico.
    """
    class Meta:
        managed = False  # No crear tabla en la base de datos
        default_permissions = ()  # No crear permisos automáticos (add, change, delete, view)
        permissions = [
            # Permisos modulares (alto nivel)
            ('can_manage_users', 'Puede gestionar usuarios (crear, editar, eliminar)'),
            ('can_view_users', 'Puede ver usuarios'),
            ('can_manage_roles', 'Puede gestionar roles y permisos'),
            ('can_view_roles', 'Puede ver roles y permisos'),
            
            # Permisos granulares (acciones específicas)
            ('can_create_users', 'Puede crear usuarios'),
            ('can_edit_users', 'Puede editar usuarios'),
            ('can_delete_users', 'Puede eliminar usuarios'),
            ('can_create_roles', 'Puede crear roles'),
            ('can_edit_roles', 'Puede editar roles'),
            ('can_delete_roles', 'Puede eliminar roles'),
        ]
        verbose_name = 'Permiso de Usuarios'
        verbose_name_plural = 'Permisos de Usuarios'


class MantenimientoPermissions(models.Model):
    """
    Meta modelo para permisos de tablas de mantenimiento/misceláneas.
    Controla acceso a tablas de configuración del sistema.
    """
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            # Permisos modulares
            ('can_manage_maintenance_tables', 'Puede gestionar todas las tablas de mantenimiento'),
            ('can_view_maintenance_tables', 'Puede ver tablas de mantenimiento'),
            
            # Permisos específicos por tabla
            ('can_manage_document_types', 'Puede gestionar tipos de documentos'),
            ('can_manage_companies', 'Puede gestionar empresas'),
            ('can_manage_product_catalog', 'Puede gestionar catálogo de productos'),
            ('can_manage_warehouse_catalog', 'Puede gestionar catálogo de almacenes'),
            ('can_manage_stowage_types', 'Puede gestionar tipos de estibaje'),
        ]
        verbose_name = 'Permiso de Mantenimiento'
        verbose_name_plural = 'Permisos de Mantenimiento'


class ProveedorPermissions(models.Model):
    """
    Meta modelo para permisos específicos de proveedores.
    Separado de importaciones para control independiente.
    """
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            # Permisos para rol de proveedor
            ('can_upload_documents', 'Puede cargar documentos DUA'),
            ('can_manage_own_documents', 'Puede gestionar sus propios documentos'),
            ('can_view_own_documents', 'Puede ver sus propios documentos'),
            ('can_download_own_documents', 'Puede descargar sus propios documentos'),
        ]
        verbose_name = 'Permiso de Proveedor'
        verbose_name_plural = 'Permisos de Proveedor'


# ========================================
# DYNAMIC PERMISSION SYSTEM
# ========================================

class CustomPermissionCategory(BaseModel):
    """
    Categorías para organizar permisos dinámicos por módulo.
    Ejemplo: ventas, finanzas, compras, etc.
    Hereda de BaseModel para tener auditoría automática via django-simple-history.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nombre técnico de la categoría (ej: ventas, finanzas)"
    )
    display_name = models.CharField(
        max_length=200,
        help_text="Nombre para mostrar en UI (ej: Ventas, Finanzas)"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción de qué permisos agrupa esta categoría"
    )
    icon = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Nombre del ícono para el frontend"
    )
    order = models.IntegerField(
        default=0,
        help_text="Orden de visualización"
    )

    class Meta:
        db_table = 'custom_permission_category'
        verbose_name = 'Categoría de Permiso'
        verbose_name_plural = 'Categorías de Permisos'
        ordering = ['order', 'display_name']

    def __str__(self):
        return self.display_name


class CustomPermission(BaseModel):
    """
    Permisos dinámicos creados por administradores sin código.
    Se sincronizan automáticamente con django.contrib.auth.models.Permission.
    Hereda de BaseModel para tener auditoría automática via django-simple-history.
    """
    
    PERMISSION_TYPE_CHOICES = [
        ('modular', 'Modular (alto nivel)'),
        ('granular', 'Granular (acción específica)'),
    ]
    
    ACTION_TYPE_CHOICES = [
        ('manage', 'Gestionar (crear/editar/eliminar)'),
        ('view', 'Ver (solo lectura)'),
        ('create', 'Crear'),
        ('edit', 'Editar'),
        ('delete', 'Eliminar'),
        ('approve', 'Aprobar'),
        ('export', 'Exportar'),
        ('import', 'Importar'),
        ('custom', 'Personalizado'),
    ]
    
    category = models.ForeignKey(
        CustomPermissionCategory,
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text="Categoría a la que pertenece este permiso"
    )
    
    codename = models.CharField(
        max_length=100,
        unique=True,
        help_text="Código del permiso (ej: can_manage_sales). Debe empezar con 'can_'"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Nombre descriptivo del permiso (ej: Puede gestionar ventas)"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Descripción detallada de qué permite hacer"
    )
    
    permission_type = models.CharField(
        max_length=20,
        choices=PERMISSION_TYPE_CHOICES,
        default='modular',
        help_text="Tipo de permiso: modular (alto nivel) o granular (específico)"
    )
    
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        default='manage',
        help_text="Tipo de acción que permite"
    )
    
    parent_permission = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_permissions',
        help_text="Permiso padre en la jerarquía (ej: can_manage_sales incluye can_create_sales)"
    )
    
    django_permission = models.OneToOneField(
        Permission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='custom_permission',
        help_text="Permiso nativo de Django asociado"
    )
    
    is_system = models.BooleanField(
        default=False,
        help_text="Si es True, el permiso no puede ser eliminado (permisos del sistema)"
    )
    
    # Campos de auditoría heredados de BaseModel:
    # - created_by, modified_by (via HistoricalRecords)
    # - created_date, modified_date, deleted_date
    # - state (para soft delete)
    # - historical (para historial completo de cambios)
    
    class Meta:
        db_table = 'custom_permission'
        verbose_name = 'Permiso Personalizado'
        verbose_name_plural = 'Permisos Personalizados'
        ordering = ['category__order', 'permission_type', 'name']

    def __str__(self):
        return f"{self.category.display_name} - {self.name}"
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe save para:
        1. Validar formato del codename
        2. Auto-crear Permission nativo de Django
        """
        from django.contrib.contenttypes.models import ContentType
        
        # Validar que codename empiece con 'can_'
        if not self.codename.startswith('can_'):
            raise ValueError("El codename debe empezar con 'can_'")
        
        # Validar que no exista permiso circular en jerarquía
        if self.parent_permission:
            if self._is_circular_hierarchy():
                raise ValueError("No se puede crear una jerarquía circular de permisos")
        
        # Guardar el CustomPermission primero
        super().save(*args, **kwargs)
        
        # Crear o actualizar el Permission nativo de Django
        if not self.django_permission:
            # Obtener el ContentType para CustomPermission
            content_type = ContentType.objects.get_for_model(CustomPermission)
            
            # Crear el permiso nativo
            django_perm, created = Permission.objects.get_or_create(
                codename=self.codename,
                content_type=content_type,
                defaults={'name': self.name}
            )
            
            self.django_permission = django_perm
            # Guardar de nuevo para actualizar la relación (sin entrar en recursión infinita)
            super().save(update_fields=['django_permission'])
    
    def _is_circular_hierarchy(self):
        """Detecta si hay una referencia circular en la jerarquía de permisos"""
        visited = set()
        current = self.parent_permission
        
        while current:
            if current.id in visited or current.id == self.id:
                return True
            visited.add(current.id)
            current = current.parent_permission
        
        return False
    
    def delete(self, *args, **kwargs):
        """
        Sobrescribe delete para:
        1. Prevenir eliminación de permisos del sistema
        2. Implementar soft delete (via BaseModel)
        3. Desactivar el Permission nativo de Django
        """
        if self.is_system:
            raise ValueError("Los permisos del sistema no pueden ser eliminados")
        
        # Soft delete via BaseModel
        super().delete(*args, **kwargs)
        
        # Nota: No eliminamos el django_permission porque puede estar asignado a usuarios/grupos
        # Solo marcamos como inactivo el CustomPermission


class PermissionChangeAudit(BaseModel):
    """
    Registro específico de cambios en permisos para auditoría detallada.
    Complementa el HistoricalRecords automático con logs específicos de negocio.
    Hereda de BaseModel para tener auditoría automática via django-simple-history.
    """
    
    ACTION_CHOICES = [
        ('created', 'Creado'),
        ('updated', 'Actualizado'),
        ('deleted', 'Eliminado'),
        ('assigned', 'Asignado a usuario/grupo'),
        ('revoked', 'Revocado de usuario/grupo'),
    ]
    
    permission = models.ForeignKey(
        CustomPermission,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        help_text="Permiso afectado por este cambio"
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Tipo de acción realizada"
    )
    
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='permission_changes_made',
        help_text="Usuario que realizó el cambio"
    )
    
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_changes_received',
        help_text="Usuario al que se le asignó/revocó el permiso (si aplica)"
    )
    
    target_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_changes',
        help_text="Grupo al que se le asignó/revocó el permiso (si aplica)"
    )
    
    before_value = models.JSONField(
        null=True,
        blank=True,
        help_text="Valor antes del cambio (para updates)"
    )
    
    after_value = models.JSONField(
        null=True,
        blank=True,
        help_text="Valor después del cambio (para updates)"
    )
    
    reason = models.TextField(
        blank=True,
        help_text="Razón del cambio (opcional)"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Dirección IP desde donde se realizó el cambio"
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text="User agent del navegador/cliente"
    )
    
    # Campos heredados de BaseModel:
    # - created_date (timestamp del evento)
    # - historical (historial de cambios en este log)
    
    class Meta:
        db_table = 'permission_change_audit'
        verbose_name = 'Auditoría de Permiso'
        verbose_name_plural = 'Auditorías de Permisos'
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.action} - {self.permission.name} - {self.created_date}"