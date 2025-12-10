from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """Кастомная пагинация с поддержкой параметра limit."""
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100

