from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from records.serializers import PageNumberSerializer
from records.services import get_tasted_record_detail, get_tasted_record_feed2
from records.tasted_record.serializers import TastedRecordDetailSerializer, TastedRecordFeedSerializer
from records.models import Tasted_Record
from common.utils import get_object, create, update, delete


class TastedRecordFeedView(APIView):
    """
    홈 피드의 시음기록 list를 최신순으로 가져옵니다. (이후 팔로워 기능 추가)
    Returns:
        시음기록: id, 시음 내용, 사진, 조회수, 좋아요, 생성일, 사진
        프로필: id, 닉네임, 프로필 사진
        원두:  이름, 유형
        원두 맛&평가: 별점, 맛

    주의
    - id로 조회하는 것이 아닌, 팔로워, 최신순 조회
    - 나만보기로 설정한 시음기록은 제외
    """

    def get(self, request, *args, **kwargs):
        page_serializer = PageNumberSerializer(data=request.GET)
        if page_serializer.is_valid():
            page = page_serializer.validated_data["page"]
        else:
            return Response(page_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        records, has_next = get_tasted_record_feed2(request.user, page)
        tasted_record_serializer = TastedRecordFeedSerializer(records, many=True)

        return Response({"records": tasted_record_serializer.data, "has_next": has_next}, status=status.HTTP_200_OK)


class TastedRecordDetailApiView(APIView):
    """
    시음기록 상세정보 조회, 생성, 수정, 삭제 API
    Args:
        pk
    Returns:
        시음기록: id, 시음 내용, 사진, 조회수, 생성일, 좋아요
        프로필: id, 닉네임, 프로필 사진
        원두: 원두 상세정보, 원두 맛&평가
    """

    def get(self, request, pk):
        _, response = get_object(pk, Tasted_Record)
        if response:
            return response
        
        record = get_tasted_record_detail(pk)

        record_serializer = TastedRecordDetailSerializer(record)
        return Response(record_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        return create(request, TastedRecordDetailSerializer)
    
    def put(self, request, pk):
        return update(request, pk, Tasted_Record, TastedRecordDetailSerializer, False)

    def patch(self, request, pk):
        return update(request, pk, Tasted_Record, TastedRecordDetailSerializer, True)

    def delete(self, request, pk):
        return delete(request, pk, Tasted_Record)
