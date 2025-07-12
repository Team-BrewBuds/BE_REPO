from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from repo.records.models import Post
from tests.factorys import (
    CustomUserFactory,
    PhotoFactory,
    PostFactory,
    RelationshipFactory,
)

pytestmark = pytest.mark.django_db


class TestPostListCreateAPIView:
    """
    게시글 목록 조회 및 생성 API 테스트
    작성한 테스트 케이스
    - [조회] 게시글 목록 조회 성공 테스트
    - [조회] 게시글 빈 목록 조회 성공 테스트
    - [조회] 게시글 목록 최신순 정렬 테스트
    - [조회] 게시글 주제별 필터링 테스트
    - [조회] 미인증 사용자의 게시글 조회시 최신순 조회정렬 테스트
    - [생성] 게시글 생성 성공 테스트
    - [생성] 게시글 생성 시 사진 포함 테스트
    - [생성] 필수 필드 누락 시 400 에러 반환 테스트
    - [생성] 미인증 사용자의 게시글 생성 시도시 401 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/records/post/"

    def test_get_post_list_success(self, authenticated_client):
        """게시글 목록 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        posts = PostFactory.create_batch(3)

        # When
        response = client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3

    def test_get_post_list_empty(self, authenticated_client):
        """게시글 빈 목록 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()

        # When
        response = client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert len(response.data["results"]) == 0

    def test_get_post_list_order_by_latest(self, authenticated_client):
        """게시글 목록 최신순 정렬 테스트"""
        # Given
        client, user = authenticated_client()
        posts = [PostFactory() for _ in range(3)]

        # When
        response = client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert results[0]["id"] > results[1]["id"] > results[2]["id"]

    @pytest.mark.parametrize("subject", list(dict(Post.SUBJECT_TYPE_CHOICES).keys()))
    def test_get_post_list_filter_by_subject(self, authenticated_client, subject):
        """게시글 주제별 필터링 테스트"""
        # Given
        client, user = authenticated_client()
        target_posts = PostFactory.create_batch(2, subject=subject)
        other_posts = PostFactory.create_batch(2, subject="normal")
        subject_choices = dict(Post.SUBJECT_TYPE_CHOICES)

        # When
        response = client.get(f"{self.url}?subject={subject}")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 2
        assert all(post["subject"] == subject_choices.get(subject) for post in response.data["results"])

    def test_get_post_list_order_by_latest_unauthenticated(self, api_client):
        """미인증 사용자의 게시글 조회시 최신순 조회정렬 테스트"""
        # Given
        PostFactory(created_at=timezone.now() - timedelta(days=3))
        PostFactory(created_at=timezone.now() - timedelta(days=2))
        PostFactory(created_at=timezone.now() - timedelta(days=1))
        PostFactory(created_at=timezone.now())

        # When
        response = api_client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        for i in range(len(results) - 1):
            assert results[i]["id"] > results[i + 1]["id"]

    def test_create_post_success(self, authenticated_client):
        """게시글 생성 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post_data = {
            "title": "Test Title",
            "content": "Test Content",
            "subject": "normal",
            "tag": "tag1,tag2",
        }

        # When
        response = client.post(self.url, post_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert Post.objects.count() == 1
        assert Post.objects.first().author == user
        assert Post.objects.first().title == post_data["title"]

    def test_create_post_with_photos(self, authenticated_client, create_test_image):
        """게시글 생성 시 사진 포함 테스트"""
        # Given
        client, user = authenticated_client()
        photo1 = PhotoFactory(photo_url=create_test_image, post=None)
        photo2 = PhotoFactory(photo_url=create_test_image, post=None)
        post_data = {
            "title": "Test Title",
            "content": "Test Content",
            "subject": "normal",
            "tag": "tag1,tag2",
            "photos": [photo1.id, photo2.id],
        }

        # When
        response = client.post(self.url, post_data, format="multipart")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        post_id = response.data["id"]
        assert Post.objects.get(id=post_id).photo_set.count() == 2

    def test_create_post_missing_required_fields(self, authenticated_client):
        """필수 필드 누락 시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        incomplete_data = {
            # title 필드 누락
            "content": "Test Content",
            "subject": "normal",
        }

        # When
        response = client.post(self.url, incomplete_data, format="json")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_post_unauthorized(self, api_client):
        """미인증 사용자의 게시글 생성 시도시 401 에러 반환 테스트"""
        # Given
        post_data = {
            "title": "Test Title",
            "content": "Test Content",
            "subject": "normal",
        }

        # When
        response = api_client.post(self.url, post_data, format="json")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Post.objects.count() == 0


class TestPostDetailAPIView:
    """
    게시글 상세 조회 및 수정/삭제 API 테스트
    작성한 테스트 케이스
    - [조회] 게시글 상세 조회 성공 테스트
    - [조회] 게시글 상세 조회 시 조회수 증가 테스트
    - [수정] 게시글 수정 성공 테스트
    - [삭제] 게시글 삭제 성공 테스트
    - [권한] 게시글 작성자가 아닌 사용자의 게시글 수정/삭제 시도 시 403 에러 반환 테스트
    - [권한] 미인증 사용자의 게시글 수정/삭제 시도 시 401 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/records/post/"

    def test_get_post_detail_success(self, authenticated_client):
        """게시글 상세 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()

        # When
        response = client.get(f"{self.url}{post.id}/")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == post.id
        assert response.data["title"] == post.title
        assert response.data["content"] == post.content

    def test_get_post_detail_view_count_increase(self, authenticated_client):
        """게시글 상세 조회 시 조회수 증가 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        initial_view_count = post.view_cnt

        # When
        response = client.get(f"{self.url}{post.id}/")

        # Then
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.view_cnt == initial_view_count + 1

    def test_update_post_success(self, authenticated_client):
        """게시글 수정 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory(author=user)
        update_data = {
            "title": "Updated Title",
            "content": "Updated Content",
            "subject": "normal",
        }

        # When
        response = client.put(f"{self.url}{post.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.title == update_data["title"]
        assert post.content == update_data["content"]
        assert post.subject == update_data["subject"]

    def test_partial_update_post_success(self, authenticated_client):
        """게시글 부분 수정 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory(author=user)
        update_data = {
            "title": "Updated Title",
        }

        # When
        response = client.patch(f"{self.url}{post.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.title == update_data["title"]

    def test_delete_post_success(self, authenticated_client):
        """게시글 삭제 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory(author=user)

        # When
        response = client.delete(f"{self.url}{post.id}/")

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Post.objects.filter(id=post.id).exists()

    def test_update_post_by_non_author(self, authenticated_client):
        """게시글 작성자가 아닌 사용자의 수정 시도시 403 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        other_user_post = PostFactory()
        update_data = {
            "title": "Updated Title",
            "content": "Updated Content",
            "subject": "normal",
        }

        # When
        response = client.put(f"{self.url}{other_user_post.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_post_by_non_author(self, authenticated_client):
        """게시글 작성자가 아닌 사용자의 삭제 시도시 403 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        other_user_post = PostFactory()

        # When
        response = client.delete(f"{self.url}{other_user_post.id}/")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Post.objects.filter(id=other_user_post.id).exists()

    def test_update_post_unauthorized(self, api_client):
        """미인증 사용자의 게시글 수정 시도시 401 에러 반환 테스트"""
        # Given
        post = PostFactory()
        update_data = {
            "title": "Updated Title",
            "content": "Updated Content",
            "subject": "normal",
        }

        # When
        response = api_client.put(f"{self.url}{post.id}/", update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_post_unauthorized(self, api_client):
        """미인증 사용자의 게시글 삭제 시도시 401 에러 반환 테스트"""
        # Given
        post = PostFactory()

        # When
        response = api_client.delete(f"{self.url}{post.id}/")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Post.objects.filter(id=post.id).exists()


class TestTopSubjectPostsAPIView:
    """
    주제별 조회수 상위 60개 인기 게시글 조회 API 테스트
    작성한 테스트 케이스
    - [조회] 인증된 사용자의 주제별 인기 게시글 조회 성공 테스트
    - [조회] 비인증 사용자의 인기 게시글 조회 성공 테스트
    - [조회] 빈 목록 조회 성공 테스트
    - [조회] 주제별 필터링 테스트
    - [조회] 차단된 사용자의 게시글 제외 테스트
    """

    def setup_method(self):
        self.url = "/records/post/top/"

    def test_get_top_posts_authenticated_success(self, authenticated_client):
        """인증된 사용자의 주제별 인기 게시글 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        posts = PostFactory.create_batch(12)

        # When
        response = client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 12  # 페이지네이션
        assert response.data["results"][0]["view_cnt"] >= response.data["results"][1]["view_cnt"]  # 조회수 내림차순

    def test_get_top_posts_unauthenticated_success(self, api_client):
        """비인증 사용자의 인기 게시글 조회 성공 테스트"""
        # Given
        posts = PostFactory.create_batch(12)

        # When
        response = api_client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 12  # 페이지네이션
        assert response.data["results"][0]["view_cnt"] >= response.data["results"][1]["view_cnt"]  # 조회수 내림차순

    def test_get_top_posts_empty(self, api_client):
        """빈 목록 조회 성공 테스트"""
        # Given
        # When
        response = api_client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_get_top_posts_filter_by_subject(self, authenticated_client):
        """주제별 필터링 테스트"""
        # Given
        client, user = authenticated_client()
        target_posts = PostFactory.create_batch(2, subject="normal")
        other_posts = PostFactory.create_batch(2, subject="cafe")
        subject_choices = dict(Post.SUBJECT_TYPE_CHOICES)

        # When
        response = client.get(f"{self.url}?subject=normal")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert all(post["subject"] == subject_choices["normal"] for post in response.data["results"])

    def test_get_top_posts_exclude_blocked_user(self, authenticated_client):
        """차단된 사용자의 게시글 제외 테스트"""
        # Given
        client, user = authenticated_client()
        blocked_user = CustomUserFactory()
        RelationshipFactory(from_user=user, to_user=blocked_user, relationship_type="block")

        blocked_posts = PostFactory.create_batch(2, author=blocked_user)
        posts = PostFactory.create_batch(10)

        blocked_posts_ids = [blocked_post.id for blocked_post in blocked_posts]

        # When
        response = client.get(self.url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10
        for post in response.data["results"]:
            assert post["id"] not in blocked_posts_ids
            assert post["author"]["id"] != blocked_user.id
