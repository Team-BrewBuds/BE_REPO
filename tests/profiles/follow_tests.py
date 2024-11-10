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

    def test_get_following_list_api_view_success(self, authenticated_client):
        """
        팔로잉 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        RelationshipFactory(from_user=user, to_user=CustomUserFactory(), relationship_type="follow")
        RelationshipFactory(from_user=user, to_user=CustomUserFactory(), relationship_type="follow")

        relation_type = "following"

        url = f"/profiles/follow/?type={relation_type}"

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

        url = f"/profiles/follow/?type={relation_type}"

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
        url = f"/profiles/follow/?type={relation_type}"

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
        url = f"/profiles/follow/?type={relation_type}"

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
        url = f"/profiles/follow/?type={relation_type}"

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
        url = f"/profiles/follow/?type={relation_type}"

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
        url = f"/profiles/follow/?type={relation_type}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
