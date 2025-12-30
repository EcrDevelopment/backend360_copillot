# Solución: Errores de Formato de Datos en Frontend

## Problema Reportado

Errores en consola del navegador:
```javascript
InternalTable.js:104 Uncaught TypeError: rawData.some is not a function
adminRoles.js:28 Uncaught (in promise) TypeError: permissions.forEach is not a function
```

## Causa

Estos errores indican que el frontend espera **arrays** pero está recibiendo **objetos** o datos en formato incorrecto.

## Diagnóstico

### ✅ Backend está correcto

Los ViewSets en `usuarios/views.py` están configurados correctamente:

- `UserViewSet`, `RoleViewSet`, `PermissionViewSet` **SÍ retornan arrays** vía DRF
- Los serializers están configurados correctamente con `many=True` donde corresponde
- Los `get_queryset()` retornan QuerySets que DRF serializa a arrays

### ❌ Posibles causas del problema

1. **Caché del navegador** - El navegador tiene datos antiguos en caché
2. **Estado de Redux/Context** - El estado del frontend tiene datos obsoletos
3. **Transformación incorrecta en frontend** - El código frontend está transformando mal los datos
4. **Endpoints incorrectos** - El frontend está llamando endpoints que ya no existen

## Soluciones

### Solución 1: Limpiar Caché del Navegador (MÁS PROBABLE)

```bash
# En el navegador:
1. Abrir DevTools (F12)
2. Ir a Network tab
3. Click derecho → "Clear browser cache"
4. O usar Ctrl+Shift+Delete → Limpiar caché

# Alternativamente, hacer hard refresh:
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### Solución 2: Verificar Endpoints en Frontend

El frontend debe llamar a estos endpoints correctamente:

```javascript
// CORRECTO - Endpoint de lista (retorna array)
GET /api/accounts/usuarios/          → [{...}, {...}]
GET /api/accounts/roles/              → [{...}, {...}]
GET /api/accounts/permisos/           → [{...}, {...}]

// INCORRECTO - Endpoint de detalle (retorna objeto)
GET /api/accounts/usuarios/1/         → {...}
GET /api/accounts/roles/1/            → {...}
```

**Verificar en código frontend:**
```javascript
// ❌ MAL - Está llamando endpoint de detalle cuando debería listar
axios.get('/api/accounts/usuarios/1/')

// ✅ BIEN - Llama endpoint de lista
axios.get('/api/accounts/usuarios/')
```

### Solución 3: Verificar Transformación de Datos

**Ejemplo del error en `adminRoles.js:28`:**

```javascript
// ❌ MAL - Asume que permissions es un array
const groupPermissions = (permissions) => {
    permissions.forEach(perm => {  // Error si permissions es un objeto
        // ...
    });
};

// ✅ BIEN - Verifica que sea array primero
const groupPermissions = (permissions) => {
    const permsArray = Array.isArray(permissions) ? permissions : [];
    permsArray.forEach(perm => {
        // ...
    });
};
```

**Ejemplo del error en `InternalTable.js:104`:**

```javascript
// ❌ MAL - Asume que rawData es array
const filteredData = rawData.some(item => {  // Error si rawData es objeto
    // ...
});

// ✅ BIEN - Convierte a array o valida
const dataArray = Array.isArray(rawData) ? rawData : [rawData];
const filteredData = dataArray.some(item => {
    // ...
});
```

### Solución 4: Verificar Respuestas del Backend

**Probar manualmente los endpoints:**

```bash
# Con curl
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/accounts/usuarios/

# Con HTTPie
http GET http://localhost:8000/api/accounts/usuarios/ Authorization:"Bearer YOUR_TOKEN"

# Debe retornar:
[
    {
        "id": 1,
        "username": "user1",
        "roles": [1, 2],
        "permissions": [10, 11],
        ...
    },
    ...
]
```

### Solución 5: Resetear Estado del Frontend

```javascript
// En el frontend, limpiar localStorage/sessionStorage
localStorage.clear();
sessionStorage.clear();

// O específicamente:
localStorage.removeItem('usuarios');
localStorage.removeItem('roles');
localStorage.removeItem('permissions');
```

## Verificación Final

Después de aplicar las soluciones, verificar en DevTools:

1. **Network tab**: Ver qué devuelve el endpoint
   ```
   GET /api/accounts/usuarios/
   Status: 200 OK
   Response: [...array de usuarios...]
   ```

2. **Console tab**: No debe haber más errores de `forEach` o `some`

3. **Application tab**: Verificar que no haya datos obsoletos en localStorage

## Comandos para Probar Backend

```bash
# Verificar que el servidor esté corriendo
python manage.py runserver

# En otra terminal, probar endpoints
curl -X GET http://localhost:8000/api/accounts/usuarios/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Debe retornar un array JSON
```

## Resumen

**El backend está CORRECTO** ✅ - Los ViewSets retornan arrays

**El problema está en el frontend** ❌:
1. Caché del navegador con datos antiguos
2. Frontend llamando endpoints incorrectos
3. Frontend transformando mal los datos

**Solución más rápida**: Limpiar caché del navegador y hacer hard refresh (Ctrl+Shift+R)
