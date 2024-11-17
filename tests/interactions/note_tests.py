import pytest
from rest_framework import status

from repo.records.models import Note
from tests.factorys import NoteFactory, PostFactory, TastedRecordFactory

pytestmark = pytest.mark.django_db


class TestNoteAPIView:
    """
    노트 API 테스트
    작성한 테스트 케이스
    - [일반] 노트 생성 성공 테스트
    - [일반] 노트 삭제 성공 테스트
    - [예외] 이미 존재하는 노트 생성 시 200 응답 테스트
    - [예외] 존재하지 않는 노트 삭제 시 404 응답 테스트
    """

    def test_create_note_success(self, authenticated_client):
        """노트 생성 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        url = f"/records/note/post/{post.id}/"

        # When
        response = client.post(url)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert Note.objects.count() == 1
        assert Note.objects.filter(author=user, post=post).exists()

    def test_delete_note_success(self, authenticated_client):
        """노트 삭제 성공 테스트"""
        # Given
        client, user = authenticated_client()
        tasted_record = TastedRecordFactory()
        note = NoteFactory(author=user, tasted_record=tasted_record)
        url = f"/records/note/tasted_record/{tasted_record.id}/"

        # When
        response = client.delete(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert Note.objects.count() == 0

    def test_create_duplicate_note(self, authenticated_client):
        """이미 존재하는 노트 생성 시 200 응답 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        note = NoteFactory(author=user, post=post)
        url = f"/records/note/post/{post.id}/"

        # When
        response = client.post(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "note already exists"
        assert Note.objects.count() == 1

    def test_delete_nonexistent_note(self, authenticated_client):
        """존재하지 않는 노트 삭제 시 404 응답 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        url = f"/records/note/post/{post.id}/"

        # When
        response = client.delete(url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "note not found"
