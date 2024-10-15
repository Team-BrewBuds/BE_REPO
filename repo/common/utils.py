from typing import Optional, Tuple, Type

from django.db.models import Model
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer


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


def delete(request: Request, pk: int, model: Type[Model]) -> Response:
    """
    주어진 primary key와 모델을 사용하여 객체를 삭제
    Args:
        request (Request): 클라이언트로부터의 요청 객체
        pk (int): 삭제할 객체의 primary key
        model (Model): 삭제할 객체의 모델 클래스
    Returns:
        Response: 삭제 결과에 따라 HTTP 응답을 반환
    작성자 : hwstar1204
    """

    data, response = get_object(pk, model)
    if response:
        return response

    data.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
