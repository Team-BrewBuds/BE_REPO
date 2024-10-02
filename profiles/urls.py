from django.urls import path, include
from profiles import views

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('/', include('allauth.urls'), name='socialaccount_signup'),
    path("kakao/login/", views.KakaoCallbackView.as_view(), name="kakao_callback"),
    path("kakao/login/finish/", views.KakaoLoginView.as_view(), name="kakao_login_todjango"),
    path('login/oauth/naver/', views.NaverLoginView.as_view(), name='naver-login'),
    
    path('user/complete-registration/', views.RegistrationView.as_view(), name='complete_registration'),

   
    # 스키마를 제공하는 엔드포인트
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Redoc UI
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
