import pytest
from django.urls import reverse
from rest_framework import status

from repo.records.models import Note


@pytest.mark.django_db
def test_get_notes(api_client, user, post, post_note):
    api_client.force_authenticate(user=user)
    post.save()
    post_note.save()
    url = reverse("note-list", kwargs={"object_type": "post", "object_id": post.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


@pytest.mark.django_db
def test_create_note_success(api_client, user, post):
    api_client.force_authenticate(user=user)
    post.save()
    url = reverse("note-list", kwargs={"object_type": "post", "object_id": post.id})
    response = api_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    assert Note.objects.count() == 1


@pytest.mark.django_db
def test_get_note_detail(api_client, post_note):
    post_note.save()
    url = reverse("note-detail", kwargs={"id": post_note.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_delete_note_detail(api_client, post_note):
    post_note.save()
    url = reverse("note-detail", kwargs={"id": post_note.id})
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Note.objects.filter(id=post_note.id).exists()
