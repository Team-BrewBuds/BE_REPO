import logging

from boto3.exceptions import Boto3Error
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from repo.common.exception.exceptions import (
    BaseAPIException,
    InternalServerErrorException,
    NotFoundException,
    S3Exception,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    original_exc = exc  # 원본 예외 정보 보존

    # django 예외 처리 (get_object_or_404)
    if isinstance(exc, Http404):
        exc = NotFoundException()

    # S3 관련 예외 처리
    if isinstance(exc, Boto3Error):
        exc = S3Exception()

    # DRF 기본 예외 처리
    response = exception_handler(exc, context)

    if response is not None:
        create_error_log(exc, context, original_exc)

        if isinstance(exc, BaseAPIException):
            response.data = exc.error_response
            if exc.status_code >= 500:
                logger.error(f"[Custom Server Error] {type(exc).__name__}: {exc.custom_detail}")
            elif exc.status_code == 404:
                logger.info(f"[Resource Not Found] {type(exc).__name__}: {exc.custom_detail}")
            else:
                logger.warning(f"[Custom Client Error] {type(exc).__name__}: {exc.custom_detail}")

        elif isinstance(exc, ValidationError):
            response.data = {
                "message": exc.detail,
                "code": exc.get_codes(),
                "status": exc.status_code,
            }
            logger.info(f"[Validation Error] Fields: {list(exc.detail.keys()) if isinstance(exc.detail, dict) else 'N/A'}")

        elif isinstance(exc, APIException):
            data = {
                "message": exc.detail,
                "code": exc.get_codes(),
                "status": exc.status_code,
            }
            logger.warning(f"[Unhandled APIException] Type: {type(exc).__name__}, Data: {data}")
            response.data = data
        return response

    # 처리되지 않은 예외
    logger.critical("Unhandled exception occurred")
    create_error_log(exc, context, original_exc)
    return Response(InternalServerErrorException().error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_error_log(exc, context, original_exc=None):
    """
    상세한 예외 정보를 로깅하는 함수
    """
    # 기본 예외 정보
    exception_to_log = original_exc if original_exc else exc

    # 요청 정보 추출
    request = context.get("request")
    view = context.get("view")

    # 사용자 정보
    user_info = "Anonymous"
    if request and hasattr(request, "user") and request.user.is_authenticated:
        user_info = f"User ID: {request.user.id}, Username: {getattr(request.user, 'username', 'N/A')}"

    # 요청 정보
    request_info = "No request info"
    if request:
        request_info = f"{request.method} {request.get_full_path()}"

    # View 정보
    view_info = "No view info"
    if view:
        view_info = f"{view.__class__.__module__}.{view.__class__.__name__}"
        if hasattr(view, "action"):
            view_info += f".{view.action}"

    logger.error(
        f"[API Exception] {type(exception_to_log).__name__}: {str(exception_to_log)} | "
        f"User: {user_info} | Request: {request_info} | View: {view_info}",
        exc_info=True,  # 스택 트레이스 포함
    )
