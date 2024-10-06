import json

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_get_tasted_records_feed(api_client, tasted_record):
    url = reverse("tasted-record-feed")
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data.get("records")) == 1


@pytest.mark.django_db
def test_get_tasted_records_detail(api_client, tasted_record):
    url = reverse("tasted-record-detail", kwargs={"pk": tasted_record.id})
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert_tasted_record_detail(response.data, tasted_record)


@pytest.mark.django_db
def test_get_post_feed(api_client, post):
    url = reverse("post-feed")
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data.get("records")) == 1


@pytest.mark.django_db
def test_get_post_detail(api_client, post):
    url = reverse("post-detail", kwargs={"pk": post.id})
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_200_OK
    # print(response.cookies.get("post_viewed"))
    assert_post_detail(response.data, post)

def assert_tasted_record_detail(response_data, tasted_record):
    assert response_data.get("id") == tasted_record.id
    assert response_data.get("bean")["name"] == tasted_record.bean.name
    assert response_data.get("taste_review")["star"] == tasted_record.taste_review.star
    assert response_data.get("taste_review")["flavor"] == tasted_record.taste_review.flavor
    assert response_data.get("photos") == []
    assert response_data.get("like_cnt") == 0
    assert response_data.get("view_cnt") == 1
    assert response_data.get("content") == tasted_record.content
    # print('생성 시간: ', tasted_record.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f"))
    assert response_data.get("created_at") == tasted_record.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f")
    print(json.dumps(response_data.get("user"), indent=4))
    assert response_data.get("author")['id'] == tasted_record.author.id
    assert response_data.get("author")["nickname"] == tasted_record.author.nickname
    assert response_data.get("author")["profile_image"] == tasted_record.author.profile_image
    assert response_data.get("bean")["bean_type"] == tasted_record.bean.bean_type


def assert_post_detail(response_data, post):
    assert response_data.get("id") == post.id
    assert response_data.get("title") == post.title
    assert response_data.get("content") == post.content
    assert response_data.get("subject") == post.subject
    assert response_data.get("view_cnt") == 1
    assert response_data.get("like_cnt") == 0
    assert response_data.get("created_at") == post.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f")
    assert response_data.get("author")['id'] == post.author.id
    assert response_data.get("author")["nickname"] == post.author.nickname
    assert response_data.get("author")["profile_image"] == post.author.profile_image
    assert response_data.get("tasted_record")["id"] == post.tasted_record.id
    assert response_data.get("photos") == []
