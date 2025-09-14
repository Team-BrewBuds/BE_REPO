import logging
import traceback

from boto3.exceptions import Boto3Error
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken

from repo.common.exception.exceptions import (
    BaseAPIException,
    InternalServerErrorException,
    NotFoundException,
    S3Exception,
    TokenException,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    original_exc = exc  # 원본 예외 정보 보존

    # django 예외 처리 (get_object_or_404)
    if isinstance(exc, Http404):
        exc = NotFoundException()

    # JWT 토큰 관련 예외 처리
    if isinstance(exc, InvalidToken):
        exc = TokenException()

    # S3 관련 예외 처리
    if isinstance(exc, Boto3Error):
        exc = S3Exception()

    # DRF 기본 예외 처리
    response = exception_handler(exc, context)

    if response is not None:
        create_error_log(exc, context, original_exc)

        if isinstance(exc, BaseAPIException):
            response.data = exc.error_response
        elif isinstance(exc, APIException):  # 코드상에서 예상하지 못한 APIException을 위한 처리
            logger.error("[!!!Need to check this APIException (uncaught exception)!!!]")
            response.data = f"message: {exc.detail}, code: {exc.get_codes()}, status: {exc.status_code}"
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

    # 스택 트레이스 정보
    stack_trace = traceback.format_exc()

    # 상세 로깅
    logger.error(
        "\n"
        + "=" * 80
        + "\n[EXCEPTION DETAILS]"
        + f"\nException Type: {type(exception_to_log).__name__}"
        + f"\nException Message: {str(exception_to_log)}"
        + f"\nUser: {user_info}"
        + f"\nRequest: {request_info}"
        + f"\nView: {view_info}"
        + f"\n\n[STACK TRACE]\n{stack_trace}"
        + f"\n\n[CONTEXT]\n{context}"
        + "\n"
        + "=" * 80
    )
