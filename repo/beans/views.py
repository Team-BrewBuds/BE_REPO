from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from repo.beans.models import Bean
from repo.beans.schemas import *
from repo.beans.serializers import BeanSerializer
from repo.beans.services import BeanService


@BeanSchema.bena_name_list_schema
class BeanNameListView(APIView):
    def get(self, request):
        beans = Bean.objects.all().order_by("name")

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_beans = paginator.paginate_queryset(beans, request)

        serializer = BeanSerializer(paginated_beans, many=True)
        return paginator.get_paginated_response(serializer.data)


@BeanSchema.bean_name_search_schema
class BeanNameSearchView(APIView):

    def __init__(self):
        self.bean_service = BeanService()

    def get(self, request):
        name = request.query_params.get("name")
        beans = self.bean_service.search_beans_by_name(name).order_by("name")

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_beans = paginator.paginate_queryset(beans, request)

        serializer = BeanSerializer(paginated_beans, many=True)
        return paginator.get_paginated_response(serializer.data)
