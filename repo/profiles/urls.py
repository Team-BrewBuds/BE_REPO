from django.urls import path, include

from repo.profiles import views

urlpatterns = [
    path('/', include('allauth.urls'), name='socialaccount_signup'),
    path("login/oauth/kakao/", views.KakaoCallbackView.as_view(), name="kakao_callback"),
    path("login/kakao/finish/", views.KakaoLoginView.as_view(), name="kakao_login_todjango"),
    
    path('login/oauth/naver/', views.NaverCallbackView.as_view(), name='naver_callback'),
    path("login/naver/finish/", views.NaverLoginView.as_view(), name="naver_login_todjango"),
    
    path('user/complete-registration/', views.RegistrationView.as_view(), name='complete_registration'),
    path('follow/', views.FollowAPIView.as_view(), name='follow'),
    path('recommend/', views.BudyRecommendAPIView.as_view(), name='budy-recommend'),

]
