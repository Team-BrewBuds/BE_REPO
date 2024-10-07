import pytest
import json
from django.urls import reverse
from rest_framework import status

from repo.records.models import Post


@pytest.mark.django_db
def test_get_top_posts_all(api_client, multiple_posts):
    url = reverse("post-top")
    data = {
        "subject": "invalid",
    }
    response = api_client.get(url, data, format="json")
    print(json.dumps(response.data, indent=4))
    assert response.status_code == status.HTTP_200_OK

    response_top_post = response.data.get("records")[0]
    top_post = Post.objects.order_by("-view_cnt")[0]
    assert response_top_post.get("id") == top_post.id
