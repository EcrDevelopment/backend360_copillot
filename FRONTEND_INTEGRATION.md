# Integración Frontend: Permisos Funcionales con Menu Config

## Objetivo

Este documento muestra cómo integrar los nuevos permisos funcionales del backend con la configuración del menú del frontend.

## Mapeo de Permisos

### Permisos del Backend → Permisos del Frontend

Los 14 permisos funcionales del backend deben mapearse a los permisos que usa el frontend:

#### Módulo de Usuarios

| Permiso Backend (Nuevo) | Permiso Frontend (Antiguo) | Uso en Menu |
|-------------------------|---------------------------|-------------|
| `usuarios.can_manage_users` | `user.registrar_usuario`, `user.editar_usuario`, `user.eliminar_usuario` | Gestión completa de usuarios |
| `usuarios.can_view_users` | `user.listar_usuarios`, `user.ver_perfil` | Ver listado y perfiles |
| `usuarios.can_manage_roles` | `user.asignar_roles`, `user.gestionar_permisos` | Administrar roles y permisos |
| `usuarios.can_view_roles` | - | Ver roles disponibles |

#### Módulo de Almacén

| Permiso Backend (Nuevo) | Permiso Frontend (Antiguo) | Uso en Menu |
|-------------------------|---------------------------|-------------|
| `almacen.can_manage_warehouse` | `almacen.gestionar_productos`, `almacen.gestionar_movimientos`, `almacen.realizar_ajustes` | Gestión completa de almacén |
| `almacen.can_view_warehouse` | `almacen.ver_modulo`, `almacen.ver_productos` | Ver información de almacén |
| `almacen.can_view_warehouse_reports` | `almacen.generar_reportes` | Acceso a reportes |
| `almacen.can_manage_stock` | `almacen.gestionar_stock` | Gestionar inventario y transferencias |
| `almacen.can_view_stock` | `almacen.ver_stock`, `almacen.ver_kardex` | Ver niveles de inventario |

#### Módulo de Importaciones

| Permiso Backend (Nuevo) | Permiso Frontend (Antiguo) | Uso en Menu |
|-------------------------|---------------------------|-------------|
| `importaciones.can_manage_importaciones` | `importaciones.registrar_flete_internacional`, `importaciones.editar_flete_internacional`, `importaciones.eliminar_flete_internacional` | Gestión completa de importaciones |
| `importaciones.can_view_importaciones` | `importaciones.ver_modulo`, `importaciones.ver_fletes_internacionales` | Ver información de importaciones |
| `importaciones.can_view_importaciones_reports` | `importaciones.ver_reporte_flete`, `importaciones.ver_reporte_estibas` | Acceso a reportes |
| `importaciones.can_manage_documents` | `importaciones.administrar_documentos_dua`, `importaciones.crear_expedientes_dua`, `importaciones.editar_expedientes_dua` | Gestionar documentos |
| `importaciones.can_view_documents` | `importaciones.descargar_expedientes_dua` | Ver y descargar documentos |

## Ejemplo de Configuración del Menu

### Estructura Recomendada

```javascript
const menuConfig = [
  {
    key: 'usuarios',
    label: 'Usuarios',
    icon: <UserOutlined />,
    // Usar el nuevo permiso funcional
    permissions: ['usuarios.can_view_users'],
    children: [
      {
        key: 'usuarios-lista',
        label: 'Lista de Usuarios',
        path: '/usuarios',
        permissions: ['usuarios.can_view_users']
      },
      {
        key: 'usuarios-crear',
        label: 'Crear Usuario',
        path: '/usuarios/crear',
        permissions: ['usuarios.can_manage_users']
      },
      {
        key: 'usuarios-roles',
        label: 'Gestionar Roles',
        path: '/usuarios/roles',
        permissions: ['usuarios.can_manage_roles']
      }
    ]
  },
  {
    key: 'almacen',
    label: 'Almacén',
    icon: <DatabaseOutlined />,
    // Un permiso para acceso al módulo completo
    permissions: ['almacen.can_view_warehouse'],
    children: [
      {
        key: 'almacen-productos',
        label: 'Productos',
        path: '/almacen/productos',
        permissions: ['almacen.can_view_warehouse']
      },
      {
        key: 'almacen-stock',
        label: 'Stock',
        path: '/almacen/stock',
        permissions: ['almacen.can_view_stock']
      },
      {
        key: 'almacen-movimientos',
        label: 'Movimientos',
        path: '/almacen/movimientos',
        permissions: ['almacen.can_manage_warehouse']
      },
      {
        key: 'almacen-transferencias',
        label: 'Transferencias',
        path: '/almacen/transferencias',
        permissions: ['almacen.can_manage_stock']
      },
      {
        key: 'almacen-reportes',
        label: 'Reportes',
        path: '/almacen/reportes',
        permissions: ['almacen.can_view_warehouse_reports']
      }
    ]
  },
  {
    key: 'importaciones',
    label: 'Importaciones',
    icon: <GlobalOutlined />,
    permissions: ['importaciones.can_view_importaciones'],
    children: [
      {
        key: 'importaciones-lista',
        label: 'Lista de Importaciones',
        path: '/importaciones',
        permissions: ['importaciones.can_view_importaciones']
      },
      {
        key: 'importaciones-crear',
        label: 'Nueva Importación',
        path: '/importaciones/crear',
        permissions: ['importaciones.can_manage_importaciones']
      },
      {
        key: 'importaciones-documentos',
        label: 'Documentos',
        path: '/importaciones/documentos',
        permissions: ['importaciones.can_view_documents']
      },
      {
        key: 'importaciones-reportes',
        label: 'Reportes',
        path: '/importaciones/reportes',
        permissions: ['importaciones.can_view_importaciones_reports']
      }
    ]
  }
];
```

## Función de Validación de Permisos

### Verificar si el usuario tiene acceso

```javascript
/**
 * Verifica si el usuario tiene al menos uno de los permisos requeridos
 * @param {Array} requiredPermissions - Permisos requeridos para el item del menú
 * @param {Array} userPermissions - Permisos del usuario actual
 * @returns {boolean}
 */
const hasPermission = (requiredPermissions, userPermissions) => {
  if (!requiredPermissions || requiredPermissions.length === 0) {
    return true; // Item sin restricción
  }
  
  if (!userPermissions || userPermissions.length === 0) {
    return false; // Usuario sin permisos
  }
  
  // El usuario necesita AL MENOS UNO de los permisos requeridos (OR logic)
  return requiredPermissions.some(perm => 
    userPermissions.includes(perm)
  );
};

/**
 * Filtra el menú según los permisos del usuario
 * @param {Array} menuItems - Items del menú
 * @param {Array} userPermissions - Permisos del usuario
 * @returns {Array} - Menu filtrado
 */
const filterMenuByPermissions = (menuItems, userPermissions) => {
  return menuItems
    .filter(item => hasPermission(item.permissions, userPermissions))
    .map(item => {
      if (item.children) {
        return {
          ...item,
          children: filterMenuByPermissions(item.children, userPermissions)
        };
      }
      return item;
    })
    .filter(item => !item.children || item.children.length > 0);
};
```

## Obtener Permisos del Usuario desde Backend

```javascript
/**
 * Obtiene los permisos del usuario desde el backend
 * @param {number} userId - ID del usuario
 * @returns {Promise<Array>} - Array de permisos
 */
const fetchUserPermissions = async (userId) => {
  try {
    const response = await axios.get(`/api/accounts/usuarios/${userId}/`);
    
    // El backend devuelve IDs de permisos
    const permissionIds = response.data.permissions || [];
    
    // Obtener detalles de los permisos
    const permsResponse = await axios.get('/api/accounts/permisos/?all=true');
    const allPermissions = permsResponse.data;
    
    // Mapear IDs a codenames (ej: "almacen.can_view_warehouse")
    const userPermissions = permissionIds.map(id => {
      const perm = allPermissions.find(p => p.id === id);
      if (perm) {
        // Formato: "app_label.codename"
        return `${perm.content_type.app_label}.${perm.codename}`;
      }
      return null;
    }).filter(Boolean);
    
    return userPermissions;
  } catch (error) {
    console.error('Error al obtener permisos:', error);
    return [];
  }
};
```

## Ejemplo de Uso en React

```javascript
import React, { useEffect, useState } from 'react';
import { Menu } from 'antd';
import { useNavigate } from 'react-router-dom';

const MainMenu = ({ userId }) => {
  const [filteredMenu, setFilteredMenu] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const loadMenu = async () => {
      // Obtener permisos del usuario
      const userPermissions = await fetchUserPermissions(userId);
      
      // Filtrar menú según permisos
      const filtered = filterMenuByPermissions(menuConfig, userPermissions);
      
      setFilteredMenu(filtered);
    };
    
    loadMenu();
  }, [userId]);

  const handleMenuClick = ({ key, item }) => {
    const menuItem = findMenuItem(filteredMenu, key);
    if (menuItem?.path) {
      navigate(menuItem.path);
    }
  };

  return (
    <Menu
      mode="inline"
      items={filteredMenu}
      onClick={handleMenuClick}
    />
  );
};
```

## Consideraciones para Escalabilidad

### 1. Cache de Permisos
```javascript
// Guardar permisos en localStorage para evitar consultas repetidas
const cacheUserPermissions = (userId, permissions) => {
  localStorage.setItem(
    `user_permissions_${userId}`,
    JSON.stringify({
      permissions,
      timestamp: Date.now()
    })
  );
};

const getCachedPermissions = (userId, maxAge = 5 * 60 * 1000) => {
  const cached = localStorage.getItem(`user_permissions_${userId}`);
  if (!cached) return null;
  
  const { permissions, timestamp } = JSON.parse(cached);
  
  // Verificar si el cache no ha expirado (5 minutos por defecto)
  if (Date.now() - timestamp > maxAge) {
    return null;
  }
  
  return permissions;
};
```

### 2. Permisos Jerárquicos

Si un usuario tiene `can_manage_warehouse`, automáticamente tiene `can_view_warehouse`:

```javascript
const PERMISSION_HIERARCHY = {
  'almacen.can_manage_warehouse': ['almacen.can_view_warehouse'],
  'almacen.can_manage_stock': ['almacen.can_view_stock'],
  'usuarios.can_manage_users': ['usuarios.can_view_users'],
  'usuarios.can_manage_roles': ['usuarios.can_view_roles'],
  'importaciones.can_manage_importaciones': ['importaciones.can_view_importaciones'],
  'importaciones.can_manage_documents': ['importaciones.can_view_documents'],
};

const expandPermissions = (userPermissions) => {
  const expanded = new Set(userPermissions);
  
  userPermissions.forEach(perm => {
    const implied = PERMISSION_HIERARCHY[perm] || [];
    implied.forEach(impliedPerm => expanded.add(impliedPerm));
  });
  
  return Array.from(expanded);
};
```

### 3. Manejo de Roles

```javascript
/**
 * Los roles SystemAdmin y superusuarios tienen acceso a todo
 */
const isAdmin = (user) => {
  return user.is_superuser || 
         user.groups?.some(g => g.name === 'SystemAdmin');
};

const getUserPermissions = async (userId) => {
  const response = await axios.get(`/api/accounts/usuarios/${userId}/`);
  
  // Si es admin, retornar todos los permisos disponibles
  if (isAdmin(response.data)) {
    const allPerms = await axios.get('/api/accounts/permisos/?all=true');
    return allPerms.data.map(p => `${p.content_type.app_label}.${p.codename}`);
  }
  
  // Sino, retornar solo sus permisos
  return fetchUserPermissions(userId);
};
```

## Migración Gradual

Para migrar gradualmente desde los permisos antiguos a los nuevos:

```javascript
const LEGACY_TO_FUNCTIONAL_MAP = {
  // Usuarios
  'user.registrar_usuario': 'usuarios.can_manage_users',
  'user.editar_usuario': 'usuarios.can_manage_users',
  'user.eliminar_usuario': 'usuarios.can_manage_users',
  'user.listar_usuarios': 'usuarios.can_view_users',
  'user.ver_perfil': 'usuarios.can_view_users',
  
  // Almacén
  'almacen.ver_modulo': 'almacen.can_view_warehouse',
  'almacen.gestionar_productos': 'almacen.can_manage_warehouse',
  'almacen.gestionar_stock': 'almacen.can_manage_stock',
  'almacen.ver_stock': 'almacen.can_view_stock',
  'almacen.generar_reportes': 'almacen.can_view_warehouse_reports',
  
  // Importaciones
  'importaciones.ver_modulo': 'importaciones.can_view_importaciones',
  'importaciones.administrar_documentos_dua': 'importaciones.can_manage_documents',
  'importaciones.ver_reporte_flete': 'importaciones.can_view_importaciones_reports',
};

/**
 * Convierte permisos legacy a permisos funcionales
 */
const convertToFunctionalPermissions = (legacyPermissions) => {
  const functional = new Set();
  
  legacyPermissions.forEach(perm => {
    const functionalPerm = LEGACY_TO_FUNCTIONAL_MAP[perm];
    if (functionalPerm) {
      functional.add(functionalPerm);
    }
  });
  
  return Array.from(functional);
};
```

## Testing

### Unit Test para Validación de Permisos

```javascript
describe('hasPermission', () => {
  test('should allow access with correct permission', () => {
    const required = ['almacen.can_view_warehouse'];
    const user = ['almacen.can_view_warehouse', 'usuarios.can_view_users'];
    
    expect(hasPermission(required, user)).toBe(true);
  });
  
  test('should deny access without permission', () => {
    const required = ['almacen.can_manage_warehouse'];
    const user = ['almacen.can_view_warehouse'];
    
    expect(hasPermission(required, user)).toBe(false);
  });
  
  test('should allow access with any of multiple permissions', () => {
    const required = ['almacen.can_manage_warehouse', 'almacen.can_view_warehouse'];
    const user = ['almacen.can_view_warehouse'];
    
    expect(hasPermission(required, user)).toBe(true);
  });
});
```

## Resumen

1. **Usa los 14 permisos funcionales** en lugar de los ~2000 permisos de tabla
2. **Implementa jerarquía** para que permisos "manage" impliquen permisos "view"
3. **Cache los permisos** del usuario para mejor rendimiento
4. **Migra gradualmente** usando el mapeo de permisos legacy → funcionales
5. **Filtra el menú dinámicamente** según los permisos del usuario
6. **Maneja roles especiales** (SystemAdmin) que tienen acceso completo

---

**Nota**: Una vez que compartas tu `menuConfig` actual, puedo proporcionar un ejemplo de migración específico para tu estructura.
