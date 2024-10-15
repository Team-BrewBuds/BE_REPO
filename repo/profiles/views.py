import random

import requests
from allauth.socialaccount.providers.apple import views as apple_view
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.naver import views as naver_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.profiles.models import CustomUser, Relationship, UserDetail
from repo.profiles.serializers import BudyRecommendSerializer, UserRegisterSerializer

BASE_BACKEND_URL = settings.BASE_BACKEND_URL

KAKAO_REST_API_KEY = settings.KAKAO_REST_API_KEY
KAKAO_CLIENT_SECRET = settings.KAKAO_CLIENT_SECRET
KAKAO_REDIRECT_URI = settings.KAKAO_REDIRECT_URI

NAVER_CLIENT_ID = settings.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = settings.NAVER_CLIENT_SECRET
NAVER_REDIRECT_URI = settings.NAVER_REDIRECT_URI

APPLE_CLIENT_ID = settings.APPLE_CLIENT_ID
APPLE_CLIENT_SECRET = settings.APPLE_CLIENT_SECRET
APPLE_REDIRECT_URI = settings.APPLE_REDIRECT_URI


class KakaoCallbackView(APIView):
    """
    Kakao 로그인 후 사용자 정보를 처리하는 콜백 API
    Args:
        request: 클라이언트로부터 받은 요청 객체, access_token을 포함함.
    Returns:
        JSON 응답: 카카오 로그인 인증 결과 및 사용자 정보.
        성공 시: 카카오 OAuth2를 통해 받아온 프로필 정보를 백엔드에 전달하고 처리된 결과 반환.
        실패 시: 로그인 실패 메시지와 HTTP 상태 코드.

    담당자: blakej2432
    """

    def get(self, request):
        kakao_access_token = request.data.get("access_token")

        profile_request = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {kakao_access_token}"},
        )

        data = {"access_token": kakao_access_token}
        accept = requests.post(f"{BASE_BACKEND_URL}/profiles/login/kakao/finish/", data=data)

        accept_status = accept.status_code
        accept_json = accept.json()

        if accept_status != 200:
            return JsonResponse({"err_msg": "failed to signin"}, status=accept_status)

        return JsonResponse(accept_json)


class NaverCallbackView(APIView):
    """
    Naver 로그인 후 사용자 정보를 처리하는 콜백 API
    Args:
        request: 클라이언트로부터 받은 요청 객체, access_token을 포함함.
    Returns:
        JSON 응답: 네이버 로그인 인증 결과 및 사용자 정보.
        성공 시: 네이버 OAuth2를 통해 받아온 프로필 정보를 백엔드에 전달하고 처리된 결과 반환.
        실패 시: 로그인 실패 메시지와 HTTP 상태 코드.

    담당자: blakej2432
    """

    def get(self, request):
        naver_access_token = request.data.get("access_token")

        # 네이버 사용자 정보 API 호출
        profile_request = requests.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {naver_access_token}"},
        )

        # NaverLogin View에 POST 요청
        data = {"access_token": naver_access_token}
        accept = requests.post(f"{BASE_BACKEND_URL}/profiles/login/naver/finish/", data=data)

        accept_status = accept.status_code
        accept_json = accept.json()

        if accept_status != 200:
            return JsonResponse({"err_msg": "failed to signin"}, status=accept_status)

        return JsonResponse(accept_json)


class AppleCallbackView(APIView):
    """
    Apple 로그인 후 사용자 정보를 처리하는 콜백 API
    Args:
        request: 클라이언트로부터 받은 요청 객체, authorization_code 포함.
    Returns:
        JSON 응답: Apple OAuth2를 통해 받아온 프로필 정보를 백엔드에 전달하고 처리된 결과 반환.
        성공 시: Apple OAuth2를 통해 받은 access_token을 이용해 사용자 로그인 처리.
        실패 시: 로그인 실패 메시지와 HTTP 상태 코드.

    담당자: blakej2432
    """

    def get(self, request):
        authorization_code = request.data.get("code")

        # Apple 서버로 access_token 요청
        token_request = requests.post(
            "https://appleid.apple.com/auth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": APPLE_CLIENT_ID,
                "client_secret": APPLE_CLIENT_SECRET,
                "code": authorization_code,
                "grant_type": "authorization_code",
                "redirect_uri": APPLE_REDIRECT_URI,
            },
        )

        if token_request.status_code != 200:
            return JsonResponse({"err_msg": "failed to get access token from Apple"}, status=token_request.status_code)

        token_response = token_request.json()
        apple_access_token = token_response.get("access_token")

        if not apple_access_token:
            return JsonResponse({"err_msg": "Apple access token not found"}, status=400)

        data = {"access_token": apple_access_token}
        accept = requests.post(f"{BASE_BACKEND_URL}/profiles/login/apple/finish/", data=data)

        accept_status = accept.status_code
        accept_json = accept.json()

        if accept_status != 200:
            return JsonResponse({"err_msg": "failed to signin"}, status=accept_status)

        return JsonResponse(accept_json)


class KakaoLoginView(SocialLoginView):
    """
    Kakao 소셜 로그인 후 장고 CustomUserModel에서 등록/확인 위한 API
    Args:
        request: 클라이언트의 로그인 요청.
    Returns:
        JSON 응답: Kakao OAuth2 인증 후 사용자 로그인 결과(jwt 토큰 반환).

    담당자: blakej2432
    """

    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = KAKAO_REDIRECT_URI


class NaverLoginView(SocialLoginView):
    """
    Naver 소셜 로그인 후 사용자 정보를 CustomUserModel에 저장하는 API
    Args:
        request: 클라이언트의 로그인 요청.
    Returns:
        JSON 응답: Naver OAuth2 인증 후 사용자 로그인 결과(JWT 토큰 반환).

    담당자: blakej2432
    """

    adapter_class = naver_view.NaverOAuth2Adapter
    client_class = OAuth2Client
    callback_url = NAVER_REDIRECT_URI


class AppleLoginView(SocialLoginView):
    """
    Apple 소셜 로그인 후 사용자 정보를 CustomUserModel에 저장하는 API
    Args:
        request: 클라이언트의 로그인 요청.
    Returns:
        JSON 응답: Apple OAuth2 인증 후 사용자 로그인 결과(JWT 토큰 반환).

    담당자: blakej2432
    """

    adapter_class = apple_view.AppleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = NAVER_REDIRECT_URI


# TODO: 회원가입 구현
class RegistrationView(APIView):
    """
    사용자 회원가입을 처리하는 API
    """

    def get(self, request):
        # user = request.user
        # serializer = UserRegisterSerializer(user)

        # return Response(serializer.data)
        return Response("회원가입 완료")

    def patch(self, request):
        user = request.user  # 현재 로그인한 사용자
        serializer = UserRegisterSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            # 회원가입 완료 처리
            serializer.save(is_active=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# TODO: Profile - User 정보 수정 관련 구현
# class UpdateUserInfoView(generics.UpdateAPIView):
#     queryset = CustomUser.objects.all()
#     serializer_class = UserRegisterSerializer
#     permission_classes = [permissions.IsAuthenticated]  # 로그인한 사용자만 가능

#     def get_object(self):
#         # 현재 로그인한 유저의 정보를 업데이트
#         return self.request.user

#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)

#         return Response(serializer.data)


# class GetUserInfoView(generics.RetrieveAPIView):
#     queryset = CustomUser.objects.all()
#     serializer_class = UserRegisterSerializer
#     permission_classes = [permissions.IsAuthenticated]  # 로그인한 사용자만 가능

#     def get_object(self):
#         # 현재 로그인한 유저 정보를 반환
#         return self.request.user


class FollowAPIView(APIView):
    """
    팔로우, 팔로우 취소 API
    Args:
        (post) follow_user_id: 팔로우할 사용자의 id
        (delete) following_user_id: 팔로우 취소할 사용자의 id
    Returns:
        팔로우 성공 시: HTTP 201 Created
        팔로우 취소 성공 시: HTTP 200 OK
        실패 시: HTTP 400 Bad Request or 404 Not Found

    담당자: hwstar1204
    """

    def post(self, request):
        user = request.user
        follow_user_id = request.data.get("follow_user_id")
        if not follow_user_id:
            return Response({"error": "follow_user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        follow_user = get_object_or_404(CustomUser, id=follow_user_id)

        relationship, created = Relationship.custom_objects.follow(user, follow_user)
        if not created:
            return Response({"error": "already following"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": "create follow success"}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        user = request.user
        following_user_id = request.data.get("following_user_id")
        if not following_user_id:
            return Response({"error": "following_user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        following_user = get_object_or_404(CustomUser, id=following_user_id)

        relationship, deleted = Relationship.custom_objects.unfollow(user, following_user)
        if not deleted:
            return Response({"error": "not following"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": "delete follow success"}, status=status.HTTP_200_OK)

class BudyRecommendAPIView(APIView):
    """
    유저의 커피 즐기는 방식 6개 중 한가지 방식에 해당 하는 유저 리스트 반환
    Args:
        request: 클라이언트로부터 받은 요청 객체
    Returns:
        users:
            user: 유저의 커피 생활 방식에 해당 하는 유저 리스트 반환 (10명)
            follower_cnt: 유저의 팔로워 수
        category: 커피 생활 방식
        실패 시: HTTP 404 Not Found

    담당자: hwtar1204
    """
    @extend_schema(
        summary="버디 추천",
        description="유저의 커피 즐기는 방식 6개 중 한가지 방식에 해당 하는 유저 리스트 반환 (10명 랜덤순)",
        responses={200: BudyRecommendSerializer},
        tags=["recommend"],
    )
    def get(self, request):
        user = request.user

        user_detail = get_object_or_404(UserDetail, user=user)
        coffee_life_helper = user_detail.get_coffee_life_helper()
        true_categories = coffee_life_helper.get_true_categories()

        if not true_categories:
            # 커피 생활을 선택하지 않은 경우 무작위 카테고리에 해당 하는 유저 리스트 반환
            random_category = random.choice(UserDetail.COFFEE_LIFE_CHOICES)
            user_list = (
                CustomUser.objects.select_related("user_detail")
                .filter(user_detail__coffee_life__contains={random_category: True})
                .order_by("?")[:10]
            )
        else:
            random_true_category = random.choice(true_categories)
            user_list = (
                CustomUser.objects.select_related("user_detail")
                .filter(user_detail__coffee_life__contains={random_true_category: True})
                .order_by("?")[:10]
            )

        recommend_user_list = []
        for user in user_list:
            recommend_user_list.append({"user": user, "follower_cnt": Relationship.custom_objects.followers(user).count()})

        serializer = BudyRecommendSerializer(recommend_user_list, many=True)
        category = random_true_category if true_categories else random_category
        response_data = {"users": serializer.data, "category": category}

        return Response(response_data, status=status.HTTP_200_OK)
