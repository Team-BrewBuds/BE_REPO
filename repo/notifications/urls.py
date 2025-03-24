from django.urls import path

from .views import *

urlpatterns = [
    path("", UserNotificationAPIView.as_view(), name="notifications"),
    path("settings/", NotificationSettingAPIView.as_view(), name="notification-settings"),
    path("devices/", NotificationTokenAPIView.as_view(), name="notification-devices"),
    # 테스트용 API (개발 환경에서만 사용)
    path("test/", NotificationTestAPIView.as_view(), name="notification-test"),
]
