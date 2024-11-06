import pytest
from rest_framework.exceptions import ErrorDetail

from repo.profiles.models import UserDetail


@pytest.mark.django_db
def test_get__my_profile(api_client, user):
    response = api_client.get("/profiles/")

    expected_data = {
        "id": user.id,
        "nickname": user.nickname,
        "profile_image": user.profile_image.url,
        "coffee_life": UserDetail.default_coffee_life(),
        "following_cnt": 0,
        "follower_cnt": 0,
        "post_cnt": 0,
        "is_user_following": False,
        "is_user_blocking": False,
    }

    assert response.data["id"] == expected_data["id"]
    assert response.data["nickname"] == expected_data["nickname"]
    assert response.data["profile_image"] == expected_data["profile_image"]
    assert response.data["coffee_life"] == expected_data["coffee_life"]
    assert response.data["follower_cnt"] == expected_data["follower_cnt"]
    assert response.data["following_cnt"] == expected_data["following_cnt"]
    assert response.data["post_cnt"] == expected_data["post_cnt"]
    assert response.data["is_user_following"] == expected_data["is_user_following"]
    assert response.data["is_user_blocking"] == expected_data["is_user_blocking"]


#  팔로워수, 팔로잉수, 게시물수 확인 테스트 코드
@pytest.mark.django_db
def test_get_my_profile_following_and_follower_cnt(api_client, user, following, follower, create_posts_20):
    response = api_client.get("/profiles/")

    expected_data = {"following_cnt": 1, "follower_cnt": 1, "post_cnt": 20}

    assert response.data["follower_cnt"] == expected_data["follower_cnt"]
    assert response.data["following_cnt"] == expected_data["following_cnt"]
    assert response.data["post_cnt"] == expected_data["post_cnt"]


@pytest.mark.django_db
def test_get_my_profile_by_unauthenticated_user(api_client, unauthenticated_user):
    response = api_client.get("/profiles/")
    assert response.status_code == 401
    assert response.data["error"] == "user not authenticated"


@pytest.mark.django_db
def test_update_my_profile_user_and_user_detail(api_client, user):
    expected_coffee_life = {
        "coffee_bean": 3,
        "cafe_tour": 3,
        "coffee_extraction": 3,
        "coffee_study": 3,
        "cafe_alba": 3,
    }
    expected_preferred_bean_taste = {
        "body": 3,
        "acidity": 3,
        "bitterness": 3,
        "sweetness": 3,
    }

    update_data = {
        "nickname": "new_nickname",
        "user_detail": {
            "introduction": "new_introduction",
            "profile_link": "http://profile.com/",
            "coffee_life": expected_coffee_life,
            "preferred_bean_taste": expected_preferred_bean_taste,
            "is_certificated": False,
        },
    }
    response = api_client.patch("/profiles/", data=update_data, format="json")

    user.refresh_from_db()
    updated_user_detail = user.user_detail

    assert response.status_code == 200
    assert user.nickname == "new_nickname"
    assert updated_user_detail.introduction == "new_introduction"
    assert updated_user_detail.profile_link == "http://profile.com/"
    assert updated_user_detail.coffee_life == expected_coffee_life
    assert updated_user_detail.preferred_bean_taste == expected_preferred_bean_taste
    assert updated_user_detail.is_certificated is False


@pytest.mark.django_db
def test_update_my_profile_ununique_nickname(api_client, user, other_user):
    invalid_data = {"nickname": other_user.nickname}
    response = api_client.patch("/profiles/", data=invalid_data)
    assert response.status_code == 400
    assert response.data["nickname"] == [ErrorDetail(string="사용자 with this 닉네임 already exists.", code="unique")]


@pytest.mark.django_db
def test_get_other_profile(api_client, user, other_user):
    response = api_client.get(f"/profiles/{other_user.id}/")

    expected_data = {
        "id": other_user.id,
        "nickname": other_user.nickname,
        "profile_image": other_user.profile_image.url,
        "coffee_life": UserDetail.default_coffee_life(),
        "following_cnt": 0,
        "follower_cnt": 0,
        "post_cnt": 0,
        "is_user_following": False,
        "is_user_blocking": False,
    }

    assert response.data["id"] == expected_data["id"]
    assert response.data["nickname"] == expected_data["nickname"]
    assert response.data["profile_image"] == expected_data["profile_image"]
    assert response.data["coffee_life"] == expected_data["coffee_life"]
    assert response.data["follower_cnt"] == expected_data["follower_cnt"]
    assert response.data["following_cnt"] == expected_data["following_cnt"]
    assert response.data["post_cnt"] == expected_data["post_cnt"]
    assert response.data["is_user_following"] == expected_data["is_user_following"]
    assert response.data["is_user_blocking"] == expected_data["is_user_blocking"]
