from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from django.db import transaction

from repo.notifications.fcm import FCMService
from repo.notifications.models import NotificationSetting, UserDevice
from repo.profiles.models import CustomUser


class AbstractNotificationService(ABC):
    """
    공통 알림 서비스 추상 클래스

    - 모든 알림 클래스는 이 클래스를 상속하여 구현해야 함
    - 모든 알림 서비스에서 공통으로 사용되는 메서드를 정의
    - 알림 전송 로직 추상화
        1. 알림 대상 선정
        2. 알림 전송 제외 조건 체크
        3. 알림 Data 구성
        4. FCM 푸시 알림 전송
        5. 알림 저장
    """

    def __init__(self):
        """
        알림 서비스 초기화
        """
        self.fcm_service = FCMService()

    @staticmethod
    def check_notification_settings(user: CustomUser, notification_type: str) -> bool:
        """
        사용자의 알림 설정 확인

        Args:
            user: 사용자
            notification_type: 알림 유형

        Returns:
            알림 설정 여부
        """

        try:
            notification_settings = NotificationSetting.objects.get(user=user)
            return getattr(notification_settings, notification_type, False)
        except NotificationSetting.DoesNotExist:
            return False

    @staticmethod
    def get_device_token(user: CustomUser) -> Optional[str]:
        """
        사용자의 디바이스 토큰 조회
        """
        device = UserDevice.objects.filter(user=user, is_active=True).first()
        return device.device_token if device else None

    @staticmethod
    def get_device_tokens(user_ids: List[int]) -> List[str]:
        """
        사용자들의 디바이스 토큰 조회
        """
        tokens = UserDevice.objects.filter(user_id__in=user_ids, is_active=True).values_list("device_token", flat=True)
        return list(tokens)

    @transaction.atomic
    def send_notification(self, notification_type: str, **kwargs) -> None:
        """
        알림 전송 템플릿 메서드
        - 알림 전송 프로세스를 정의하고 순서를 보장

        Args:
            notification_type: 알림 유형 (comment, like, follow 등)
            **kwargs: 각 알림 유형별 필요한 추가 인자
        """
        # 1. 알림 대상 선정
        target_users = self._select_noti_targets(**kwargs)
        if not target_users:
            return

        # 2. 알림 전송 제외 조건 체크
        target_users = self._filter_excluded_users(target_users, notification_type)
        if not target_users:
            return

        # 3. 알림 데이터 및 메시지 구성
        data, messages = self._create_noti_data(notification_type, **kwargs)
        if not data or not messages:
            return

        # 4. 디바이스 토큰 조회
        device_tokens = self._get_device_tokens(target_users)
        if not device_tokens:
            return

        # 5. FCM 푸시 알림 전송
        self._send_push_noti(device_tokens, messages, data)

        # 6. 알림 저장
        self._save_noti_record(target_users, notification_type, data, messages)

    @abstractmethod
    def _select_noti_targets(self, **kwargs) -> List[CustomUser]:
        """
        알림 대상 선정
        알림을 수신할 대상 사용자 목록을 반환

        Returns:
            알림 대상 사용자 목록
        """
        pass

    @abstractmethod
    def _filter_excluded_users(self, users: List[CustomUser], notification_type: str) -> List[CustomUser]:
        """
        알림 전송 제외 대상 필터링
        - 알림 설정 OFF 유저
        - 자신이 트리거한 알림 대상자

        Args:
            users: 알림 대상 사용자 목록
            notification_type: 알림 유형

        Returns:
            필터링된 사용자 목록
        """
        pass

    @abstractmethod
    def _create_noti_data(self, notification_type: str, **kwargs) -> Tuple[Dict, Dict]:
        """
        알림 데이터 및 메시지 구성

        Args:
            notification_type: 알림 유형
            **kwargs: 각 알림 유형별 필요한 추가 인자

        Returns:
            (알림 데이터, 알림 메시지)
        """
        pass

    @abstractmethod
    def _get_device_tokens(self, users: List[CustomUser]) -> List[str]:
        """
        사용자들의, 디바이스 토큰 조회

        Args:
            users: 사용자 목록

        Returns:
            디바이스 토큰 목록
        """
        pass

    @abstractmethod
    def _send_push_noti(self, device_tokens: List[str], messages: Dict, data: Dict) -> None:
        """
        FCM 푸시 알림 전송

        Args:
            device_tokens: 디바이스 토큰 목록
            messages: 알림 메시지
            data: 알림 데이터
        """
        pass

    @abstractmethod
    def _save_noti_record(self, users: List[CustomUser], notification_type: str, data: Dict, messages: Dict) -> None:
        """
        알림 저장

        Args:
            users: 사용자 목록
            notification_type: 알림 유형
            data: 알림 데이터
            messages: 알림 메시지
        """
        pass
