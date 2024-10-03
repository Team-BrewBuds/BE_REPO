import pytest
from django.urls import reverse
from rest_framework import status
from records.models import Comment


@pytest.mark.django_db
def test_get_comments(api_client, user, post):
    url = reverse('comment-list', kwargs={'object_type': 'post', 'object_id': post.post_id})
    response = api_client.get(url, {'page': 1})
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_get_post_comment(api_client, user, post):
    api_client.force_authenticate(user=user)
    url = reverse('comment-list', kwargs={'object_type': 'post', 'object_id': post.post_id})
    data = {'content': 'Test Post Comment'}
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert Comment.objects.filter(content='Test Post Comment', user=user, post=post).exists()

@pytest.mark.django_db
def test_get_tasted_record_comment(api_client, user, tasted_record):
    api_client.force_authenticate(user=user)
    url = reverse('comment-list', kwargs={'object_type': 'tasted_record', 'object_id': tasted_record.tasted_record_id})
    data = {"content": "Test Tasted_Record Comment"}
    response = api_client.post(url,data)
    assert response.status_code == status.HTTP_200_OK
    assert Comment.objects.filter(content='Test Tasted_Record Comment', user=user, tasted_record=tasted_record).exists()


@pytest.mark.django_db
def test_post_comment_without_content(api_client, user, post):
    api_client.force_authenticate(user=user)
    url = reverse('comment-list', kwargs={'object_type': 'post', 'object_id': post.post_id})
    data = {}
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'content is required' in response.data['error']


@pytest.mark.django_db
def test_post_comment_not_fount_id(api_client, user, post):
    api_client.force_authenticate(user=user)
    url = reverse('comment-list', kwargs={'object_type': 'post', 'object_id': post.post_id+100})
    data = {'content': 'Test Post Comment'}
    response = api_client.post(url, data)
    assert response.data['detail'] == "No Post matches the given query."
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_parent_comment(api_client, user, post):
    api_client.force_authenticate(user=user)
    parent_comment = Comment.objects.create(user=user, post=post, content="Parent Comment")
    child_comment = Comment.objects.create(user=user, post=post, content="child_comment Comment", parent_id=parent_comment)
    url = reverse('comment-list', kwargs={'object_type': 'post', 'object_id': post.post_id})
    response = api_client.get(url)
    assert response.data['comments'][0]['replies'][0]['comment_id'] == child_comment.comment_id
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_patch_comment(api_client, user, post):
    api_client.force_authenticate(user=user)
    comment = Comment.objects.create(user=user, post=post, content="Test Comment")
    url = reverse('comment-detail', kwargs={'id': comment.comment_id})
    data = {'content': 'Test Patch Comment'}
    response = api_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert Comment.objects.filter(content='Test Patch Comment', user=user, post=post).exists()



@pytest.mark.django_db
def test_create_comment(api_client, user,post):
    api_client.force_authenticate(user=user)
    url = reverse('comment-list', kwargs={'object_type': 'post', 'object_id': post.post_id})
    data = {'content': 'New Comment'}
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert Comment.objects.filter(content='New Comment', post=post).exists()

@pytest.mark.django_db
def test_create_reply_comment(api_client, user, post, post_comment):
    api_client.force_authenticate(user=user)
    post_comment.save()
    url = reverse('comment-list', kwargs={'object_type': 'post', 'object_id': post.post_id})
    data = {'content': 'Reply Comment', 'parent_id': post_comment.comment_id}
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert Comment.objects.filter(content='Reply Comment', parent_id=post_comment).exists()

@pytest.mark.django_db
def test_delete_parent_comment_does_not_delete_child(api_client, user, post, post_comment):
    api_client.force_authenticate(user=user)
    post_comment.save()
    reply_comment = Comment.objects.create(content='Reply Comment', post=post, user=user, parent_id=post_comment)
    
    url = reverse('comment-detail', kwargs={'id': post_comment.comment_id})

    response = api_client.delete(url)
    assert response.status_code == status.HTTP_200_OK
    
    reply_comment.refresh_from_db()
    assert Comment.objects.filter(comment_id=reply_comment.comment_id).exists()

@pytest.mark.django_db
def test_delete_parent_comment_soft_delete(api_client, user, post, post_comment):
    api_client.force_authenticate(user=user)
    post_comment.save()
    reply_comment = Comment.objects.create(content='Reply Comment', post=post, user=user, parent_id=post_comment)
    
    url = reverse('comment-detail', kwargs={'id': post_comment.comment_id})

    response = api_client.delete(url)
    assert response.status_code == status.HTTP_200_OK

    post_comment.refresh_from_db()  
    assert post_comment.is_deleted == True
    assert post_comment.content == "삭제된 댓글입니다."

    assert Comment.objects.filter(comment_id=reply_comment.comment_id).exists()