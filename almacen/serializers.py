from rest_framework import serializers

from importaciones.models import Producto, Empresa
from .models import *


class GremisionCabSerializer(serializers.ModelSerializer):
    class Meta:
        model = GremisionCab
        fields = '__all__'

class GremisionDetSerializer(serializers.ModelSerializer):
    class Meta:
        model = GremisionDet
        fields = [
            #"grenumser",
            #"grenumdoc",
            "itemorden",
            "itemcodigo",
            "itemdescripcion",
            "itemcantidad",
            "itemumedida",
            "itemumedida_origen",
        ]

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'  # Incluye todos los campos de BaseModel

class AlmacenSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(queryset=Empresa.objects.all())
    empresa_nombre = serializers.CharField(source='empresa.razon_social', read_only=True)
    almacen_nombre = serializers.SerializerMethodField()
    class Meta:
        model = Almacen
        fields = '__all__'

    def get_almacen_nombre(self, obj):
        return f"{obj.codigo} - {obj.descripcion} - {obj.empresa.razon_social}"


class AlmacenSelectSerializer(serializers.ModelSerializer):
    # Solo lo mínimo para el Dropdown
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Almacen
        fields = ['id', 'codigo', 'descripcion', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.codigo} - {obj.descripcion}"




class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'


# Serializer para mostrar info básica de Empresa (read-only)
class EmpresaSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'razon_social', 'nombre_empresa']

# Serializer para mostrar info básica de Almacen (read-only)
class AlmacenSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Almacen
        fields = ['id', 'codigo', 'descripcion']

# Serializer para mostrar info básica de Producto (read-only)
class ProductoSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'codigo_producto', 'nombre_producto']

# Serializer para Notas (opcional, si quieres anidarlas)
class MovimientoAlmacenNotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoAlmacenNota
        fields = ['item_erp', 'texto_descripcion', 'texto_detalle'] # Campos relevantes

# Serializer Principal para MovimientoAlmacen
class MovimientoAlmacenSerializer(serializers.ModelSerializer):
    # Usamos los serializers simples para mostrar nombres en lugar de IDs
    empresa = EmpresaSimpleSerializer(read_only=True)
    almacen = AlmacenSimpleSerializer(read_only=True)
    producto = ProductoSimpleSerializer(read_only=True)
    notas = serializers.SerializerMethodField()

    class Meta:
        model = MovimientoAlmacen
        fields = '__all__'

    def get_fecha_documento(self, obj):
        # Retornamos la fecha "nativa" (sin conversión)
        # Si obj.fecha_documento es None, devolvemos None
        return obj.fecha_documento.date() if obj.fecha_documento else None


    #metodo para obtener notas
    def get_notas(self, obj):
        # 1. Buscar el mapa de notas pre-cargado que pasamos desde la vista
        notas_map = self.context.get('notas_map')

        # 2. Si el mapa no existe (ej. en la vista de 'detalle' o si falló),
        #    ejecuta la consulta original (más lenta) como fallback.
        if notas_map is None:
            # self.context.get('request', {}).user # Ejemplo si necesitaras el usuario
            # print("ADVERTENCIA: Ejecutando consulta N+1 en get_notas (probablemente en vista de detalle)") # Debug
            notas_objects = MovimientoAlmacenNota.objects.filter(
                empresa=obj.empresa,
                id_erp_cab=obj.id_erp_cab
            )
        else:
            # 3. Si el mapa SÍ existe (en la vista de 'lista'), busca las notas en él.
            #    Es una búsqueda en memoria, ¡súper rápida!
            key = (obj.empresa_id, obj.id_erp_cab)
            notas_objects = notas_map.get(key, []) # Devuelve la lista de notas o una lista vacía

        # 4. Serializar las notas encontradas (ya sea del mapa o de la BD)
        # Pasamos el 'context' por si MovimientoAlmacenNotaSerializer lo necesita
        return MovimientoAlmacenNotaSerializer(notas_objects, many=True, context=self.context).data

class StockSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Stock.
    Expone los nombres de las relaciones para el frontend.
    """
    empresa = EmpresaSimpleSerializer(read_only=True)
    almacen = AlmacenSimpleSerializer(read_only=True)
    producto = ProductoSimpleSerializer(read_only=True)

    class Meta:
        model = Stock
        fields = [
            'id',
            'empresa',
            'almacen',
            'producto',
            'cantidad_actual',
            'cantidad_en_transito',  # <-- ¡AÑADIDO!
            'fecha_ultimo_movimiento'
        ]

# Serializer simple para la acción de recibir
class RecepcionSerializer(serializers.Serializer):
    cantidad_recibida = serializers.DecimalField(max_digits=15, decimal_places=6)

    # ¡CORREGIDO!
    # El campo se llama 'notas_recepcion' para coincidir con el modelo.
    # 'required=False' lo hace opcional.
    notas_recepcion = serializers.CharField(allow_blank=True, required=False)

class TransferenciaSerializer(serializers.ModelSerializer):
    """
    Serializer para la lista de Transferencias 'EN_TRANSITO'.
    Muestra información anidada para el frontend.
    """
    # Usamos los serializers simples que ya definiste
    empresa = EmpresaSimpleSerializer(read_only=True)
    almacen_origen = AlmacenSimpleSerializer(read_only=True)
    almacen_destino = AlmacenSimpleSerializer(read_only=True)
    producto = ProductoSimpleSerializer(read_only=True)

    class Meta:
        model = Transferencia  # <-- CORREGIDO
        fields = [
            'id',
            'empresa',
            'almacen_origen',
            'almacen_destino',
            'producto',
            'cantidad_enviada',
            'cantidad_recibida',
            'fecha_envio',
            'estado',
            'id_erp_salida_cab',
            'id_erp_salida_det'
        ]



# serializer del componente de estibaje
class TipoEstibajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEstibaje
        fields = '__all__'


class DetalleEstibajeSerializer(serializers.ModelSerializer):
    # Campos de solo lectura para mostrar nombres en el frontend si fuera necesario
    nombre_servicio = serializers.CharField(source='tipo_estibaje.nombre', read_only=True)

    class Meta:
        model = DetalleEstibaje
        fields = ['id', 'tipo_estibaje', 'nombre_servicio', 'cantidad_sacos', 'precio_unitario', 'subtotal']
        read_only_fields = ['subtotal']  # El subtotal se calcula en el modelo o aquí


class RegistroEstibajeSerializer(serializers.ModelSerializer):
    # Escritura anidada: Esperamos una lista de detalles en el JSON
    detalles = DetalleEstibajeSerializer(many=True)

    # Campos extra para mostrar info legible
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)

    class Meta:
        model = RegistroEstibaje
        fields = [
            'id', 'empresa', 'tipo_documento', 'nro_documento',
            'transportista_nombre', 'transportista_ruc', 'placa_vehiculo', 'fecha_registro',
            'producto_nombre','total_sacos_procesados', 'costo_total_operacion',
            'observaciones', 'creado_por', 'creado_por_nombre',
            'detalles'
        ]

    def create(self, validated_data):
        """
        Sobrescribimos create para guardar Cabecera + Detalles en una sola transacción.
        """
        detalles_data = validated_data.pop('detalles')

        with transaction.atomic():
            # 1. Crear la Cabecera
            registro = RegistroEstibaje.objects.create(**validated_data)

            # 2. Crear los Detalles vinculados
            for detalle_data in detalles_data:
                DetalleEstibaje.objects.create(registro=registro, **detalle_data)

            # Opcional: Recalcular totales en cabecera si no confías en lo que manda el front
            # registro.calcular_totales()

        return registro