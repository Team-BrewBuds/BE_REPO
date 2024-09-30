import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from profiles.models import User
from records.models import Post, Tasted_Record
from beans.models import Bean, Bean_Taste_Review

@pytest.mark.django_db
class TestLikeApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return User.objects.create(nickname='testuser', login_type='naver')

    @pytest.fixture
    def bean(self):
        return Bean.objects.create(
            name='Test Bean',
            bean_type='single',
            is_decaf=False,
            origin_country='Test origin Country'
        )

    @pytest.fixture
    def bean_taste_review(self):
        return Bean_Taste_Review.objects.create(
            flavor='Test Flavor', body=3, acidity=3, bitterness=3, sweetness=3,
            star=3, place='Test Place'
        )

    @pytest.fixture
    def tasted_record(self,user, bean, bean_taste_review):
        return Tasted_Record.objects.create(user=user, bean=bean, taste_and_review= bean_taste_review, content='Test Content',tag='tags' )

    @pytest.fixture
    def post(self, user, tasted_record):
        return Post.objects.create(user=user, title='Test Post', content='Test Content', subject='Test Subject', tag='Test Tag', tasted_record=tasted_record)



    def test_like_post(self, api_client, user, post):
        api_client.force_authenticate(user=user)
        url = reverse('records-likes')
        data = {'object_type': 'post', 'object_id': post.post_id}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert user in post.like_cnt.all()
        assert post.like_cnt.count() == 1

    def test_unlike_post(self, api_client, user, post):
        post.like_cnt.add(user)
        api_client.force_authenticate(user=user)
        url = reverse('records-likes')
        data = {'object_type': 'post', 'object_id': post.post_id}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert user not in post.like_cnt.all()
        assert post.like_cnt.count() == 0


    def test_like_tasted_record(self, api_client, user, tasted_record):
        api_client.force_authenticate(user=user)
        url = reverse('records-likes')
        data = {'object_type': 'tasted_record', 'object_id': tasted_record.tasted_record_id}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert user in tasted_record.like_cnt.all()

    def test_unlike_tasted_record(self, api_client, user, tasted_record):
        tasted_record.like_cnt.add(user)
        api_client.force_authenticate(user=user)
        url = reverse('records-likes')
        data = {'object_type': 'tasted_record', 'object_id': tasted_record.tasted_record_id}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert user not in tasted_record.like_cnt.all()
        assert tasted_record.like_cnt.count() == 0

    def test_missing_object_id(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('records-likes')
        data = {'object_type': 'post'}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_object_type(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('records-likes')
        data = {'object_id': 1}
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
