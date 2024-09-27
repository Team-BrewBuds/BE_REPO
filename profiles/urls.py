from django.urls import path

from profiles import views

urlpatterns = [
    path("test/", views.test),  # 초기 테스트용 url (이후 삭제 해주세요)
]
