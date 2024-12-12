import pytest
from rest_framework import status

from repo.records.models import Comment
from tests.factorys import (
    CommentFactory,
    PostFactory,
    TastedRecordFactory,
)

pytestmark = pytest.mark.django_db


class TestCommentAPIView:
    """
    댓글 목록 조회 및 생성 API 테스트
    작성한 테스트 케이스
    - [조회] 게시글 댓글 목록 조회 성공 테스트
    - [조회] 시음기록 댓글 목록 조회 성공 테스트
    - [조회] 댓글 빈 목록 조회 성공 테스트
    - [조회] 잘못된 object_type으로 조회 시 400 에러 반환 테스트
    - [조회] 존재하지 않는 객체 조회 시 404 에러 반환 테스트
    - [생성] 게시글 댓글 생성 성공 테스트
    - [생성] 시음기록 댓글 생성 성공 테스트
    - [생성] 대댓글 생성 성공 테스트
    - [생성] 필수 필드 누락 시 400 에러 반환 테스트
    - [생성] 미인증 사용자의 댓글 생성 시도시 401 에러 반환 테스트
    """

    def setup_method(self):
        self.base_url = "/records/comment/"

    def test_get_post_comments_success(self, authenticated_client):
        """게시글 댓글 목록 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        comments = CommentFactory.create_batch(3, post=post)
        url = f"{self.base_url}post/{post.id}/"

        # When
        response = client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3

    def test_get_tasted_record_comments_success(self, authenticated_client):
        """시음기록 댓글 목록 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        tasted_record = TastedRecordFactory()
        comments = CommentFactory.create_batch(3, tasted_record=tasted_record)
        url = f"{self.base_url}tasted_record/{tasted_record.id}/"

        # When
        response = client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3

    def test_get_empty_comments_success(self, authenticated_client):
        """댓글 빈 목록 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        url = f"{self.base_url}post/{post.id}/"

        # When
        response = client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert len(response.data["results"]) == 0

    def test_get_comments_invalid_object_type(self, authenticated_client):
        """잘못된 object_type으로 조회 시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        url = f"{self.base_url}invalid_type/1/"

        # When
        response = client.get(url)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_comments_object_not_found(self, authenticated_client):
        """존재하지 않는 객체 조회 시 404 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        url = f"{self.base_url}post/{post.id + 9999}/"

        # When
        response = client.get(url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_post_comment_success(self, authenticated_client):
        """게시글 댓글 생성 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        url = f"{self.base_url}post/{post.id}/"
        comment_data = {
            "content": "Test Comment",
        }

        # When
        response = client.post(url, comment_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert Comment.objects.count() == 1
        assert Comment.objects.first().content == comment_data["content"]
        assert Comment.objects.first().author == user
        assert Comment.objects.first().post == post

    def test_create_tasted_record_comment_success(self, authenticated_client):
        """시음기록 댓글 생성 성공 테스트"""
        # Given
        client, user = authenticated_client()
        tasted_record = TastedRecordFactory()
        url = f"{self.base_url}tasted_record/{tasted_record.id}/"
        comment_data = {
            "content": "Test Comment",
        }

        # When
        response = client.post(url, comment_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert Comment.objects.count() == 1
        assert Comment.objects.first().content == comment_data["content"]
        assert Comment.objects.first().author == user
        assert Comment.objects.first().tasted_record == tasted_record

    def test_create_reply_comment_success(self, authenticated_client):
        """대댓글 생성 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        parent_comment = CommentFactory(post=post)
        url = f"{self.base_url}post/{post.id}/"
        comment_data = {"content": "Test Reply", "parent": parent_comment.id}

        # When
        response = client.post(url, comment_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert Comment.objects.count() == 2
        reply = Comment.objects.latest("id")
        assert reply.content == comment_data["content"]
        assert reply.parent == parent_comment

    def test_create_comment_missing_content(self, authenticated_client):
        """필수 필드 누락 시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        url = f"{self.base_url}post/{post.id}/"
        comment_data = {}  # content 필드 누락

        # When
        response = client.post(url, comment_data, format="json")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_comment_unauthorized(self, api_client):
        """미인증 사용자의 댓글 생성 시도시 401 에러 반환 테스트"""
        # Given
        post = PostFactory()
        url = f"{self.base_url}post/{post.id}/"
        comment_data = {
            "content": "Test Comment",
        }

        # When
        response = api_client.post(url, comment_data, format="json")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Comment.objects.count() == 0


class TestCommentDetailAPIView:
    """
    댓글 상세 조회, 수정, 삭제 API 테스트
    작성한 테스트 케이스
    - [조회] 댓글 상세 조회 성공 테스트
    - [조회] 대댓글이 있는 댓글 상세 조회 성공 테스트
    - [수정] 댓글 수정 성공 테스트
    - [수정] 댓글 작성자가 아닌 사용자의 수정 시도시 403 에러 반환 테스트
    - [삭제] 댓글 삭제 성공 테스트 (soft delete)
    - [삭제] 대댓글 삭제 성공 테스트 (hard delete)
    - [삭제] 댓글 작성자가 아닌 사용자의 삭제 시도시 403 에러 반환 테스트
    """

    def setup_method(self):
        self.base_url = "/records/comment/"

    def test_get_comment_detail_success(self, authenticated_client):
        """댓글 상세 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        comment = CommentFactory()

        # When
        response = client.get(f"{self.base_url}{comment.id}/")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == comment.id
        assert response.data["content"] == comment.content

    def test_get_comment_with_replies_success(self, authenticated_client):
        """대댓글이 있는 댓글 상세 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        parent_comment = CommentFactory()
        replies = CommentFactory.create_batch(3, parent=parent_comment)

        # When
        response = client.get(f"{self.base_url}{parent_comment.id}/")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["replies"]) == 3

    def test_update_comment_success(self, authenticated_client):
        """댓글 수정 성공 테스트"""
        # Given
        client, user = authenticated_client()
        comment = CommentFactory(author=user)
        update_data = {"content": "Updated Comment Content"}

        # When
        response = client.patch(f"{self.base_url}{comment.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        comment.refresh_from_db()
        assert comment.content == update_data["content"]

    def test_update_comment_by_non_author(self, authenticated_client):
        """댓글 작성자가 아닌 사용자의 수정 시도시 403 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        other_user_comment = CommentFactory()
        update_data = {"content": "Updated Comment Content"}

        # When
        response = client.patch(f"{self.base_url}{other_user_comment.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_parent_comment_success(self, authenticated_client):
        """댓글 삭제 성공 테스트 (soft delete)"""
        # Given
        client, user = authenticated_client()
        comment = CommentFactory(author=user)

        # When
        response = client.delete(f"{self.base_url}{comment.id}/")

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        comment.refresh_from_db()
        assert comment.is_deleted is True
        assert comment.content == "삭제된 댓글입니다."

    def test_delete_reply_comment_success(self, authenticated_client):
        """대댓글 삭제 성공 테스트 (hard delete)"""
        # Given
        client, user = authenticated_client()
        parent_comment = CommentFactory()
        reply = CommentFactory(author=user, parent=parent_comment)

        # When
        response = client.delete(f"{self.base_url}{reply.id}/")

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(id=reply.id).exists()

    def test_delete_comment_by_non_author(self, authenticated_client):
        """댓글 작성자가 아닌 사용자의 삭제 시도시 403 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        other_user_comment = CommentFactory()

        # When
        response = client.delete(f"{self.base_url}{other_user_comment.id}/")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Comment.objects.filter(id=other_user_comment.id).exists()
