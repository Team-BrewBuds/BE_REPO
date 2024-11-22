from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.permissions import IsOwnerOrReadOnly
from repo.common.utils import get_paginated_response_with_class
from repo.common.view_counter import update_view_count
from repo.records.models import TastedRecord
from repo.records.services import (
    get_annonymous_tasted_records_feed,
    get_tasted_record_feed,
)
from repo.records.tasted_record.schemas import TastedRecordSchema
from repo.records.tasted_record.serializers import (
    TastedRecordCreateUpdateSerializer,
    TastedRecordDetailSerializer,
    TastedRecordListSerializer,
)
from repo.records.tasted_record.service import TastedRecordService


@TastedRecordSchema.tasted_record_list_create_schema_view
class TastedRecordListCreateAPIView(APIView):
    """
    홈 피드의 시음기록 list를 최신순으로 가져옵니다.
    Returns:
        시음기록: id, 시음 내용, 사진, 조회수, 좋아요, 생성일, 사진
        프로필: id, 닉네임, 프로필 사진
        원두:  이름, 유형
        원두 맛&평가: 별점, 맛

    주의
    - id로 조회하는 것이 아닌, 팔로워, 최신순 조회
    - 나만보기로 설정한 시음기록은 제외

    담당자 : hwstar1204
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        serializer_class = TastedRecordListSerializer
        user = request.user
        if not user.is_authenticated:
            tasted_records = get_annonymous_tasted_records_feed()
            return get_paginated_response_with_class(request, tasted_records, serializer_class)

        tasted_records = get_tasted_record_feed(request, user)
        return get_paginated_response_with_class(request, tasted_records, serializer_class)

    def post(self, request):
        serializer = TastedRecordCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tasted_record_service = TastedRecordService()
        tasted_record = tasted_record_service.create(request.user, serializer.validated_data)

        response_serializer = TastedRecordDetailSerializer(tasted_record, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@TastedRecordSchema.tasted_record_detail_schema_view
class TastedRecordDetailApiView(APIView):
    """
    시음기록 상세정보 조회, 생성, 수정, 삭제 API
    Args:
        pk
    Returns:
        시음기록: id, 시음 내용, 사진, 조회수, 생성일, 좋아요
        프로필: id, 닉네임, 프로필 사진
        원두: 원두 상세정보, 원두 맛&평가

    담당자 : hwstar1204
    """

    permission_classes = [IsOwnerOrReadOnly]
    serializer_class = TastedRecordCreateUpdateSerializer
    response_serializer_class = TastedRecordDetailSerializer

    def __init__(self):
        self.tasted_record_service = TastedRecordService()

    def get_object(self, pk):
        tasted_record = get_object_or_404(TastedRecord, pk=pk)
        self.check_object_permissions(self.request, tasted_record)
        return tasted_record

    def get(self, request, pk):
        tasted_record = self.get_object(pk)
        tasted_record_detail = self.tasted_record_service.get_record_detail(tasted_record.id)

        # 쿠키 기반 조회수 업데이트
        response = update_view_count(request, tasted_record_detail, Response(), "tasted_record_viewed")
        response.data = self.response_serializer_class(tasted_record_detail, context={"request": request}).data
        response.status_code = status.HTTP_200_OK

        return response

    def put(self, request, pk):
        tasted_record = self.get_object(pk)
        serializer = self.serializer_class(tasted_record, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        updated_tasted_record = self.tasted_record_service.update(tasted_record, serializer.validated_data)

        response_serializer = self.response_serializer_class(updated_tasted_record, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        tasted_record = self.get_object(pk)
        serializer = self.serializer_class(tasted_record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_tasted_record = self.tasted_record_service.update(tasted_record, serializer.validated_data)

        response_serializer = self.response_serializer_class(updated_tasted_record, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        tasted_record = self.get_object(pk)
        tasted_record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
