import pytest
from rest_framework import status

from tests.factorys import (
    BeanFactory,
    BeanTasteReviewFactory,
    NoteFactory,
    TastedRecordFactory,
)


@pytest.mark.django_db
class TestUserBeanListAPIView:
    """
    UserBeanListAPIView 테스트
    작성한 테스트 목록
    - [일반] 사용자의 원두 리스트 조회 성공 테스트
    - [일반] 원두 노트가 없는 사용자의 리스트 조회 테스트
    - [정렬] 최신순 정렬 테스트
    - [정렬] 평균 별점 정렬 테스트
    - [정렬] 시음기록 개수 정렬 테스트
    - [필터링] 원두 종류, 원산지, 디카페인 필터링 테스트
    - [필터링] 로스팅 포인트 필터링 테스트
    - [필터링] 평균 별점 필터링 테스트
    - [예외] 존재하지 않는 사용자의 원두 리스트 조회 테스트
    """

    def setup_method(self):
        self.url = "/beans/profile/"

    def test_get_user_bean_list_success(self, authenticated_client):
        """
        사용자의 원두 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        beans = [BeanFactory() for _ in range(3)]

        # 사용자가 원두에 대한 노트 작성
        for bean in beans:
            NoteFactory(author=user, bean=bean)

        url = f"{self.url}{user.id}/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_get_user_bean_list_empty(self, authenticated_client):
        """
        원두 노트가 없는 사용자의 리스트 조회 테스트
        """
        # Given
        api_client, user = authenticated_client()
        url = f"{self.url}{user.id}/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_get_user_bean_list_ordering_by_created_at(self, authenticated_client):
        """
        최신순 정렬 테스트
        """
        # Given
        api_client, user = authenticated_client()
        beans = [BeanFactory() for _ in range(3)]
        latest_notes = None

        for i, bean in enumerate(beans):
            note = NoteFactory(author=user, bean=bean)
            note.created_at = f"2023-01-0{i+1}"
            note.save()

            if i == len(beans) - 1:
                latest_notes = note

        url = f"{self.url}{user.id}/"  # default ordering = -note__created_at

        # When
        response = api_client.get(f"{url}")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == latest_notes.bean.id

    def test_get_user_bean_list_ordering_by_avg_star(self, authenticated_client):
        """
        평균 별점 정렬 테스트
        """
        # Given
        api_client, user = authenticated_client()
        beans = [BeanFactory() for _ in range(3)]

        for i, bean in enumerate(beans):
            NoteFactory(author=user, bean=bean)

            star_ratings = [1.0, 2.5, 3.0, 5.0]
            TastedRecordFactory(
                author=user,
                bean=bean,
                taste_review=BeanTasteReviewFactory(
                    flavor="",
                    body=3,
                    acidity=3,
                    bitterness=3,
                    sweetness=3,
                    star=star_ratings[i],
                ),
            )

        url = f"{self.url}{user.id}/"
        ordering = "-avg_star"

        # When
        response = api_client.get(f"{url}?ordering={ordering}")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == sorted(response.data["results"], key=lambda x: x["avg_star"], reverse=True)

    def test_get_user_bean_list_ordering_by_tasted_records_cnt(self, authenticated_client):
        """
        시음기록 개수 정렬 테스트
        """
        # Given
        api_client, user = authenticated_client()
        beans = [BeanFactory() for _ in range(3)]

        for bean in beans:
            NoteFactory(author=user, bean=bean)
            TastedRecordFactory(
                author=user,
                bean=bean,
                taste_review=BeanTasteReviewFactory(flavor="", body=3, acidity=3, bitterness=3, sweetness=3, star=3.0),
            )

        url = f"{self.url}{user.id}/"
        ordering = "-tasted_records_cnt"

        # When
        response = api_client.get(f"{url}?ordering={ordering}")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == sorted(
            response.data["results"],
            key=lambda x: x["tasted_records_cnt"],
            reverse=True,
        )

    @pytest.mark.parametrize(
        "filters,expected_count",
        [
            ({"bean_type": "single"}, 2),
            ({"origin_country": "케냐"}, 1),
            ({"is_decaf": False}, 2),
            ({"bean_type": "single", "origin_country": "케냐"}, 1),
            ({"bean_type": "single", "is_decaf": False}, 2),
            ({"origin_country": "케냐", "is_decaf": False}, 1),
            ({"bean_type": "single", "origin_country": "케냐", "is_decaf": False}, 1),
        ],
    )
    def test_get_user_bean_list_with_filters(self, authenticated_client, filters, expected_count):
        """
        필터링 테스트 (원두 종류, 원산지, 디카페인)
        """
        # Given
        api_client, user = authenticated_client()
        beans = [
            BeanFactory(
                bean_type="single",
                origin_country="케냐",
                is_decaf=False,
                roast_point=3,
                name="테스트 원두 1",
            ),
            BeanFactory(
                bean_type="single",
                origin_country="에티오피아",
                is_decaf=False,
                roast_point=4,
                name="테스트 원두 2",
            ),
            BeanFactory(
                bean_type="blend",
                origin_country="브라질",
                is_decaf=True,
                roast_point=5,
                name="테스트 원두 3",
            ),
        ]

        for bean in beans:
            bean.save()
            NoteFactory(author=user, bean=bean)

        url = f"{self.url}{user.id}/"

        # When
        query_params = "&".join([f"{key}={value}" for key, value in filters.items()])
        response = api_client.get(f"{url}?{query_params}")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == expected_count

    @pytest.mark.parametrize(
        "filters,expected_count",
        [
            ({"roast_point_min": 1, "roast_point_max": 5}, 3),
            ({"roast_point_min": 1, "roast_point_max": 3}, 2),
            ({"roast_point_min": 3, "roast_point_max": 3}, 1),
            ({"roast_point_min": 5}, 1),
            ({"roast_point_max": 1}, 1),
        ],
    )
    def test_get_user_bean_list_roast_point_filter(self, authenticated_client, filters, expected_count):
        """
        로스팅 포인트 필터링 테스트
        """
        # Given
        api_client, user = authenticated_client()
        beans = [
            BeanFactory(bean_type="single", roast_point=1),
            BeanFactory(bean_type="single", roast_point=3),
            BeanFactory(bean_type="blend", roast_point=5),
        ]

        for bean in beans:
            NoteFactory(author=user, bean=bean)

        url = f"{self.url}{user.id}/"

        # When
        query_params = "&".join([f"{key}={value}" for key, value in filters.items()])
        response = api_client.get(f"{url}?{query_params}")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == expected_count

    @pytest.mark.parametrize(
        "filters,expected_count",
        [
            ({"avg_star_min": 1.0, "avg_star_max": 5.0}, 4),
            ({"avg_star_min": 1.0, "avg_star_max": 3.0}, 3),
            ({"avg_star_min": 3.0, "avg_star_max": 3.0}, 1),
            ({"avg_star_min": 5.0}, 1),
            ({"avg_star_max": 1.0}, 1),
        ],
    )
    def test_get_user_bean_list_avg_star_filter(self, authenticated_client, filters, expected_count):
        """
        평균 별점 필터링 테스트
        """
        # Given
        api_client, user = authenticated_client()
        beans = [
            BeanFactory(bean_type="single"),
            BeanFactory(bean_type="single"),
            BeanFactory(bean_type="single"),
            BeanFactory(bean_type="blend"),
        ]

        for i, bean in enumerate(beans):
            NoteFactory(author=user, bean=bean)

            star_ratings = [1.0, 2.5, 3.0, 5.0]
            TastedRecordFactory(
                author=user,
                bean=bean,
                taste_review=BeanTasteReviewFactory(
                    flavor="",
                    body=3,
                    acidity=3,
                    bitterness=3,
                    sweetness=3,
                    star=star_ratings[i],
                    place="테스트 장소",
                ),
            )

        url = f"{self.url}{user.id}/"

        # When
        query_params = "&".join([f"{key}={value}" for key, value in filters.items()])
        response = api_client.get(f"{url}?{query_params}")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == expected_count

    def test_get_user_bean_list_invalid_user(self, api_client, non_existent_user_id):
        """
        존재하지 않는 사용자의 원두 리스트 조회 테스트
        """
        # Given
        url = f"{self.url}{non_existent_user_id}/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND
