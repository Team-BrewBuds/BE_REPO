from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from repo.profiles import views

urlpatterns = [
    path("/", include("allauth.urls"), name="socialaccount_signup"),
    path("login/oauth/kakao/", views.KakaoCallbackView.as_view(), name="kakao_callback"),
    path("login/kakao/finish/", views.KakaoLoginView.as_view(), name="kakao_login_todjango"),
    path("login/oauth/naver/", views.NaverCallbackView.as_view(), name="naver_callback"),
    path("login/naver/finish/", views.NaverLoginView.as_view(), name="naver_login_todjango"),
    path("login/oauth/apple/", views.AppleCallbackView.as_view(), name="apple_callback"),
    path("login/apple/finish/", views.AppleLoginView.as_view(), name="apple_login_todjango"),
    path("user/complete-registration/", views.RegistrationView.as_view(), name="complete_registration"),
    path("", views.MyProfileAPIView.as_view(), name="my_profile"),
    path("<int:id>/", views.OtherProfileAPIView.as_view(), name="other_profile"),
    path("follow/<int:id>/", views.FollowAPIView.as_view(), name="follow"),
    path("recommend/", views.BudyRecommendAPIView.as_view(), name="budy-recommend"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
