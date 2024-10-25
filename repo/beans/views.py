from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from repo.beans.models import Bean
from repo.beans.schemas import BeanSchema
from repo.beans.serializers import BeanSerializer


@BeanSchema.bena_name_list_schema
class BeanNameListView(APIView):
    def get(self, request):
        beans = Bean.objects.all()

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_beans = paginator.paginate_queryset(beans, request)

        serializer = BeanSerializer(paginated_beans, many=True)
        return paginator.get_paginated_response(serializer.data)


@BeanSchema.bean_name_search_schema
class BeanNameSearchView(APIView):
    def get(self, request):
        name = request.query_params.get("name")
        if not name:
            return BeanNameListView().get(request)

        beans = Bean.objects.filter(name__contains=name).order_by("name")

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_beans = paginator.paginate_queryset(beans, request)

        serializer = BeanSerializer(paginated_beans, many=True)
        return paginator.get_paginated_response(serializer.data)
