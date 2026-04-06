import datetime

import pytest
from rest_framework import status

from repo.offboarding.models import ExportRequest

pytestmark = pytest.mark.django_db

URL = "/offboarding/closure/export-requests/"


class TestExportRequestsAPIView:
    """
    ExportRequestsAPIView 테스트
    - [일반] 미인증 사용자 접근 시 401
    - [일반] POST 신청 성공 → 201, DB 저장 확인
    - [일반] GET 신청 내역 조회 성공 → 200, 필드 확인
    - [일반] PUT 이메일 수정 성공 → 200, 변경된 이메일 확인
    - [예외] POST 중복 신청 → 409
    - [예외] GET 신청 내역 없는 경우 → 404
    - [예외] PUT 신청 내역 없는 경우 → 404
    - [예외] 유효하지 않은 이메일 형식으로 POST → 400
    - [예외] 마감일 이후 POST 신청 → 410
    """

    def test_unauthenticated_access(self, api_client):
        """미인증 사용자 접근 시 401"""
        response = api_client.post(URL, {"export_email": "test@test.com"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_export_request_success(self, authenticated_client):
        """이메일 신청 성공 → 201, DB 저장 확인"""
        # Given
        client, user = authenticated_client()
        # When
        response = client.post(URL, {"export_email": "export@test.com"}, format="json")
        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["export_email"] == "export@test.com"
        assert response.data["user_id"] == user.id
        assert response.data["username"] == user.nickname
        assert ExportRequest.objects.filter(user=user).exists()

    def test_get_export_request_success(self, authenticated_client):
        """신청 내역 조회 성공 → 200, 필드 확인"""
        # Given
        client, user = authenticated_client()
        ExportRequest.objects.create(user=user, export_email="export@test.com")
        # When
        response = client.get(URL)
        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["export_email"] == "export@test.com"
        assert response.data["user_id"] == user.id
        assert response.data["username"] == user.nickname
        assert "created_at" in response.data

    def test_put_export_request_success(self, authenticated_client):
        """이메일 수정 성공 → 200, 변경된 이메일 확인"""
        # Given
        client, user = authenticated_client()
        ExportRequest.objects.create(user=user, export_email="old@test.com")
        # When
        response = client.put(URL, {"export_email": "new@test.com"}, format="json")
        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["export_email"] == "new@test.com"
        assert ExportRequest.objects.get(user=user).export_email == "new@test.com"

    def test_post_duplicate_request(self, authenticated_client):
        """중복 신청 → 409"""
        # Given
        client, user = authenticated_client()
        ExportRequest.objects.create(user=user, export_email="first@test.com")
        # When
        response = client.post(URL, {"export_email": "second@test.com"}, format="json")
        # Then
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_get_no_request(self, authenticated_client):
        """신청 내역 없는 경우 GET → 404"""
        # Given
        client, user = authenticated_client()
        # When
        response = client.get(URL)
        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_no_request(self, authenticated_client):
        """신청 내역 없는 경우 PUT → 404"""
        # Given
        client, user = authenticated_client()
        # When
        response = client.put(URL, {"export_email": "new@test.com"}, format="json")
        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post_invalid_email(self, authenticated_client):
        """유효하지 않은 이메일 형식 → 400"""
        # Given
        client, user = authenticated_client()
        # When
        response = client.post(URL, {"export_email": "not-an-email"}, format="json")
        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_after_deadline(self, authenticated_client, monkeypatch):
        """마감일 이후 신청 → 410"""
        # Given
        client, user = authenticated_client()

        class FakeDate(datetime.date):
            @classmethod
            def today(cls):
                return datetime.date(2100, 1, 1)

        monkeypatch.setattr("repo.offboarding.views.datetime.date", FakeDate)
        # When
        response = client.post(URL, {"export_email": "export@test.com"}, format="json")
        # Then
        assert response.status_code == status.HTTP_410_GONE
