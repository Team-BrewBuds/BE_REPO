import pytest
from rest_framework import status

from tests.factorys import CustomUserFactory, UserDetailFactory

pytestmark = pytest.mark.django_db


class TestMyProfileAPIView:
    """
    MyProfileAPIView 테스트
    작성한 테스트 목록
    - [일반] 내 프로필 조회 성공 테스트
    - [일반] 내 프로필 수정 성공 테스트
    - [예외] 인증되지 않은 사용자의 프로필 조회 실패 테스트
    - [예외] 잘못된 데이터로 프로필 수정 실패 테스트
    - [예외] 이미 사용 중인 닉네임으로 프로필 수정 실패 테스트
    """

    def test_get_my_profile_success(self, authenticated_client):
        """
        내 프로필 조회 성공 테스트
        """
        # Given
        client, user = authenticated_client()
        url = "/profiles/"

        # When
        response = client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user.id
        assert response.data["nickname"] == user.nickname

    def test_patch_my_profile_success(self, authenticated_client):
        """
        내 프로필 수정 성공 테스트
        """
        # Given
        client, user = authenticated_client()
        UserDetailFactory(user=user)
        url = "/profiles/"

        # When
        update_data = {
            "nickname": "newnickname",
            "user_detail": {"introduction": "newintroduction", "coffee_life": {"cafe_tour": True, "coffee_extraction": True}},
        }

        response = client.patch(url, data=update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["nickname"] == "newnickname"
        assert response.data["user_detail"]["introduction"] == "newintroduction"
        assert response.data["user_detail"]["coffee_life"]["cafe_tour"] is True
        assert response.data["user_detail"]["coffee_life"]["coffee_extraction"] is True

    def test_get_my_profile_unauthorized(self, api_client):
        """
        인증되지 않은 사용자의 프로필 조회 실패 테스트
        """
        # Given
        url = "/profiles/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_my_profile_emptry_nickname_data(self, authenticated_client):
        """
        잘못된 데이터로 프로필 수정 실패 테스트
        """
        # Given
        client, user = authenticated_client()
        UserDetailFactory(user=user)
        url = "/profiles/"

        # When
        invalid_data = {
            "nickname": "",  # 빈 문자열은 유효하지 않음
        }

        response = client.patch(url, data=invalid_data, format="json")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "닉네임은 공백일 수 없습니다."  # msg from model manager

    def test_patch_my_profile_nickname_already_exists(self, authenticated_client):
        """
        이미 사용 중인 닉네임으로 프로필 수정 실패 테스트
        """
        # Given
        client, _ = authenticated_client()
        other_user = CustomUserFactory()
        other_user.nickname = "othernickname"
        other_user.save()

        url = "/profiles/"

        # When
        update_data = {
            "nickname": "othernickname",
        }

        response = client.patch(url, data=update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["nickname"][0] == "사용자 with this 닉네임 already exists."  # msg from db
        assert response.data["nickname"][0].code == "unique"


class TestOtherProfileAPIView:
    """
    OtherProfileAPIView 테스트
    작성한 테스트 목록
    - [일반] 다른 사용자 프로필 조회 성공 테스트
    - [예외] 인증되지 않은 사용자의 프로필 조회 실패 테스트
    """

    def test_get_other_profile_success(self, authenticated_client):
        """
        다른 사용자 프로필 조회 성공 테스트
        """
        # Given
        client, _ = authenticated_client()
        other_user = CustomUserFactory()
        UserDetailFactory(user=other_user)

        # When
        url = f"/profiles/{other_user.id}/"

        response = client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == other_user.id
        assert response.data["nickname"] == other_user.nickname

    def test_get_other_profile_unauthorized(self, api_client):
        """
        인증되지 않은 사용자의 프로필 조회 실패 테스트
        """
        # Given
        url = "/profiles/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
