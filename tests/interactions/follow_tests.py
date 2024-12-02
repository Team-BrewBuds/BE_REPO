import pytest
from rest_framework import status

from tests.factorys import CustomUserFactory, RelationshipFactory

pytestmark = pytest.mark.django_db


class TestFollowListAPIView:
    """
    팔로우 리스트 조회 API 테스트
    작성한 테스트 케이스
    - [일반] 팔로잉 리스트 조회 성공 테스트
    - [일반] 팔로워 리스트 조회 성공 테스트
    - [일반] 팔로워/팔로잉 빈 리스트 조회 응답 테스트
    - [정렬] 최근 관계 설정 순으로 정렬되는지 테스트
    - [일반] 팔로잉 리스트 내 사용자와 나와의 팔로우 여부 확인
    - [일반] 팔로워 리스트 내 사용자와 나와의 팔로우 여부 확인
    - [예외] 팔로잉/팔로워 타입이 아닌 경우 400 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/interactions/relationship/follow/"

    def test_get_following_list_api_view_success(self, authenticated_client):
        """
        팔로잉 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        RelationshipFactory(from_user=user, to_user=CustomUserFactory(), relationship_type="follow")
        RelationshipFactory(from_user=user, to_user=CustomUserFactory(), relationship_type="follow")

        relation_type = "following"

        url = f"{self.url}?type={relation_type}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_get_follower_list_api_view_success(self, authenticated_client):
        """
        팔로워 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        RelationshipFactory(from_user=CustomUserFactory(), to_user=user, relationship_type="follow")
        RelationshipFactory(from_user=CustomUserFactory(), to_user=user, relationship_type="follow")

        relation_type = "follower"

        url = f"{self.url}?type={relation_type}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_get_follow_list_api_view_empty_list_204_response(self, authenticated_client):
        """
        팔로워/팔로잉 빈 리스트 조회 응답 테스트
        """
        # Given
        api_client, user = authenticated_client()
        relation_type = "following"
        url = f"{self.url}?type={relation_type}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_get_follow_list_api_view_sort_by_latest_relation_setting(self, authenticated_client):
        """
        최근 관계 설정 순으로 정렬되는지 테스트
        """
        # Given
        api_client, user = authenticated_client()
        relationship_1 = RelationshipFactory(from_user=user, to_user=CustomUserFactory(), relationship_type="follow")
        relationship_2 = RelationshipFactory(from_user=user, to_user=CustomUserFactory(), relationship_type="follow")

        relation_type = "following"
        url = f"{self.url}?type={relation_type}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["user"]["id"] == relationship_2.to_user.id
        assert response.data["results"][1]["user"]["id"] == relationship_1.to_user.id

    def test_get_following_list_with_follow_status(self, authenticated_client):
        """
        팔로잉 리스트 내 사용자와 나와의 팔로우 여부 확인
        """
        # Given
        api_client, user = authenticated_client()
        RelationshipFactory(from_user=user, to_user=CustomUserFactory(), relationship_type="follow")
        RelationshipFactory(from_user=user, to_user=CustomUserFactory(), relationship_type="follow")

        relation_type = "following"
        url = f"{self.url}?type={relation_type}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["is_following"] is True
        assert response.data["results"][1]["is_following"] is True

    def test_get_follower_list_with_follow_status(self, authenticated_client):
        """
        팔로워 리스트 내 사용자와 나와의 팔로우 여부 확인
        """
        # Given
        api_client, user = authenticated_client()
        RelationshipFactory(from_user=CustomUserFactory(), to_user=user, relationship_type="follow")
        RelationshipFactory(from_user=CustomUserFactory(), to_user=user, relationship_type="follow")

        relation_type = "follower"
        url = f"{self.url}?type={relation_type}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["is_following"] is False
        assert response.data["results"][1]["is_following"] is False

    def test_get_follow_list_api_view_invalid_type_parameter(self, authenticated_client):
        """
        팔로잉/팔로워 타입이 아닌 경우 400 에러 반환 테스트
        """
        # Given
        api_client, user = authenticated_client()
        relation_type = "invalid"
        url = f"{self.url}?type={relation_type}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["message"] == "Invalid follow type"
        assert response.data["code"] == "bad_request"
        assert response.data["status"] == 400


class TestFollowListCreateDeleteAPIView:
    """
    팔로우 관계 조회/생성/삭제 API 테스트
    """

    def setup_method(self):
        self.url = "/interactions/relationship/follow/"

    def test_create_following_relationship_success(self, authenticated_client):
        """
        팔로잉 관계 생성 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        target_user = CustomUserFactory()
        url = f"{self.url}{target_user.id}/"

        # When
        response = api_client.post(url)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] == "follow"

    def test_create_follower_relationship_success(self, authenticated_client):
        """
        팔로워 관계 생성 성공 테스트
        """
        # Given
        api_client1, user1 = authenticated_client()
        api_client2, user2 = authenticated_client()
        url = f"{self.url}{user1.id}/"
        # When
        response = api_client2.post(url)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] == "follow"

    def test_delete_following_relationship_success(self, authenticated_client):
        """
        팔로잉 관계 삭제 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        target_user = CustomUserFactory()
        RelationshipFactory(from_user=user, to_user=target_user, relationship_type="follow")
        url = f"{self.url}{target_user.id}/"

        # When
        response = api_client.delete(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] == "unfollow"

    def test_delete_follower_relationship_success(self, authenticated_client):
        """
        팔로워 관계 삭제 성공 테스트
        """
        # Given
        api_client1, user1 = authenticated_client()
        api_client2, user2 = authenticated_client()
        RelationshipFactory(from_user=user2, to_user=user1, relationship_type="follow")
        url = f"{self.url}{user1.id}/"

        # When
        response = api_client2.delete(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] == "unfollow"

    def test_get_follow_relationship_blocked_user_403(self, authenticated_client):
        """
        팔로잉/팔로워 관계 조회 시 차단 관계인 경우 403 에러 반환 테스트
        """
        # Given
        api_client, user = authenticated_client()
        blocked_user = CustomUserFactory()
        RelationshipFactory(from_user=user, to_user=blocked_user, relationship_type="block")
        url = f"{self.url}{blocked_user.id}/"

        # When
        response = api_client.post(url)

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["message"] == "user is blocking or blocked"
        assert response.data["code"] == "forbidden"
        assert response.data["status"] == 403

    def test_get_follow_relationship_not_found_user_404(self, authenticated_client, non_existent_user_id):
        """
        팔로잉/팔로워 관계 조회 시 존재하지 않는 사용자인 경우 404 에러 반환 테스트
        """
        # Given
        api_client, user = authenticated_client()
        url = f"{self.url}{non_existent_user_id}/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_follow_relationship_already_following_409(self, authenticated_client):
        """
        이미 팔로우 중인 사용자를 다시 팔로우할 때 409 에러 반환 테스트
        """
        # Given
        api_client, user = authenticated_client()
        target_user = CustomUserFactory()
        RelationshipFactory(from_user=user, to_user=target_user, relationship_type="follow")
        url = f"{self.url}{target_user.id}/"

        # When
        response = api_client.post(url)

        # Then
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["message"] == "user is already following"
        assert response.data["code"] == "conflict"
        assert response.data["status"] == 409
