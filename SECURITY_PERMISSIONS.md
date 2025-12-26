# Sistema de Roles y Permisos - Backend360

## Descripción General

Este documento describe el sistema mejorado de roles y permisos implementado para garantizar las mejores prácticas de seguridad y robustez en la aplicación.

## Roles Definidos

### 1. SystemAdmin
**Descripción**: Administrador del sistema con acceso completo.

**Permisos**:
- `mantenimiento.tabla_tipo_documentos`: Gestionar tablas de mantenimiento
- `sistema.gestionar_configuracion`: Administrar configuración del sistema
- `sistema.ver_logs_auditoria`: Ver registros de auditoría
- `sistema.gestionar_respaldos`: Gestionar respaldos del sistema

### 2. AccountsAdmin
**Descripción**: Administrador de usuarios y cuentas.

**Permisos**:
- `user.listar_usuarios`: Ver lista de usuarios
- `user.registrar_usuario`: Crear nuevos usuarios
- `user.editar_usuario`: Modificar usuarios existentes
- `user.eliminar_usuario`: Eliminar usuarios
- `user.asignar_roles`: Asignar roles a usuarios
- `user.gestionar_permisos`: Gestionar permisos de usuarios
- `user.ver_perfil`: Ver perfiles de usuarios

### 3. AccountsUser
**Descripción**: Usuario estándar con permisos básicos.

**Permisos**:
- `user.editar_perfil`: Editar su propio perfil
- `user.ver_perfil`: Ver su propio perfil
- `user.cambiar_password`: Cambiar su contraseña

### 4. ImportacionesAdmin
**Descripción**: Administrador del módulo de importaciones.

**Permisos**:
- `importaciones.ver_modulo`: Acceso al módulo
- `importaciones.ver_fletes_internacionales`: Ver fletes
- `importaciones.registrar_flete_internacional`: Crear fletes
- `importaciones.editar_flete_internacional`: Editar fletes
- `importaciones.eliminar_flete_internacional`: Eliminar fletes
- `importaciones.ver_reporte_flete`: Ver reportes de fletes
- `importaciones.ver_reporte_estibas`: Ver reportes de estibas
- `importaciones.administrar_documentos_dua`: Administrar documentos DUA
- `importaciones.administrar_expedientes_dua`: Administrar expedientes DUA
- `importaciones.crear_expedientes_dua`: Crear expedientes
- `importaciones.editar_expedientes_dua`: Editar expedientes
- `importaciones.eliminar_expedientes_dua`: Eliminar expedientes
- `importaciones.descargar_expedientes_dua`: Descargar expedientes
- Y más...

### 5. ImportacionesAsistente
**Descripción**: Asistente con permisos limitados en importaciones.

**Permisos**:
- Subconjunto de permisos de ImportacionesAdmin
- Sin permisos de eliminación
- Sin permisos de creación de fletes

### 6. AlmacenAdmin
**Descripción**: Administrador del módulo de almacén.

**Permisos**:
- `almacen.ver_modulo`: Acceso al módulo
- `almacen.gestionar_productos`: CRUD de productos
- `almacen.gestionar_stock`: Gestionar inventario
- `almacen.gestionar_movimientos`: Gestionar movimientos
- `almacen.ver_kardex`: Ver kardex
- `almacen.generar_reportes`: Generar reportes
- `almacen.realizar_ajustes`: Realizar ajustes de inventario

### 7. AlmacenOperador
**Descripción**: Operador de almacén con permisos limitados.

**Permisos**:
- `almacen.ver_modulo`: Acceso al módulo
- `almacen.ver_productos`: Ver productos (solo lectura)
- `almacen.ver_stock`: Ver stock (solo lectura)
- `almacen.registrar_movimientos`: Registrar movimientos
- `almacen.ver_kardex`: Ver kardex

### 8. Proveedor
**Descripción**: Proveedor externo con acceso limitado.

**Permisos**:
- `proveedor.cargar_documentos`: Cargar documentos
- `proveedor.administrar_documentos`: Gestionar sus documentos
- `proveedor.ver_documentos_propios`: Ver solo sus documentos
- `proveedor.descargar_documentos_propios`: Descargar sus documentos

## Clases de Permisos Personalizadas

### Permisos por Rol

1. **IsSystemAdmin**: Solo administradores del sistema
2. **IsAccountsAdmin**: Solo administradores de usuarios
3. **IsImportacionesAdmin**: Solo administradores de importaciones
4. **IsAlmacenAdmin**: Solo administradores de almacén

### Permisos de Capacidad

1. **CanManageUsers**: Puede gestionar usuarios (SystemAdmin o AccountsAdmin)
2. **CanAccessImportaciones**: Puede acceder al módulo de importaciones
3. **CanAccessAlmacen**: Puede acceder al módulo de almacén
4. **CanEditDocuments**: Puede editar documentos
5. **CanDeleteResource**: Puede eliminar recursos (solo admins)

### Permisos Especiales

1. **IsOwnerOrAdmin**: Puede acceder solo a sus propios recursos o ser admin
2. **ReadOnly**: Solo operaciones de lectura (GET, HEAD, OPTIONS)

## Validación de Entrada

### InputValidator

Clase utilitaria para validar y sanitizar entradas de usuario:

- **sanitize_html()**: Previene XSS escapando HTML
- **sanitize_string()**: Limpia strings de caracteres de control
- **validate_username()**: Valida formato de nombre de usuario
- **validate_password_strength()**: Valida fortaleza de contraseña
  - Mínimo 8 caracteres
  - Al menos una mayúscula
  - Al menos una minúscula
  - Al menos un número
  - Al menos un carácter especial
- **validate_email()**: Valida formato de email
- **validate_phone()**: Valida formato de teléfono
- **validate_ruc()**: Valida RUC peruano (11 dígitos)
- **sanitize_filename()**: Previene path traversal
- **validate_file_extension()**: Valida extensiones permitidas
- **validate_file_size()**: Valida tamaño máximo de archivo

## Sistema de Auditoría

### AuditLog

Sistema de registro de acciones sensibles:

```python
# Registrar una acción
AuditLog.log_action(
    user=request.user,
    action='create',
    resource_type='User',
    resource_id=user.id,
    status='success',
    ip_address=get_client_ip(request)
)
```

**Métodos especializados**:
- `log_authentication()`: Eventos de login/logout
- `log_permission_denied()`: Intentos de acceso denegados
- `log_user_management()`: Gestión de usuarios
- `log_document_operation()`: Operaciones sobre documentos
- `log_data_export()`: Exportaciones de datos

### Decorador de Auditoría

```python
@audit_action('create', 'Document')
def create_document(self, request, *args, **kwargs):
    # ... código ...
```

## Middleware de Seguridad

### 1. AuditMiddleware
Registra automáticamente acciones sensibles (POST, PUT, PATCH, DELETE) en rutas auditadas.

### 2. SecurityHeadersMiddleware
Agrega headers de seguridad a todas las respuestas:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 3. RateLimitMiddleware
Previene ataques de fuerza bruta:
- 100 requests por minuto por IP
- Responde con HTTP 429 si se excede

## Configuración

### settings.py

```python
# Middleware (agregar después de AuthenticationMiddleware)
MIDDLEWARE = [
    # ... otros middleware ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'usuarios.middleware.AuditMiddleware',
    'usuarios.middleware.SecurityHeadersMiddleware',
    'usuarios.middleware.RateLimitMiddleware',
    # ... resto de middleware ...
]

# Logging para auditoría
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/audit.log',
        },
    },
    'loggers': {
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Throttling para DRF
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

## Uso en Views

### Ejemplo 1: ViewSet con Permisos

```python
from usuarios.permissions import CanAccessImportaciones, IsImportacionesAdmin

class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    permission_classes = [IsAuthenticated, CanAccessImportaciones]
    
    def get_permissions(self):
        if self.action in ['destroy', 'create']:
            # Solo admins pueden crear/eliminar
            return [IsAuthenticated(), IsImportacionesAdmin()]
        return super().get_permissions()
```

### Ejemplo 2: APIView con Auditoría

```python
from usuarios.audit_log import AuditLog, get_client_ip

class CrearDocumentoView(APIView):
    permission_classes = [IsAuthenticated, CanEditDocuments]
    
    def post(self, request):
        # ... lógica de creación ...
        
        # Registrar en auditoría
        AuditLog.log_document_operation(
            user=request.user,
            action='create',
            document_id=documento.id,
            ip_address=get_client_ip(request)
        )
        
        return Response(...)
```

### Ejemplo 3: Validación de Entrada

```python
from usuarios.validators import InputValidator

class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    
    def validate_username(self, value):
        return InputValidator.validate_username(value)
    
    def validate_password(self, value):
        return InputValidator.validate_password_strength(value)
    
    def validate_email(self, value):
        return InputValidator.validate_email(value)
```

## Mejores Prácticas

1. **Siempre validar entrada del usuario** usando InputValidator
2. **Nunca usar AllowAny** en endpoints sensibles
3. **Registrar acciones críticas** en el log de auditoría
4. **Aplicar principio de mínimo privilegio** al asignar roles
5. **Verificar permisos a nivel de objeto** cuando sea necesario
6. **Usar HTTPS en producción** para proteger tokens JWT
7. **Rotar tokens periódicamente** usando ROTATE_REFRESH_TOKENS
8. **Monitorear logs de auditoría** regularmente
9. **Implementar 2FA** para usuarios privilegiados (futuro)
10. **Hacer backups regulares** de la base de datos

## Migración de Código Existente

### Paso 1: Actualizar imports

```python
# Antes
from rest_framework.permissions import AllowAny

# Después
from usuarios.permissions import CanAccessImportaciones
```

### Paso 2: Actualizar permission_classes

```python
# Antes
permission_classes = [AllowAny]

# Después
permission_classes = [IsAuthenticated, CanAccessImportaciones]
```

### Paso 3: Agregar validación

```python
# Antes
username = request.data.get('username')

# Después
from usuarios.validators import InputValidator
username = InputValidator.validate_username(request.data.get('username'))
```

### Paso 4: Agregar auditoría

```python
# Después de operación exitosa
AuditLog.log_action(
    user=request.user,
    action='update',
    resource_type='User',
    resource_id=user_id,
    ip_address=get_client_ip(request)
)
```

## Troubleshooting

### Error: "No tiene permisos requeridos"
- Verificar que el usuario tenga el rol correcto asignado
- Verificar que el rol tenga los permisos necesarios
- Verificar en usuarios/roles.py la definición del rol

### Error: "Rate limit exceeded"
- El cliente está enviando demasiadas requests
- Esperar 1 minuto o ajustar el límite en RateLimitMiddleware
- En producción, usar Redis para rate limiting distribuido

### Los logs de auditoría no se generan
- Verificar que el directorio logs/ exista
- Verificar permisos de escritura en el directorio
- Verificar configuración de LOGGING en settings.py

## Recursos Adicionales

- Django REST Framework Permissions: https://www.django-rest-framework.org/api-guide/permissions/
- Django Role Permissions: https://django-role-permissions.readthedocs.io/
- OWASP Security Best Practices: https://owasp.org/www-project-top-ten/
