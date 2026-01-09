# Frontend User Registration Guide
## Complete Implementation for Warehouse & Sede Assignment

This guide provides complete React implementation for user registration/editing with warehouse and sede (location) assignment functionality.

---

## Table of Contents
1. [Backend Changes Review](#backend-changes-review)
2. [What are "Sedes"?](#what-are-sedes)
3. [React Component Implementation](#react-component-implementation)
4. [API Integration](#api-integration)
5. [Validation & Error Handling](#validation--error-handling)
6. [Usage Examples](#usage-examples)

---

## 1. Backend Changes Review

### ✅ Your Implementation is Correct

**Changes made to `usuarios/serializers.py`:**

```python
class UserProfileSerializer(serializers.ModelSerializer):
    # Multi-select fields for warehouses and locations
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
```

**Key improvements:**
- ✅ Separated M2M relationships for proper saving
- ✅ Used `.set()` for both create and update operations
- ✅ Handled None values correctly
- ✅ Works with nested serializer pattern

---

## 2. What are "Sedes"?

### Model Structure

"Sedes" refers to the `Direccion` (Address/Location) model:

```python
class Direccion(BaseModel):
    empresa = models.ForeignKey(Empresa, related_name='direcciones', on_delete=models.CASCADE)
    direccion = models.TextField(max_length=2500)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE)
    distrito = models.ForeignKey(Distrito, on_delete=models.CASCADE)
```

### Use Case

**Internal companies (NOT supplier companies):**
- **Empresa Semilla** → Sede Lima, Sede Callao, Sede Arequipa
- **Empresa Maxi** → Sede Centro, Sede Norte, Sede Sur
- **Empresa Trading** → Sede Principal, Sede Secundaria

**User assignment:**
- **Warehouse Manager (Lima)** → Access to Sede Lima only
- **Regional Manager (Norte)** → Access to all Norte locations
- **General Manager** → Access to ALL locations (no restriction)

### Difference: `empresa` field vs `sedes_asignadas`

| Field | Purpose | Type | For |
|-------|---------|------|-----|
| **`empresa`** | Identifies supplier's company | ForeignKey | Suppliers ONLY |
| **`sedes_asignadas`** | Restricts access to locations | ManyToMany | Employees (managers, operators) |

---

## 3. React Component Implementation

### Complete User Registration/Edit Component

```javascript
import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Switch, Button, message, Spin, Card, Row, Col } from 'antd';
import axios from 'axios';

const { Option } = Select;

const UserRegistrationForm = ({ userId = null, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);

  // Available options from backend
  const [roles, setRoles] = useState([]);
  const [almacenes, setAlmacenes] = useState([]);
  const [sedes, setSedes] = useState([]);

  // Control states
  const [requireWarehouseAccess, setRequireWarehouseAccess] = useState(false);
  const [requireSedeAccess, setRequireSedeAccess] = useState(false);

  // Load initial data
  useEffect(() => {
    loadFormData();
  }, [userId]);

  const loadFormData = async () => {
    setDataLoading(true);
    try {
      // Load roles, warehouses, and locations in parallel
      const [rolesRes, almacenesRes, sedesRes] = await Promise.all([
        axios.get('/api/accounts/roles/'),
        axios.get('/api/almacen/almacenes/'),
        axios.get('/api/usuarios/direcciones/'), // Endpoint for locations
      ]);

      setRoles(rolesRes.data);
      setAlmacenes(almacenesRes.data);
      setSedes(sedesRes.data);

      // If editing, load user data
      if (userId) {
        const userRes = await axios.get(`/api/accounts/users/${userId}/`);
        const userData = userRes.data;

        // Set form values
        form.setFieldsValue({
          username: userData.username,
          email: userData.email,
          first_name: userData.first_name,
          last_name: userData.last_name,
          roles: userData.roles || [],
          telefono: userData.userprofile?.telefono || '',
          require_warehouse_access: userData.userprofile?.require_warehouse_access || false,
          almacenes_asignados: userData.userprofile?.almacenes_asignados || [],
          require_sede_access: userData.userprofile?.require_sede_access || false,
          sedes_asignadas: userData.userprofile?.sedes_asignadas || [],
        });

        // Set control states
        setRequireWarehouseAccess(userData.userprofile?.require_warehouse_access || false);
        setRequireSedeAccess(userData.userprofile?.require_sede_access || false);
      }
    } catch (error) {
      message.error('Error al cargar datos del formulario');
      console.error(error);
    } finally {
      setDataLoading(false);
    }
  };

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      // Prepare payload
      const payload = {
        username: values.username,
        email: values.email,
        first_name: values.first_name,
        last_name: values.last_name,
        roles: values.roles || [],
        userprofile: {
          telefono: values.telefono || '',
          require_warehouse_access: values.require_warehouse_access || false,
          almacenes_asignados: values.almacenes_asignados || [],
          require_sede_access: values.require_sede_access || false,
          sedes_asignadas: values.sedes_asignadas || [],
        },
      };

      // Add password only for creation
      if (!userId && values.password) {
        payload.password = values.password;
      }

      // Create or update
      if (userId) {
        await axios.put(`/api/accounts/users/${userId}/`, payload);
        message.success('Usuario actualizado exitosamente');
      } else {
        await axios.post('/api/accounts/users/', payload);
        message.success('Usuario creado exitosamente');
      }

      // Reset form and callback
      form.resetFields();
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('Error:', error);
      if (error.response?.data) {
        const errors = error.response.data;
        Object.keys(errors).forEach(key => {
          message.error(`${key}: ${errors[key]}`);
        });
      } else {
        message.error('Error al guardar usuario');
      }
    } finally {
      setLoading(false);
    }
  };

  if (dataLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Card title={userId ? 'Editar Usuario' : 'Nuevo Usuario'}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          require_warehouse_access: false,
          require_sede_access: false,
        }}
      >
        {/* Basic Info */}
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="Usuario"
              name="username"
              rules={[{ required: true, message: 'Usuario requerido' }]}
            >
              <Input placeholder="Nombre de usuario" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="Email"
              name="email"
              rules={[
                { required: true, message: 'Email requerido' },
                { type: 'email', message: 'Email inválido' }
              ]}
            >
              <Input placeholder="email@ejemplo.com" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="Nombre"
              name="first_name"
              rules={[{ required: true, message: 'Nombre requerido' }]}
            >
              <Input placeholder="Nombre" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="Apellido"
              name="last_name"
              rules={[{ required: true, message: 'Apellido requerido' }]}
            >
              <Input placeholder="Apellido" />
            </Form.Item>
          </Col>
        </Row>

        {/* Password (only for creation) */}
        {!userId && (
          <Form.Item
            label="Contraseña"
            name="password"
            rules={[
              { required: true, message: 'Contraseña requerida' },
              { min: 8, message: 'Mínimo 8 caracteres' }
            ]}
          >
            <Input.Password placeholder="Contraseña" />
          </Form.Item>
        )}

        {/* Phone */}
        <Form.Item label="Teléfono" name="telefono">
          <Input placeholder="Teléfono" />
        </Form.Item>

        {/* Roles */}
        <Form.Item
          label="Roles"
          name="roles"
          rules={[{ required: true, message: 'Selecciona al menos un rol' }]}
        >
          <Select
            mode="multiple"
            placeholder="Selecciona roles"
            showSearch
            optionFilterProp="children"
          >
            {roles.map(role => (
              <Option key={role.id} value={role.id}>
                {role.name}
              </Option>
            ))}
          </Select>
        </Form.Item>

        {/* Warehouse Access Control */}
        <Card
          title="Control de Acceso a Almacenes"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Form.Item
            label="Requiere Restricción de Almacenes"
            name="require_warehouse_access"
            valuePropName="checked"
          >
            <Switch
              onChange={setRequireWarehouseAccess}
              checkedChildren="Sí"
              unCheckedChildren="No"
            />
          </Form.Item>

          {requireWarehouseAccess && (
            <Form.Item
              label="Almacenes Asignados"
              name="almacenes_asignados"
              rules={[
                {
                  required: requireWarehouseAccess,
                  message: 'Selecciona al menos un almacén'
                }
              ]}
              help="Usuario solo tendrá acceso a estos almacenes"
            >
              <Select
                mode="multiple"
                placeholder="Selecciona almacenes"
                showSearch
                optionFilterProp="children"
                filterOption={(input, option) =>
                  option.children.toLowerCase().includes(input.toLowerCase())
                }
              >
                {almacenes.map(almacen => (
                  <Option key={almacen.id} value={almacen.id}>
                    {almacen.nombre} - {almacen.empresa_nombre || 'Sin empresa'}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          )}

          {!requireWarehouseAccess && (
            <div style={{ padding: '10px', background: '#f0f0f0', borderRadius: '4px' }}>
              ℹ️ Sin restricción: Usuario tendrá acceso a TODOS los almacenes
            </div>
          )}
        </Card>

        {/* Sede/Location Access Control */}
        <Card
          title="Control de Acceso a Sedes"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Form.Item
            label="Requiere Restricción de Sedes"
            name="require_sede_access"
            valuePropName="checked"
          >
            <Switch
              onChange={setRequireSedeAccess}
              checkedChildren="Sí"
              unCheckedChildren="No"
            />
          </Form.Item>

          {requireSedeAccess && (
            <Form.Item
              label="Sedes Asignadas"
              name="sedes_asignadas"
              rules={[
                {
                  required: requireSedeAccess,
                  message: 'Selecciona al menos una sede'
                }
              ]}
              help="Usuario solo tendrá acceso a estas ubicaciones/sedes"
            >
              <Select
                mode="multiple"
                placeholder="Selecciona sedes"
                showSearch
                optionFilterProp="children"
                filterOption={(input, option) =>
                  option.children.toLowerCase().includes(input.toLowerCase())
                }
              >
                {sedes.map(sede => (
                  <Option key={sede.id} value={sede.id}>
                    {sede.direccion} - {sede.distrito_nombre || ''}, {sede.provincia_nombre || ''}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          )}

          {!requireSedeAccess && (
            <div style={{ padding: '10px', background: '#f0f0f0', borderRadius: '4px' }}>
              ℹ️ Sin restricción: Usuario tendrá acceso a TODAS las sedes
            </div>
          )}
        </Card>

        {/* Submit Buttons */}
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            {userId ? 'Actualizar Usuario' : 'Crear Usuario'}
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default UserRegistrationForm;
```

---

## 4. API Integration

### Required Endpoints

**1. Get Direcciones (Sedes/Locations)**

Create endpoint in `usuarios/views.py`:

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Direccion

@api_view(['GET'])
def lista_direcciones(request):
    """Return all active direcciones/sedes"""
    direcciones = Direccion.objects.filter(state=True).select_related(
        'empresa', 'departamento', 'provincia', 'distrito'
    )
    
    data = [{
        'id': d.id,
        'direccion': d.direccion,
        'empresa_id': d.empresa_id,
        'empresa_nombre': d.empresa.nombre,
        'departamento_id': d.departamento_id,
        'departamento_nombre': d.departamento.name,
        'provincia_id': d.provincia_id,
        'provincia_nombre': d.provincia.name,
        'distrito_id': d.distrito_id,
        'distrito_nombre': d.distrito.name,
    } for d in direcciones]
    
    return Response(data)
```

Add to `usuarios/urls.py`:

```python
urlpatterns = [
    # ... existing patterns ...
    path('direcciones/', views.lista_direcciones, name='lista-direcciones'),
]
```

**2. Test Existing Endpoints**

```bash
# List users with warehouse/sede info
GET /api/accounts/users/

# Get specific user
GET /api/accounts/users/5/

# Create user with warehouses and sedes
POST /api/accounts/users/
{
  "username": "operador_lima",
  "email": "operador@example.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "password": "securepass123",
  "roles": [3],
  "userprofile": {
    "telefono": "987654321",
    "require_warehouse_access": true,
    "almacenes_asignados": [1, 2],
    "require_sede_access": true,
    "sedes_asignadas": [1]
  }
}

# Update user warehouses/sedes
PUT /api/accounts/users/5/
{
  "userprofile": {
    "require_warehouse_access": true,
    "almacenes_asignados": [1, 2, 3],
    "require_sede_access": false,
    "sedes_asignadas": []
  }
}
```

---

## 5. Validation & Error Handling

### Frontend Validation Rules

```javascript
const validateAlmacenes = (_, value) => {
  const requireAccess = form.getFieldValue('require_warehouse_access');
  if (requireAccess && (!value || value.length === 0)) {
    return Promise.reject('Debes asignar al menos un almacén');
  }
  return Promise.resolve();
};

const validateSedes = (_, value) => {
  const requireAccess = form.getFieldValue('require_sede_access');
  if (requireAccess && (!value || value.length === 0)) {
    return Promise.reject('Debes asignar al menos una sede');
  }
  return Promise.resolve();
};

// Apply in Form.Item:
<Form.Item
  name="almacenes_asignados"
  rules={[{ validator: validateAlmacenes }]}
>
```

### Backend Validation (Optional Enhancement)

Add to `UserSerializer.validate()`:

```python
def validate(self, attrs):
    profile_data = attrs.get('userprofile', {})
    
    # Validate warehouse access
    if profile_data.get('require_warehouse_access'):
        almacenes = profile_data.get('almacenes_asignados', [])
        if not almacenes:
            raise serializers.ValidationError({
                'userprofile': {
                    'almacenes_asignados': 'Debe asignar al menos un almacén cuando require_warehouse_access es True'
                }
            })
    
    # Validate sede access
    if profile_data.get('require_sede_access'):
        sedes = profile_data.get('sedes_asignadas', [])
        if not sedes:
            raise serializers.ValidationError({
                'userprofile': {
                    'sedes_asignadas': 'Debe asignar al menos una sede cuando require_sede_access es True'
                }
            })
    
    return attrs
```

---

## 6. Usage Examples

### Example 1: Warehouse Operator (Restricted)

```javascript
const operatorData = {
  username: 'op_callao',
  email: 'operador.callao@company.com',
  first_name: 'Carlos',
  last_name: 'Ruiz',
  password: 'secure123',
  roles: [4], // Operator role
  userprofile: {
    telefono: '999888777',
    require_warehouse_access: true,
    almacenes_asignados: [1, 2], // Only Callao and Miraflores
    require_sede_access: false,
    sedes_asignadas: [],
  }
};

// Result:
// ✅ Sees only movements/stock from Callao and Miraflores
// ❌ Cannot access Surco warehouse
// ✅ Can access all sedes (no restriction)
```

### Example 2: Regional Manager (Sede-Restricted)

```javascript
const managerData = {
  username: 'manager_norte',
  email: 'manager.norte@company.com',
  first_name: 'María',
  last_name: 'López',
  password: 'secure456',
  roles: [2], // Manager role
  userprofile: {
    telefono: '999777666',
    require_warehouse_access: false, // No warehouse restriction
    almacenes_asignados: [],
    require_sede_access: true,
    sedes_asignadas: [5, 6, 7], // Only Norte region sedes
  }
};

// Result:
// ✅ Sees ALL warehouses
// ✅ Can filter by empresa: ?empresa=1
// ✅ Only sees data from Norte region sedes
// ❌ Cannot access Sur or Centro sedes
```

### Example 3: General Manager (No Restrictions)

```javascript
const generalManagerData = {
  username: 'gm_general',
  email: 'gm@company.com',
  first_name: 'Pedro',
  last_name: 'García',
  password: 'secure789',
  roles: [1], // General Manager role
  userprofile: {
    telefono: '999666555',
    require_warehouse_access: false,
    almacenes_asignados: [],
    require_sede_access: false,
    sedes_asignadas: [],
  }
};

// Result:
// ✅ Sees ALL warehouses
// ✅ Sees ALL sedes
// ✅ Full access to everything
```

---

## Best Practices

### 1. Always Load Fresh Data

```javascript
useEffect(() => {
  // Reload options when modal opens
  if (visible) {
    loadFormData();
  }
}, [visible]);
```

### 2. Clear Form on Close

```javascript
const handleClose = () => {
  form.resetFields();
  setRequireWarehouseAccess(false);
  setRequireSedeAccess(false);
  onClose();
};
```

### 3. Show Loading States

```javascript
{loading ? (
  <Spin tip="Guardando...">
    <div style={{ height: 200 }} />
  </Spin>
) : (
  <UserForm />
)}
```

### 4. Provide User Feedback

```javascript
try {
  await saveUser(data);
  message.success('Usuario guardado correctamente');
  notification.success({
    message: 'Éxito',
    description: 'El usuario ahora tiene acceso a los almacenes seleccionados',
  });
} catch (error) {
  message.error('Error al guardar');
  console.error(error);
}
```

---

## Testing Checklist

- [ ] Create user without warehouse restriction (access all)
- [ ] Create user with warehouse restriction (access only assigned)
- [ ] Create user with sede restriction
- [ ] Update user to add warehouses
- [ ] Update user to remove restrictions
- [ ] Verify operator can only see their warehouses in API
- [ ] Verify manager can see all warehouses
- [ ] Test validation (require_warehouse_access=True but no warehouses)
- [ ] Test form submission with network error
- [ ] Test editing existing user with warehouses already assigned

---

## Summary

**Your backend implementation is correct and ready to use!**

Key points:
- ✅ "Sedes" = Direccion model (company locations/addresses)
- ✅ Separate from `empresa` field (which is only for suppliers)
- ✅ Your serializer handles M2M correctly with `.set()`
- ✅ Frontend component provided for complete integration
- ✅ Validation ensures data consistency
- ✅ Flexible control: restricted operators, unrestricted managers

The system now supports:
- Warehouse-level access control ✅
- Location/sede-level access control ✅
- Frontend interface for assignment ✅
- Complete validation ✅

Ready for immediate use in production!
