from datetime import datetime, timedelta
from typing import Optional, Tuple, Type

from django.db.models import Model, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from repo.records.models import Comment, Post, TastedRecord


def get_object(pk: int, model: Type[Model]) -> Tuple[Optional[Model], Optional[Response]]:
    """
    주어진 기본 키(pk)와 모델을 사용하여 객체를 검색
    Args:
        pk (int): 검색할 객체의 기본 키
        model (Model): 검색할 모델 클래스
        반환값:
        tuple: 첫 번째 요소는 검색된 객체 또는 None, 두 번째 요소는 오류 응답 또는 None
        - (None, Response): 기본 키가 제공되지 않은 경우
        - (None, Response): 객체를 찾을 수 없는 경우
        - (data, None): 객체가 성공적으로 검색된 경우
    작성자 : hwstar1204
    """

    if not pk:
        return None, Response({"error": "PK is required"}, status=status.HTTP_400_BAD_REQUEST)

    data = model.objects.filter(pk=pk).first()
    if not data:
        return None, Response({"error": "Data not found"}, status=status.HTTP_404_NOT_FOUND)

    return data, None


def create(request: Request, serializer_class: Type[Serializer]) -> Response:
    """
    주어진 직렬화 클래스를 사용하여 새 객체를 생성
    Args:
        request (Request): 클라이언트로부터의 요청 객체
        serializer_class (Serializer): 객체를 직렬화할 직렬화 클래스
    Returns:
        Response: 생성 결과에 따라 HTTP 응답을 반환
    """

    data_serializer = serializer_class(data=request.data)
    if data_serializer.is_valid():
        data_serializer.save()
        return Response(data_serializer.data, status=status.HTTP_201_CREATED)
    return Response(data_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def update(request: Request, pk: int, model: Type[Model], serializer_class: Type[Serializer], partial: bool = False) -> Response:
    """
    주어진 primary key와 모델을 사용하여 객체를 업데이트
    Args:
        request (Request): 클라이언트로부터의 요청 객체
        pk (int): 업데이트할 객체의 primary key
        model (Model): 업데이트할 객체의 모델 클래스
        serializer_class (Serializer): 객체를 직렬화할 직렬화 클래스
        partial (bool, optional): 부분 업데이트 여부를 지정합니다. 기본값은 False
    Returns:
        Response: 업데이트 결과에 따라 HTTP 응답을 반환
    작성자 : hwstar1204
    """

    data, response = get_object(pk, model)
    if response:
        return response

    data_serializer = serializer_class(data, data=request.data, context={"request": request}, partial=partial)
    if data_serializer.is_valid():
        data_serializer.save()
        return Response(data_serializer.data, status=status.HTTP_200_OK)
    return Response(data_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_paginated_response_with_class(request: Request, queryset: QuerySet, serializer_class: Type[Serializer]) -> Response:
    """
    페이지네이션된 응답을 생성하는 매서드 (직렬화 클래스 사용)

    Args:
        request (Request): 클라이언트로부터의 요청 객체
        queryset (QuerySet): 페이지네이션할 쿼리셋
        serializer_class (Type[Serializer]): 데이터를 직렬화할 직렬화 클래스

    Returns:
        Response: 페이지네이션된 응답
    """
    paginator = PageNumberPagination()
    data = paginator.paginate_queryset(queryset, request)
    serialized_data = serializer_class(data, many=True, context={"request": request}).data
    return paginator.get_paginated_response(serialized_data)


def get_time_difference(object_created_at: timezone) -> str:
    """
    주어진 객체의 생성 시간과 현재 시간의 차이를 반환
    Args:
        object_created_at (datetime): 객체의 생성 시간
    Returns:
        timedelta: 현재 시간과 객체의 생성 시간의 차이
    작성자 : hwstar1204
    """

    now = timezone.now()
    time_difference = now - object_created_at

    if (years_ago := time_difference // timedelta(days=365)) > 0:
        return f"{years_ago}년 전"
    if (months_ago := (time_difference % timedelta(days=365)) // timedelta(days=30)) > 0:
        return f"{months_ago}개월 전"
    if (days_ago := (time_difference % timedelta(days=365)) // timedelta(days=1)) > 0:
        return f"{days_ago}일 전"
    if (hours_ago := time_difference // timedelta(hours=1)) > 0:
        return f"{hours_ago}시간 전"
    if (minutes_ago := (time_difference % timedelta(hours=1)) // timedelta(minutes=1)) > 0:
        return f"{minutes_ago}분 전"
    return "방금 전"


def get_last_monday(date: timezone) -> timezone:
    """
    주어진 날짜의 지난주 월요일을 반환
    Args:
        date (timezone): 날짜
    Returns:
        timezone: 지난주 월요일
    """
    return date - timedelta(days=date.weekday() + 7)


def get_first_photo_url(obj: Model) -> Optional[str]:
    """
    주어진 객체의 첫 번째 사진 URL을 반환
    Args:
        obj: 사진 URL을 가져올 객체
    Returns:
        str: 객체의 첫 번째 사진 URL
    작성자 : hwstar1204
    """

    if obj and hasattr(obj, "photo_set") and obj.photo_set.exists():
        return obj.photo_set.first().photo_url.url
    return None


def get_object_by_type(object_type, object_id):
    """
    주어진 타입과 ID에 해당하는 객체를 반환합니다.

    Args:
        object_type: 객체 타입 ('post' 또는 'tasted_record' 또는 'comment')
        object_id: 객체 ID

    Returns:
        Post or TastedRecord or Comment: 요청된 객체

    Raises:
        ValueError: 유효하지 않은 object_type이 전달된 경우
    """
    if object_type == "post":
        obj = get_object_or_404(Post, pk=object_id)
    elif object_type == "tasted_record":
        obj = get_object_or_404(TastedRecord, pk=object_id)
    elif object_type == "comment":
        obj = get_object_or_404(Comment, pk=object_id)
    else:
        raise ValueError("invalid object_type")

    return obj


def make_date_format(date: datetime | None) -> str | None:
    """
    주어진 날짜를 문자열로 변환
    Args:
        date (datetime | None): 날짜
    Returns:
        str | None: 날짜 문자열
    """
    if date:
        return date.strftime("%Y-%m-%d %H:%M:%S")
    return None
