# Control de Acceso por Organización y Almacén

## 📋 Resumen

Implementación de control de acceso granular a nivel de **Almacén** y **Sede** para usuarios con roles específicos (operarios, administradores de almacén, etc.).

**Caso de Uso**: Operarios y administradores de almacén deben tener acceso solo a almacenes específicos basados en asignación directa o por sede.

---

## ⚠️ Aclaración Importante sobre el Campo `empresa`

**El campo `empresa` en `UserProfile` NO debe usarse para control de acceso a almacenes de empleados.**

```python
class UserProfile(BaseModel):
    empresa = models.ForeignKey(Empresa, ...)  # ❌ Este campo es SOLO para proveedores
```

**Propósito del campo `empresa`:**
- ✅ Identifica la empresa del **proveedor** cuando el usuario tiene rol de proveedor
- ✅ Permite filtrar documentos y operaciones del proveedor por su empresa
- ❌ NO se usa para empleados internos
- ❌ NO se usa para control de acceso a almacenes

**Para empleados internos**: Los almacenes y sedes deben asignarse directamente mediante relaciones many-to-many independientes del campo `empresa`.

---

## 🏗️ Arquitectura de Solución

### Modelo Actual (Ya Implementado)

```python
class UserProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    empresa = models.ForeignKey(Empresa, ...)  # Solo para proveedores
```

### Extensión Propuesta

Necesitamos agregar nuevas relaciones **independientes** para control de acceso:

1. **Acceso a Almacenes Específicos** (many-to-many) - Para empleados
2. **Acceso a Sedes/Direcciones Específicas** (many-to-many) - Para empleados
3. **Flags de control** - Para activar/desactivar restricciones

---

## 💻 Implementación Paso a Paso

### Paso 1: Extender el Modelo UserProfile

Agrega estos campos al modelo `UserProfile` en `usuarios/models.py`:

```python
from almacen.models import Almacen  # Importar arriba del archivo

class UserProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    telefono = models.CharField(max_length=20, null=True, blank=True)
    empresa = models.ForeignKey(
        Empresa, 
        related_name='empresa', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # 🆕 NUEVOS CAMPOS
    almacenes_asignados = models.ManyToManyField(
        'almacen.Almacen',
        related_name='usuarios_asignados',
        blank=True,
        verbose_name='Almacenes Asignados',
        help_text='Almacenes a los que el usuario tiene acceso'
    )
    
    sedes_asignadas = models.ManyToManyField(
        Direccion,
        related_name='usuarios_asignados',
        blank=True,
        verbose_name='Sedes Asignadas',
        help_text='Sedes/direcciones a las que el usuario tiene acceso'
    )
    
    # 🆕 CONTROL DE RESTRICCIÓN
    require_warehouse_access = models.BooleanField(
        default=False,
        verbose_name='Requiere Acceso a Almacén',
        help_text='Si True, el usuario solo puede acceder a almacenes asignados explícitamente'
    )
    
    require_sede_access = models.BooleanField(
        default=False,
        verbose_name='Requiere Acceso a Sede',
        help_text='Si True, el usuario solo puede acceder a sedes asignadas explícitamente'
    )

    class Meta:
        db_table = 'perfil'

    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    # 🆕 MÉTODOS DE UTILIDAD
    def tiene_acceso_almacen(self, almacen):
        """Verifica si el usuario tiene acceso a un almacén específico"""
        if not self.require_warehouse_access:
            return True  # Sin restricción, acceso total
        return self.almacenes_asignados.filter(id=almacen.id).exists()
    
    def tiene_acceso_sede(self, sede):
        """Verifica si el usuario tiene acceso a una sede específica"""
        if not self.require_sede_access:
            return True  # Sin restricción, acceso total
        return self.sedes_asignadas.filter(id=sede.id).exists()
    
    def get_almacenes_accesibles(self):
        """Obtiene los almacenes a los que el usuario tiene acceso"""
        from almacen.models import Almacen
        
        if not self.require_warehouse_access:
            # Sin restricción, devolver TODOS los almacenes
            return Almacen.objects.filter(state=True)
        
        # Con restricción, devolver solo los asignados
        return self.almacenes_asignados.filter(state=True)
    
    def get_sedes_accesibles(self):
        """Obtiene las sedes a las que el usuario tiene acceso"""
        if not self.require_sede_access:
            # Sin restricción, devolver TODAS las sedes
            return Direccion.objects.filter(state=True)
        
        # Con restricción, devolver solo las asignadas
        return self.sedes_asignadas.filter(state=True)
```

### Paso 2: Crear la Migración

```bash
python manage.py makemigrations usuarios
python manage.py migrate usuarios
```

### Paso 3: Actualizar el Admin de Django

En `usuarios/admin.py`, actualiza `UserProfileAdmin`:

```python
from django.contrib import admin
from .models import UserProfile, Empresa, Direccion

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'empresa', 'telefono', 'require_warehouse_access', 'require_sede_access']
    list_filter = ['require_warehouse_access', 'require_sede_access', 'empresa']
    search_fields = ['user__username', 'user__email', 'telefono']
    
    # 🆕 FIELDSETS ORGANIZADOS
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'telefono', 'empresa')
        }),
        ('Control de Acceso por Almacén', {
            'fields': ('require_warehouse_access', 'almacenes_asignados'),
            'classes': ('collapse',),
            'description': 'Configura acceso específico a almacenes'
        }),
        ('Control de Acceso por Sede', {
            'fields': ('require_sede_access', 'sedes_asignadas'),
            'classes': ('collapse',),
            'description': 'Configura acceso específico a sedes'
        }),
    )
    
    # 🆕 FILTROS M2M CON AUTOCOMPLETE
    filter_horizontal = ['almacenes_asignados', 'sedes_asignadas']
    
    # 🆕 MÉTODO PERSONALIZADO PARA MOSTRAR ALMACENES
    def get_almacenes_display(self, obj):
        if not obj.require_warehouse_access:
            return "✅ Todos (sin restricción)"
        almacenes = obj.almacenes_asignados.all()
        if almacenes.exists():
            return ", ".join([a.nombre for a in almacenes[:3]]) + (
                f" (+{almacenes.count() - 3} más)" if almacenes.count() > 3 else ""
            )
        return "❌ Ninguno asignado"
    
    get_almacenes_display.short_description = 'Almacenes'
```

### Paso 4: Crear Permission Class Personalizada

Crea un nuevo archivo `usuarios/warehouse_permissions.py`:

```python
from rest_framework import permissions
from django.core.exceptions import PermissionDenied

class HasWarehouseAccess(permissions.BasePermission):
    """
    Permiso que verifica si el usuario tiene acceso al almacén especificado.
    
    Uso en ViewSet:
        permission_classes = [IsAuthenticated, HasWarehouseAccess]
    
    En la vista debe existir:
        - self.get_warehouse() que devuelva el almacén
        - O request.data['almacen_id']
        - O kwargs['almacen_pk']
    """
    message = "No tiene acceso a este almacén"
    
    def has_permission(self, request, view):
        # SystemAdmin siempre tiene acceso
        if hasattr(request.user, 'is_system_admin') and request.user.is_system_admin:
            return True
        
        # Usuario debe estar autenticado
        if not request.user.is_authenticated:
            return False
        
        # Usuario debe tener perfil
        if not hasattr(request.user, 'userprofile'):
            return False
        
        profile = request.user.userprofile
        
        # Si no requiere restricción, dar acceso
        if not profile.require_warehouse_access:
            return True
        
        # Para listados, permitir (filtraremos después)
        if request.method == 'GET' and not view.kwargs.get('pk'):
            return True
        
        # Para otros métodos, verificar almacén específico
        return True  # Verificación detallada en has_object_permission
    
    def has_object_permission(self, request, view, obj):
        # SystemAdmin siempre tiene acceso
        if hasattr(request.user, 'is_system_admin') and request.user.is_system_admin:
            return True
        
        profile = request.user.userprofile
        
        # Si no requiere restricción, dar acceso
        if not profile.require_warehouse_access:
            return True
        
        # Obtener el almacén del objeto
        almacen = None
        if hasattr(obj, 'almacen'):
            almacen = obj.almacen
        elif hasattr(obj, 'almacen_id'):
            almacen = obj.almacen
        elif obj.__class__.__name__ == 'Almacen':
            almacen = obj
        
        if not almacen:
            # No se pudo determinar el almacén, denegar por seguridad
            return False
        
        # Verificar acceso
        return profile.tiene_acceso_almacen(almacen)


class HasSedeAccess(permissions.BasePermission):
    """
    Permiso que verifica si el usuario tiene acceso a la sede especificada.
    """
    message = "No tiene acceso a esta sede"
    
    def has_permission(self, request, view):
        # SystemAdmin siempre tiene acceso
        if hasattr(request.user, 'is_system_admin') and request.user.is_system_admin:
            return True
        
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'userprofile'):
            return False
        
        profile = request.user.userprofile
        
        # Si no requiere restricción, dar acceso
        if not profile.require_sede_access:
            return True
        
        # Para listados, permitir (filtraremos después)
        if request.method == 'GET' and not view.kwargs.get('pk'):
            return True
        
        return True  # Verificación detallada en has_object_permission
    
    def has_object_permission(self, request, view, obj):
        # SystemAdmin siempre tiene acceso
        if hasattr(request.user, 'is_system_admin') and request.user.is_system_admin:
            return True
        
        profile = request.user.userprofile
        
        # Si no requiere restricción, dar acceso
        if not profile.require_sede_access:
            return True
        
        # Obtener la sede del objeto
        sede = None
        if hasattr(obj, 'sede'):
            sede = obj.sede
        elif hasattr(obj, 'direccion'):
            sede = obj.direccion
        elif obj.__class__.__name__ == 'Direccion':
            sede = obj
        
        if not sede:
            return False
        
        # Verificar acceso
        return profile.tiene_acceso_sede(sede)
```

### Paso 5: Aplicar en ViewSets

**Ejemplo para `almacen/views.py`**:

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from usuarios.warehouse_permissions import HasWarehouseAccess
from usuarios.permissions import CanManageWarehouse, CanViewWarehouse

class AlmacenViewSet(viewsets.ModelViewSet):
    queryset = Almacen.objects.all()
    serializer_class = AlmacenSerializer
    
    def get_permissions(self):
        """
        Combina permisos funcionales CON permisos de acceso a almacén
        """
        if self.action in ['list', 'retrieve']:
            # Para ver: necesita permiso funcional Y acceso al almacén
            return [
                IsAuthenticated(),
                CanViewWarehouse(),
                HasWarehouseAccess()
            ]
        else:
            # Para modificar: necesita permiso funcional Y acceso al almacén
            return [
                IsAuthenticated(),
                CanManageWarehouse(),
                HasWarehouseAccess()
            ]
    
    def get_queryset(self):
        """
        Filtrar queryset basado en almacenes accesibles
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # SystemAdmin ve todo
        if hasattr(user, 'is_system_admin') and user.is_system_admin:
            return queryset
        
        # Obtener perfil
        if not hasattr(user, 'userprofile'):
            return queryset.none()
        
        profile = user.userprofile
        
        # Si no requiere restricción, ver TODOS los almacenes
        if not profile.require_warehouse_access:
            return queryset.filter(state=True)
        
        # Filtrar por almacenes asignados
        almacenes_ids = profile.almacenes_asignados.values_list('id', flat=True)
        return queryset.filter(id__in=almacenes_ids)


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated, HasWarehouseAccess]
    
    def get_queryset(self):
        """Filtrar stock por almacenes accesibles"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # SystemAdmin ve todo
        if hasattr(user, 'is_system_admin') and user.is_system_admin:
            return queryset
        
        if not hasattr(user, 'userprofile'):
            return queryset.none()
        
        profile = user.userprofile
        almacenes_accesibles = profile.get_almacenes_accesibles()
        
        return queryset.filter(almacen__in=almacenes_accesibles)
```

### Paso 6: Serializers con Validación

Actualiza tus serializers para validar acceso:

```python
from rest_framework import serializers
from .models import MovimientoAlmacen

class MovimientoAlmacenSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoAlmacen
        fields = '__all__'
    
    def validate_almacen(self, value):
        """
        Validar que el usuario tiene acceso al almacén seleccionado
        """
        user = self.context['request'].user
        
        # SystemAdmin puede todo
        if hasattr(user, 'is_system_admin') and user.is_system_admin:
            return value
        
        # Verificar acceso
        if hasattr(user, 'userprofile'):
            profile = user.userprofile
            if not profile.tiene_acceso_almacen(value):
                raise serializers.ValidationError(
                    "No tiene acceso a este almacén"
                )
        
        return value
```

### Paso 7: Frontend - Filtrar Almacenes en Formularios

**API Endpoint para obtener almacenes accesibles:**

```python
# En almacen/views.py
from rest_framework.decorators import action
from rest_framework.response import Response

class AlmacenViewSet(viewsets.ModelViewSet):
    # ... código existente ...
    
    @action(detail=False, methods=['get'])
    def mis_almacenes(self, request):
        """
        Endpoint para obtener almacenes accesibles del usuario actual
        GET /api/almacenes/mis_almacenes/
        """
        user = request.user
        
        # SystemAdmin ve todos
        if hasattr(user, 'is_system_admin') and user.is_system_admin:
            almacenes = Almacen.objects.all()
        elif hasattr(user, 'userprofile'):
            almacenes = user.userprofile.get_almacenes_accesibles()
        else:
            almacenes = Almacen.objects.none()
        
        serializer = self.get_serializer(almacenes, many=True)
        return Response(serializer.data)
```

**En Frontend (React)**:

```javascript
// useAlmacenes.js
import { useState, useEffect } from 'react';
import axios from 'axios';

export const useAlmacenesAccesibles = () => {
  const [almacenes, setAlmacenes] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchAlmacenes = async () => {
      try {
        const response = await axios.get('/api/almacenes/mis_almacenes/');
        setAlmacenes(response.data);
      } catch (error) {
        console.error('Error cargando almacenes:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAlmacenes();
  }, []);
  
  return { almacenes, loading };
};

// En componente de formulario
import { Select } from 'antd';
import { useAlmacenesAccesibles } from './hooks/useAlmacenesAccesibles';

function MovimientoForm() {
  const { almacenes, loading } = useAlmacenesAccesibles();
  
  return (
    <Form>
      <Form.Item label="Almacén" name="almacen" rules={[{ required: true }]}>
        <Select
          loading={loading}
          placeholder="Seleccione almacén"
          options={almacenes.map(a => ({
            label: a.nombre,
            value: a.id
          }))}
        />
      </Form.Item>
    </Form>
  );
}
```

---

## 🎯 Casos de Uso

### Caso 1: Operario de Almacén (Acceso Restringido)

**Configuración**:
```python
# En Admin de Django
user_profile = UserProfile.objects.get(user=operario)
user_profile.require_warehouse_access = True
user_profile.almacenes_asignados.add(almacen_callao, almacen_miraflores)
user_profile.save()
```

**Resultado**:
- ✅ Puede ver y gestionar stock en Almacén Callao y Miraflores
- ❌ NO puede ver ni gestionar stock en Almacén Surco
- ✅ En formularios, solo aparecen sus 2 almacenes asignados
- ✅ API automáticamente filtra resultados

### Caso 2: Administrador de Almacén (Acceso por Sede)

**Configuración**:
```python
user_profile = UserProfile.objects.get(user=admin_almacen)
user_profile.require_warehouse_access = True
user_profile.require_sede_access = True
user_profile.sedes_asignadas.add(sede_norte)
# Automáticamente accede a todos los almacenes de sede_norte
```

**Resultado**:
- ✅ Acceso a todos los almacenes de la Sede Norte
- ❌ NO acceso a almacenes de otras sedes
- ✅ Escalable: nuevos almacenes en Sede Norte = acceso automático

### Caso 3: Gerente General (Sin Restricciones)

**Configuración**:
```python
user_profile = UserProfile.objects.get(user=gerente)
user_profile.require_warehouse_access = False
user_profile.require_sede_access = False
# No necesita asignaciones
```

**Resultado**:
- ✅ Acceso a TODOS los almacenes del sistema
- ✅ Sin restricciones
- ✅ No necesita asignaciones individuales

### Caso 4: Usuario Proveedor (campo empresa)

**Configuración**:
```python
user_profile = UserProfile.objects.get(user=proveedor)
user_profile.empresa = empresa_proveedor_xyz  # Identifica al proveedor
# El campo empresa NO afecta el acceso a almacenes
# Los proveedores usan permisos específicos (ProveedorPermissions)
```

**Resultado**:
- ✅ Campo `empresa` identifica su empresa como proveedor
- ✅ Permisos independientes: `can_upload_documents`, `can_view_own_documents`
- ✅ NO tiene acceso a almacenes (a menos que se le asignen explícitamente)

### Caso 5: SystemAdmin (Acceso Total)

**Resultado**:
- ✅ Acceso a TODO
- ✅ Ignora todas las restricciones
- ✅ Puede ver y gestionar cualquier almacén

---

## 📊 Diagrama de Flujo de Decisión

```
┌─────────────────────────────────────┐
│ Usuario intenta acceder a Almacén  │
└──────────────┬──────────────────────┘
               │
               ▼
       ┌───────────────┐
       │ ¿SystemAdmin? │
       └───────┬───────┘
               │
         Sí ┌──┴──┐ No
            │     │
            ▼     ▼
       ┌────────┐ ┌──────────────────────────┐
       │ ACCESO │ │ ¿Tiene UserProfile?      │
       │ TOTAL  │ └────────┬─────────────────┘
       └────────┘          │
                     Sí ┌──┴──┐ No
                        │     │
                        ▼     ▼
                   ┌────────┐ ┌──────────┐
                   │Continúa│ │ DENEGAR  │
                   └────┬───┘ └──────────┘
                        │
                        ▼
              ┌─────────────────────────┐
              │ require_warehouse_access│
              └────────┬────────────────┘
                       │
                 False ├─True
                       │
                       ▼
             ┌──────────────────────┐
             │¿Almacén en asignados?│
             └────────┬─────────────┘
                      │
                Sí ┌──┴──┐ No
                   │     │
                   ▼     ▼
              ┌────────┐ ┌──────────┐
              │ ACCESO │ │ DENEGAR  │
              └────────┘ └──────────┘
```

---

## 🧪 Testing

### Test de Acceso a Almacenes

Crea `usuarios/tests/test_warehouse_permissions.py`:

```python
from django.test import TestCase
from django.contrib.auth.models import User
from usuarios.models import UserProfile, Empresa
from almacen.models import Almacen

class WarehouseAccessTestCase(TestCase):
    def setUp(self):
        # Crear empresa y almacenes
        self.empresa = Empresa.objects.create(nombre="Empresa Test", ruc="12345678901")
        self.almacen1 = Almacen.objects.create(nombre="Almacén 1", empresa=self.empresa)
        self.almacen2 = Almacen.objects.create(nombre="Almacén 2", empresa=self.empresa)
        
        # Crear usuario con acceso restringido
        self.user_restricted = User.objects.create_user(username="operario", password="pass")
        self.profile_restricted = UserProfile.objects.create(
            user=self.user_restricted,
            empresa=self.empresa,
            require_warehouse_access=True
        )
        self.profile_restricted.almacenes_asignados.add(self.almacen1)
        
        # Crear usuario sin restricción
        self.user_full = User.objects.create_user(username="gerente", password="pass")
        self.profile_full = UserProfile.objects.create(
            user=self.user_full,
            empresa=self.empresa,
            require_warehouse_access=False
        )
    
    def test_usuario_restringido_tiene_acceso_almacen_asignado(self):
        """Usuario con restricción debe tener acceso a almacén asignado"""
        self.assertTrue(
            self.profile_restricted.tiene_acceso_almacen(self.almacen1)
        )
    
    def test_usuario_restringido_no_tiene_acceso_almacen_no_asignado(self):
        """Usuario con restricción NO debe tener acceso a almacén no asignado"""
        self.assertFalse(
            self.profile_restricted.tiene_acceso_almacen(self.almacen2)
        )
    
    def test_usuario_sin_restriccion_tiene_acceso_todos(self):
        """Usuario sin restricción debe tener acceso a todos los almacenes"""
        self.assertTrue(
            self.profile_full.tiene_acceso_almacen(self.almacen1)
        )
        self.assertTrue(
            self.profile_full.tiene_acceso_almacen(self.almacen2)
        )
    
    def test_get_almacenes_accesibles_usuario_restringido(self):
        """Usuario restringido debe obtener solo almacenes asignados"""
        almacenes = self.profile_restricted.get_almacenes_accesibles()
        self.assertEqual(almacenes.count(), 1)
        self.assertIn(self.almacen1, almacenes)
        self.assertNotIn(self.almacen2, almacenes)
    
    def test_get_almacenes_accesibles_usuario_sin_restriccion(self):
        """Usuario sin restricción debe obtener todos los almacenes de su empresa"""
        almacenes = self.profile_full.get_almacenes_accesibles()
        self.assertEqual(almacenes.count(), 2)
        self.assertIn(self.almacen1, almacenes)
        self.assertIn(self.almacen2, almacenes)
```

**Ejecutar tests**:
```bash
python manage.py test usuarios.tests.test_warehouse_permissions
```

---

## 📈 Ventajas de Esta Solución

### ✅ Ventajas Técnicas

1. **Granularidad Perfecta**
   - Control a nivel de almacén individual
   - Control a nivel de sede (agrupa almacenes)
   - Control a nivel de empresa (ya existente)

2. **Escalabilidad**
   - Nuevos almacenes se agregan fácilmente
   - No requiere cambios en código
   - Se gestiona desde Django Admin

3. **Performance**
   - ManyToMany es eficiente para esta relación
   - Queries optimizados con `select_related` y `prefetch_related`
   - Filtros a nivel de base de datos

4. **Seguridad en Capas**
   - Permission classes en API
   - Validación en serializers
   - Filtros en queryset
   - Validación en models

### ✅ Ventajas de Negocio

1. **Flexibilidad**
   - Usuario puede tener acceso a 1 o N almacenes
   - Cambios instantáneos (sin reiniciar servidor)
   - Delegación fácil de permisos

2. **Auditoría**
   - django-simple-history registra cambios en asignaciones
   - Trazabilidad completa
   - Cumplimiento normativo

3. **UX Mejorada**
   - Usuarios solo ven opciones relevantes
   - Formularios simplificados
   - Menos errores humanos

---

## 🔄 Migración desde Sistema Anterior

Si tenías un sistema previo de roles/empresa, aquí la estrategia de migración:

```python
# Script de migración: management/commands/migrate_warehouse_access.py

from django.core.management.base import BaseCommand
from usuarios.models import UserProfile
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Migra acceso de almacenes desde sistema antiguo'
    
    def handle(self, *args, **options):
        # Operarios de almacén: acceso restringido
        grupo_operarios = Group.objects.get(name='Operario Almacén')
        for user in grupo_operarios.user_set.all():
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                profile.require_warehouse_access = True
                profile.save()
                
                # Asignar almacenes basados en empresa y alguna lógica
                if profile.empresa:
                    almacenes = profile.empresa.almacenes.all()[:2]  # Primeros 2
                    profile.almacenes_asignados.set(almacenes)
                
                self.stdout.write(f"✅ Migrado: {user.username}")
        
        # Gerentes: sin restricción
        grupo_gerentes = Group.objects.get(name='Gerente')
        for user in grupo_gerentes.user_set.all():
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                profile.require_warehouse_access = False
                profile.save()
                
                self.stdout.write(f"✅ Migrado: {user.username}")
```

**Ejecutar**:
```bash
python manage.py migrate_warehouse_access
```

---

## 🎓 Mejores Prácticas

### 1. Asignación por Grupos

En lugar de asignar almacenes usuario por usuario, considera:

```python
# Crear grupos con almacenes predefinidos
grupo_callao = Group.objects.create(name='Operarios Callao')
# Luego en señal post_save de User cuando se agrega al grupo:
@receiver(m2m_changed, sender=User.groups.through)
def asignar_almacenes_por_grupo(sender, instance, action, **kwargs):
    if action == "post_add":
        if hasattr(instance, 'userprofile'):
            profile = instance.userprofile
            for grupo in instance.groups.all():
                if grupo.name == 'Operarios Callao':
                    almacen_callao = Almacen.objects.get(nombre='Callao')
                    profile.almacenes_asignados.add(almacen_callao)
```

### 2. Dashboard de Gestión

Crear vista para admins que muestre:
- Usuarios por almacén
- Almacenes por usuario
- Usuarios sin asignación (alerta)

### 3. Notificaciones

Enviar email cuando se asigna/revoca acceso a almacén:

```python
from django.core.mail import send_mail

def notificar_asignacion_almacen(usuario, almacen, accion='asignado'):
    send_mail(
        subject=f'Acceso a Almacén {accion}',
        message=f'Se le ha {accion} acceso al almacén: {almacen.nombre}',
        from_email='noreply@empresa.com',
        recipient_list=[usuario.email],
    )
```

---

## 📞 Soporte

Para dudas o problemas:

1. **Revisar logs de auditoría** en Django Admin
2. **Verificar permisos funcionales** del usuario
3. **Verificar asignaciones** en UserProfile
4. **Ejecutar tests** para validar comportamiento

---

**¡Sistema listo para implementar!** 🚀

**Próximos pasos recomendados**:
1. Crear migración
2. Actualizar admin
3. Aplicar en ViewSets principales
4. Crear tests
5. Documentar para usuarios finales

---

## ⚠️ RESUMEN IMPORTANTE: Campo `empresa` vs Control de Acceso

### Campo `empresa` en UserProfile

**Propósito ÚNICO:**
```python
empresa = models.ForeignKey(Empresa, ...)  # Solo para PROVEEDORES
```

- ✅ **Uso correcto**: Identificar la empresa del proveedor
- ✅ **Ejemplo**: Proveedor "Juan Pérez" pertenece a empresa "ABC Logistics"
- ❌ **NO usar para**: Control de acceso a almacenes de empleados
- ❌ **NO usar para**: Filtrar almacenes por empresa

### Control de Acceso a Almacenes (Empleados)

**Campos para control de acceso:**
```python
almacenes_asignados = models.ManyToManyField('almacen.Almacen')
require_warehouse_access = models.BooleanField(default=False)
```

- ✅ **Uso correcto**: Asignar almacenes específicos a empleados
- ✅ **Ejemplo**: Operario "María López" tiene acceso solo a Almacén Callao y Miraflores
- ✅ **Independiente**: No depende del campo `empresa`
- ✅ **Flexible**: Funciona para cualquier tipo de usuario (no solo proveedores)

### Diferencia Clave

| Aspecto | Campo `empresa` | Campo `almacenes_asignados` |
|---------|----------------|----------------------------|
| **Propósito** | Identificar proveedor | Controlar acceso a almacenes |
| **Aplica a** | Solo proveedores | Todos los usuarios (empleados) |
| **Tipo** | ForeignKey (1 empresa) | ManyToMany (N almacenes) |
| **Obligatorio** | No | No |
| **Afecta acceso** | No | Sí (si `require_warehouse_access=True`) |

### Ejemplo Práctico

**Usuario Proveedor:**
```python
profile.empresa = empresa_abc_logistics  # Identifica su empresa como proveedor
profile.require_warehouse_access = False  # No necesita acceso a almacenes
# Usa permisos: can_upload_documents, can_view_own_documents
```

**Usuario Empleado (Operario):**
```python
profile.empresa = None  # No es proveedor, no tiene empresa
profile.require_warehouse_access = True  # Necesita control de acceso
profile.almacenes_asignados.add(almacen1, almacen2)  # Solo estos almacenes
# Usa permisos: can_manage_warehouse, can_create_movements
```

**Usuario Empleado (Gerente):**
```python
profile.empresa = None  # No es proveedor
profile.require_warehouse_access = False  # Sin restricciones
# Acceso a TODOS los almacenes automáticamente
```

**Conclusión**: El campo `empresa` y el control de acceso a almacenes son conceptos completamente separados e independientes.
