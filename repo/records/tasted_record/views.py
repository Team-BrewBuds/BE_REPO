from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.beans.models import Bean, BeanTasteReview
from repo.common.serializers import PageNumberSerializer
from repo.common.utils import delete, get_object
from repo.common.view_counter import update_view_count
from repo.records.models import TastedRecord
from repo.records.services import get_tasted_record_detail, get_tasted_record_feed
from repo.records.tasted_record.serializers import (
    TastedRecordCreateUpdateSerializer,
    TastedRecordDetailSerializer,
    TastedRecordListSerializer,
)
from repo.records.tasted_record.service import update_tasted_record


@extend_schema_view(
    get=extend_schema(
        parameters=[PageNumberSerializer],
        responses={200: TastedRecordListSerializer},
        summary="홈 시음기록 리스트 조회",
        description="""
            홈 피드의 시음기록 list를 최신순으로 가져옵니다.
            순서: 팔로잉, 최신순
            담당자 : hwstar1204
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

    def get(self, request, *args, **kwargs):
        tasted_records = get_tasted_record_feed(request.user)

        paginator = PageNumberPagination()
        paginator.page_size = 12
        paginated_tasted_records = paginator.paginate_queryset(tasted_records, request)

        serializer = TastedRecordListSerializer(paginated_tasted_records, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TastedRecordCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                bean_data = serializer.validated_data["bean"]
                bean, created = Bean.objects.get_or_create(**bean_data)
                if created:
                    bean.is_user_created = True
                    bean.save()

                taste_review_data = serializer.validated_data["taste_review"]
                taste_review = BeanTasteReview.objects.create(**taste_review_data)

                tasted_record = TastedRecord.objects.create(
                    author=request.user,
                    bean=bean,
                    taste_review=taste_review,
                    content=serializer.validated_data["content"],
                )

                photos = serializer.validated_data.get("photos", [])
                tasted_record.photo_set.set(photos)

            response_serializer = TastedRecordCreateUpdateSerializer(tasted_record)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

    def get(self, request, pk):
        _, response = get_object(pk, TastedRecord)
        if response:
            return response

        tasted_record = get_tasted_record_detail(pk)

        instance, response = update_view_count(request, tasted_record, Response(), "tasted_record_viewed")

        serializer = TastedRecordDetailSerializer(instance, context={"request": request})
        response.data = serializer.data
        response.status = status.HTTP_200_OK
        return response

    def put(self, request, pk):
        instance = get_object_or_404(TastedRecord, pk=pk)
        return self._handle_update(request, instance, partial=False)

    def patch(self, request, pk):
        instance = get_object_or_404(TastedRecord, pk=pk)
        return self._handle_update(request, instance, partial=True)

    def _handle_update(self, request, instance, partial):
        serializer = TastedRecordCreateUpdateSerializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():

            validated_data = serializer.validated_data

            instance = update_tasted_record(instance, validated_data)

            response_serializer = TastedRecordCreateUpdateSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        return delete(request, pk, TastedRecord)
