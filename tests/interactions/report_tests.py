import pytest
from rest_framework import status

from repo.records.models import Report
from tests.factorys import PostFactory

pytestmark = pytest.mark.django_db


class TestReportAPIView:
    """
    신고 API 테스트
    작성한 테스트 케이스
    - [일반] 신고 성공 테스트
    - [예외] 동일한 컨텐츠에 대한 중복 신고 시 200 응답 테스트
    - [예외] 필수 필드 누락시 400 에러 반환 테스트
    - [예외] 유효하지 않은 object_type 파라미터 전달 시 400 에러 반환 테스트
    - [예외] 미인증 사용자의 신고 시도시 401 에러 반환 테스트
    - [예외] 존재하지 않는 객체 신고시 404 에러 반환 테스트

    """

    def test_report_success(self, authenticated_client):
        """신고 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()

        data = {"object_type": "post", "object_id": post.id, "reason": "부적절한 내용"}
        url = "/records/report/"

        # When
        response = client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["target_author"] == post.author.nickname
        assert Report.objects.count() == 1

    def test_duplicate_report(self, authenticated_client):
        """동일한 컨텐츠에 대한 중복 신고 시 200 응답 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        data = {"object_type": "post", "object_id": post.id, "reason": "부적절한 내용"}
        url = "/records/report/"

        # When
        client.post(url, data=data)  # 첫 번째 신고
        response = client.post(url, data=data)  # 중복 신고

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "이미 신고한 컨텐츠입니다."
        assert Report.objects.count() == 1

    def test_missing_required_fields(self, authenticated_client):
        """필수 필드 누락시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        url = "/records/report/"

        # When - object_type 누락
        response1 = client.post(url, data={"object_id": 1, "reason": "부적절한 내용"})
        # When - reason 누락
        response2 = client.post(url, data={"object_type": "post", "object_id": 1})

        # Then
        assert response1.status_code == status.HTTP_400_BAD_REQUEST
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_object_type(self, authenticated_client):
        """유효하지 않은 object_type 파라미터 전달 시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        data = {"object_type": "invalid_type", "object_id": 1, "reason": "부적절한 내용"}
        url = "/records/report/"

        # When
        response = client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_self_report(self, authenticated_client):
        """자기 자신의 컨텐츠 신고시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory(author=user)
        data = {"object_type": "post", "object_id": post.id, "reason": "부적절한 내용"}
        url = "/records/report/"

        # When
        response = client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthorized_report(self, client):
        """미인증 사용자의 신고 시도시 401 에러 반환 테스트"""
        # Given
        post = PostFactory()
        data = {"object_type": "post", "object_id": post.id, "reason": "부적절한 내용"}
        url = "/records/report/"

        # When
        response = client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"] == "로그인이 필요한 서비스입니다."

    def test_not_found_object(self, authenticated_client):
        """존재하지 않는 객체 신고시 404 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory()
        data = {"object_type": "post", "object_id": post.id + 9999, "reason": "부적절한 내용"}
        url = "/records/report/"

        # When
        response = client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND
