from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Кастомный класс для пагинации с размером страницы в 6 элемеентов.

    Позволяет изменять размер страницы с помощью параметра запроса limit.
    """

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100
