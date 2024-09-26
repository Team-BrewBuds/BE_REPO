from rest_framework.views import APIView
from rest_framework.response import Response

from records.models import Tasted_Record
from records.tasted_record.serializers import TastedRecordListSerializer

class TastedRecordListCreateApiView(APIView):
    """
    홈화면에서 시음기록을 보여주는 Post list를 최신순으로 가져옵니다.
    시음기록 : id, 시음 내용, 사진, 조회수, 좋아요, 생성일, 사진
    프로필 : id, 닉네임, 프로필 사진
    원두 : 이름, 유형
    원두 맛&평가 : 별점, 맛

    주의
    - id로 조회하는 것이 아닌, 팔로워, 최신순 조회
    - 나만보기로 설정한 시음기록은 제외
    """

    def get(self, request):
        tr_list = Tasted_Record.objects.filter(is_private=False).order_by('-created_at')[:12]
        serializer = TastedRecordListSerializer(tr_list, many=True)

        return Response(serializer.data, status=200)

    def post(self, request):
        pass

class TastedRecordDetailApiView(APIView):
    """
    시음기록 상세보기
    시음기록 : id, 시음 내용, 사진, 조회수, 생성일, 좋아요,
    프로필 : id, 닉네임, 프로필 사진 - user_id 사용
    원두 상세정보 : 유형, 국가, 지역, 품종, 가공방식, 로스터리, 로스팅포인트, 추출방식, 음료유형 - bean_id 사용
    원두 맛&평가 : 맛, 별점, 시음날짜, 시음 장소 - bean_taste_review_id 사용
    """

    def get(self, request, pk):
        pass

    def put(self, request, pk):
        pass

    def delete(self, request, pk):
        pass
