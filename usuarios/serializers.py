from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from localizacion.serializers import DepartamentoSerializer, ProvinciaSerializer, DistritoSerializer
from .models import PasswordResetToken, UserProfile, Empresa, Direccion
from  localizacion.models import  Departamento, Provincia, Distrito
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User, Group, Permission
from .validators import InputValidator

from almacen.models import Almacen

from .audit_log import AuditLog, get_client_ip

'''
por alguna razon ahora en mi frontend tengo el problema de no esta funcionando el refresh token cambiaste algo
de como se guarda el token al hacer login o como se hace al refrescar porque mi frontend lo validad constantemente 
con Axios y ya estaba todo configurado antes pero de repente dejo de funcionar.
'''


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes user roles and permissions.
    Uses Django's native auth system (Groups and Permissions).
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Don't include roles and permissions in token payload to keep token size small
        # Frontend should fetch roles and permissions separately via API endpoints
        # Only include essential user identifier
        token['username'] = user.username
        return token

    @staticmethod
    def _get_user_permissions(user):
        """
        Get all permissions for user (from groups + user-specific permissions).
        Returns a dict with permission codenames as keys and True as values.
        """
        permissions = {}
        
        # Get all permissions (including from groups)
        all_perms = user.get_all_permissions()
        
        # Convert to dict format: {'app.permission_codename': True}
        for perm in all_perms:
            permissions[perm.replace('.', '_')] = True
        
        # Also add codename-only format for backwards compatibility
        for perm in user.user_permissions.all():
            permissions[perm.codename] = True
        
        for group in user.groups.all():
            for perm in group.permissions.all():
                permissions[perm.codename] = True
        
        return permissions

    def validate(self, attrs):
        data = super().validate(attrs)

        # 1. Datos del usuario (Tu código original)
        user_info = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'nombre': self.user.first_name,
            'apellido': self.user.last_name,
        }

        profile = getattr(self.user, 'userprofile', None)
        if profile:
            user_info['telefono'] = profile.telefono if profile.telefono else None
            user_info['empresa_id'] = profile.empresa.id if profile.empresa else None

        data['user'] = user_info

        # 2. ROLES (IDs de Grupos) - Esto está bien
        data['roles'] = list(self.user.groups.values_list('id', flat=True))

        # =========================================================================
        # 3. CORRECCIÓN DE PERMISOS (LA PARTE QUE FALTABA)
        # =========================================================================

        # A. Recolectar IDs de permisos nativos de Django (Directos + Grupos)
        # -------------------------------------------------------------------
        perm_ids = set()
        # Permisos directos
        perm_ids.update(self.user.user_permissions.values_list('id', flat=True))
        # Permisos heredados de sus Roles (Grupos)
        perm_ids.update(Permission.objects.filter(group__user=self.user).values_list('id', flat=True))

        # B. Traducir esos IDs a tus "CustomPermission" (Strings bonitos)
        # -------------------------------------------------------------------
        from .models import CustomPermission  # Importamos aquí para evitar errores circulares

        # Buscamos en tu tabla personalizada los permisos que coincidan con los IDs nativos
        custom_perms = CustomPermission.objects.filter(
            django_permission_id__in=perm_ids,
            state=True
        ).select_related('category')

        # C. Formatear como espera el Frontend: "categoria.codename"
        # -------------------------------------------------------------------
        permissions_list = []
        for cp in custom_perms:
            # Si category existe usamos su 'name' (ej: importaciones), sino 'sistema'
            cat_key = cp.category.name if cp.category else 'sistema'

            # Resultado: "importaciones.can_view_importaciones"
            permissions_list.append(f"{cat_key}.{cp.codename}")

        # Agregamos permiso especial si es superusuario (opcional)
        if self.user.is_superuser:
            permissions_list.append('sistema.superuser_access')

        # D. Asignar la lista de strings a la respuesta
        data['permissions'] = permissions_list
        # =========================================================================

        return data

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No existe un usuario con este correo.")
        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        # Desactivar tokens anteriores antes de generar uno nuevo
        PasswordResetToken.objects.filter(user=user, active=True).update(active=False)

        # Generar el token de acceso JWT
        token = RefreshToken.for_user(user).access_token

        # Guardar el token y usuario en la base de datos
        PasswordResetToken.objects.create(user=user, token=token)

        # Crear el enlace de restablecimiento
        reset_link = f"{settings.FRONTEND_URL}/reset-password/confirm?token={token}&user={user.id}"
        site_name = "Semilla-360°"

        # Cargar y renderizar la plantilla HTML
        html_content = render_to_string("emails/password_reset.html", {
            'reset_link': reset_link,
            'site_name': site_name,
        })
        text_content = strip_tags(html_content)  # Genera una versión de texto plano sin HTML

        # Configurar el correo
        subject = "Restablecimiento de contraseña"
        from_email = settings.DEFAULT_FROM_EMAIL
        email_message = EmailMultiAlternatives(subject, text_content, from_email, [email])
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        user = self.context['user']
        user.set_password(data['password'])
        user.save()
        return data

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    user_id = serializers.IntegerField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        """Valida la fortaleza de la nueva contraseña usando InputValidator"""
        try:
            return InputValidator.validate_password_strength(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def validate(self, attrs):
        token = attrs.get('token')
        user_id = attrs.get('user_id')
        new_password = attrs.get('new_password')

        # Verifica la existencia del token
        try:
            token_instance = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("El token es inválido.")


        # Verifica si el token ha expirado
        if token_instance.is_expired():
            raise serializers.ValidationError("El token ha expirado, realiza una nueva solicitud.")

        # Verifica si el token esta activo
        if not token_instance.active:
            raise serializers.ValidationError("El token ya ha sido usado o invalidado.")

        # Verifica si el user_id coincide con el del token
        if token_instance.user.id != user_id:
            raise serializers.ValidationError("El usuario no coincide con el token proporcionado.")

        # Asegura que el usuario existe
        if not User.objects.filter(id=user_id).exists():
            raise serializers.ValidationError("El usuario no existe.")

        # Si todo es válido, devuelve los atributos validados
        return attrs

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'codename', 'name', 'content_type']

class RoleSerializer(serializers.ModelSerializer):  # Role == Group
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all()
    )
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']

class UserProfileSerializer(serializers.ModelSerializer):
    # Definimos explícitamente para que DRF sepa cómo manejar los IDs
    almacenes_asignados = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Almacen.objects.filter(state=True), required=False
    )
    sedes_asignadas = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Direccion.objects.filter(state=True), required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'telefono', 'empresa',
            'require_warehouse_access', 'almacenes_asignados',
            'require_sede_access', 'sedes_asignadas'
        ]

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    roles = serializers.PrimaryKeyRelatedField(
        many=True, source="groups", queryset=Group.objects.all(), required=False
    )
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, source="user_permissions", queryset=Permission.objects.all(), required=False
    )
    userprofile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "id", "username", "password", "email", "first_name", "last_name",
            "roles", "permissions", "userprofile", "is_active"
        ]
        read_only_fields = ["id"]

    def validate_username(self, value):
        """Valida el nombre de usuario usando InputValidator"""
        try:
            return InputValidator.validate_username(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_email(self, value):
        """Valida el email usando InputValidator"""
        try:
            return InputValidator.validate_email(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_password(self, value):
        """Valida la fortaleza de la contraseña usando InputValidator"""
        try:
            return InputValidator.validate_password_strength(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "La contraseña es obligatoria para crear un usuario."})
        
        # Sanitizar campos de texto
        if 'first_name' in attrs:
            attrs['first_name'] = InputValidator.sanitize_string(attrs['first_name'], max_length=150)
        if 'last_name' in attrs:
            attrs['last_name'] = InputValidator.sanitize_string(attrs['last_name'], max_length=150)
        
        return super().validate(attrs)

    def create(self, validated_data):
        roles = validated_data.pop("groups", [])
        perms = validated_data.pop("user_permissions", [])
        profile_data = validated_data.pop("userprofile", {})
        password = validated_data.pop("password")

        # 1. Separar datos M2M del perfil (no se pueden guardar en el create)
        almacenes = profile_data.pop('almacenes_asignados', [])
        sedes = profile_data.pop('sedes_asignadas', [])

        # 2. Crear Usuario
        user = User.objects.create_user(password=password, **validated_data)
        user.groups.set(roles)
        user.user_permissions.set(perms)

        # 3. Crear Perfil (sin M2M)
        profile = UserProfile.objects.create(user=user, **profile_data)

        # 4. Asignar M2M ahora que el perfil existe
        if almacenes:
            profile.almacenes_asignados.set(almacenes)
        if sedes:
            profile.sedes_asignadas.set(sedes)

        return user

    def update(self, instance, validated_data):
        roles = validated_data.pop("groups", None)
        perms = validated_data.pop("user_permissions", None)
        profile_data = validated_data.pop("userprofile", {})
        password = validated_data.pop("password", None)

        # Actualizar usuario base
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()

        if roles is not None:
            instance.groups.set(roles)
        if perms is not None:
            instance.user_permissions.set(perms)

        # Actualizar Perfil
        profile = getattr(instance, "userprofile", None)

        # Si no existe perfil y mandan datos, crearlo
        if not profile and profile_data:
            # Extraer M2M antes de crear
            almacenes = profile_data.pop('almacenes_asignados', [])
            sedes = profile_data.pop('sedes_asignadas', [])

            profile = UserProfile.objects.create(user=instance, **profile_data)

            profile.almacenes_asignados.set(almacenes)
            profile.sedes_asignadas.set(sedes)

        elif profile:
            # Extraer M2M para actualizar aparte
            almacenes = profile_data.pop('almacenes_asignados', None)
            sedes = profile_data.pop('sedes_asignadas', None)

            # Actualizar campos simples
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

            # Actualizar M2M usando .set()
            if almacenes is not None:
                profile.almacenes_asignados.set(almacenes)
            if sedes is not None:
                profile.sedes_asignadas.set(sedes)

        return instance

class DireccionSerializer(serializers.ModelSerializer):
    # Mantenemos esto para que al CREAR una dirección se use el ID
    empresa = serializers.PrimaryKeyRelatedField(queryset=Empresa.objects.all())

    # Serializers anidados (solo lectura) para ver el detalle
    departamento = DepartamentoSerializer(read_only=True)
    provincia = ProvinciaSerializer(read_only=True)
    distrito = DistritoSerializer(read_only=True)

    # 🆕 CAMPOS EXTRA PARA EL FRONTEND (SOLO LECTURA)
    # Esto permite mostrar "Empresa Semilla" en lugar de "5"
    empresa_nombre = serializers.CharField(source='empresa.razon_social', read_only=True)

    # Este campo crea el string completo para el Select del UserManager
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Direccion
        fields = '__all__'

    def get_full_name(self, obj):
        """
        Genera un nombre legible: 'Av. Perú 123 (Empresa X) - Lima, Miraflores'
        """
        # Obtenemos los nombres de forma segura (por si son nulos)
        empresa = obj.empresa.razon_social if obj.empresa else 'Sin Empresa'
        distrito = obj.distrito.name if obj.distrito else ''
        provincia = obj.provincia.name if obj.provincia else ''

        # Construimos la ubicación geográfica
        ubicacion = f"{provincia}, {distrito}".strip(', ')

        # Retornamos el formato final
        return f"{obj.direccion} ({empresa}) - {ubicacion}"

class EmpresaSerializer(serializers.ModelSerializer):
    direcciones = DireccionSerializer(many=True, read_only=True)

    class Meta:
        model = Empresa
        fields = '__all__'


# ========================================
# DYNAMIC PERMISSION SYSTEM SERIALIZERS
# ========================================

from .models import CustomPermissionCategory, CustomPermission, PermissionChangeAudit


class CustomPermissionCategorySerializer(serializers.ModelSerializer):
    """
    Serializer para categorías de permisos dinámicos.
    """
    permissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomPermissionCategory
        fields = [
            'id', 'name', 'display_name', 'description', 'icon', 'order',
            'state', 'created_date', 'modified_date', 'permissions_count'
        ]
        read_only_fields = ['id', 'created_date', 'modified_date']
    
    def get_permissions_count(self, obj):
        """Retorna el número de permisos activos en esta categoría"""
        return obj.permissions.filter(state=True).count()


class CustomPermissionSerializer(serializers.ModelSerializer):
    """
    Serializer para permisos dinámicos.
    Incluye validación de formato y jerarquía.
    """
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    parent_permission_name = serializers.CharField(source='parent_permission.name', read_only=True)
    django_permission_id = serializers.IntegerField(source='django_permission.id', read_only=True)
    child_permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomPermission
        fields = [
            'id', 'category', 'category_name', 'codename', 'name', 'description',
            'permission_type', 'action_type', 'parent_permission', 'parent_permission_name',
            'django_permission', 'django_permission_id', 'is_system', 'state',
            'created_date', 'modified_date', 'child_permissions'
        ]
        read_only_fields = ['id', 'django_permission', 'created_date', 'modified_date']
    
    def get_child_permissions(self, obj):
        """Retorna los permisos hijos activos"""
        children = obj.child_permissions.filter(state=True)
        return [{'id': c.id, 'name': c.name, 'codename': c.codename} for c in children]
    
    def validate_codename(self, value):
        """Valida que el codename tenga el formato correcto"""
        if not value.startswith('can_'):
            raise serializers.ValidationError("El codename debe empezar con 'can_'")
        
        # Validar que solo contenga letras minúsculas y guiones bajos
        import re
        if not re.match(r'^can_[a-z_]+$', value):
            raise serializers.ValidationError(
                "El codename solo puede contener letras minúsculas y guiones bajos después de 'can_'"
            )
        
        return value
    
    def validate(self, attrs):
        """Validaciones adicionales"""
        # Validar que no se cree jerarquía circular
        if 'parent_permission' in attrs and attrs['parent_permission']:
            parent = attrs['parent_permission']
            if self.instance and parent.id == self.instance.id:
                raise serializers.ValidationError({
                    'parent_permission': 'Un permiso no puede ser su propio padre'
                })
        
        return attrs

    class CustomPermissionSerializer(serializers.ModelSerializer):
        """
        Serializer para permisos dinámicos.
        Sincroniza automáticamente con auth_permission de Django.
        """
        category_name = serializers.CharField(source='category.display_name', read_only=True)
        parent_permission_name = serializers.CharField(source='parent_permission.name', read_only=True)
        django_permission_id = serializers.IntegerField(source='django_permission.id', read_only=True)
        child_permissions = serializers.SerializerMethodField()

        class Meta:
            model = CustomPermission
            fields = [
                'id', 'category', 'category_name', 'codename', 'name', 'description',
                'permission_type', 'action_type', 'parent_permission', 'parent_permission_name',
                'django_permission', 'django_permission_id', 'is_system', 'state',
                'created_date', 'modified_date', 'child_permissions'
            ]
            read_only_fields = ['id', 'django_permission', 'created_date', 'modified_date', 'is_system']

        def get_child_permissions(self, obj):
            children = obj.child_permissions.filter(state=True)
            return [{'id': c.id, 'name': c.name, 'codename': c.codename} for c in children]

        def validate_codename(self, value):
            if not value.startswith('can_'):
                raise serializers.ValidationError("El codename debe empezar con 'can_'")
            import re
            if not re.match(r'^can_[a-z_]+$', value):
                raise serializers.ValidationError("Solo letras minúsculas y guiones bajos después de 'can_'")
            return value

        def validate(self, attrs):
            if 'parent_permission' in attrs and attrs['parent_permission']:
                parent = attrs['parent_permission']
                if self.instance and parent.id == self.instance.id:
                    raise serializers.ValidationError({'parent_permission': 'Un permiso no puede ser su propio padre'})
            return attrs

        def create(self, validated_data):
            """
            Crea el CustomPermission y asegura que exista el Permission nativo de Django.
            """
            codename = validated_data.get('codename')
            name = validated_data.get('name')

            # 1. SINCRONIZACIÓN: Crear/Obtener permiso nativo
            # Usamos el ContentType de 'User' para centralizar todo bajo la app 'usuarios'
            try:
                content_type = ContentType.objects.get_for_model(User)
            except:
                content_type = ContentType.objects.first()

            django_perm, _ = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )

            # Vincular
            validated_data['django_permission'] = django_perm

            # 2. CREACIÓN ORIGINAL
            from .audit_log import get_client_ip
            permission = super().create(validated_data)

            # 3. AUDITORÍA
            request = self.context.get('request')
            if request:
                PermissionChangeAudit.objects.create(
                    permission=permission,
                    action='created',
                    performed_by=request.user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    reason=f"Permiso creado via API"
                )

            return permission

        def update(self, instance, validated_data):
            """
            Actualiza CustomPermission y sincroniza cambios de nombre/codename con Django.
            """
            from .audit_log import get_client_ip

            before_value = {
                'name': instance.name,
                'description': instance.description,
                'permission_type': instance.permission_type,
                'action_type': instance.action_type,
                'parent_permission_id': instance.parent_permission_id if instance.parent_permission else None
            }

            # 1. ACTUALIZACIÓN ORIGINAL
            permission = super().update(instance, validated_data)

            # 2. SINCRONIZACIÓN: Actualizar permiso nativo si cambió algo
            if permission.django_permission:
                dp = permission.django_permission
                changed = False

                # Sincronizar Codename
                if dp.codename != permission.codename:
                    dp.codename = permission.codename
                    changed = True

                # Sincronizar Nombre
                if dp.name != permission.name:
                    dp.name = permission.name
                    changed = True

                if changed:
                    dp.save()

            # 3. AUDITORÍA
            request = self.context.get('request')
            if request:
                PermissionChangeAudit.objects.create(
                    permission=permission,
                    action='updated',
                    performed_by=request.user,
                    before_value=before_value,
                    after_value={
                        'name': permission.name,
                        'description': permission.description,
                        'permission_type': permission.permission_type,
                        'action_type': permission.action_type,
                        'parent_permission_id': permission.parent_permission_id if permission.parent_permission else None
                    },
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    reason=f"Permiso actualizado via API"
                )

            return permission


class PermissionChangeAuditSerializer(serializers.ModelSerializer):
    """
    Serializer para registros de auditoría de permisos.
    Solo lectura.
    """
    permission_name = serializers.CharField(source='permission.name', read_only=True)
    permission_codename = serializers.CharField(source='permission.codename', read_only=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)
    target_user_username = serializers.CharField(source='target_user.username', read_only=True)
    target_group_name = serializers.CharField(source='target_group.name', read_only=True)

    class Meta:
        model = PermissionChangeAudit
        fields = [
            'id', 'permission', 'permission_name', 'permission_codename',
            'action', 'performed_by', 'performed_by_username',
            'target_user', 'target_user_username',
            'target_group', 'target_group_name',
            'before_value', 'after_value', 'reason',
            'ip_address', 'user_agent', 'created_date'
        ]
        read_only_fields = fields

class PermissionAssignmentSerializer(serializers.Serializer):
    """
    Serializer para asignar/revocar permisos a usuarios o grupos.
    """
    permission_id = serializers.IntegerField(required=True)
    user_id = serializers.IntegerField(required=False, allow_null=True)
    group_id = serializers.IntegerField(required=False, allow_null=True)
    action = serializers.ChoiceField(choices=['assign', 'revoke'], required=True)
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        group_id = attrs.get('group_id')

        if not user_id and not group_id:
            raise serializers.ValidationError("Debe especificar user_id o group_id")

        if user_id and group_id:
            raise serializers.ValidationError("Solo puede especificar user_id O group_id, no ambos")

        try:
            permission = CustomPermission.objects.get(id=attrs['permission_id'], state=True)
            attrs['permission'] = permission
        except CustomPermission.DoesNotExist:
            raise serializers.ValidationError({'permission_id': 'El permiso no existe o está inactivo'})

        if user_id:
            try:
                user = User.objects.get(id=user_id)
                attrs['user'] = user
            except User.DoesNotExist:
                raise serializers.ValidationError({'user_id': 'El usuario no existe'})

        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                attrs['group'] = group
            except Group.DoesNotExist:
                raise serializers.ValidationError({'group_id': 'El grupo no existe'})

        return attrs


