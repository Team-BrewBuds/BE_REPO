import pytest
from rest_framework import status

from repo.profiles.models import CustomUser
from tests.factorys import CustomUserFactory, UserDetailFactory

pytestmark = pytest.mark.django_db


class TestBudyRecommendAPIView:
    """
    사용자의 커피 생활 방식에 따른 추천 유저 리스트 반환 테스트
    작성한 테스트 케이스
    - [성공] 사용자의 커피 생활 방식에 따른 추천 유저 리스트 반환 성공 테스트
    - [성공] 사용자의 커피 생활 방식이 없을 경우 랜덤으로 카테고리 선택 테스트
    - [예외] 인증되지 않은 사용자의 경우 401 에러 반환 테스트
    """

    @pytest.mark.parametrize(
        "coffee_life",
        ["cafe_tour", "coffee_extraction", "coffee_study", "cafe_alba", "cafe_work", "cafe_operation"],
    )
    def test_get_budy_recommend_api_view(self, authenticated_client, coffee_life):
        """
        사용자의 커피 생활 방식에 따른 추천 유저 리스트 반환 성공 테스트
        """

        # Given
        api_client, user = authenticated_client()

        # 사용자 커피 생활 방식 설정
        user_detail = UserDetailFactory(user=user)
        for key in user_detail.coffee_life.keys():
            user_detail.coffee_life[key] = False
        user_detail.coffee_life[coffee_life] = True
        user_detail.save()

        # 추천할 유저 10명 생성
        for _ in range(10):
            user = UserDetailFactory(user=CustomUserFactory())
            for key in user.coffee_life.keys():
                user.coffee_life[key] = False
            user.coffee_life[coffee_life] = True
            user.save()

        url = "/profiles/recommend/"

        # When
        response = api_client.get(url)

        # Then
        recommended_user_ids = [user["user"]["id"] for user in response.data["users"]]
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["users"]) == 10  # 추천 유저 10명인지 확인
        assert response.data["category"] == coffee_life  # 선택된 카테고리가 올바른지 확인
        assert user.id not in recommended_user_ids  # 나는 추천 유저에 포함되지 않았는지 확인

        for recommended_user_id in recommended_user_ids:  # 모든 추천 유저가 해당 coffee_life 값이 True인지 확인
            recommended_user = CustomUser.objects.get(id=recommended_user_id)
            assert recommended_user.user_detail.coffee_life[coffee_life] is True

    def test_get_budy_recommend_api_view_no_coffee_life(self, authenticated_client):
        """
        사용자의 커피 생활 방식이 없을 경우 랜덤으로 카테고리 선택 테스트
        """

        # Given
        api_client, user = authenticated_client()

        user_detail = UserDetailFactory(user=user)
        for key in user_detail.coffee_life.keys():
            user_detail.coffee_life[key] = False
        user_detail.save()

        # 추천할 유저 10명 생성
        recommend_users = [UserDetailFactory(user=CustomUserFactory()) for _ in range(10)]

        url = "/profiles/recommend/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["users"]) != 0
        assert user.id not in [user["user"]["id"] for user in response.data["users"]]  # 나는 추천 유저에 포함되지 않았는지 확인
        assert response.data["category"] in user_detail.coffee_life.keys()  # 무작위로 선정된 카테고리가 올바른지 확인

    def test_get_budy_recommend_api_view_unauthenticated(self, api_client):
        """
        인증되지 않은 사용자의 경우 401 에러 반환 테스트
        """
        # Given
        url = "/profiles/recommend/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
