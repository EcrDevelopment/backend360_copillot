# Frontend Implementation Guide
# Complete Guide for Integrating Dynamic Permissions System with React/Vue Frontend

## Table of Contents
1. [Overview](#overview)
2. [API Client Setup](#api-client-setup)
3. [Permission Management Components](#permission-management-components)
4. [Usage in Application](#usage-in-application)
5. [Best Practices](#best-practices)

---

## Overview

This guide provides complete frontend implementation for the Dynamic Permissions System with:
- ✅ React components (can be adapted for Vue/Angular)
- ✅ API client with error handling
- ✅ Permission management UI
- ✅ Real-time permission checking
- ✅ Audit log viewing
- ✅ Permission hierarchy visualization

---

## API Client Setup

### 1. Create API Service (`src/services/permissionsApi.js`)

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authentication token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ===== Permission Categories API =====

export const permissionsApi = {
  // Categories
  categories: {
    list: () => apiClient.get('/accounts/permission-categories/'),
    
    get: (id) => apiClient.get(`/accounts/permission-categories/${id}/`),
    
    create: (data) => apiClient.post('/accounts/permission-categories/', data),
    
    update: (id, data) => apiClient.patch(`/accounts/permission-categories/${id}/`, data),
    
    delete: (id) => apiClient.delete(`/accounts/permission-categories/${id}/`),
    
    getPermissions: (id) => apiClient.get(`/accounts/permission-categories/${id}/permissions/`),
  },
  
  // Custom Permissions
  permissions: {
    list: (params = {}) => apiClient.get('/accounts/custom-permissions/', { params }),
    
    get: (id) => apiClient.get(`/accounts/custom-permissions/${id}/`),
    
    create: (data) => apiClient.post('/accounts/custom-permissions/', data),
    
    update: (id, data) => apiClient.patch(`/accounts/custom-permissions/${id}/`, data),
    
    delete: (id) => apiClient.delete(`/accounts/custom-permissions/${id}/`),
    
    getHistory: (id) => apiClient.get(`/accounts/custom-permissions/${id}/history/`),
    
    getHierarchy: (id) => apiClient.get(`/accounts/custom-permissions/${id}/hierarchy/`),
    
    assign: (data) => apiClient.post('/accounts/custom-permissions/assign/', data),
    
    bulkCreate: (data) => apiClient.post('/accounts/custom-permissions/bulk_create/', data),
  },
  
  // Audit Logs
  audits: {
    list: (params = {}) => apiClient.get('/accounts/permission-audits/', { params }),
    
    get: (id) => apiClient.get(`/accounts/permission-audits/${id}/`),
    
    recent: () => apiClient.get('/accounts/permission-audits/recent/'),
    
    byUser: (userId) => apiClient.get('/accounts/permission-audits/by_user/', {
      params: { user_id: userId }
    }),
  },
};

export default permissionsApi;
```

---

## Permission Management Components

### 2. Permission Categories List (`src/components/permissions/CategoryList.jsx`)

```jsx
import React, { useState, useEffect } from 'react';
import { permissionsApi } from '../../services/permissionsApi';
import { 
  Table, Button, Modal, Form, Input, InputNumber, 
  message, Popconfirm, Space, Card 
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, AppstoreOutlined } from '@ant-design/icons';

const CategoryList = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const response = await permissionsApi.categories.list();
      setCategories(response.data.results || response.data);
    } catch (error) {
      message.error('Error loading categories: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingCategory(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (category) => {
    setEditingCategory(category);
    form.setFieldsValue(category);
    setModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await permissionsApi.categories.delete(id);
      message.success('Category deleted successfully');
      loadCategories();
    } catch (error) {
      message.error('Error deleting category: ' + error.message);
    }
  };

  const handleSubmit = async (values) => {
    try {
      if (editingCategory) {
        await permissionsApi.categories.update(editingCategory.id, values);
        message.success('Category updated successfully');
      } else {
        await permissionsApi.categories.create(values);
        message.success('Category created successfully');
      }
      setModalVisible(false);
      loadCategories();
    } catch (error) {
      message.error('Error saving category: ' + error.message);
    }
  };

  const columns = [
    {
      title: 'Icon',
      dataIndex: 'icon',
      key: 'icon',
      render: (icon) => icon || <AppstoreOutlined />,
      width: 80,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Display Name',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Order',
      dataIndex: 'order',
      key: 'order',
      width: 100,
    },
    {
      title: 'Permissions',
      key: 'permissions_count',
      render: (_, record) => (
        <Button size="small" onClick={() => viewPermissions(record.id)}>
          View
        </Button>
      ),
      width: 120,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this category?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
      width: 180,
    },
  ];

  const viewPermissions = (categoryId) => {
    // Navigate to permissions list filtered by category
    window.location.href = `/permissions?category=${categoryId}`;
  };

  return (
    <Card 
      title="Permission Categories" 
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          New Category
        </Button>
      }
    >
      <Table 
        columns={columns} 
        dataSource={categories} 
        rowKey="id" 
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingCategory ? 'Edit Category' : 'New Category'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            label="Name (code)"
            name="name"
            rules={[
              { required: true, message: 'Please enter category name' },
              { pattern: /^[a-z_]+$/, message: 'Only lowercase letters and underscores' }
            ]}
          >
            <Input placeholder="e.g., ventas" />
          </Form.Item>

          <Form.Item
            label="Display Name"
            name="display_name"
            rules={[{ required: true, message: 'Please enter display name' }]}
          >
            <Input placeholder="e.g., Ventas" />
          </Form.Item>

          <Form.Item
            label="Description"
            name="description"
          >
            <Input.TextArea rows={3} placeholder="Category description" />
          </Form.Item>

          <Form.Item
            label="Icon"
            name="icon"
          >
            <Input placeholder="e.g., shopping-cart" />
          </Form.Item>

          <Form.Item
            label="Order"
            name="order"
            initialValue={10}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingCategory ? 'Update' : 'Create'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default CategoryList;
```

### 3. Permissions List (`src/components/permissions/PermissionList.jsx`)

```jsx
import React, { useState, useEffect } from 'react';
import { permissionsApi } from '../../services/permissionsApi';
import {
  Table, Button, Modal, Form, Input, Select, message,
  Popconfirm, Space, Card, Tag, Tooltip
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, HistoryOutlined, ApartmentOutlined } from '@ant-design/icons';

const { Option } = Select;

const PermissionList = () => {
  const [permissions, setPermissions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [historyModalVisible, setHistoryModalVisible] = useState(false);
  const [hierarchyModalVisible, setHierarchyModalVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState(null);
  const [permissionHistory, setPermissionHistory] = useState([]);
  const [permissionHierarchy, setPermissionHierarchy] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadPermissions();
    loadCategories();
  }, []);

  const loadPermissions = async () => {
    setLoading(true);
    try {
      const response = await permissionsApi.permissions.list();
      setPermissions(response.data.results || response.data);
    } catch (error) {
      message.error('Error loading permissions: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await permissionsApi.categories.list();
      setCategories(response.data.results || response.data);
    } catch (error) {
      message.error('Error loading categories: ' + error.message);
    }
  };

  const handleCreate = () => {
    setEditingPermission(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (permission) => {
    setEditingPermission(permission);
    form.setFieldsValue({
      ...permission,
      parent_permission: permission.parent_permission?.id,
    });
    setModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await permissionsApi.permissions.delete(id);
      message.success('Permission deleted successfully');
      loadPermissions();
    } catch (error) {
      message.error('Error deleting permission: ' + error.message);
    }
  };

  const handleSubmit = async (values) => {
    try {
      if (editingPermission) {
        await permissionsApi.permissions.update(editingPermission.id, values);
        message.success('Permission updated successfully');
      } else {
        await permissionsApi.permissions.create(values);
        message.success('Permission created successfully');
      }
      setModalVisible(false);
      loadPermissions();
    } catch (error) {
      message.error('Error saving permission: ' + error.response?.data?.error || error.message);
    }
  };

  const viewHistory = async (permission) => {
    try {
      const response = await permissionsApi.permissions.getHistory(permission.id);
      setPermissionHistory(response.data);
      setHistoryModalVisible(true);
    } catch (error) {
      message.error('Error loading history: ' + error.message);
    }
  };

  const viewHierarchy = async (permission) => {
    try {
      const response = await permissionsApi.permissions.getHierarchy(permission.id);
      setPermissionHierarchy(response.data);
      setHierarchyModalVisible(true);
    } catch (error) {
      message.error('Error loading hierarchy: ' + error.message);
    }
  };

  const columns = [
    {
      title: 'Codename',
      dataIndex: 'codename',
      key: 'codename',
      render: (text) => <code>{text}</code>,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Category',
      dataIndex: ['category', 'display_name'],
      key: 'category',
    },
    {
      title: 'Type',
      dataIndex: 'permission_type',
      key: 'permission_type',
      render: (type) => (
        <Tag color={type === 'modular' ? 'blue' : 'green'}>
          {type}
        </Tag>
      ),
    },
    {
      title: 'Action',
      dataIndex: 'action_type',
      key: 'action_type',
      render: (action) => action && <Tag>{action}</Tag>,
    },
    {
      title: 'System',
      dataIndex: 'is_system_permission',
      key: 'is_system_permission',
      render: (isSystem) => isSystem && <Tag color="red">System</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="View History">
            <Button
              type="link"
              icon={<HistoryOutlined />}
              onClick={() => viewHistory(record)}
            />
          </Tooltip>
          <Tooltip title="View Hierarchy">
            <Button
              type="link"
              icon={<ApartmentOutlined />}
              onClick={() => viewHierarchy(record)}
            />
          </Tooltip>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            disabled={record.is_system_permission}
          >
            Edit
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this permission?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
            disabled={record.is_system_permission}
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              disabled={record.is_system_permission}
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
      width: 200,
    },
  ];

  return (
    <Card
      title="Custom Permissions"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          New Permission
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={permissions}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      {/* Create/Edit Modal */}
      <Modal
        title={editingPermission ? 'Edit Permission' : 'New Permission'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            label="Category"
            name="category"
            rules={[{ required: true, message: 'Please select category' }]}
          >
            <Select placeholder="Select category">
              {categories.map(cat => (
                <Option key={cat.id} value={cat.id}>
                  {cat.display_name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="Codename"
            name="codename"
            rules={[
              { required: true, message: 'Please enter codename' },
              {
                pattern: /^can_[a-z_]+$/,
                message: 'Must start with "can_" and use lowercase letters and underscores'
              }
            ]}
          >
            <Input placeholder="e.g., can_manage_sales" />
          </Form.Item>

          <Form.Item
            label="Name"
            name="name"
            rules={[{ required: true, message: 'Please enter name' }]}
          >
            <Input placeholder="e.g., Puede gestionar ventas" />
          </Form.Item>

          <Form.Item
            label="Description"
            name="description"
          >
            <Input.TextArea rows={2} placeholder="Permission description" />
          </Form.Item>

          <Form.Item
            label="Permission Type"
            name="permission_type"
            rules={[{ required: true, message: 'Please select type' }]}
          >
            <Select placeholder="Select type">
              <Option value="modular">Modular (High-level)</Option>
              <Option value="granular">Granular (Action-specific)</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Action Type"
            name="action_type"
          >
            <Select placeholder="Select action" allowClear>
              <Option value="manage">Manage (Full Access)</Option>
              <Option value="view">View (Read Only)</Option>
              <Option value="create">Create</Option>
              <Option value="edit">Edit</Option>
              <Option value="delete">Delete</Option>
              <Option value="approve">Approve</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Parent Permission (Optional)"
            name="parent_permission"
          >
            <Select
              placeholder="Select parent permission"
              allowClear
              showSearch
              optionFilterProp="children"
            >
              {permissions
                .filter(p => p.permission_type === 'modular')
                .map(perm => (
                  <Option key={perm.id} value={perm.id}>
                    {perm.codename} - {perm.name}
                  </Option>
                ))}
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingPermission ? 'Update' : 'Create'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* History Modal */}
      <Modal
        title="Permission History"
        open={historyModalVisible}
        onCancel={() => setHistoryModalVisible(false)}
        footer={null}
        width={800}
      >
        <Table
          dataSource={permissionHistory.historical_records || []}
          columns={[
            {
              title: 'Date',
              dataIndex: 'history_date',
              render: (date) => new Date(date).toLocaleString(),
            },
            {
              title: 'User',
              dataIndex: 'history_user',
              render: (user) => user?.username || 'System',
            },
            {
              title: 'Change Type',
              dataIndex: 'history_type',
              render: (type) => (
                <Tag color={type === '+' ? 'green' : type === '~' ? 'blue' : 'red'}>
                  {type === '+' ? 'Created' : type === '~' ? 'Updated' : 'Deleted'}
                </Tag>
              ),
            },
          ]}
          rowKey="history_id"
          pagination={{ pageSize: 5 }}
        />
      </Modal>

      {/* Hierarchy Modal */}
      <Modal
        title="Permission Hierarchy"
        open={hierarchyModalVisible}
        onCancel={() => setHierarchyModalVisible(false)}
        footer={null}
        width={600}
      >
        {permissionHierarchy && (
          <div>
            <h4>Ancestors (Parents):</h4>
            {permissionHierarchy.ancestors?.length > 0 ? (
              <ul>
                {permissionHierarchy.ancestors.map(p => (
                  <li key={p.id}>
                    <code>{p.codename}</code> - {p.name}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No parent permissions</p>
            )}

            <h4>Descendants (Children):</h4>
            {permissionHierarchy.descendants?.length > 0 ? (
              <ul>
                {permissionHierarchy.descendants.map(p => (
                  <li key={p.id}>
                    <code>{p.codename}</code> - {p.name}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No child permissions</p>
            )}
          </div>
        )}
      </Modal>
    </Card>
  );
};

export default PermissionList;
```

### 4. Permission Assignment Component (`src/components/permissions/PermissionAssignment.jsx`)

```jsx
import React, { useState, useEffect } from 'react';
import { permissionsApi } from '../../services/permissionsApi';
import {
  Modal, Form, Select, Input, Button, message, Space, Transfer
} from 'antd';

const { Option } = Select;
const { TextArea } = Input;

const PermissionAssignment = ({ visible, onClose, onSuccess }) => {
  const [permissions, setPermissions] = useState([]);
  const [users, setUsers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible) {
      loadData();
    }
  }, [visible]);

  const loadData = async () => {
    try {
      const [permsRes, usersRes, groupsRes] = await Promise.all([
        permissionsApi.permissions.list(),
        fetch('/api/accounts/users/').then(r => r.json()),
        fetch('/api/accounts/roles/').then(r => r.json()),
      ]);
      
      setPermissions(permsRes.data.results || permsRes.data);
      setUsers(usersRes.results || usersRes);
      setGroups(groupsRes.results || groupsRes);
    } catch (error) {
      message.error('Error loading data: ' + error.message);
    }
  };

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      await permissionsApi.permissions.assign(values);
      message.success(`Permission ${values.action}ed successfully`);
      form.resetFields();
      onSuccess && onSuccess();
      onClose();
    } catch (error) {
      message.error('Error: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="Assign/Revoke Permission"
      open={visible}
      onCancel={onClose}
      footer={null}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Form.Item
          label="Permission"
          name="permission_id"
          rules={[{ required: true, message: 'Please select permission' }]}
        >
          <Select
            placeholder="Select permission"
            showSearch
            optionFilterProp="children"
          >
            {permissions.map(perm => (
              <Option key={perm.id} value={perm.id}>
                {perm.codename} - {perm.name}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label="Target Type"
          name="target_type"
          rules={[{ required: true, message: 'Please select target type' }]}
        >
          <Select placeholder="Assign to user or group?">
            <Option value="user">User</Option>
            <Option value="group">Group (Role)</Option>
          </Select>
        </Form.Item>

        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) => 
            prevValues.target_type !== currentValues.target_type
          }
        >
          {({ getFieldValue }) => {
            const targetType = getFieldValue('target_type');
            
            if (targetType === 'user') {
              return (
                <Form.Item
                  label="User"
                  name="user_id"
                  rules={[{ required: true, message: 'Please select user' }]}
                >
                  <Select placeholder="Select user" showSearch optionFilterProp="children">
                    {users.map(user => (
                      <Option key={user.id} value={user.id}>
                        {user.username} - {user.first_name} {user.last_name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              );
            }
            
            if (targetType === 'group') {
              return (
                <Form.Item
                  label="Group (Role)"
                  name="group_id"
                  rules={[{ required: true, message: 'Please select group' }]}
                >
                  <Select placeholder="Select group">
                    {groups.map(group => (
                      <Option key={group.id} value={group.id}>
                        {group.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              );
            }
            
            return null;
          }}
        </Form.Item>

        <Form.Item
          label="Action"
          name="action"
          rules={[{ required: true, message: 'Please select action' }]}
        >
          <Select placeholder="Assign or revoke?">
            <Option value="assign">Assign (Grant Permission)</Option>
            <Option value="revoke">Revoke (Remove Permission)</Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="Reason"
          name="reason"
        >
          <TextArea 
            rows={2} 
            placeholder="Reason for this action (for audit log)" 
          />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              Submit
            </Button>
            <Button onClick={onClose}>
              Cancel
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default PermissionAssignment;
```

### 5. Audit Logs Viewer (`src/components/permissions/AuditLogViewer.jsx`)

```jsx
import React, { useState, useEffect } from 'react';
import { permissionsApi } from '../../services/permissionsApi';
import { Table, Card, Select, DatePicker, Button, Space, Tag, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';

const { RangePicker } = DatePicker;
const { Option } = Select;

const AuditLogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({});

  useEffect(() => {
    loadLogs();
  }, [filters]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const response = await permissionsApi.audits.list(filters);
      setLogs(response.data.results || response.data);
    } catch (error) {
      message.error('Error loading audit logs: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentLogs = async () => {
    setLoading(true);
    try {
      const response = await permissionsApi.audits.recent();
      setLogs(response.data);
      message.success('Showing logs from last 24 hours');
    } catch (error) {
      message.error('Error loading recent logs: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Date',
      dataIndex: 'created_date',
      key: 'created_date',
      render: (date) => new Date(date).toLocaleString(),
      sorter: true,
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      render: (action) => {
        const colors = {
          created: 'green',
          updated: 'blue',
          deleted: 'red',
          assigned: 'cyan',
          revoked: 'orange',
        };
        return <Tag color={colors[action] || 'default'}>{action.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Permission',
      dataIndex: ['permission', 'codename'],
      key: 'permission',
      render: (codename) => <code>{codename}</code>,
    },
    {
      title: 'User',
      dataIndex: ['performed_by', 'username'],
      key: 'performed_by',
    },
    {
      title: 'Target User',
      dataIndex: ['target_user', 'username'],
      key: 'target_user',
      render: (username) => username || '-',
    },
    {
      title: 'Target Group',
      dataIndex: ['target_group', 'name'],
      key: 'target_group',
      render: (name) => name || '-',
    },
    {
      title: 'Reason',
      dataIndex: 'reason',
      key: 'reason',
      render: (reason) => reason || '-',
    },
    {
      title: 'IP Address',
      dataIndex: 'ip_address',
      key: 'ip_address',
      render: (ip) => ip || '-',
    },
  ];

  return (
    <Card
      title="Audit Logs"
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadRecentLogs}
          >
            Recent (24h)
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => loadLogs()}
          >
            Refresh
          </Button>
        </Space>
      }
    >
      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Filter by action"
          style={{ width: 150 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, action: value })}
        >
          <Option value="created">Created</Option>
          <Option value="updated">Updated</Option>
          <Option value="deleted">Deleted</Option>
          <Option value="assigned">Assigned</Option>
          <Option value="revoked">Revoked</Option>
        </Select>
      </Space>

      <Table
        columns={columns}
        dataSource={logs}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
      />
    </Card>
  );
};

export default AuditLogViewer;
```

---

## Usage in Application

### 6. Main Permissions Management Page (`src/pages/PermissionsManagement.jsx`)

```jsx
import React, { useState } from 'react';
import { Tabs, Button, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import CategoryList from '../components/permissions/CategoryList';
import PermissionList from '../components/permissions/PermissionList';
import AuditLogViewer from '../components/permissions/AuditLogViewer';
import PermissionAssignment from '../components/permissions/PermissionAssignment';

const { TabPane } = Tabs;

const PermissionsManagement = () => {
  const [assignmentModalVisible, setAssignmentModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('permissions');

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
        <h1>Permissions Management</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setAssignmentModalVisible(true)}
        >
          Assign/Revoke Permission
        </Button>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="Permissions" key="permissions">
          <PermissionList />
        </TabPane>
        
        <TabPane tab="Categories" key="categories">
          <CategoryList />
        </TabPane>
        
        <TabPane tab="Audit Logs" key="audits">
          <AuditLogViewer />
        </TabPane>
      </Tabs>

      <PermissionAssignment
        visible={assignmentModalVisible}
        onClose={() => setAssignmentModalVisible(false)}
        onSuccess={() => {
          // Refresh data if needed
          if (activeTab === 'audits') {
            window.location.reload();
          }
        }}
      />
    </div>
  );
};

export default PermissionsManagement;
```

### 7. Permission Check Hook (`src/hooks/usePermissions.js`)

```javascript
import { useState, useEffect } from 'react';

export const usePermissions = () => {
  const [userPermissions, setUserPermissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserPermissions();
  }, []);

  const loadUserPermissions = async () => {
    try {
      const response = await fetch('/api/accounts/permisos/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      const data = await response.json();
      setUserPermissions(data.map(p => p.codename));
    } catch (error) {
      console.error('Error loading permissions:', error);
    } finally {
      setLoading(false);
    }
  };

  const hasPermission = (codename) => {
    return userPermissions.includes(codename);
  };

  const hasAnyPermission = (codenames) => {
    return codenames.some(codename => hasPermission(codename));
  };

  const hasAllPermissions = (codenames) => {
    return codenames.every(codename => hasPermission(codename));
  };

  return {
    userPermissions,
    loading,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
  };
};

// Usage Example
/*
const MyComponent = () => {
  const { hasPermission, loading } = usePermissions();

  if (loading) return <Spin />;

  return (
    <div>
      {hasPermission('usuarios.can_manage_users') && (
        <Button>Manage Users</Button>
      )}
      {hasPermission('usuarios.can_edit_users') && (
        <Button>Edit User</Button>
      )}
    </div>
  );
};
*/
```

### 8. Protected Route Component (`src/components/ProtectedRoute.jsx`)

```jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { usePermissions } from '../hooks/usePermissions';
import { Spin } from 'antd';

const ProtectedRoute = ({ 
  children, 
  requiredPermission, 
  requiredPermissions = [],
  requireAll = false  // true = AND logic, false = OR logic
}) => {
  const { hasPermission, hasAnyPermission, hasAllPermissions, loading } = usePermissions();

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  // Single permission check
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <Navigate to="/unauthorized" />;
  }

  // Multiple permissions check
  if (requiredPermissions.length > 0) {
    const hasAccess = requireAll 
      ? hasAllPermissions(requiredPermissions)
      : hasAnyPermission(requiredPermissions);
    
    if (!hasAccess) {
      return <Navigate to="/unauthorized" />;
    }
  }

  return children;
};

export default ProtectedRoute;

// Usage Example in Routes
/*
<Route 
  path="/users" 
  element={
    <ProtectedRoute requiredPermission="usuarios.can_view_users">
      <UsersPage />
    </ProtectedRoute>
  } 
/>

<Route 
  path="/users/edit" 
  element={
    <ProtectedRoute 
      requiredPermissions={[
        'usuarios.can_manage_users',
        'usuarios.can_edit_users'
      ]}
      requireAll={false}  // User needs EITHER permission
    >
      <EditUserPage />
    </ProtectedRoute>
  } 
/>
*/
```

---

## Best Practices

### 1. Permission Caching

```javascript
// src/utils/permissionCache.js
const CACHE_KEY = 'user_permissions';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export const permissionCache = {
  set: (permissions) => {
    const data = {
      permissions,
      timestamp: Date.now(),
    };
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
  },

  get: () => {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const { permissions, timestamp } = JSON.parse(cached);
    const isExpired = Date.now() - timestamp > CACHE_DURATION;

    return isExpired ? null : permissions;
  },

  clear: () => {
    localStorage.removeItem(CACHE_KEY);
  },
};
```

### 2. Error Handling

```javascript
// src/utils/errorHandler.js
import { message } from 'antd';

export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error
    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 400:
        message.error(data.error || 'Invalid request');
        break;
      case 401:
        message.error('Unauthorized. Please login again.');
        // Redirect to login
        window.location.href = '/login';
        break;
      case 403:
        message.error('You do not have permission to perform this action');
        break;
      case 404:
        message.error('Resource not found');
        break;
      case 500:
        message.error('Server error. Please try again later.');
        break;
      default:
        message.error('An error occurred');
    }
  } else if (error.request) {
    // Request made but no response
    message.error('No response from server. Check your connection.');
  } else {
    // Other errors
    message.error(error.message);
  }
};
```

### 3. Real-time Permission Updates

```javascript
// src/services/permissionSync.js
import { permissionsApi } from './permissionsApi';
import { permissionCache } from '../utils/permissionCache';

export const syncPermissions = async () => {
  try {
    const response = await fetch('/api/accounts/permisos/');
    const permissions = await response.json();
    
    // Update cache
    permissionCache.set(permissions.map(p => p.codename));
    
    // Emit event for components to refresh
    window.dispatchEvent(new CustomEvent('permissions-updated', {
      detail: { permissions }
    }));
    
    return permissions;
  } catch (error) {
    console.error('Error syncing permissions:', error);
    throw error;
  }
};

// Call this after login or when permissions might have changed
```

### 4. Menu Configuration with Permissions

```javascript
// src/config/menuConfig.js
export const menuConfig = [
  {
    key: 'usuarios',
    label: 'Usuarios',
    icon: 'UserOutlined',
    permissions: ['usuarios.can_view_users', 'usuarios.can_manage_users'],
    requireAll: false,  // Show if user has ANY of these permissions
    children: [
      {
        key: 'usuarios-list',
        label: 'Lista de Usuarios',
        path: '/usuarios',
        permissions: ['usuarios.can_view_users'],
      },
      {
        key: 'usuarios-create',
        label: 'Crear Usuario',
        path: '/usuarios/create',
        permissions: ['usuarios.can_create_users', 'usuarios.can_manage_users'],
        requireAll: false,
      },
    ],
  },
  {
    key: 'almacen',
    label: 'Almacén',
    icon: 'ShopOutlined',
    permissions: ['almacen.can_view_warehouse', 'almacen.can_manage_warehouse'],
    requireAll: false,
    children: [
      {
        key: 'almacen-stock',
        label: 'Stock',
        path: '/almacen/stock',
        permissions: ['almacen.can_view_stock'],
      },
      {
        key: 'almacen-movements',
        label: 'Movimientos',
        path: '/almacen/movements',
        permissions: ['almacen.can_manage_warehouse', 'almacen.can_create_movements'],
        requireAll: false,
      },
    ],
  },
  // ... more menu items
];

// Filter menu based on user permissions
export const filterMenuByPermissions = (menu, userPermissions) => {
  return menu.filter(item => {
    if (!item.permissions || item.permissions.length === 0) {
      return true;  // Show items without permission requirements
    }

    const hasAccess = item.requireAll
      ? item.permissions.every(p => userPermissions.includes(p))
      : item.permissions.some(p => userPermissions.includes(p));

    if (!hasAccess) {
      return false;
    }

    // Filter children recursively
    if (item.children) {
      item.children = filterMenuByPermissions(item.children, userPermissions);
    }

    return true;
  });
};
```

---

## Summary

This frontend implementation provides:

1. ✅ **Complete API Integration** - All 16 endpoints covered
2. ✅ **Permission Management UI** - Create, edit, delete permissions
3. ✅ **Category Management** - Organize permissions by module
4. ✅ **Assignment Interface** - Assign/revoke permissions to users/groups
5. ✅ **Audit Log Viewer** - Complete visibility of changes
6. ✅ **Permission Hierarchy** - View parent-child relationships
7. ✅ **Protected Routes** - Secure pages based on permissions
8. ✅ **Permission Hooks** - Reusable permission checking
9. ✅ **Menu Filtering** - Dynamic menu based on user permissions
10. ✅ **Error Handling** - Comprehensive error management

**Next Steps:**
1. Install dependencies: `npm install axios antd react-router-dom`
2. Copy components to your React project
3. Update API base URL in `permissionsApi.js`
4. Add routes to your router
5. Integrate with your authentication system
6. Test with the provided test script

The system is production-ready and fully functional!
