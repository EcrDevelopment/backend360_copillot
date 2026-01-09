# Sistema de Gestión Dinámica de Permisos

## Descripción General

Este documento describe cómo implementar un sistema que permite a los administradores crear, editar y eliminar permisos funcionales dinámicamente desde el frontend, sin necesidad de modificar código o crear migraciones.

**IMPORTANTE**: Esta implementación utiliza el sistema de auditoría existente con `django-simple-history` y `BaseModel`. Ver `AUDIT_INTEGRATION_GUIDE.md` para detalles completos de integración con auditoría.

## Arquitectura

### Componentes del Sistema

1. **Modelo de Permisos Dinámicos** - Almacena permisos personalizados creados por administradores
2. **API de Gestión de Permisos** - Endpoints CRUD para administrar permisos
3. **Interfaz de Administración** - UI en frontend para gestión de permisos
4. **Sistema de Validación** - Asegura que solo administradores pueden crear permisos
5. **Sistema de Auditoría** - Integrado con BaseModel y django-simple-history

## Implementación Backend

### 1. Modelo de Permisos Dinámicos

**NOTA**: Estos modelos heredan de `BaseModel` para aprovechar el sistema de auditoría existente con `django-simple-history`. Esto proporciona:
- Tracking automático de cambios (HistoricalRecords)
- Soft delete
- Campos de auditoría (created_date, modified_date, deleted_date)
- Tracking de usuario vía JWTCompatibleHistoryMiddleware

```python
# usuarios/models.py

from base.models import BaseModel
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

class CustomPermissionCategory(BaseModel):
    """
    Categorías para organizar permisos personalizados.
    Hereda de BaseModel para auditoría completa automática.
    Ejemplos: 'usuarios', 'almacen', 'importaciones', 'ventas', 'finanzas'
    """
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Para UI
    order = models.IntegerField(default=0)  # Para ordenar en UI
    is_active = models.BooleanField(default=True)
    
    # NO necesitamos created_at, updated_at, created_by - vienen de BaseModel
    # BaseModel proporciona: state, created_date, modified_date, deleted_date, historical
    
    class Meta:
        verbose_name = 'Categoría de Permiso'
        verbose_name_plural = 'Categorías de Permisos'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.display_name


class CustomPermission(BaseModel):
    """
    Permisos personalizados creados dinámicamente por administradores.
    Hereda de BaseModel para auditoría completa automática.
    Se sincronizan automáticamente con django.contrib.auth.models.Permission
    """
    PERMISSION_TYPES = [
        ('modular', 'Modular (Alto Nivel)'),
        ('granular', 'Granular (Acción Específica)'),
    ]
    
    ACTION_TYPES = [
        ('manage', 'Gestionar (Completo)'),
        ('view', 'Ver (Solo Lectura)'),
        ('create', 'Crear'),
        ('edit', 'Editar'),
        ('delete', 'Eliminar'),
        ('approve', 'Aprobar'),
        ('report', 'Reportes'),
        ('export', 'Exportar'),
        ('custom', 'Personalizado'),
    ]
    
    # Información básica
    category = models.ForeignKey(CustomPermissionCategory, on_delete=models.CASCADE, related_name='permissions')
    codename = models.CharField(max_length=100, unique=True, 
                                help_text="Nombre técnico del permiso (ej: can_manage_sales)")
    name = models.CharField(max_length=255, 
                           help_text="Nombre descriptivo (ej: 'Puede gestionar ventas')")
    description = models.TextField(blank=True, null=True)
    
    # Clasificación
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES, default='modular')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, default='custom')
    
    # Jerarquía de permisos
    parent_permission = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='child_permissions',
                                         help_text="Permiso padre (ej: can_manage incluye can_create, can_edit, can_delete)")
    
    # Permisos relacionados (para OR logic)
    equivalent_permissions = models.ManyToManyField('self', blank=True, symmetrical=True,
                                                    help_text="Permisos equivalentes que también otorgan este acceso")
    
    # Estado
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False, 
                                    help_text="Permisos del sistema no pueden ser eliminados")
    order = models.IntegerField(default=0)
    
    # NO necesitamos campos de auditoría - vienen de BaseModel
    # BaseModel proporciona: state, created_date, modified_date, deleted_date, historical
    # El tracking de usuario se maneja automáticamente vía HistoricalRecords + JWTCompatibleHistoryMiddleware
    
    # Referencia a Permission de Django
    django_permission = models.OneToOneField(Permission, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='custom_permission')
    
    class Meta:
        verbose_name = 'Permiso Personalizado'
        verbose_name_plural = 'Permisos Personalizados'
        ordering = ['category', 'order', 'codename']
    
    def __str__(self):
        return f"{self.category.name}.{self.codename}"
    
    def clean(self):
        """Validaciones personalizadas"""
        # Validar formato del codename
        if not self.codename.startswith('can_'):
            raise ValidationError({'codename': 'El codename debe empezar con "can_"'})
        
        # Validar que no sea circular la jerarquía
        if self.parent_permission:
            if self.parent_permission == self:
                raise ValidationError({'parent_permission': 'Un permiso no puede ser padre de sí mismo'})
            
            # Verificar que no haya ciclos
            parent = self.parent_permission
            visited = {self.id}
            while parent:
                if parent.id in visited:
                    raise ValidationError({'parent_permission': 'Jerarquía circular detectada'})
                visited.add(parent.id)
                parent = parent.parent_permission
    
    def save(self, *args, **kwargs):
        """Al guardar, sincronizar con Permission de Django"""
        self.full_clean()
        
        # Crear o actualizar Permission de Django
        if not self.django_permission:
            # Obtener o crear ContentType para CustomPermission
            content_type = ContentType.objects.get_for_model(CustomPermission)
            
            # Crear Permission de Django
            django_perm, created = Permission.objects.get_or_create(
                codename=self.codename,
                content_type=content_type,
                defaults={'name': self.name}
            )
            self.django_permission = django_perm
        else:
            # Actualizar Permission existente
            self.django_permission.name = self.name
            self.django_permission.save()
        
        super().save(*args, **kwargs)
    
    def delete(self, using=None, keep_parents=False):
        """
        Prevenir eliminación de permisos del sistema.
        BaseModel.delete() hace soft delete automáticamente.
        """
        if self.is_system:
            raise ValidationError("Los permisos del sistema no pueden ser eliminados")
        
        # BaseModel.delete() hace soft delete (state=False, deleted_date=now)
        # No elimina físicamente, solo marca como inactivo
        super().delete(using=using, keep_parents=keep_parents)
    
    def hard_delete(self):
        """
        Eliminar permanentemente incluyendo Permission de Django.
        Solo usar cuando realmente sea necesario.
        """
        if self.is_system:
            raise ValidationError("Los permisos del sistema no pueden ser eliminados")
        
        # Eliminar Permission de Django asociado
        if self.django_permission:
            self.django_permission.delete()
        
        # Hard delete del BaseModel
        super().hard_delete()
    
    def get_full_permission_string(self):
        """Retorna el string completo del permiso (ej: usuarios.can_manage_users)"""
        return f"{self.category.name}.{self.codename}"
    
    def get_all_implied_permissions(self):
        """
        Retorna todos los permisos que este permiso implica (hijos en jerarquía).
        Útil para implementar la lógica: can_manage incluye can_create, can_edit, can_delete.
        Solo retorna permisos activos (state=True).
        """
        implied = [self]
        for child in self.child_permissions.filter(is_active=True, state=True):
            implied.extend(child.get_all_implied_permissions())
        return implied
```

### 2. Serializers para la API

**NOTA**: Los serializers usan los campos de BaseModel (created_date, modified_date, state) en lugar de campos personalizados.

```python
# usuarios/serializers.py

from rest_framework import serializers
from .models import CustomPermission, CustomPermissionCategory

class CustomPermissionCategorySerializer(serializers.ModelSerializer):
    permissions_count = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomPermissionCategory
        fields = ['id', 'name', 'display_name', 'description', 'icon', 
                 'order', 'is_active', 'permissions_count', 
                 'created_date', 'modified_date', 'state', 'created_by_username']
        read_only_fields = ['created_date', 'modified_date', 'state']
    
    def get_permissions_count(self, obj):
        return obj.permissions.filter(is_active=True, state=True).count()
    
    def get_created_by_username(self, obj):
        # BaseModel + HistoricalRecords permite acceder al primer registro histórico
        first_history = obj.historical.first()
        return first_history.history_user.username if first_history and first_history.history_user else None


class CustomPermissionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_display = serializers.CharField(source='category.display_name', read_only=True)
    full_permission = serializers.CharField(source='get_full_permission_string', read_only=True)
    parent_permission_name = serializers.CharField(source='parent_permission.codename', read_only=True, allow_null=True)
    child_permissions = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomPermission
        fields = [
            'id', 'category', 'category_name', 'category_display',
            'codename', 'name', 'description', 'full_permission',
            'permission_type', 'action_type',
            'parent_permission', 'parent_permission_name',
            'child_permissions', 'equivalent_permissions',
            'is_active', 'is_system', 'order',
            'created_date', 'modified_date', 'deleted_date', 'state',
            'created_by_username'
        ]
        read_only_fields = ['created_date', 'modified_date', 'deleted_date', 'state', 'django_permission']
    
    def get_child_permissions(self, obj):
        children = obj.child_permissions.filter(is_active=True, state=True).values('id', 'codename', 'name')
        return list(children)
    
    def get_created_by_username(self, obj):
        # Acceder al historial para obtener quién creó el permiso
        first_history = obj.historical.first()
        return first_history.history_user.username if first_history and first_history.history_user else None
    
    def validate_codename(self, value):
        """Validar formato del codename"""
        if not value.startswith('can_'):
            raise serializers.ValidationError("El codename debe empezar con 'can_'")
        
        # Validar caracteres permitidos
        import re
        if not re.match(r'^can_[a-z_]+$', value):
            raise serializers.ValidationError(
                "El codename solo puede contener letras minúsculas y guiones bajos después de 'can_'"
            )
        
        return value
    
    def validate(self, data):
        """Validaciones a nivel de objeto"""
        # Si es permiso granular, debe tener padre
        if data.get('permission_type') == 'granular' and not data.get('parent_permission'):
            raise serializers.ValidationError({
                'parent_permission': 'Los permisos granulares deben tener un permiso padre modular'
            })
        
        return data
    
    def create(self, validated_data):
        # Asignar usuario creador
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PermissionAssignmentSerializer(serializers.Serializer):
    """Serializer para asignar/quitar permisos a usuarios o grupos"""
    permission_ids = serializers.ListField(child=serializers.IntegerField())
    user_ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=True)
    group_ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=True)
    action = serializers.ChoiceField(choices=['add', 'remove'])
```

### 3. ViewSets para la API

```python
# usuarios/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from .models import CustomPermission, CustomPermissionCategory
from .serializers import CustomPermissionSerializer, CustomPermissionCategorySerializer, PermissionAssignmentSerializer
from .permissions import IsSystemAdmin

class CustomPermissionCategoryViewSet(viewsets.ModelViewSet):
    """
    API para gestionar categorías de permisos.
    Solo administradores del sistema pueden crear/modificar categorías.
    """
    queryset = CustomPermissionCategory.objects.all()
    serializer_class = CustomPermissionCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Solo SystemAdmin puede crear/editar/eliminar categorías"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsSystemAdmin()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """Obtener todos los permisos de una categoría"""
        category = self.get_object()
        perms = category.permissions.filter(is_active=True)
        serializer = CustomPermissionSerializer(perms, many=True)
        return Response(serializer.data)


class CustomPermissionViewSet(viewsets.ModelViewSet):
    """
    API para gestionar permisos personalizados.
    Solo administradores del sistema pueden crear/modificar permisos.
    """
    queryset = CustomPermission.objects.filter(is_active=True)
    serializer_class = CustomPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['category', 'permission_type', 'action_type', 'is_system']
    search_fields = ['codename', 'name', 'description']
    ordering_fields = ['order', 'codename', 'created_at']
    ordering = ['category', 'order']
    
    def get_permissions(self):
        """Solo SystemAdmin puede crear/editar/eliminar permisos"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsSystemAdmin()]
        return [permissions.IsAuthenticated()]
    
    def destroy(self, request, *args, **kwargs):
        """Prevenir eliminación de permisos del sistema"""
        instance = self.get_object()
        if instance.is_system:
            return Response(
                {'error': 'Los permisos del sistema no pueden ser eliminados'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """Obtener jerarquía completa de un permiso (padre e hijos)"""
        permission = self.get_object()
        
        # Obtener padre y todos los ancestros
        ancestors = []
        parent = permission.parent_permission
        while parent:
            ancestors.append({
                'id': parent.id,
                'codename': parent.codename,
                'name': parent.name
            })
            parent = parent.parent_permission
        
        # Obtener todos los hijos (recursivo)
        def get_children(perm):
            children = []
            for child in perm.child_permissions.filter(is_active=True):
                children.append({
                    'id': child.id,
                    'codename': child.codename,
                    'name': child.name,
                    'children': get_children(child)
                })
            return children
        
        return Response({
            'permission': CustomPermissionSerializer(permission).data,
            'ancestors': ancestors,
            'descendants': get_children(permission)
        })
    
    @action(detail=False, methods=['post'])
    def assign(self, request):
        """Asignar permisos a usuarios o grupos"""
        serializer = PermissionAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        permission_ids = serializer.validated_data['permission_ids']
        user_ids = serializer.validated_data.get('user_ids', [])
        group_ids = serializer.validated_data.get('group_ids', [])
        action_type = serializer.validated_data['action']
        
        # Obtener permisos de Django
        custom_perms = CustomPermission.objects.filter(id__in=permission_ids)
        django_perms = [cp.django_permission for cp in custom_perms if cp.django_permission]
        
        # Asignar/quitar a usuarios
        if user_ids:
            users = User.objects.filter(id__in=user_ids)
            for user in users:
                if action_type == 'add':
                    user.user_permissions.add(*django_perms)
                else:
                    user.user_permissions.remove(*django_perms)
        
        # Asignar/quitar a grupos
        if group_ids:
            groups = Group.objects.filter(id__in=group_ids)
            for group in groups:
                if action_type == 'add':
                    group.permissions.add(*django_perms)
                else:
                    group.permissions.remove(*django_perms)
        
        return Response({
            'message': f'Permisos {action_type}ed successfully',
            'affected_users': len(user_ids),
            'affected_groups': len(group_ids)
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Crear múltiples permisos a la vez (útil para configuración inicial)"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

### 4. URLs

```python
# usuarios/urls.py (agregar a las URLs existentes)

from rest_framework.routers import DefaultRouter
from .views import CustomPermissionViewSet, CustomPermissionCategoryViewSet

router = DefaultRouter()
router.register(r'custom-permissions', CustomPermissionViewSet, basename='custom-permission')
router.register(r'permission-categories', CustomPermissionCategoryViewSet, basename='permission-category')

urlpatterns = router.urls
```

## Implementación Frontend

### 1. Interfaz de Gestión de Permisos

```javascript
// pages/admin/PermissionManagement.jsx

import React, { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Switch,
  message, Popconfirm, Tabs, Tag, Space, Tree
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, 
  LockOutlined, UnlockOutlined, FolderOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

const PermissionManagement = () => {
  const [permissions, setPermissions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [categoryModalVisible, setCategoryModalVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState(null);
  const [form] = Form.useForm();
  const [categoryForm] = Form.useForm();

  useEffect(() => {
    fetchCategories();
    fetchPermissions();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/api/accounts/permission-categories/');
      setCategories(response.data);
    } catch (error) {
      message.error('Error al cargar categorías');
    }
  };

  const fetchPermissions = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/accounts/custom-permissions/');
      setPermissions(response.data);
    } catch (error) {
      message.error('Error al cargar permisos');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingPermission(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingPermission(record);
    form.setFieldsValue({
      category: record.category,
      codename: record.codename,
      name: record.name,
      description: record.description,
      permission_type: record.permission_type,
      action_type: record.action_type,
      parent_permission: record.parent_permission,
      is_active: record.is_active,
      order: record.order,
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values) => {
    try {
      if (editingPermission) {
        await axios.put(
          `/api/accounts/custom-permissions/${editingPermission.id}/`,
          values
        );
        message.success('Permiso actualizado exitosamente');
      } else {
        await axios.post('/api/accounts/custom-permissions/', values);
        message.success('Permiso creado exitosamente');
      }
      setModalVisible(false);
      fetchPermissions();
    } catch (error) {
      message.error('Error al guardar permiso: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`/api/accounts/custom-permissions/${id}/`);
      message.success('Permiso eliminado exitosamente');
      fetchPermissions();
    } catch (error) {
      message.error('Error al eliminar permiso');
    }
  };

  const handleCreateCategory = async (values) => {
    try {
      await axios.post('/api/accounts/permission-categories/', values);
      message.success('Categoría creada exitosamente');
      setCategoryModalVisible(false);
      categoryForm.resetFields();
      fetchCategories();
    } catch (error) {
      message.error('Error al crear categoría');
    }
  };

  const columns = [
    {
      title: 'Categoría',
      dataIndex: 'category_display',
      key: 'category',
      filters: categories.map(cat => ({ text: cat.display_name, value: cat.id })),
      onFilter: (value, record) => record.category === value,
    },
    {
      title: 'Código',
      dataIndex: 'codename',
      key: 'codename',
      render: (text, record) => (
        <Space>
          <code>{record.full_permission}</code>
          {record.is_system && <Tag color="blue">Sistema</Tag>}
        </Space>
      ),
    },
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Tipo',
      dataIndex: 'permission_type',
      key: 'type',
      render: (type) => (
        <Tag color={type === 'modular' ? 'green' : 'orange'}>
          {type === 'modular' ? 'Modular' : 'Granular'}
        </Tag>
      ),
    },
    {
      title: 'Acción',
      dataIndex: 'action_type',
      key: 'action',
    },
    {
      title: 'Padre',
      dataIndex: 'parent_permission_name',
      key: 'parent',
      render: (parent) => parent || '-',
    },
    {
      title: 'Hijos',
      dataIndex: 'child_permissions',
      key: 'children',
      render: (children) => children?.length || 0,
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'status',
      render: (active) => (
        <Tag color={active ? 'success' : 'default'}>
          {active ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Editar
          </Button>
          {!record.is_system && (
            <Popconfirm
              title="¿Está seguro de eliminar este permiso?"
              onConfirm={() => handleDelete(record.id)}
              okText="Sí"
              cancelText="No"
            >
              <Button type="link" danger icon={<DeleteOutlined />}>
                Eliminar
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div className="permission-management">
      <div className="page-header">
        <h2>Gestión de Permisos</h2>
        <Space>
          <Button
            type="default"
            icon={<FolderOutlined />}
            onClick={() => setCategoryModalVisible(true)}
          >
            Nueva Categoría
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            Nuevo Permiso
          </Button>
        </Space>
      </div>

      <Tabs defaultActiveKey="permissions">
        <TabPane tab="Permisos" key="permissions">
          <Table
            columns={columns}
            dataSource={permissions}
            loading={loading}
            rowKey="id"
            pagination={{ pageSize: 20 }}
          />
        </TabPane>
        
        <TabPane tab="Categorías" key="categories">
          <Table
            dataSource={categories}
            rowKey="id"
            columns={[
              { title: 'Nombre', dataIndex: 'display_name' },
              { title: 'Código', dataIndex: 'name', render: text => <code>{text}</code> },
              { title: 'Permisos', dataIndex: 'permissions_count' },
              { title: 'Orden', dataIndex: 'order' },
            ]}
          />
        </TabPane>
      </Tabs>

      {/* Modal para Crear/Editar Permiso */}
      <Modal
        title={editingPermission ? 'Editar Permiso' : 'Nuevo Permiso'}
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            permission_type: 'modular',
            action_type: 'custom',
            is_active: true,
            order: 0,
          }}
        >
          <Form.Item
            name="category"
            label="Categoría"
            rules={[{ required: true, message: 'Seleccione una categoría' }]}
          >
            <Select placeholder="Seleccione categoría">
              {categories.map(cat => (
                <Option key={cat.id} value={cat.id}>{cat.display_name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="codename"
            label="Código del Permiso"
            rules={[
              { required: true, message: 'Ingrese el código' },
              { pattern: /^can_[a-z_]+$/, message: 'Debe empezar con "can_" y solo minúsculas con guiones bajos' }
            ]}
            extra="Ejemplo: can_manage_sales, can_view_reports"
          >
            <Input placeholder="can_manage_something" disabled={!!editingPermission} />
          </Form.Item>

          <Form.Item
            name="name"
            label="Nombre Descriptivo"
            rules={[{ required: true, message: 'Ingrese el nombre' }]}
          >
            <Input placeholder="Puede gestionar ventas" />
          </Form.Item>

          <Form.Item name="description" label="Descripción">
            <TextArea rows={3} placeholder="Descripción detallada del permiso" />
          </Form.Item>

          <Form.Item
            name="permission_type"
            label="Tipo de Permiso"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="modular">Modular (Alto Nivel)</Option>
              <Option value="granular">Granular (Acción Específica)</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="action_type"
            label="Tipo de Acción"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="manage">Gestionar (Completo)</Option>
              <Option value="view">Ver (Solo Lectura)</Option>
              <Option value="create">Crear</Option>
              <Option value="edit">Editar</Option>
              <Option value="delete">Eliminar</Option>
              <Option value="approve">Aprobar</Option>
              <Option value="report">Reportes</Option>
              <Option value="export">Exportar</Option>
              <Option value="custom">Personalizado</Option>
            </Select>
          </Form.Item>

          <Form.Item name="parent_permission" label="Permiso Padre (Opcional)">
            <Select
              placeholder="Seleccione permiso padre"
              allowClear
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {permissions
                .filter(p => p.permission_type === 'modular' && p.id !== editingPermission?.id)
                .map(p => (
                  <Option key={p.id} value={p.id}>
                    {p.full_permission} - {p.name}
                  </Option>
                ))}
            </Select>
          </Form.Item>

          <Form.Item name="order" label="Orden">
            <Input type="number" />
          </Form.Item>

          <Form.Item name="is_active" label="Activo" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingPermission ? 'Actualizar' : 'Crear'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                Cancelar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal para Nueva Categoría */}
      <Modal
        title="Nueva Categoría"
        visible={categoryModalVisible}
        onCancel={() => setCategoryModalVisible(false)}
        footer={null}
      >
        <Form
          form={categoryForm}
          layout="vertical"
          onFinish={handleCreateCategory}
          initialValues={{ is_active: true, order: 0 }}
        >
          <Form.Item
            name="name"
            label="Código"
            rules={[
              { required: true, message: 'Ingrese el código' },
              { pattern: /^[a-z_]+$/, message: 'Solo minúsculas y guiones bajos' }
            ]}
          >
            <Input placeholder="ventas" />
          </Form.Item>

          <Form.Item
            name="display_name"
            label="Nombre para Mostrar"
            rules={[{ required: true, message: 'Ingrese el nombre' }]}
          >
            <Input placeholder="Ventas" />
          </Form.Item>

          <Form.Item name="description" label="Descripción">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item name="icon" label="Icono (Opcional)">
            <Input placeholder="shopping-cart" />
          </Form.Item>

          <Form.Item name="order" label="Orden">
            <Input type="number" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Crear
              </Button>
              <Button onClick={() => setCategoryModalVisible(false)}>
                Cancelar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PermissionManagement;
```

### 2. Integración con Menu Config

```javascript
// utils/permissionLoader.js

import axios from 'axios';

/**
 * Carga permisos dinámicos desde el backend
 */
export const loadDynamicPermissions = async () => {
  try {
    const response = await axios.get('/api/accounts/custom-permissions/?is_active=true');
    return response.data;
  } catch (error) {
    console.error('Error loading dynamic permissions:', error);
    return [];
  }
};

/**
 * Carga categorías de permisos
 */
export const loadPermissionCategories = async () => {
  try {
    const response = await axios.get('/api/accounts/permission-categories/?is_active=true');
    return response.data;
  } catch (error) {
    console.error('Error loading categories:', error);
    return [];
  }
};

/**
 * Construye menú dinámico basado en permisos disponibles
 */
export const buildDynamicMenu = (categories, permissions, userPermissions) => {
  const menu = [];
  
  categories.forEach(category => {
    // Filtrar permisos de esta categoría que el usuario tiene
    const categoryPermissions = permissions.filter(p => 
      p.category === category.id && 
      userPermissions.includes(p.full_permission)
    );
    
    if (categoryPermissions.length > 0) {
      const menuItem = {
        key: category.name,
        label: category.display_name,
        icon: category.icon,
        permission: categoryPermissions[0].full_permission, // Permiso mínimo para ver
        children: categoryPermissions.map(perm => ({
          key: `${category.name}-${perm.codename}`,
          label: perm.name,
          permission: perm.full_permission,
          to: `/${category.name}/${perm.codename}`,
        }))
      };
      
      menu.push(menuItem);
    }
  });
  
  return menu;
};
```

## Migración

### Script de Migración para Permisos Existentes

```python
# usuarios/management/commands/migrate_to_dynamic_permissions.py

from django.core.management.base import BaseCommand
from usuarios.models import CustomPermission, CustomPermissionCategory, UsuariosPermissions, AlmacenPermissions, ImportacionesPermissions

class Command(BaseCommand):
    help = 'Migra permisos existentes al sistema dinámico'
    
    def handle(self, *args, **options):
        # Crear categorías
        usuarios_cat, _ = CustomPermissionCategory.objects.get_or_create(
            name='usuarios',
            defaults={
                'display_name': 'Usuarios',
                'description': 'Permisos para gestión de usuarios',
                'order': 1
            }
        )
        
        almacen_cat, _ = CustomPermissionCategory.objects.get_or_create(
            name='almacen',
            defaults={
                'display_name': 'Almacén',
                'description': 'Permisos para gestión de almacén',
                'order': 2
            }
        )
        
        importaciones_cat, _ = CustomPermissionCategory.objects.get_or_create(
            name='importaciones',
            defaults={
                'display_name': 'Importaciones',
                'description': 'Permisos para gestión de importaciones',
                'order': 3
            }
        )
        
        # Migrar permisos de usuarios
        usuarios_perms = [
            ('can_manage_users', 'Puede gestionar usuarios', 'modular', 'manage', None, True),
            ('can_view_users', 'Puede ver usuarios', 'modular', 'view', None, True),
            ('can_create_users', 'Puede crear usuarios', 'granular', 'create', 'can_manage_users', True),
            ('can_edit_users', 'Puede editar usuarios', 'granular', 'edit', 'can_manage_users', True),
            ('can_delete_users', 'Puede eliminar usuarios', 'granular', 'delete', 'can_manage_users', True),
        ]
        
        for codename, name, perm_type, action_type, parent_codename, is_system in usuarios_perms:
            parent = None
            if parent_codename:
                parent = CustomPermission.objects.filter(codename=parent_codename).first()
            
            CustomPermission.objects.get_or_create(
                codename=codename,
                defaults={
                    'category': usuarios_cat,
                    'name': name,
                    'permission_type': perm_type,
                    'action_type': action_type,
                    'parent_permission': parent,
                    'is_system': is_system,
                }
            )
        
        # Similar para almacen e importaciones...
        
        self.stdout.write(self.style.SUCCESS('Permisos migrados exitosamente'))
```

## Documentación de Uso

Ver archivos adjuntos:
- `DYNAMIC_PERMISSIONS_GUIDE.md` - Guía completa para administradores
- `API_PERMISSIONS.md` - Documentación de la API

## Ventajas del Sistema Dinámico

1. **Sin Código**: Crear permisos sin modificar código ni migraciones
2. **Flexibilidad**: Adaptarse a nuevos módulos sin desarrollo
3. **Auditoría**: Tracking de quién crea/modifica permisos
4. **Jerarquía**: Soporte para permisos padre-hijo
5. **Integración**: Compatible con sistema Django nativo
6. **UI Amigable**: Interfaz de administración intuitiva

## Seguridad

- Solo administradores del sistema pueden crear/editar permisos
- Permisos del sistema no pueden ser eliminados
- Validación de formato y duplicados
- Auditoría completa de cambios
- Sincronización automática con Django

---

**Versión**: 1.0  
**Fecha**: 2026-01-02
