import pytest
from rest_framework import status

from repo.common.utils import get_first_photo_url
from tests.factorys import (
    NoteFactory,
    PhotoFactory,
    PostFactory,
    TastedRecordFactory,
)

pytestmark = pytest.mark.django_db


class TestUserNoteAPIView:
    """
    사용자 노트 조회 API 테스트
    작성한 테스트 목록
    - [일반] 사용자의 노트 리스트 조회 성공 테스트
    - [일반] 사용자의 노트 리스트 내 사진 조회 성공 테스트
    - [일반] 사용자의 빈 노트 리스트 조회 성공 테스트
    - [예외] 존재하지 않는 사용자의 노트 리스트 조회 테스트
    """

    def test_get_user_note_list_success(self, authenticated_client):
        """
        사용자의 노트 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()

        posts = [PostFactory() for _ in range(3)]
        post_ids = [post.id for post in posts]
        for post in posts:
            NoteFactory(author=user, post=post)

        tasted_records = [TastedRecordFactory() for _ in range(3)]
        tasted_record_ids = [record.id for record in tasted_records]
        for record in tasted_records:
            NoteFactory(author=user, tasted_record=record)

        url = f"/profiles/{user.id}/notes/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == len(post_ids + tasted_record_ids)

        for note in response.data["results"]:
            if "post_id" in note.keys():
                assert note["post_id"] in post_ids
            else:
                assert note["tasted_record_id"] in tasted_record_ids

    def test_get_user_note_list_with_photo_success(self, authenticated_client):
        """
        사용자의 노트 리스트 내 사진 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        post = PostFactory()
        NoteFactory(author=user, post=post)
        PhotoFactory.create_batch(3, post=post)

        url = f"/profiles/{user.id}/notes/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["photo_url"] == get_first_photo_url(post)

    def test_get_user_note_list_empty(self, authenticated_client):
        """
        사용자의 노트 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        url = f"/profiles/{user.id}/notes/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_get_user_note_list_invalid_user(self, authenticated_client, non_existent_user_id):
        """
        존재하지 않는 사용자의 노트 리스트 조회 테스트
        """
        # Given
        api_client, _ = authenticated_client()
        url = f"/profiles/{non_existent_user_id}/notes/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND
