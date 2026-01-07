# core/pagination.py
from rest_framework.pagination import PageNumberPagination


class DynamicPagination(PageNumberPagination):
    """
    Paginación global para todo el proyecto.
    Características:
    1. page_size por defecto: 10
    2. Permite al cliente elegir el tamaño: ?page_size=50
    3. Permite DESACTIVAR la paginación: ?pagination=off o ?all=true
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        # Si la URL tiene ?pagination=off o ?all=true, retorna None (sin paginar)
        if request.query_params.get('pagination') == 'off' or \
                request.query_params.get('all') == 'true':
            return None

        return super().paginate_queryset(queryset, request, view)