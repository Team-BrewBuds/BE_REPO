import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from repo.profiles.models import Relationship

User = get_user_model()


@pytest.fixture
def user1():
    return User.objects.create(
        nickname="testuser1", login_type="naver", email="testuser1@naver.com", profile_image="http://example.com/profile.jpg"
    )


@pytest.fixture
def user2():
    return User.objects.create(
        nickname="testuser2", login_type="kakao", email="testuser2@kakao.com", profile_image="http://example.com/profile.jpg"
    )


@pytest.mark.django_db
def test_follow_user_successfully(api_client, user1, user2):
    api_client.force_authenticate(user=user1)

    response = api_client.post(reverse("follow"), {"follow_user_id": user2.id})

    assert response.status_code == status.HTTP_201_CREATED
    print(response)
    assert Relationship.objects.filter(from_user=user1, to_user=user2, relationship_type="follow").exists()


@pytest.mark.django_db
def test_follow_user_already_following(api_client, user1, user2):
    Relationship.objects.create(from_user=user1, to_user=user2, relationship_type="follow")
    api_client.force_authenticate(user=user1)

    response = api_client.post(reverse("follow"), {"follow_user_id": user2.id})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "already following"


@pytest.mark.django_db
def test_follow_user_id_missing(api_client, user1, user2):
    api_client.force_authenticate(user=user1)

    response = api_client.post(reverse("follow"), {})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "follow_user_id is required"


@pytest.mark.django_db
def test_unfollow_user_successfully(api_client, user1, user2):
    Relationship.objects.create(from_user=user1, to_user=user2, relationship_type="follow")
    api_client.force_authenticate(user=user1)

    response = api_client.delete(reverse("follow"), {"following_user_id": user2.id})

    assert response.status_code == status.HTTP_200_OK
    assert not Relationship.objects.filter(from_user=user1, to_user=user2, relationship_type="follow").exists()


@pytest.mark.django_db
def test_unfollow_user_not_following(api_client, user1, user2):
    api_client.force_authenticate(user=user1)

    response = api_client.delete(reverse("follow"), {"following_user_id": user2.id})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "not following"


@pytest.mark.django_db
def test_unfollow_user_id_missing(api_client, user1, user2):
    api_client.force_authenticate(user=user1)

    response = api_client.delete(reverse("follow"), {})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "following_user_id is required"
