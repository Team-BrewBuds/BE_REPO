import logging

from boto3.exceptions import Boto3Error
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

from repo.common.exception.exceptions import (
    BaseAPIException,
    InternalServerErrorException,
    NotFoundException,
    S3Exception,
)

logger = logging.getLogger("django.server")


def custom_exception_handler(exc, context):

    # django 예외 처리 (get_object_or_404)
    if isinstance(exc, Http404):
        exc = NotFoundException()

    # S3 관련 예외 처리
    if isinstance(exc, Boto3Error):
        exc = S3Exception()

    # DRF 기본 예외 처리
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, BaseAPIException):
            create_error_log(exc, context)
            response.data = exc.error_response

        # 코드상에서 예상하지 못한 APIException을 위한 처리
        elif isinstance(exc, APIException):
            logger.error("[!!!Need to check this exception!!!]")
            create_error_log(exc, context)
            response.data = format_response(exc)

        return response

    # 처리되지 않은 예외
    print(exc, context)
    return Response(InternalServerErrorException().error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def format_response(exc):
    return {"message": exc.detail, "code": exc.get_codes(), "status": exc.status_code}


def create_error_log(exc, context):
    logger.error(f"Exception: {exc}")
    logger.error(f"context: {context}")
