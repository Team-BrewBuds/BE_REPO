import pytest
from rest_framework import status

from tests.factorys import BeanFactory, BeanTasteReviewFactory, TastedRecordFactory

pytestmark = pytest.mark.django_db


class TestUserTastedRecordListAPIView:
    """
    사용자 시음기록 리스트 조회 API 테스트
    작성한 테스트 케이스
    - [일반] 사용자의 시음기록 리스트 조회 성공 테스트
    - [필터링] 원두 종류, 원산지, 디카페인, 별점 필터링 성공 테스트
    - [정렬] 최신순, 별점순, 좋아요순 정렬 성공 테스트
    - [예외] 존재하지 않는 사용자의 시음기록 리스트 조회 테스트
    """

    def test_get_user_tasted_record_list(self, authenticated_client):
        """
        사용자의 시음기록 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        tasted_records = [TastedRecordFactory(author=user) for _ in range(3)]
        # When
        url = f"/profiles/{user.id}/tasted-records/"
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
        url = f"/profiles/{user.id}/tasted-records/"
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
        url = f"/profiles/{user.id}/tasted-records/?ordering={ordering}"
        response = api_client.get(url)

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
        url = f"/profiles/{non_existent_user_id}/tasted-records/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND
