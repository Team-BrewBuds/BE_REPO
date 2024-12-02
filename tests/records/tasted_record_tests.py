import pytest
from rest_framework import status

from repo.records.models import TastedRecord
from tests.factorys import (
    BeanFactory,
    BeanTasteReviewFactory,
    PhotoFactory,
    TastedRecordFactory,
)

pytestmark = pytest.mark.django_db


class TestTastedRecordListCreateAPIView:
    """
    시음기록 목록 조회 및 생성 API 테스트
    작성한 테스트 케이스
    - [조회] 시음기록 목록 조회 성공 테스트
    - [조회] 나만보기 시음기록 제외 테스트
    - [조회] 시음기록 빈 목록 조회 성공 테스트
    - [조회] 시음기록 목록 최신순 정렬 테스트
    - [조회] 비인증 사용자의 시음기록 목록 조회 테스트
    - [생성] 시음기록 생성 성공 테스트
    - [생성] 시음기록 생성 시 사진 포함 테스트
    - [생성] 필수 필드 누락 시 400 에러 반환 테스트
    - [생성] 미인증 사용자의 시음기록 생성 시도시 401 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/records/tasted_record/"

    def test_get_tasted_record_list_success(self, authenticated_client):
        """시음기록 목록 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        tasted_records = TastedRecordFactory.create_batch(3, is_private=False)

        # When
        response = client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_get_tasted_record_list_private_exclude(self, authenticated_client):
        """나만보기 시음기록 제외 테스트"""
        # Given
        client, user = authenticated_client()
        private_tasted_records = TastedRecordFactory.create_batch(3, is_private=True)

        # When
        response = client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_get_tasted_record_list_empty(self, authenticated_client):
        """시음기록 빈 목록 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()

        # When
        response = client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert len(response.data["results"]) == 0

    def test_get_tasted_record_list_order_by_latest(self, authenticated_client):
        """시음기록 목록 최신순 정렬 테스트"""
        # Given
        client, user = authenticated_client()
        tasted_records = TastedRecordFactory.create_batch(3, is_private=False)

        # When
        response = client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert results[0]["id"] > results[1]["id"] > results[2]["id"]

    def test_get_tasted_record_list_unauthenticated(self, api_client):
        """비인증 사용자의 시음기록 목록 조회 테스트"""
        # Given
        records = TastedRecordFactory.create_batch(3, is_private=False)

        # When
        response = api_client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_create_tasted_record_success(self, authenticated_client):
        """시음기록 생성 성공 테스트"""
        # Given
        client, user = authenticated_client()
        bean = BeanFactory()
        taste_review = BeanTasteReviewFactory()

        record_data = {
            "bean": {
                "id": bean.id,
                "name": bean.name,
                "bean_type": bean.bean_type,
                "origin_country": bean.origin_country,
            },
            "taste_review": {
                "id": taste_review.id,
                "flavor": taste_review.flavor,
                "star": taste_review.star,
                "bitterness": taste_review.bitterness,
                "sweetness": taste_review.sweetness,
                "acidity": taste_review.acidity,
                "body": taste_review.body,
                "place": "카페",
            },
            "content": "맛있는 커피였다.",
            "is_private": False,
        }

        # When
        response = client.post(self.url, record_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["bean"]["id"] == bean.id
        assert response.data["content"] == record_data["content"]
        assert response.data["is_private"] == record_data["is_private"]

    def test_create_tasted_record_with_photos(self, authenticated_client, create_test_image):
        """시음기록 생성 시 사진 포함 테스트"""
        # Given
        client, user = authenticated_client()
        photo1 = PhotoFactory(photo_url=create_test_image, tasted_record=None)
        photo2 = PhotoFactory(photo_url=create_test_image, tasted_record=None)
        bean = BeanFactory()
        taste_review = BeanTasteReviewFactory()

        record_data = {
            "bean": {
                "id": bean.id,
                "name": bean.name,
                "bean_type": bean.bean_type,
                "origin_country": bean.origin_country,
            },
            "taste_review": {
                "id": taste_review.id,
                "flavor": taste_review.flavor,
                "star": taste_review.star,
                "bitterness": taste_review.bitterness,
                "sweetness": taste_review.sweetness,
                "acidity": taste_review.acidity,
                "body": taste_review.body,
                "place": "카페",
            },
            "content": "맛있는 커피였다.",
            "is_private": False,
            "photos": [photo1.id, photo2.id],
        }

        # When
        response = client.post(self.url, record_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        record_id = response.data["id"]
        assert TastedRecord.objects.get(id=record_id).photo_set.count() == 2

    def test_create_tasted_record_missing_required_fields(self, authenticated_client):
        """필수 필드 누락 시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        incomplete_data = {
            # content 필드 누락
            "rating": 4.5,
            "is_private": False,
        }

        # When
        response = client.post(self.url, incomplete_data, format="json")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_tasted_record_unauthorized(self, api_client):
        """미인증 사용자의 시음기록 생성 시도시 401 에러 반환 테스트"""
        # Given
        record_data = {
            "content": "맛있는 커피였습니다.",
            "rating": 4.5,
            "is_private": False,
        }

        # When
        response = api_client.post(self.url, record_data, format="json")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert TastedRecord.objects.count() == 0


class TestTastedRecordDetailAPIView:
    """
    시음기록 상세 조회 및 수정/삭제 API 테스트
    작성한 테스트 케이스
    - [조회] 시음기록 상세 조회 성공 테스트
    - [조회] 시음기록 상세 조회 시 조회수 증가 테스트
    - [수정] 시음기록 수정 성공 테스트
    - [수정] 시음기록 부분 수정 성공 테스트
    - [삭제] 시음기록 삭제 성공 테스트
    - [권한] 시음기록 작성자가 아닌 사용자의 수정/삭제 시도 시 403 에러 반환 테스트
    - [권한] 미인증 사용자의 시음기록 수정/삭제 시도 시 401 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/records/tasted_record/"

    def test_get_tasted_record_detail_success(self, authenticated_client):
        """시음기록 상세 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        record = TastedRecordFactory()

        # When
        response = client.get(f"{self.url}{record.id}/")

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_get_tasted_record_detail_view_count_increase(self, authenticated_client):
        """시음기록 상세 조회 시 조회수 증가 테스트"""
        # Given
        client, user = authenticated_client()
        record = TastedRecordFactory()
        initial_view_count = record.view_cnt

        # When
        response = client.get(f"{self.url}{record.id}/")

        # Then
        assert response.status_code == status.HTTP_200_OK
        record.refresh_from_db()
        assert record.view_cnt == initial_view_count + 1

    def test_update_tasted_record_success(self, authenticated_client):
        """시음기록 수정 성공 테스트"""
        # Given
        client, user = authenticated_client()
        record = TastedRecordFactory(author=user)
        photo = PhotoFactory()
        update_data = {
            "content": "수정된 내용입니다.",
            "is_private": True,
            "tag": "test_tag",
            "bean": {
                "bean_type": "single",
                "is_decaf": True,
                "name": "테스트 원두",
                "origin_country": "에티오피아",
                "extraction": "필터",
                "roast_point": 3,
                "process": "워시드",
                "region": "예가체프",
                "bev_type": True,
                "roastery": "테스트 로스터리",
                "variety": "게이샤",
                "is_user_created": True,
            },
            "taste_review": {
                "flavor": "초콜릿, 견과류",
                "body": 3,
                "acidity": 4,
                "bitterness": 2,
                "sweetness": 4,
                "star": 4.0,
                "place": "테스트 카페",
            },
            "photos": [photo.id],
        }

        # When
        response = client.put(f"{self.url}{record.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        record.refresh_from_db()
        assert record.content == update_data["content"]
        assert record.is_private == update_data["is_private"]
        assert record.tag == update_data["tag"]
        assert record.bean.bean_type == update_data["bean"]["bean_type"]
        assert record.bean.name == update_data["bean"]["name"]
        assert record.taste_review.flavor == update_data["taste_review"]["flavor"]
        assert record.taste_review.star == update_data["taste_review"]["star"]
        assert record.photo_set.first().id == photo.id

    def test_partial_update_tasted_record_success(self, authenticated_client):
        """시음기록 부분 수정 성공 테스트"""
        # Given
        client, user = authenticated_client()
        record = TastedRecordFactory(author=user)
        update_data = {
            "content": "부분 수정된 내용입니다.",
        }

        # When
        response = client.patch(f"{self.url}{record.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        record.refresh_from_db()
        assert record.content == update_data["content"]

    def test_delete_tasted_record_success(self, authenticated_client):
        """시음기록 삭제 성공 테스트"""
        # Given
        client, user = authenticated_client()
        record = TastedRecordFactory(author=user)

        # When
        response = client.delete(f"{self.url}{record.id}/")

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TastedRecord.objects.filter(id=record.id).exists()

    def test_update_tasted_record_by_non_owner(self, authenticated_client):
        """시음기록 작성자가 아닌 사용자의 수정 시도시 403 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        other_user_record = TastedRecordFactory()
        update_data = {
            "content": "수정된 내용입니다.",
            "rating": 3.5,
        }

        # When
        response = client.put(f"{self.url}{other_user_record.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_tasted_record_by_non_owner(self, authenticated_client):
        """시음기록 작성자가 아닌 사용자의 삭제 시도시 403 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        other_user_record = TastedRecordFactory()

        # When
        response = client.delete(f"{self.url}{other_user_record.id}/")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert TastedRecord.objects.filter(id=other_user_record.id).exists()

    def test_update_tasted_record_unauthorized(self, api_client):
        """미인증 사용자의 시음기록 수정 시도시 401 에러 반환 테스트"""
        # Given
        record = TastedRecordFactory()
        update_data = {
            "content": "수정된 내용입니다.",
            "rating": 3.5,
        }

        # When
        response = api_client.put(f"{self.url}{record.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_tasted_record_unauthorized(self, api_client):
        """미인증 사용자의 시음기록 삭제 시도시 401 에러 반환 테스트"""
        # Given
        record = TastedRecordFactory()

        # When
        response = api_client.delete(f"{self.url}{record.id}/")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert TastedRecord.objects.filter(id=record.id).exists()


class TestUserTastedRecordListAPIView:
    """
    사용자 시음기록 리스트 조회 API 테스트
    작성한 테스트 케이스
    - [일반] 사용자의 시음기록 리스트 조회 성공 테스트
    - [필터링] 원두 종류, 원산지, 디카페인, 별점 필터링 성공 테스트
    - [정렬] 최신순, 별점순, 좋아요순 정렬 성공 테스트
    - [예외] 존재하지 않는 사용자의 시음기록 리스트 조회 테스트
    """

    def setup_method(self):
        self.url = "/records/tasted_record/user"

    def test_get_user_tasted_record_list(self, authenticated_client):
        """
        사용자의 시음기록 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        tasted_records = [TastedRecordFactory(author=user) for _ in range(3)]
        # When
        url = f"{self.url}/{user.id}/"
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    @pytest.mark.parametrize(
        "filters, expected_count",
        [
            ({"bean_type": "single"}, 2),
            ({"bean_type": "blend"}, 1),
            ({"origin_country": "케냐"}, 2),
            ({"is_decaf": False}, 2),
            ({"bean_type": "single", "origin_country": "케냐"}, 2),
            ({"bean_type": "single", "origin_country": "케냐", "is_decaf": True}, 1),
            ({"star_min": 3}, 1),
            ({"star_max": 3}, 3),
            ({"star_min": 3, "star_max": 3}, 1),
            ({"star_min": 1, "star_max": 5}, 3),
        ],
    )
    def test_get_user_tasted_record_list_filtering(self, authenticated_client, filters, expected_count):
        """
        필터링 테스트 (원두 종류, 원산지, 디카페인, 별점)
        """
        # Given
        api_client, user = authenticated_client()
        bean_infos = [["single", "케냐", True], ["single", "케냐", False], ["blend", "에티오피아", False]]

        beans = [BeanFactory(bean_type=bean_info[0], origin_country=bean_info[1], is_decaf=bean_info[2]) for bean_info in bean_infos]
        tasted_reviews = [BeanTasteReviewFactory(star=i + 1) for i in range(3)]
        tasted_records = [TastedRecordFactory(author=user, bean=beans[i], taste_review=tasted_reviews[i]) for i in range(3)]

        # When
        url = f"{self.url}/{user.id}/"
        response = api_client.get(url, filters)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == expected_count

    @pytest.mark.parametrize(
        "ordering, expected_order",
        [
            ("-created_at", "최신순"),
            ("-taste_review__star", "별점순"),
            ("-likes", "좋아요순"),
        ],
    )
    def test_get_user_tasted_record_list_ordering(self, authenticated_client, ordering, expected_order):
        """
        정렬 테스트 (최신순, 별점순, 좋아요순)
        """
        # Given
        api_client, user = authenticated_client()
        beans = [BeanFactory() for _ in range(3)]
        tasted_reviews = [BeanTasteReviewFactory(star=i + 1) for i in range(3)]
        tasted_records = [TastedRecordFactory(author=user, bean=beans[i], taste_review=tasted_reviews[i]) for i in range(3)]

        # When
        url = f"{self.url}/{user.id}/"
        response = api_client.get(url, {"ordering": ordering})

        # Then
        records = response.data["results"]

        assert response.status_code == status.HTTP_200_OK
        assert len(records) == 3

        if ordering == "-created_at":
            response_ids = [record["id"] for record in records]
            created_records_ids = [tasted_record.id for tasted_record in sorted(tasted_records, key=lambda x: x.created_at, reverse=True)]
            assert response_ids == created_records_ids

        elif ordering == "-taste_review__star":
            assert records[0]["star"] >= records[1]["star"] >= records[2]["star"]

        elif ordering == "-likes":
            assert records[0]["likes"] >= records[1]["likes"] >= records[2]["likes"]

    def test_get_user_tasted_record_list_unauthorized(self, api_client, non_existent_user_id):
        """
        존재하지 않는 사용자의 시음기록 리스트 조회 테스트
        """
        # Given
        url = f"{self.url}/{non_existent_user_id}/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND
