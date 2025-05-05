from typing import Dict, List, Tuple

from repo.profiles.models import CustomUser

from ..base import AbstractNotificationService


class CommentNotificationService(AbstractNotificationService):
    """
    댓글 알림 서비스
    """

    def _select_noti_targets(self, **kwargs) -> List[CustomUser]:
        """
        알림 대상 선정
        """

        pass

    def _filter_excluded_users(self, users: List[CustomUser], notification_type: str) -> List[CustomUser]:
        """
        알림 전송 제외 대상 필터링
        - 알림 설정 OFF 유저
        - 자신이 트리거한 알림 대상자
        """

        pass

    def _create_noti_data(self, notification_type: str, **kwargs) -> Tuple[Dict, Dict]:
        """
        알림 데이터 및 메시지 구성
        """

        pass

    def _get_device_tokens(self, users: List[CustomUser]) -> List[str]:
        """
        사용자들의, 디바이스 토큰 조회
        """

        pass

    def _send_push_noti(self, device_tokens: List[str], messages: Dict, data: Dict) -> None:
        """
        FCM 푸시 알림 전송
        """

        pass

    def _save_noti_record(self, users: List[CustomUser], notification_type: str, data: Dict, messages: Dict) -> None:
        """
        알림 저장
        """

        pass
