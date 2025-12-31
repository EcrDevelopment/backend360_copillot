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