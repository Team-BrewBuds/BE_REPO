import pytest
from rest_framework import status

from repo.interactions.relationship.models import Relationship
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

    def setup_method(self):
        self.url = "/interactions/relationship/block/"

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

        # When
        response = api_client.get(self.url)

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

        # When
        response = api_client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == blocked_user_2.id
        assert response.data["results"][1]["id"] == blocked_user_1.id

    def test_get_block_list_unauthorized_401(self, api_client):
        """
        인증되지 않은 사용자인 경우 401 에러 반환 테스트
        """
        # Given

        # When
        response = api_client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestBlockListCreateDeleteAPIView:
    """
    차단 관계 생성 및 삭제 API 테스트
    작성한 테스트 케이스
    - [일반] 차단 관계 생성 성공 테스트
    - [일반] 차단 관계 삭제 성공 테스트
    - [예외] 차단 관계가 이미 존재하는 경우 409 에러 반환 테스트
    - [예외] 차단 관계가 존재하지 않는 경우 404 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/interactions/relationship/block/"

    def test_create_block_success(self, authenticated_client):
        """
        차단 관계 생성 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        target_user = CustomUserFactory()
        url = f"{self.url}{target_user.id}/"

        # When
        response = api_client.post(url)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] == "block"
        assert Relationship.objects.filter(from_user=user, to_user=target_user, relationship_type="block").exists()

    def test_delete_block_success(self, authenticated_client):
        """
        차단 관계 삭제 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        blocked_user = CustomUserFactory()
        RelationshipFactory(from_user=user, to_user=blocked_user, relationship_type="block")
        url = f"{self.url}{blocked_user.id}/"

        # When
        response = api_client.delete(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] == "unblock"
        assert not Relationship.objects.filter(from_user=user, to_user=blocked_user, relationship_type="block").exists()

    def test_create_block_conflict_409(self, authenticated_client):
        """
        차단 관계가 이미 존재하는 경우 409 에러 반환 테스트
        """
        # Given
        api_client, user = authenticated_client()
        blocked_user = CustomUserFactory()
        RelationshipFactory(from_user=user, to_user=blocked_user, relationship_type="block")
        url = f"{self.url}{blocked_user.id}/"

        # When
        response = api_client.post(url)

        # Then
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["message"] == "user is already blocking"
        assert response.data["code"] == "conflict"
        assert response.data["status"] == 409

    def test_delete_block_not_found_404(self, authenticated_client):
        """
        차단 관계가 존재하지 않는 경우 404 에러 반환 테스트
        """
        # Given
        api_client, user = authenticated_client()
        non_blocked_user = CustomUserFactory()
        url = f"{self.url}{non_blocked_user.id}/"

        # When
        response = api_client.delete(url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND
