# usuarios/audit_log.py
"""
Audit logging system for tracking security-relevant actions.
"""
import logging
from django.utils import timezone
from functools import wraps

# Configurar logger específico para auditoría
audit_logger = logging.getLogger('audit')


class AuditLog:
    """
    Clase para gestionar el registro de auditoría de acciones sensibles.
    """
    
    @staticmethod
    def log_action(user, action, resource_type, resource_id=None, status='success', details=None, ip_address=None):
        """
        Registra una acción en el log de auditoría.
        
        Args:
            user: Usuario que realizó la acción
            action: Tipo de acción (create, update, delete, login, etc.)
            resource_type: Tipo de recurso afectado (User, Document, etc.)
            resource_id: ID del recurso afectado
            status: Estado de la acción (success, failed, denied)
            details: Detalles adicionales
            ip_address: Dirección IP del usuario
        """
        timestamp = timezone.now().isoformat()
        username = user.username if user and hasattr(user, 'username') else 'anonymous'
        
        log_entry = {
            'timestamp': timestamp,
            'user': username,
            'user_id': user.id if user and hasattr(user, 'id') else None,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'status': status,
            'ip_address': ip_address,
            'details': details or {}
        }
        
        # Formato del mensaje de log
        message = (
            f"[{status.upper()}] User '{username}' (ID: {log_entry['user_id']}) "
            f"performed '{action}' on {resource_type}"
        )
        if resource_id:
            message += f" (ID: {resource_id})"
        if ip_address:
            message += f" from IP {ip_address}"
        
        # Registrar según el nivel de severidad
        if status == 'failed' or status == 'denied':
            audit_logger.warning(message, extra=log_entry)
        else:
            audit_logger.info(message, extra=log_entry)
    
    @staticmethod
    def log_authentication(user, action='login', status='success', ip_address=None, details=None):
        """Registra eventos de autenticación"""
        AuditLog.log_action(
            user=user,
            action=action,
            resource_type='Authentication',
            status=status,
            ip_address=ip_address,
            details=details
        )
    
    @staticmethod
    def log_permission_denied(user, action, resource_type, resource_id=None, ip_address=None):
        """Registra intentos de acceso denegados"""
        AuditLog.log_action(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status='denied',
            ip_address=ip_address,
            details={'reason': 'Insufficient permissions'}
        )
    
    @staticmethod
    def log_user_management(user, action, target_user, ip_address=None, details=None):
        """Registra acciones de gestión de usuarios"""
        AuditLog.log_action(
            user=user,
            action=action,
            resource_type='User',
            resource_id=target_user.id if target_user else None,
            status='success',
            ip_address=ip_address,
            details=details or {'target_username': target_user.username if target_user else None}
        )
    
    @staticmethod
    def log_document_operation(user, action, document_id=None, ip_address=None, details=None):
        """Registra operaciones sobre documentos"""
        AuditLog.log_action(
            user=user,
            action=action,
            resource_type='Document',
            resource_id=document_id,
            status='success',
            ip_address=ip_address,
            details=details
        )
    
    @staticmethod
    def log_data_export(user, resource_type, ip_address=None, details=None):
        """Registra exportaciones de datos"""
        AuditLog.log_action(
            user=user,
            action='export',
            resource_type=resource_type,
            status='success',
            ip_address=ip_address,
            details=details
        )


def audit_action(action_type, resource_type):
    """
    Decorador para registrar automáticamente acciones en el log de auditoría.
    
    Uso:
        @audit_action('create', 'User')
        def create_user(request, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            ip_address = get_client_ip(request)
            user = request.user if hasattr(request, 'user') else None
            
            try:
                response = func(self, request, *args, **kwargs)
                
                # Si la respuesta es exitosa (200-299), registrar como success
                if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                    resource_id = None
                    if hasattr(response, 'data') and isinstance(response.data, dict):
                        resource_id = response.data.get('id')
                    
                    AuditLog.log_action(
                        user=user,
                        action=action_type,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        status='success',
                        ip_address=ip_address
                    )
                else:
                    AuditLog.log_action(
                        user=user,
                        action=action_type,
                        resource_type=resource_type,
                        status='failed',
                        ip_address=ip_address
                    )
                
                return response
            except Exception as e:
                AuditLog.log_action(
                    user=user,
                    action=action_type,
                    resource_type=resource_type,
                    status='failed',
                    ip_address=ip_address,
                    details={'error': str(e)}
                )
                raise
        
        return wrapper
    return decorator


def get_client_ip(request):
    """Obtiene la dirección IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
