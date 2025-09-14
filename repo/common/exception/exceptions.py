from rest_framework import status
from rest_framework.exceptions import APIException


class BaseAPIException(APIException):
    """
    모든 APIException 예외의 기본 클래스
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_detail: str = "Bad Request base!"
    default_code: str = "bad_request base!"

    def __init__(self, detail=None, code=None):
        self.custom_detail = detail or self.default_detail
        self.custom_code = code or self.default_code
        super().__init__(self.custom_detail, self.custom_code)

    @property
    def error_response(self):
        """표준화된 에러 응답 포맷"""
        return {"message": self.custom_detail, "code": self.custom_code, "status": self.status_code}


class InternalServerErrorException(BaseAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Internal Server Error"
    default_code = "internal_server_error"


class BadRequestException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bad Request"
    default_code = "bad_request"


class ValidationException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Validation failed."
    default_code = "validation_failed"


class UnauthorizedException(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Unauthorized"
    default_code = "unauthorized"


class ForbiddenException(BaseAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Forbidden"
    default_code = "forbidden"


class NotFoundException(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Not Found exception"
    default_code = "not_found code"


class MethodNotAllowedException(BaseAPIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = "Method Not Allowed"
    default_code = "method_not_allowed"


class ConflictException(BaseAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"
    default_code = "conflict"


# 이미지 처리 예외
class S3Exception(BaseAPIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "S3 서비스 오류가 발생했습니다"
    default_code = "s3_error"


class FileSystemException(BaseAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "파일 시스템 오류가 발생했습니다"
    default_code = "file_system_error"


class ImageProcessingException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "이미지 처리 중 오류가 발생했습니다"
    default_code = "image_processing_error"


class TokenException(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "토큰이 유효하지 않습니다"
    default_code = "token_not_valid"
