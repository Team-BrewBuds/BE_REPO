import random

import pytest
from rest_framework import status

from repo.records.models import Post
from tests.factorys import PostFactory

pytestmark = pytest.mark.django_db


class TestUserPostListAPIView:
    """
    사용자 게시글 리스트 조회 API 테스트
    작성한 테스트 케이스
    - [일반] 사용자의 게시글 리스트 조회 성공 테스트
    - [일반] 사용자의 빈 게시글 리스트 조회 성공 테스트
    - [필터링] 주제별 게시글 리스트 조회 성공 테스트
    - [필터링] 유효하지 않은 subject 파라미터 전달 테스트
    - [정렬] 최신순 게시글 리스트 조회 성공 테스트
    - [예외] 존재하지 않는 사용자의 게시글 리스트 조회 테스트
    """

    def test_service_method_get_user_posts_by_subject(self, authenticated_client):

        api_client, user = authenticated_client()
        [PostFactory(author=user, subject="normal") for _ in range(3)]
        [PostFactory(author=user, subject="cafe") for _ in range(3)]

        # 서비스 함수 테스트
        from repo.records.services import get_user_posts_by_subject

        assert len(get_user_posts_by_subject(user, "normal")) == 3
        assert len(get_user_posts_by_subject(user, "all")) == 6

    def test_get_user_post_list_success(self, authenticated_client):
        """
        사용자의 게시글 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        posts = [PostFactory(author=user) for _ in range(3)]
        url = f"/profiles/{user.id}/posts/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_get_user_post_list_empty(self, authenticated_client):
        """
        사용자의 빈 게시글 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        url = f"/profiles/{user.id}/posts/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    @pytest.mark.parametrize("subject", ["일반", "카페", "원두", "정보", "질문", "고민", "장비"])
    def test_get_user_post_list_by_subject_success(self, authenticated_client, subject):
        """
        주제별 게시글 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        # 주제 매핑 딕셔너리 생성 (예: '일반' -> 'normal')
        subject_mapping = {kor: eng for eng, kor in Post.SUBJECT_TYPE_CHOICES}

        # 현재 주제에 해당하는 영문 코드 가져오기
        current_subject = subject_mapping.get(subject)

        # 현재 주제를 제외한 나머지 주제들의 영문 코드 리스트 생성
        remaining_subjects = list(subject_mapping.values())
        remaining_subjects.remove(current_subject)

        [PostFactory(author=user, subject=current_subject) for _ in range(3)]
        [PostFactory(author=user, subject=random.choice(remaining_subjects)) for _ in range(2)]

        url = f"/profiles/{user.id}/posts/?subject={subject}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

        for post in response.data["results"]:
            assert post["subject"] == current_subject

    def test_get_user_post_list_by_invalid_subject(self, authenticated_client):
        """
        유효하지 않은 subject 파라미터 전달 테스트
        """
        # Given
        api_client, user = authenticated_client()
        url = f"/profiles/{user.id}/posts/?subject=invalid"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_user_post_list_order_by_latest(self, authenticated_client):
        """
        최신순 게시글 리스트 조회 성공 테스트
        """
        # Given
        api_client, user = authenticated_client()
        posts = [PostFactory(author=user) for _ in range(3)]
        url = f"/profiles/{user.id}/posts/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        posts = response.data["results"]
        assert posts[0]["id"] > posts[1]["id"] > posts[2]["id"]

    def test_get_user_post_list_not_found(self, api_client, non_existent_user_id):
        """
        존재하지 않는 사용자의 게시글 리스트 조회 테스트
        """
        # Given
        url = f"/profiles/{non_existent_user_id}/posts/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND
