from rest_framework.pagination import PageNumberPagination

from api.constants import PAGE_SIZE


class PageNumberPaginationWithLimit(PageNumberPagination):
    """
    Кастомный класс для пагинации с размером страницы в 6 элементов.

    Позволяет изменять размер страницы с помощью параметра запроса limit.
    """

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
