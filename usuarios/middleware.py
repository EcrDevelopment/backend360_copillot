# usuarios/middleware.py
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs
from .audit_log import AuditLog, get_client_ip
import time

User = get_user_model()


@database_sync_to_async
def get_user(token_string):
    """
    Obtiene el usuario desde un string de Access Token JWT.
    """
    try:
        access_token = AccessToken(token_string)
        user = User.objects.get(id=access_token['user_id'])
        return user
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class JwtAuthMiddleware:
    """
    Middleware de autenticación JWT para Channels.
    Lee el token de un query parameter 'token' en la URL del WebSocket.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)

        token = query_params.get('token', [None])[0]

        if token:
            scope['user'] = await get_user(token)
        else:
            scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)


class AuditMiddleware:
    """
    Middleware para registrar acciones sensibles en el log de auditoría.
    """
    
    # Métodos que se consideran sensibles para auditoría
    AUDITED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Rutas que se deben auditar
    AUDITED_PATHS = [
        '/api/usuarios/',
        '/api/roles/',
        '/api/permissions/',
        '/api/importaciones/',
        '/api/documentos/',
        '/api/expedientes/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Guardar tiempo de inicio
        start_time = time.time()
        
        # Procesar la solicitud
        response = self.get_response(request)
        
        # Calcular tiempo de respuesta
        duration = time.time() - start_time
        
        # Auditar si es necesario
        if self._should_audit(request):
            self._audit_request(request, response, duration)
        
        return response
    
    def _should_audit(self, request):
        """Determina si la solicitud debe ser auditada"""
        # Solo auditar métodos sensibles
        if request.method not in self.AUDITED_METHODS:
            return False
        
        # Verificar si la ruta debe ser auditada
        path = request.path
        for audited_path in self.AUDITED_PATHS:
            if path.startswith(audited_path):
                return True
        
        return False
    
    def _audit_request(self, request, response, duration):
        """Registra la solicitud en el log de auditoría"""
        user = getattr(request, 'user', None)
        if not user or user.is_anonymous:
            return
        
        ip_address = get_client_ip(request)
        path = request.path
        method = request.method
        status_code = response.status_code
        
        # Determinar el tipo de recurso basado en la ruta
        resource_type = self._extract_resource_type(path)
        
        # Determinar el tipo de acción
        action = self._map_method_to_action(method)
        
        # Determinar el estado
        status = 'success' if 200 <= status_code < 400 else 'failed'
        
        # Detalles adicionales
        details = {
            'path': path,
            'method': method,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2)
        }
        
        AuditLog.log_action(
            user=user,
            action=action,
            resource_type=resource_type,
            status=status,
            ip_address=ip_address,
            details=details
        )
    
    def _extract_resource_type(self, path):
        """Extrae el tipo de recurso de la ruta"""
        if '/usuarios/' in path:
            return 'User'
        elif '/roles/' in path:
            return 'Role'
        elif '/permissions/' in path:
            return 'Permission'
        elif '/documentos/' in path:
            return 'Document'
        elif '/expedientes/' in path:
            return 'Expediente'
        elif '/importaciones/' in path:
            return 'Importacion'
        return 'Unknown'
    
    def _map_method_to_action(self, method):
        """Mapea el método HTTP a una acción de auditoría"""
        mapping = {
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        return mapping.get(method, 'unknown')


class SecurityHeadersMiddleware:
    """
    Middleware para agregar headers de seguridad a las respuestas.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Agregar headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (ajustar según necesidades)
        # response['Content-Security-Policy'] = "default-src 'self'"
        
        # Strict-Transport-Security (solo en producción con HTTPS)
        # if not settings.DEBUG:
        #     response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class RateLimitMiddleware:
    """
    Middleware simple de rate limiting para prevenir ataques de fuerza bruta.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}  # En producción, usar Redis o similar
        self.max_requests = 100  # Máximo de requests por ventana
        self.window_seconds = 60  # Ventana de tiempo en segundos
    
    def __call__(self, request):
        # Obtener identificador del cliente (IP)
        client_id = get_client_ip(request)
        
        # Limpiar contadores antiguos
        current_time = time.time()
        self._cleanup_old_entries(current_time)
        
        # Verificar límite de rate
        if self._is_rate_limited(client_id, current_time):
            # Log del intento de rate limit
            user = getattr(request, 'user', None)
            if user and not user.is_anonymous:
                AuditLog.log_action(
                    user=user,
                    action='rate_limit_exceeded',
                    resource_type='API',
                    status='denied',
                    ip_address=client_id,
                    details={'path': request.path}
                )
            
            from django.http import JsonResponse
            return JsonResponse(
                {'error': 'Rate limit exceeded. Please try again later.'},
                status=429
            )
        
        # Incrementar contador
        self._increment_counter(client_id, current_time)
        
        return self.get_response(request)
    
    def _is_rate_limited(self, client_id, current_time):
        """Verifica si el cliente ha excedido el límite de rate"""
        if client_id not in self.request_counts:
            return False
        
        requests = self.request_counts[client_id]
        recent_requests = [t for t in requests if current_time - t < self.window_seconds]
        
        return len(recent_requests) >= self.max_requests
    
    def _increment_counter(self, client_id, current_time):
        """Incrementa el contador de solicitudes del cliente"""
        if client_id not in self.request_counts:
            self.request_counts[client_id] = []
        
        self.request_counts[client_id].append(current_time)
    
    def _cleanup_old_entries(self, current_time):
        """Limpia entradas antiguas del contador"""
        for client_id in list(self.request_counts.keys()):
            self.request_counts[client_id] = [
                t for t in self.request_counts[client_id]
                if current_time - t < self.window_seconds
            ]
            
            # Eliminar cliente si no tiene requests recientes
            if not self.request_counts[client_id]:
                del self.request_counts[client_id]