import pytest
from django.urls import reverse
from rest_framework import status

from repo.profiles.models import CustomUser


@pytest.mark.django_db
def test_user_detail_with_coffee_life(api_client, multiple_users_with_coffee_life):
    user = multiple_users_with_coffee_life[0]
    api_client.force_authenticate(user=user)
    url = reverse('budy-recommend')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    import json
    # print(json.dumps(response.data, indent=4))
    true_category = user.user_detail.get_coffee_life_helper().get_true_categories()
    test_user2_id = response.data['users'][1]['user']['id']
    test_user2 = CustomUser.objects.get(id=test_user2_id)
    test_user2_true_category = test_user2.user_detail.get_coffee_life_helper().get_true_categories()
    assert any(i in test_user2_true_category for i in true_category)
