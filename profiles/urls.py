from django.urls import path, include

from profiles import views


urlpatterns = [
    path('/', include('allauth.urls'), name='socialaccount_signup'),
    path("kakao/login/", views.KakaoCallbackView.as_view(), name="kakao_callback"),
    path("kakao/login/finish/", views.KakaoLoginView.as_view(), name="kakao_login_todjango"),
    path('login/oauth/naver/', views.NaverLoginView.as_view(), name='naver-login'),
    
    path('user/complete-registration/', views.RegistrationView.as_view(), name='complete_registration'),

]
