from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from records.servieces import get_tasted_record_feed2,get_tasted_record_detail
from .serializers import TastedRecordSerializer, PageNumberSerializer,TastedRecordDetailSerializer

class TastedRecordFeedView(APIView):
    """
        홈 피드의 시음기록 list를 최신순으로 가져옵니다. (이후 팔로워 기능 추가)
        시음기록 : id, 시음 내용, 사진, 조회수, 좋아요, 생성일, 사진
        프로필 : id, 닉네임, 프로필 사진
        원두 : 이름, 유형
        원두 맛&평가 : 별점, 맛

        주의
        - id로 조회하는 것이 아닌, 팔로워, 최신순 조회
        - 나만보기로 설정한 시음기록은 제외
    """
    
    def get(self, request, *args, **kwargs):
        page_serializer = PageNumberSerializer(data=request.GET)
        if page_serializer.is_valid():
            page = page_serializer.validated_data['page']
        else:
            return Response(page_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        records, has_next = get_tasted_record_feed2(request.user, page)
        record_serializer = TastedRecordSerializer(records, many=True)

        return Response({
            'records': record_serializer.data,
            'has_next': has_next
        }, status=status.HTTP_200_OK)
    

class TastedRecordDetailApiView(APIView):
    """
    시음기록 상세보기
    시음기록 : id, 시음 내용, 사진, 조회수, 생성일, 좋아요
    프로필 : id, 닉네임, 프로필 사진
    원두 상세정보, 원두 맛&평가 
    """
    def get(self, request, *args, **kwargs):
        record_id = kwargs.get('pk')
        if not record_id:
            return Response({'error': 'Record ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        record = get_tasted_record_detail(record_id)
        if not record:
            return Response({'error': 'Record not found'}, status=status.HTTP_404_NOT_FOUND)

        record_serializer = TastedRecordDetailSerializer(record)
        return Response(record_serializer.data, status=status.HTTP_200_OK)
