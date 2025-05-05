import logging
import os
from typing import List

import firebase_admin
from django.conf import settings
from django.db import transaction
from firebase_admin import credentials, exceptions, messaging
from firebase_admin.messaging import Message, MulticastMessage, Notification

from repo.common.decorators import retry

from .models import UserDevice

logger = logging.getLogger("django.server")

SERVICE_ACCOUNT_FILE = getattr(settings, "FCM_SERVICE_ACCOUNT_FILE", None)
DRY_RUN = True if settings.DEBUG else False


class FCMService:
    """FCM 알림 서비스"""

    def __init__(self):
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Firebase Admin SDK 초기화"""
        if not SERVICE_ACCOUNT_FILE:
            raise ValueError("FCM_SERVICE_ACCOUNT_FILE 설정이 없습니다.")

        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Firebase 서비스 계정 키 파일을 찾을 수 없습니다: {SERVICE_ACCOUNT_FILE}")

        try:
            self.app = self._get_or_create_firebase_app()
            logger.info("Firebase 초기화 성공")
        except Exception as e:
            self._handle_initialization_error(e)

    def _get_or_create_firebase_app(self):
        """기존 Firebase 앱을 가져오거나 새로 생성"""
        try:
            return firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
            return firebase_admin.initialize_app(cred)

    def _handle_initialization_error(self, error):
        """초기화 에러 처리"""
        logger.error(f"Firebase 초기화 중 오류 발생: {str(error)}")
        if settings.DEBUG:
            logger.warning("개발 환경: Firebase 초기화를 건너뜁니다.")
        else:
            raise

    @staticmethod
    def _handle_invalid_token(device_token: str) -> None:
        """무효한 토큰 처리"""
        with transaction.atomic():
            UserDevice.objects.filter(device_token=device_token).delete()
            logger.info(f"Removed invalid token: {device_token}")

    def _handle_failed_tokens(self, device_tokens: List[str], response: messaging.BatchResponse) -> None:
        """실패한 토큰들 처리"""
        failed_tokens = [device_tokens[idx] for idx, resp in enumerate(response.responses) if not resp.success]
        if failed_tokens:
            with transaction.atomic():
                UserDevice.objects.filter(device_token__in=failed_tokens).delete()
                logger.info(f"Removed {len(failed_tokens)} invalid tokens")

    @retry(max_retries=3)
    def send_push_notification_to_single_device(self, device_token: str, title: str, body: str, data: dict = None) -> bool:
        """
        단일 디바이스에 알림 전송
        Returns:
            bool: 전송 성공 여부
        """
        if not device_token:
            logger.warning("디바이스 토큰이 없습니다.")
            return False

        try:
            message = Message(
                notification=Notification(title=title, body=body),
                token=device_token,
                data=data or {},
            )
            response = messaging.send(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent single message: {response}")
            return True
        except exceptions.UnauthenticatedError as e:
            self._handle_invalid_token(device_token)
            return False
        except Exception as e:
            logger.error(f"메시지 전송 중 오류 발생: {str(e)}")
            return False

    @retry(max_retries=3)
    def send_push_notification_to_multiple_devices(self, device_tokens: List[str], title: str, body: str, data: dict = None) -> bool:
        """
        여러 디바이스에 알림 전송
        Returns:
            bool: 전송 성공 여부
        """
        if not device_tokens:
            logger.warning("전송할 디바이스 토큰이 없습니다.")
            return False

        try:
            notification = Notification(title=title, body=body)
            message = MulticastMessage(tokens=device_tokens, data=data or {}, notification=notification)
            response: messaging.BatchResponse = messaging.send_each_for_multicast(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent multiple message: {response}")

            if response.failure_count > 0:
                self._handle_failed_tokens(device_tokens, response)

            return response.success_count > 0
        except Exception as e:
            logger.error(f"다중 메시지 전송 중 오류 발생: {str(e)}")
            return False

    @retry(max_retries=3)
    def send_push_notification_silent(self, device_token: str, data: dict = None) -> bool:
        """
        단일 디바이스에 무음 알림 전송
        Returns:
            bool: 전송 성공 여부
        """
        if not device_token:
            logger.warning("디바이스 토큰이 없습니다.")
            return False

        try:
            message = Message(token=device_token, data=data or {})
            response = messaging.send(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent silent message: {response}")
            return True
        except exceptions.UnauthenticatedError as e:
            self._handle_invalid_token(device_token)
            return False
        except Exception as e:
            logger.error(f"무음 메시지 전송 중 오류 발생: {str(e)}")
            return False

    @retry(max_retries=3)
    def send_push_notification_to_topic(self, topic: str, title: str, body: str, data: dict = None) -> bool:
        """
        토픽에 알림 전송
        Args:
            topic: 토픽 식별자
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터
        Returns:
            bool: 전송 성공 여부
        """
        if not topic:
            logger.warning("토픽이 지정되지 않았습니다.")
            return False

        try:
            notification = Notification(title=title, body=body)
            message = Message(data=data or {}, notification=notification, topic=topic)
            response = messaging.send(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent topic message: {response}")
            return True
        except Exception as e:
            logger.error(f"토픽 메시지 전송 중 오류 발생: {str(e)}")
            return False

    @retry(max_retries=3)
    def subscribe_topic(self, topic: str, token: str) -> bool:
        """
        토픽 구독 설정
        Args:
            topic: 구독할 토픽
            token: 디바이스 토큰
        Returns:
            bool: 구독 성공 여부
        """
        if not all([topic, token]):
            logger.warning("토픽 또는 토큰이 지정되지 않았습니다.")
            return False

        try:
            messaging.subscribe_to_topic(token, topic)
            logger.info(f"Successfully subscribed to topic: {topic}")
            return True
        except (ValueError, exceptions.FirebaseError) as e:
            logger.error(f"토픽 구독 실패: {str(e)}")
            return False

    @retry(max_retries=3)
    def unsubscribe_topic(self, topic: str, tokens: List[str]) -> bool:
        """
        토픽 구독 해지
        Args:
            topic: 해지할 토픽
            token: 디바이스 토큰
        Returns:
            bool: 해지 성공 여부
        """
        if not all([topic, tokens]):
            logger.warning("토픽 또는 토큰이 지정되지 않았습니다.")
            return False

        try:
            messaging.unsubscribe_from_topic(tokens, topic)
            logger.info(f"Successfully unsubscribed from topic: {topic}")
            return True
        except (ValueError, exceptions.FirebaseError) as e:
            logger.error(f"토픽 구독 해지 실패: {str(e)}")
            return False
