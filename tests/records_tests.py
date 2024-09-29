import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from beans.models import Bean, Bean_Taste_Review
from profiles.models import User
from records.models import Post, Tasted_Record


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_test_data(db):
    user = User.objects.create(nickname="Test User", profile_image="http://example.com/profile.jpg")

    bean = Bean.objects.create(
        name="Test Bean",
        bean_type="single",
        is_decaf=False,
        origin_country="Ethiopia",
        extraction="Espresso",
        roast_point=3,
        process="Washed",
        region="Yirgacheffe",
        bev_type=True,
        roastery="Test Roastery",
        variety="Heirloom",
    )

    tasted_records = []
    for i in range(5):
        bean_taste_review = Bean_Taste_Review.objects.create(
            flavor="Test Flavor",
            body=i,
            acidity=i,
            bitterness=i,
            sweetness=i,
            star=i,
            created_at=timezone.now(),
            place="Test Place",
        )

        tasted_record = Tasted_Record.objects.create(
            user=user,
            bean=bean,
            taste_and_review=bean_taste_review,
            content=f"Taste record content num :{i}",
        )
        tasted_records.append(tasted_record)

    post = Post.objects.create(
        user=user, title="Test Post", content="Test Post Content", subject="Test Subject", tasted_record=tasted_records[0]
    )

    return {"user": user, "bean": bean, "tasted_records": tasted_records, "post": post}


def assert_tasted_record_detail(response_data, tasted_record):
    assert response_data.get("tasted_record_id") == tasted_record.tasted_record_id
    assert response_data.get("user_id") == tasted_record.user.user_id
    assert response_data.get("bean")["name"] == tasted_record.bean.name
    assert response_data.get("taste_and_review")["star"] == tasted_record.taste_and_review.star
    assert response_data.get("taste_and_review")["flavor"] == tasted_record.taste_and_review.flavor
    assert response_data.get("photos") == []
    assert response_data.get("like_cnt") == 0
    assert response_data.get("view_cnt") == 0
    assert response_data.get("content") == tasted_record.content
    assert response_data.get("created_at") == tasted_record.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    assert response_data.get("user_nickname") == tasted_record.user.nickname
    assert response_data.get("user_profile_image") == tasted_record.user.profile_image
    assert response_data.get("bean")["bean_type"] == tasted_record.bean.bean_type


def assert_post_detail(response_data, post):
    assert response_data.get("post_id") == post.post_id
    assert response_data.get("user_id") == post.user.user_id
    assert response_data.get("title") == post.title
    assert response_data.get("content") == post.content
    assert response_data.get("subject") == post.subject
    assert response_data.get("view_cnt") == 0
    assert response_data.get("like_cnt") == 0
    assert response_data.get("created_at") == post.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    assert response_data.get("user_nickname") == post.user.nickname
    assert response_data.get("user_profile_image") == post.user.profile_image
    assert response_data.get("tasted_record")["tasted_record_id"] == post.tasted_record.tasted_record_id
    assert response_data.get("photos") == []


@pytest.mark.django_db
def test_get_tasted_records_feed(api_client, create_test_data):
    url = reverse("tasted-record-feed")
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data.get("records")) == 5


@pytest.mark.django_db
def test_get_tasted_records_detail(api_client, create_test_data):
    tasted_record = create_test_data["tasted_records"][0]
    url = reverse("tasted-record-detail", kwargs={"pk": tasted_record.tasted_record_id})
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert_tasted_record_detail(response.data, tasted_record)


@pytest.mark.django_db
def test_get_post_feed(api_client, create_test_data):
    url = reverse("post-feed")
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data.get("records")) == 1


@pytest.mark.django_db
def test_get_post_detail(api_client, create_test_data):
    post = create_test_data["post"]
    url = reverse("post-detail", kwargs={"pk": post.post_id})
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert_post_detail(response.data, post)