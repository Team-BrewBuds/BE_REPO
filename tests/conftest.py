import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from repo.profiles.models import CustomUser, UserDetail
from tests.factorys import CustomUserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user():
    def _create_user(email="test@test.com", nickname="테스트", login_type="kakao"):
        user = CustomUser.objects.create(
            email=email,
            nickname=nickname,
            login_type=login_type,
            gender="남",
            birth=1990,
        )
        return user

    return _create_user


@pytest.fixture
def create_user_detail():
    def _create_user_detail(user, coffee_life=None, preferred_bean_taste=None):
        if coffee_life is None:
            coffee_life = {
                "cafe_tour": True,
                "coffee_extraction": False,
                "coffee_study": True,
                "cafe_alba": False,
                "cafe_work": False,
                "cafe_operation": True,
            }

        if preferred_bean_taste is None:
            preferred_bean_taste = {
                "body": 3,
                "acidity": 4,
                "bitterness": 2,
                "sweetness": 5,
            }

        user_detail = UserDetail.objects.create(
            user=user,
            introduction="테스트 소개",
            profile_link="https://test.com",
            coffee_life=coffee_life,
            preferred_bean_taste=preferred_bean_taste,
            is_certificated=True,
        )
        return user_detail

    return _create_user_detail


# @pytest.fixture
# def authenticated_client(api_client, create_user):
#     def _authenticated_client(user=None):
#         if user is None:
#             user = create_user()
#         refresh = RefreshToken.for_user(user)
#         api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
#         return api_client, user

#     return _authenticated_client


@pytest.fixture
def authenticated_client(api_client):
    def _authenticated_client():
        user = CustomUserFactory()
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return api_client, user

    return _authenticated_client


@pytest.fixture
def non_existent_user_id():
    return CustomUserFactory.create().id + 9999


@pytest.fixture
def create_test_image():
    file = io.BytesIO()  # 메모리에서 테스트용 이미지 생성
    image = Image.new("RGB", (100, 100), "white")
    image.save(file, "JPEG")
    file.seek(0)

    test_image = SimpleUploadedFile(name="test.jpeg", content=file.getvalue(), content_type="image/jpeg")

    return test_image


@pytest.fixture(autouse=True)
def debug_setting(settings):
    settings.DEBUG = True
