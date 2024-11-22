import pytest
from rest_framework import status

from tests.factorys import ContentObjectFactory

pytestmark = pytest.mark.django_db


class TestLikeAPIView:
    """
    좋아요 API 테스트
    작성한 테스트 케이스
    - [일반] 좋아요 생성 성공 테스트
    - [일반] 좋아요 삭제 성공 테스트
    - [예외] 이미 존재하는 좋아요 생성 시 409 응답 테스트
    - [예외] 존재하지 않는 좋아요 삭제 시 404 응답 테스트
    - [예외] 미인증 사용자의 좋아요 생성 시 401 응답 테스트
    - [예외] 미인증 사용자의 좋아요 삭제 시 401 응답 테스트
    """

    def setup_method(self):
        self.create_object = ContentObjectFactory.create_content_object

    @pytest.mark.parametrize("object_type", ["post", "tasted_record", "comment"])
    def test_create_like_success(self, authenticated_client, object_type):
        """좋아요 생성 성공 테스트"""
        # Given
        client, user = authenticated_client()
        obj = self.create_object(object_type)
        url = f"/records/like/{object_type}/{obj.id}/"

        # When
        response = client.post(url)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["detail"] == "like created"

    @pytest.mark.parametrize("object_type", ["post", "tasted_record", "comment"])
    def test_delete_like_success(self, authenticated_client, object_type):
        """좋아요 삭제 성공 테스트"""
        # Given
        client, user = authenticated_client()
        obj = self.create_object(object_type)
        url = f"/records/like/{object_type}/{obj.id}/"

        # When
        client.post(url)  # 좋아요 생성
        response = client.delete(url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data["detail"] == "like deleted"

    @pytest.mark.parametrize("object_type", ["post", "tasted_record", "comment"])
    def test_create_like_conflict(self, authenticated_client, object_type):
        """이미 존재하는 좋아요 생성 시 409 응답 테스트"""
        # Given
        client, user = authenticated_client()
        obj = self.create_object(object_type)
        url = f"/records/like/{object_type}/{obj.id}/"

        # When
        client.post(url)  # 좋아요 생성
        response = client.post(url)  # 이미 존재하는 좋아요 생성

        # Then
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["detail"] == "like already exists"

    @pytest.mark.parametrize("object_type", ["post", "tasted_record", "comment"])
    def test_delete_like_not_found(self, authenticated_client, object_type):
        """존재하지 않는 좋아요 삭제 시 404 응답 테스트"""
        # Given
        client, user = authenticated_client()
        obj = self.create_object(object_type)
        url = f"/records/like/{object_type}/{obj.id}/"

        # When
        response = client.delete(url)  # 존재하지 않는 좋아요 삭제

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "like not found"

    def test_create_like_unauthorized(self, client):
        """미인증 사용자의 좋아요 생성 시 401 응답 테스트"""
        # Given
        obj = self.create_object("post")
        url = f"/records/like/post/{obj.id}/"

        # When
        response = client.post(url)  # 미인증 사용자의 좋아요 생성

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_like_unauthorized(self, client):
        """미인증 사용자의 좋아요 삭제 시 401 응답 테스트"""
        # Given
        obj = self.create_object("post")
        url = f"/records/like/post/{obj.id}/"

        # When
        response = client.delete(url)  # 미인증 사용자의 좋아요 삭제

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
