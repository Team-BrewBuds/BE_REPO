from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.permissions import IsOwnerOrReadOnly
from repo.common.serializers import PageNumberSerializer
from repo.common.utils import get_paginated_response_with_class
from repo.common.view_counter import update_view_count
from repo.records.models import TastedRecord
from repo.records.services import (
    get_annonymous_tasted_records_feed,
    get_tasted_record_detail,
    get_tasted_record_feed,
)
from repo.records.tasted_record.serializers import (
    TastedRecordCreateUpdateSerializer,
    TastedRecordDetailSerializer,
    TastedRecordListSerializer,
)
from repo.records.tasted_record.service import (
    create_tasted_record,
    update_tasted_record,
)


@extend_schema_view(
    get=extend_schema(
        parameters=[PageNumberSerializer],
        responses={200: TastedRecordListSerializer},
        summary="홈 [시음기록] 피드 조회",
        description="""
            홈 피드의 시음기록 list를 최신순으로 가져옵니다.
            - 순서: 팔로잉, 일반
            - 정렬: 최신순
            - 페이지네이션 적용 (12개)
            - 30분이내 조회하지않은 게시글 가져옵니다.
            - 프라이빗한 시음기록은 제외

            Notice:
            - like_cnt에서 likes로 변경
            - comments(댓글 수), is_user_noted(사용자 저장여부) 추가 됨
            - 비회원일경우 랜덤으로 시음기록을 가져옵니다.

            담당자: hwstar1204
        """,
        tags=["tasted_records"],
    ),
    post=extend_schema(
        request=TastedRecordCreateUpdateSerializer,
        responses={
            201: TastedRecordDetailSerializer,
            400: OpenApiResponse(description="Bad Request (taste_review.star type: float)"),
        },
        summary="시음기록 생성",
        description="""
            단일 시음기록을 생성합니다.
            담당자 : hwstar1204
        """,
        tags=["tasted_records"],
    ),
)
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

    def get(self, request, *args, **kwargs):
        serializer_class = TastedRecordListSerializer
        user = request.user
        if not user.is_authenticated:
            tasted_records = get_annonymous_tasted_records_feed()
            return get_paginated_response_with_class(request, tasted_records, serializer_class)

        tasted_records = get_tasted_record_feed(request, request.user)
        return get_paginated_response_with_class(request, tasted_records, serializer_class)

    def post(self, request):
        serializer = TastedRecordCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                tasted_record = create_tasted_record(request.user, serializer.validated_data)
                response_serializer = TastedRecordDetailSerializer(tasted_record, context={"request": request})

            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        responses={200: TastedRecordDetailSerializer},
        summary="시음기록 상세 조회",
        description="""
            시음기록의 상세 정보를 가져옵니다.
            담당자 : hwstar1204
        """,
        tags=["tasted_records"],
    ),
    put=extend_schema(
        request=TastedRecordCreateUpdateSerializer,
        responses={
            200: TastedRecordDetailSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
        summary="시음기록 수정",
        description="""
            시음기록의 정보를 수정합니다. (전체 수정)
            담당자 : hwstar1204
        """,
        tags=["tasted_records"],
    ),
    patch=extend_schema(
        request=TastedRecordCreateUpdateSerializer,
        responses={
            200: TastedRecordDetailSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
        summary="시음기록 수정",
        description="""
            시음기록의 정보를 수정합니다. (일부 수정)
            담당자 : hwstar1204
        """,
        tags=["tasted_records"],
    ),
    delete=extend_schema(
        responses={204: OpenApiResponse(description="No Content")},
        summary="시음기록 삭제",
        description="""
            시음기록을 삭제합니다.
            담당자 : hwstar1204
        """,
        tags=["tasted_records"],
    ),
)
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

    def get_object(self, pk):
        tasted_record = get_object_or_404(TastedRecord, pk=pk)
        self.check_object_permissions(self.request, tasted_record)
        return tasted_record

    def get(self, request, pk):
        tasted_record = self.get_object(pk)
        tasted_record_detail = get_tasted_record_detail(tasted_record.id)

        # 쿠키 기반 조회수 업데이트
        response = update_view_count(request, tasted_record_detail, Response(), "tasted_record_viewed")
        response.data = self.response_serializer_class(tasted_record_detail, context={"request": request}).data
        response.status_code = status.HTTP_200_OK

        return response

    def put(self, request, pk):
        tasted_record = self.get_object(pk)
        serializer = self.serializer_class(tasted_record, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            updated_tasted_record = update_tasted_record(tasted_record, serializer.validated_data)

        response_serializer = self.response_serializer_class(updated_tasted_record, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        tasted_record = self.get_object(pk)
        serializer = self.serializer_class(tasted_record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            updated_tasted_record = update_tasted_record(tasted_record, serializer.validated_data)

        response_serializer = self.response_serializer_class(updated_tasted_record, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        tasted_record = self.get_object(pk)
        tasted_record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
