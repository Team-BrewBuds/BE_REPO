import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestLikeApiView:

    def test_like_post(self, api_client, user, post):
        api_client.force_authenticate(user=user)
        url = reverse("records-likes")
        data = {"object_type": "post", "object_id": post.post_id}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert user in post.like_cnt.all()
        assert post.like_cnt.count() == 1

    def test_unlike_post(self, api_client, user, post):
        post.like_cnt.add(user)
        api_client.force_authenticate(user=user)
        url = reverse("records-likes")
        data = {"object_type": "post", "object_id": post.post_id}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert user not in post.like_cnt.all()
        assert post.like_cnt.count() == 0

    def test_like_tasted_record(self, api_client, user, tasted_record):
        api_client.force_authenticate(user=user)
        url = reverse("records-likes")
        data = {"object_type": "tasted_record", "object_id": tasted_record.tasted_record_id}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert user in tasted_record.like_cnt.all()

    def test_unlike_tasted_record(self, api_client, user, tasted_record):
        tasted_record.like_cnt.add(user)
        api_client.force_authenticate(user=user)
        url = reverse("records-likes")
        data = {"object_type": "tasted_record", "object_id": tasted_record.tasted_record_id}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert user not in tasted_record.like_cnt.all()
        assert tasted_record.like_cnt.count() == 0

    def test_missing_object_id(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("records-likes")
        data = {"object_type": "post"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_object_type(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("records-likes")
        data = {"object_id": 1}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
