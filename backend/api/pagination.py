from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    """Custom pagination class for Foodgram API.

    Provides pagination with default page size of 4 items,
    and allows client to override page size via 'limit' query parameter.
    """

    page_size = 4
    page_size_query_param = 'limit'
