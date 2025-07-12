from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework import status

from tests.factorys import (
    CustomUserFactory,
    PostFactory,
    RelationshipFactory,
    TastedRecordFactory,
)

pytestmark = pytest.mark.django_db


class TestFeedAPIView:
    """
    피드 조회 API 테스트
    작성한 테스트 케이스
    - [비로그인] 비로그인 사용자의 피드 조회 성공 테스트
    - [비로그인] 비로그인 사용자의 피드 조회시 최신순 조회정렬 테스트
    - [팔로잉] 팔로잉 피드 조회 성공 테스트
    - [팔로잉] 1시간 이내 작성된 컨텐츠만 포함되는지 테스트
    - [일반] 일반 피드 조회 성공 테스트
    - [일반] 차단된 사용자의 컨텐츠 제외 테스트
    - [새로고침] 새로고침 피드 조회 성공 테스트
    - [에러] 잘못된 feed_type 파라미터 요청 시 400 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/records/feed/"

    def test_get_anonymous_feed_success(self, api_client):
        """비로그인 사용자의 피드 조회 성공 테스트"""
        # Given
        posts = PostFactory.create_batch(3)
        tasted_records = TastedRecordFactory.create_batch(3, is_private=False)

        # When
        response = api_client.get(f"{self.url}?feed_type=common")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 6
        for item in response.data["results"]:
            assert "is_user_liked" in item
            assert not item["is_user_liked"]
            assert "is_user_noted" in item
            assert not item["is_user_noted"]

    def test_get_anonymous_feed_order_by_latest(self, api_client):
        """비로그인 사용자의 피드 조회시 최신순 조회정렬 테스트"""
        # Given
        post1 = PostFactory()
        tasted_record1 = TastedRecordFactory()
        post2 = PostFactory()
        tasted_record2 = TastedRecordFactory()

        # When
        response = api_client.get(f"{self.url}?feed_type=common")

        # Then
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert results[0]["id"] == tasted_record2.id
        assert results[1]["id"] == post2.id
        assert results[2]["id"] == tasted_record1.id
        assert results[3]["id"] == post1.id

    def test_get_following_feed_success(self, authenticated_client):
        """팔로잉 피드 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        following_user = CustomUserFactory()
        RelationshipFactory(from_user=user, to_user=following_user, relationship_type="follow")

        following_posts = PostFactory.create_batch(2, author=following_user)
        following_records = TastedRecordFactory.create_batch(2, author=following_user, is_private=False)

        # When
        response = client.get(f"{self.url}?feed_type=following")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 4
        authors = [item["author"]["id"] for item in response.data["results"]]
        assert all(author == following_user.id for author in authors)

    def test_get_following_feed_time_filter(self, authenticated_client):
        """1시간 이내 작성된 컨텐츠만 포함되는지 테스트"""
        # Given
        client, user = authenticated_client()
        following_user = CustomUserFactory()
        RelationshipFactory(from_user=user, to_user=following_user, relationship_type="follow")

        # 현재 시점 컨텐츠 생성
        current_post = PostFactory(author=following_user)
        current_record = TastedRecordFactory(author=following_user, is_private=False)

        # 2시간 전 컨텐츠 생성
        two_hours_ago = timezone.now() - timedelta(hours=2)

        old_post = PostFactory(author=following_user)
        old_post.created_at = two_hours_ago
        old_post.save()

        old_record = TastedRecordFactory(author=following_user, is_private=False)
        old_record.created_at = two_hours_ago
        old_record.save()

        # When
        response = client.get(f"{self.url}?feed_type=following")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        for item in response.data["results"]:
            assert item["created_at"] == "방금 전"
        content_ids = [item["id"] for item in response.data["results"]]
        assert current_post.id in content_ids
        assert current_record.id in content_ids
        assert old_post.id not in content_ids
        assert old_record.id not in content_ids

    def test_get_common_feed_success(self, authenticated_client):
        """일반 피드 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        other_user = CustomUserFactory()

        # 팔로우하지 않은 사용자의 컨텐츠
        posts = PostFactory.create_batch(2, author=other_user)
        records = TastedRecordFactory.create_batch(2, author=other_user, is_private=False)

        # When
        response = client.get(f"{self.url}?feed_type=common")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 4
        for item in response.data["results"]:
            assert item["author"]["id"] == other_user.id

    def test_get_common_feed_exclude_blocked_user(self, authenticated_client):
        """차단된 사용자의 컨텐츠 제외 테스트"""
        # Given
        client, user = authenticated_client()
        normal_user = CustomUserFactory()
        blocked_user = CustomUserFactory()

        RelationshipFactory(from_user=user, to_user=blocked_user, relationship_type="block")

        # 일반 사용자의 컨텐츠
        normal_posts = PostFactory(author=normal_user)
        normal_records = TastedRecordFactory(author=normal_user, is_private=False)

        # 차단된 사용자의 컨텐츠
        blocked_posts = PostFactory(author=blocked_user)
        blocked_records = TastedRecordFactory(author=blocked_user, is_private=False)

        # When
        response = client.get(f"{self.url}?feed_type=common")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        content_authors = [item["author"]["id"] for item in response.data["results"]]
        assert all(author == normal_user.id for author in content_authors)
        assert blocked_user.id not in content_authors

    def test_get_refresh_feed_success(self, authenticated_client):
        """새로고침 피드 조회 성공 테스트"""
        # Given
        client, user = authenticated_client()
        posts = PostFactory.create_batch(3)
        records = TastedRecordFactory.create_batch(3, is_private=False)

        # When
        response = client.get(f"{self.url}?feed_type=refresh")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 6

    def test_get_feed_invalid_feed_type(self, authenticated_client):
        """잘못된 feed_type 파라미터 요청 시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()

        # When
        response = client.get(f"{self.url}?feed_type=invalid")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data
        assert response.data["error"] == "invalid feed type"

    def test_get_following_feed_private_records_excluded(self, authenticated_client):
        """팔로잉 피드에서 비공개 시음기록 제외 테스트"""
        # Given
        client, user = authenticated_client()
        following_user = CustomUserFactory()
        RelationshipFactory(from_user=user, to_user=following_user, relationship_type="follow")

        public_record = TastedRecordFactory(author=following_user, is_private=False)
        private_record = TastedRecordFactory(author=following_user, is_private=True)

        # When
        response = client.get(f"{self.url}?feed_type=following")

        # Then
        assert response.status_code == status.HTTP_200_OK
        content_ids = [item["id"] for item in response.data["results"]]
        assert public_record.id in content_ids
        assert private_record.id not in content_ids

    def test_get_common_feed_following_user_excluded(self, authenticated_client):
        """일반 피드에서 팔로잉 중인 사용자의 컨텐츠 제외 테스트"""
        # Given
        client, user = authenticated_client()
        following_user = CustomUserFactory()
        other_user = CustomUserFactory()

        RelationshipFactory(from_user=user, to_user=following_user, relationship_type="follow")

        following_post = PostFactory(author=following_user)
        other_post = PostFactory(author=other_user)

        # When
        response = client.get(f"{self.url}?feed_type=common")

        # Then
        assert response.status_code == status.HTTP_200_OK
        content_ids = [item["id"] for item in response.data["results"]]
        assert other_post.id in content_ids
        assert following_post.id not in content_ids

    def test_get_feed_pagination(self, authenticated_client):
        """피드 페이지네이션 테스트"""
        # Given
        client, user = authenticated_client()
        posts = PostFactory.create_batch(15)

        # When
        response = client.get(f"{self.url}?feed_type=common")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "next" in response.data
        assert "previous" in response.data
        assert len(response.data["results"]) == settings.REST_FRAMEWORK["PAGE_SIZE"]

    def test_get_feed_empty_result(self, authenticated_client):
        """빈 피드 조회 테스트"""
        # Given
        client, user = authenticated_client()

        # When
        response = client.get(f"{self.url}?feed_type=common")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert len(response.data["results"]) == 0
