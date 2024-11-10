import pytest
from rest_framework import status

from tests.factorys import CustomUserFactory, RelationshipFactory

pytestmark = pytest.mark.django_db


class TestBlockListAPIView:
    """
    차단 관계 조회 API 테스트
    작성한 테스트 케이스
    - [일반] 차단 관계 조회 성공 테스트
    - [정렬] 차단 관계 조회 시 최근 차단 관계가 가장 먼저 조회되는 테스트
    - [예외] 인증되지 않은 사용자인 경우 401 에러 반환 테스트
    """

    def test_get_block_list_success(self, authenticated_client):
        """
        차단 관계 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        blocked_user = CustomUserFactory()
        RelationshipFactory(
            from_user=user,
            to_user=blocked_user,
            relationship_type="block",
        )
        url = "/profiles/block/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == blocked_user.id

    def test_get_block_list_sorted_by_latest(self, authenticated_client):
        """
        차단 관계 조회 시 최근 차단 관계가 가장 먼저 조회되는 테스트
        """
        # Given
        api_client, user = authenticated_client()
        blocked_user_1 = CustomUserFactory()
        blocked_user_2 = CustomUserFactory()
        RelationshipFactory(
            from_user=user,
            to_user=blocked_user_1,
            relationship_type="block",
        )
        RelationshipFactory(
            from_user=user,
            to_user=blocked_user_2,
            relationship_type="block",
        )
        url = "/profiles/block/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == blocked_user_2.id
        assert response.data["results"][1]["id"] == blocked_user_1.id

    def test_get_block_list_unauthorized_401(self, api_client):
        """
        인증되지 않은 사용자인 경우 401 에러 반환 테스트
        """
        # Given
        url = "/profiles/block/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
