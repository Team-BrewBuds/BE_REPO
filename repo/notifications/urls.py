from django.urls import path

from .views import *

urlpatterns = [
    # 푸시 알림 테스트용 API
    path("test-send/<str:token>/", NotificationTestAPIView.as_view(), name="test-send"),
    # 사용자별 푸시 알림 관리 API (조회, 읽음처리, 삭제)
    path("user/", UserNotificationAPIView.as_view(), name="user-notification"),
    # 알림 설정 관리 API
    path("setting/", NotificationSettingAPIView.as_view(), name="notification-setting"),
    path("token/", NotificationTokenAPIView.as_view(), name="notification-token"),
]
