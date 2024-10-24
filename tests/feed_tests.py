import pytest
from django.urls import reverse
from rest_framework import status

from repo.records.serializers import FeedSerializer


@pytest.mark.django_db
def test_follow_feed(api_client, following_user, multiple_posts, multiple_tasted_records):
    api_client.force_authenticate(user=following_user)
    url = reverse("feed-follow")
    response = api_client.get(url, {"page": 1})

    assert response.status_code == status.HTTP_200_OK
    assert "records" in response.data
    assert "has_next" in response.data

    serialized_posts = FeedSerializer(multiple_posts + multiple_tasted_records, many=True).data
    # print(json.dumps(response.data, indent=4))

    response_data = sorted(response.data["records"], key=lambda x: x["created_at"])
    serializers_data = sorted(serialized_posts, key=lambda x: x["created_at"])
    assert response_data == serializers_data


@pytest.mark.django_db
def test_refresh_feed(api_client, following_user, multiple_posts, multiple_tasted_records):
    api_client.force_authenticate(user=following_user)
    url = reverse("feed-follow")
    response = api_client.get(url, {"page": 1})

    assert response.status_code == status.HTTP_200_OK
    assert "records" in response.data
    assert "has_next" in response.data

    serialized_posts = FeedSerializer(multiple_posts + multiple_tasted_records, many=True).data
    # print(json.dumps(response.data, indent=4))

    response_data = sorted(response.data["records"], key=lambda x: x["created_at"])
    serializers_data = sorted(serialized_posts, key=lambda x: x["created_at"])
    assert response_data == serializers_data

    response = api_client.get(url, {"page": 2})
    assert response.status_code == status.HTTP_200_OK
    assert "records" in response.data
    assert "has_next" in response.data

    serialized_posts = FeedSerializer(multiple_posts + multiple_tasted_records, many=True).data

    response_data = sorted(response.data["records"], key=lambda x: x["created_at"])
    serializers_data = sorted(serialized_posts, key=lambda x: x["created_at"])
    assert response_data == serializers_data

    url = reverse("feed-refresh")
    response = api_client.get(url, {"page": 1, "last_id": response.data["records"][-1]["id"]})
    assert response.status_code == status.HTTP_200_OK
    assert "records" in response.data
    # print(json.dumps(response.data.get('records'), indent=4))

    assert "has_next" in response.data
