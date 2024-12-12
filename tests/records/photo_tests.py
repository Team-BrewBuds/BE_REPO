import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from repo.records.models import Photo
from tests.factorys import PhotoFactory, PostFactory

pytestmark = pytest.mark.django_db


class TestPhotoUploadAPI:
    """
    사진 업로드 API 테스트
    작성한 테스트 케이스
    - [일반] 사진 업로드 성공 테스트
    - [예외] 이미지가 없는 경우 400 에러 반환 테스트
    - [예외] 잘못된 파일 형식 업로드 시 400 에러 반환 테스트
    - [예외] 미인증 사용자의 업로드 시도시 401 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/records/photo/"

    def test_photo_upload_success(self, authenticated_client, create_test_image):
        """사진 업로드 성공 테스트"""
        # Given
        client, user = authenticated_client()
        test_image = create_test_image

        # When
        response = client.post(self.url, {"photo_url": [test_image]}, format="multipart")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert Photo.objects.count() == 1
        assert "photo_url" in response.data[0]

    def test_photo_upload_no_image(self, authenticated_client):
        """이미지가 없는 경우 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()

        # When
        response = client.post(self.url, {"photo_url": []}, format="multipart")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Photo.objects.count() == 0

    def test_photo_upload_invalid_format(self, authenticated_client):
        """잘못된 파일 형식 업로드 시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        invalid_file = SimpleUploadedFile("test.txt", b"invalid content", content_type="text/plain")

        # When
        response = client.post(self.url, {"photo_url": [invalid_file]}, format="multipart")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Photo.objects.count() == 0

    def test_photo_upload_unauthorized(self, api_client, create_test_image):
        """미인증 사용자의 업로드 시도시 401 에러 반환 테스트"""
        # Given
        image = create_test_image

        # When
        response = api_client.post(self.url, {"photo_url": [image]}, format="multipart")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Photo.objects.count() == 0


class TestPhotoUpdateAPI:
    """
    사진 수정 API 테스트
    작성한 테스트 케이스
    - [일반] 사진 수정 성공 테스트
    - [예외] 존재하지 않는 사진 수정 시도시 404 에러 반환 테스트
    - [예외] 다른 사용자의 사진 수정 시도시 403 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/records/photo/"

    def test_photo_update_success(self, authenticated_client, create_test_image):
        """사진 수정 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory(author=user)
        photo = PhotoFactory(post=post)
        new_image = create_test_image

        # When
        response = client.put(
            f"{self.url}?object_type=post&object_id={post.id}",
            {
                "photo_url": [new_image],
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert Photo.objects.first().photo_url.name is not None

    def test_photo_update_not_found(self, authenticated_client, create_test_image):
        """존재하지 않는 사진 수정 시도시 404 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        image = create_test_image

        # When
        response = client.put(
            f"{self.url}?object_type=post&object_id=9999",
            {
                "photo_url": [image],
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_photo_update_forbidden(self, authenticated_client, create_test_image):
        """다른 사용자의 사진 수정 시도시 403 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        other_post = PostFactory()  # 다른 사용자의 게시물
        photo = PhotoFactory(post=other_post)
        new_image = create_test_image

        # When
        response = client.put(
            f"{self.url}?object_type=post&object_id={other_post.id}",
            {
                "photo_url": [new_image],
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPhotoDeleteAPI:
    """
    사진 삭제 API 테스트
    작성한 테스트 케이스
    - [일반] 사진 삭제 성공 테스트
    - [예외] 존재하지 않는 사진 삭제 시도시 404 에러 반환 테스트
    - [예외] 다른 사용자의 사진 삭제 시도시 403 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/records/photo/"

    def test_photo_delete_success(self, authenticated_client):
        """사진 삭제 성공 테스트"""
        # Given
        client, user = authenticated_client()
        post = PostFactory(author=user)
        photo = PhotoFactory(post=post)
        object_type = "post"
        object_id = post.id

        # When
        response = client.delete(f"{self.url}?object_type={object_type}&object_id={object_id}")

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Photo.objects.count() == 0

    def test_photo_delete_not_found(self, authenticated_client):
        """존재하지 않는 사진 삭제 시도시 404 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        object_type = "post"
        object_id = 9999

        # When
        response = client.delete(f"{self.url}?object_type={object_type}&object_id={object_id}")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_photo_delete_forbidden(self, authenticated_client):
        """다른 사용자의 사진 삭제 시도시 403 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        other_post = PostFactory()  # 다른 사용자의 게시물
        photo = PhotoFactory(post=other_post)
        object_type = "post"
        object_id = other_post.id

        # When
        response = client.delete(f"{self.url}?object_type={object_type}&object_id={object_id}")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestProfilePhotoAPIView:
    """
    프로필 사진 API 테스트
    작성한 테스트 케이스
    - [일반] 프로필 사진 업로드 성공 테스트
    - [일반] 프로필 사진 삭제 성공 테스트
    - [예외] 이미지가 없는 경우 400 에러 반환 테스트
    - [예외] 잘못된 파일 형식 업로드 시 400 에러 반환 테스트
    - [예외] 미인증 사용자의 프로필 사진 업로드 시도시 401 에러 반환 테스트
    """

    def setup_method(self):
        self.url = "/records/photo/profile/"

    def test_upload_profile_photo_success(self, authenticated_client, create_test_image):
        """프로필 사진 업로드 성공 테스트"""
        # Given
        client, user = authenticated_client()
        image = create_test_image

        # When
        response = client.post(f"{self.url}", {"photo_url": image}, format="multipart")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert "photo_url" in response.data
        user.refresh_from_db()
        assert user.profile_image is not None

    def test_delete_profile_photo_success(self, authenticated_client, create_test_image):
        """프로필 사진 삭제 성공 테스트"""
        # Given
        client, user = authenticated_client()
        image = create_test_image

        # 프로필 사진 업로드
        client.post(f"{self.url}", {"photo_url": image}, format="multipart")

        # When
        response = client.delete(f"{self.url}")

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        user.refresh_from_db()
        assert user.profile_image == "" or user.profile_image is None

    def test_upload_profile_photo_no_image(self, authenticated_client):
        """이미지가 없는 경우 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()

        # When
        response = client.post(f"{self.url}", {}, format="multipart")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_profile_photo_invalid_format(self, authenticated_client):
        """잘못된 파일 형식 업로드 시 400 에러 반환 테스트"""
        # Given
        client, user = authenticated_client()
        invalid_file = SimpleUploadedFile("test.txt", b"invalid content", content_type="text/plain")

        # When
        response = client.post(f"{self.url}", {"photo_url": invalid_file}, format="multipart")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_profile_photo_unauthorized(self, api_client, create_test_image):
        """미인증 사용자의 프로필 사진 업로드 시도시 401 에러 반환 테스트"""
        # Given
        image = create_test_image

        # When
        response = api_client.post(f"{self.url}", {"photo_url": image}, format="multipart")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
