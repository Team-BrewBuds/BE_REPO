import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestLikeApiView:

    def like_unlike(self, api_client, user, object_type, object_id, should_like):
        api_client.force_authenticate(user=user)
        url = reverse("records-likes")
        data = {"object_type": object_type, "object_id": object_id}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        return response

    def test_like_post(self, api_client, user, post):
        response = self.like_unlike(api_client, user, "post", post.post_id, True)
        assert user in post.like_cnt.all()
        assert post.like_cnt.count() == 1

    def test_unlike_post(self, api_client, user, post):
        post.like_cnt.add(user)
        response = self.like_unlike(api_client, user, "post", post.post_id, False)
        assert user not in post.like_cnt.all()
        assert post.like_cnt.count() == 0

    def test_like_tasted_record(self, api_client, user, tasted_record):
        response = self.like_unlike(api_client, user, "tasted_record", tasted_record.tasted_record_id, True)
        assert user in tasted_record.like_cnt.all()

    def test_unlike_tasted_record(self, api_client, user, tasted_record):
        tasted_record.like_cnt.add(user)
        response = self.like_unlike(api_client, user, "tasted_record", tasted_record.tasted_record_id, False)
        assert user not in tasted_record.like_cnt.all()
        assert tasted_record.like_cnt.count() == 0

    def test_like_comment(self, api_client, user, post_comment):
        post_comment.save()
        response = self.like_unlike(api_client, user, "comment", post_comment.comment_id, True)
        assert user in post_comment.like_cnt.all()

    def test_unlike_comment(self, api_client, user, post_comment):
        post_comment.save()
        post_comment.like_cnt.add(user)
        response = self.like_unlike(api_client, user, "comment", post_comment.comment_id, False)
        assert user not in post_comment.like_cnt.all()
        assert post_comment.like_cnt.count() == 0

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

    def test_invalid_object_type(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("records-likes")
        data = {"object_type": "invalid_type", "object_id": 1}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
