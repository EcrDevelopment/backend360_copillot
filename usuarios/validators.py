# usuarios/validators.py
"""
Input validation and sanitization utilities for enhanced security.
"""
import re
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.html import escape

# Constantes para validación de contraseñas
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
SPECIAL_CHARS_PATTERN = r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]]'


class InputValidator:
    """
    Clase para validación y sanitización de entradas de usuario.
    """
    
    @staticmethod
    def sanitize_html(value):
        """
        Sanitiza HTML para prevenir XSS.
        Escapa todos los caracteres HTML especiales.
        """
        if not value:
            return value
        return escape(str(value))
    
    @staticmethod
    def sanitize_string(value, max_length=None):
        """
        Sanitiza una cadena de texto general.
        Remueve caracteres de control y espacios adicionales.
        """
        if not value:
            return value
        
        # Remover caracteres de control
        sanitized = re.sub(r'[\x00-\x1F\x7F]', '', str(value))
        
        # Remover espacios múltiples
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Limitar longitud si se especifica
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_username(username):
        """
        Valida un nombre de usuario.
        - Solo letras, números, guiones y guiones bajos
        - Entre 3 y 30 caracteres
        """
        if not username:
            raise ValidationError("El nombre de usuario es requerido.")
        
        if len(username) < 3 or len(username) > 30:
            raise ValidationError("El nombre de usuario debe tener entre 3 y 30 caracteres.")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError(
                "El nombre de usuario solo puede contener letras, números, guiones y guiones bajos."
            )
        
        return username
    
    @staticmethod
    def validate_password_strength(password):
        """
        Valida la fortaleza de una contraseña.
        Requisitos:
        - Mínimo 8 caracteres
        - Al menos una letra mayúscula
        - Al menos una letra minúscula
        - Al menos un número
        - Al menos un carácter especial
        """
        if not password:
            raise ValidationError("La contraseña es requerida.")
        
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ValidationError(f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.")
        
        if len(password) > PASSWORD_MAX_LENGTH:
            raise ValidationError(f"La contraseña no puede tener más de {PASSWORD_MAX_LENGTH} caracteres.")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("La contraseña debe contener al menos una letra minúscula.")
        
        if not re.search(r'[0-9]', password):
            raise ValidationError("La contraseña debe contener al menos un número.")
        
        if not re.search(SPECIAL_CHARS_PATTERN, password):
            raise ValidationError(
                "La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?\":{}|<>_-+=[])"
            )
        
        # Verificar que no tenga espacios
        if ' ' in password:
            raise ValidationError("La contraseña no puede contener espacios.")
        
        return password
    
    @staticmethod
    def validate_email(email):
        """
        Valida un correo electrónico.
        """
        if not email:
            raise ValidationError("El correo electrónico es requerido.")
        
        validator = EmailValidator()
        validator(email)
        
        return email.lower()
    
    @staticmethod
    def validate_phone(phone):
        """
        Valida un número de teléfono.
        Acepta formatos comunes con o sin código de país.
        """
        if not phone:
            return phone
        
        # Remover espacios, guiones y paréntesis
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Verificar que solo contenga números y opcionalmente un + al inicio
        if not re.match(r'^\+?\d{7,15}$', cleaned):
            raise ValidationError(
                "El número de teléfono debe contener entre 7 y 15 dígitos, "
                "opcionalmente precedido por un signo '+'."
            )
        
        return cleaned
    
    @staticmethod
    def validate_ruc(ruc):
        """
        Valida un RUC peruano (11 dígitos).
        """
        if not ruc:
            raise ValidationError("El RUC es requerido.")
        
        # Remover espacios y guiones
        cleaned = re.sub(r'[\s\-]', '', ruc)
        
        # Verificar que tenga 11 dígitos
        if not re.match(r'^\d{11}$', cleaned):
            raise ValidationError("El RUC debe contener exactamente 11 dígitos.")
        
        return cleaned
    
    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitiza un nombre de archivo para prevenir path traversal.
        """
        if not filename:
            return filename
        
        # Remover caracteres peligrosos
        sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Remover secuencias de path traversal
        sanitized = sanitized.replace('..', '')
        
        # Limitar longitud
        if len(sanitized) > 255:
            # Mantener la extensión si existe
            parts = sanitized.rsplit('.', 1)
            if len(parts) == 2:
                name, ext = parts
                sanitized = name[:250] + '.' + ext
            else:
                sanitized = sanitized[:255]
        
        return sanitized
    
    @staticmethod
    def validate_file_extension(filename, allowed_extensions):
        """
        Valida que un archivo tenga una extensión permitida.
        
        Args:
            filename: Nombre del archivo
            allowed_extensions: Lista de extensiones permitidas (ej: ['pdf', 'jpg', 'png'])
        """
        if not filename:
            raise ValidationError("El nombre de archivo es requerido.")
        
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if ext not in allowed_extensions:
            raise ValidationError(
                f"Extensión de archivo no permitida. "
                f"Extensiones permitidas: {', '.join(allowed_extensions)}"
            )
        
        return True
    
    @staticmethod
    def validate_file_size(file_size, max_size_mb=10):
        """
        Valida que un archivo no exceda el tamaño máximo permitido.
        
        Args:
            file_size: Tamaño del archivo en bytes
            max_size_mb: Tamaño máximo en megabytes
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise ValidationError(
                f"El archivo excede el tamaño máximo permitido de {max_size_mb}MB."
            )
        
        return True
    
    @staticmethod
    def sanitize_sql_like_pattern(pattern):
        """
        Sanitiza un patrón LIKE de SQL para prevenir inyección SQL.
        Escapa caracteres especiales de SQL LIKE.
        """
        if not pattern:
            return pattern
        
        # Escapar caracteres especiales de LIKE
        sanitized = pattern.replace('\\', '\\\\')
        sanitized = sanitized.replace('%', '\\%')
        sanitized = sanitized.replace('_', '\\_')
        
        return sanitized
    
    @staticmethod
    def validate_integer_range(value, min_value=None, max_value=None):
        """
        Valida que un valor entero esté en un rango específico.
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError("El valor debe ser un número entero.")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"El valor debe ser al menos {min_value}.")
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"El valor no debe exceder {max_value}.")
        
        return int_value
    
    @staticmethod
    def validate_url(url):
        """
        Valida una URL básica.
        """
        if not url:
            return url
        
        # Patrón básico de URL
        url_pattern = re.compile(
            r'^https?://'  # http:// o https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # o IP
            r'(?::\d+)?'  # puerto opcional
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            raise ValidationError("La URL no es válida.")
        
        return url


class SecureQueryBuilder:
    """
    Constructor de queries seguro para prevenir inyección SQL.
    """
    
    @staticmethod
    def build_safe_filter(**kwargs):
        """
        Construye filtros seguros para queries de Django ORM.
        Sanitiza valores de entrada.
        """
        safe_filters = {}
        
        for key, value in kwargs.items():
            if isinstance(value, str):
                # Sanitizar strings
                safe_filters[key] = InputValidator.sanitize_string(value)
            else:
                safe_filters[key] = value
        
        return safe_filters
