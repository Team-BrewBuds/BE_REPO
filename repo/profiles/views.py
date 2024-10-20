import random

import jwt
import requests
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.naver import views as naver_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from repo.profiles.models import CustomUser, Relationship, UserDetail
from repo.profiles.serializers import (
    BudyRecommendSerializer,
    UserDetailSignupSerializer,
    UserFollowListSerializer,
    UserProfileSerializer,
    UserSignupSerializer,
    UserUpdateSerializer,
)
from repo.profiles.services import get_follower_list, get_following_list

BASE_BACKEND_URL = settings.BASE_BACKEND_URL

KAKAO_REST_API_KEY = settings.KAKAO_REST_API_KEY
KAKAO_CLIENT_SECRET = settings.KAKAO_CLIENT_SECRET
KAKAO_REDIRECT_URI = settings.KAKAO_REDIRECT_URI

NAVER_CLIENT_ID = settings.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = settings.NAVER_CLIENT_SECRET
NAVER_REDIRECT_URI = settings.NAVER_REDIRECT_URI


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
        request: 클라이언트로부터 받은 요청 객체, id_token을 포함함.
    Returns:
        JSON 응답: Apple 로그인 인증 결과 및 사용자 정보.
        성공 시: Apple OAuth2를 통해 받아온 프로필 정보를 백엔드에 전달하고 처리된 결과 반환.
        실패 시: 로그인 실패 메시지와 HTTP 상태 코드.

    담당자: blakej2432
    """

    def get(self, request):
        apple_id_token = request.data.get("id_token")
        data = {"id_token": apple_id_token}
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

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        user = self.request.user
        if not user.is_authenticated:
            return response

        if user.login_type is None:
            user.login_type = "kakao"
            user.save()

        return response


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

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        user = self.request.user
        if not user.is_authenticated:
            return response

        if user.login_type is None:
            user.login_type = "naver"
            user.save()

        return response


class AppleLoginView(APIView):
    """
    Apple 소셜 로그인 후 프론트엔드에서 받은 id_token을 처리하는 API
    Args:
        request: 클라이언트의 로그인 요청.
    Returns:
        JSON 응답: apple id_token 복호화 후 사용자 로그인 결과(JWT 토큰 반환).

    담당자: blakej2432
    """

    def post(self, request):
        apple_id_token = request.data.get("id_token")
        if not apple_id_token:
            return Response({"detail": "id_token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_token = jwt.decode(apple_id_token, options={"verify_signature": False})
            user_email = decoded_token.get("email")

            user, created = CustomUser.objects.get_or_create(email=user_email, defaults={"email": user_email})

            if created:
                user.login_type = "apple"

            user.last_login = now()
            user.save()

            # JWT 토큰 발급
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # 응답 데이터 반환
            return Response(
                {
                    "access_token": access_token,
                    "refresh_token": str(refresh),
                    "user": {
                        "pk": user.pk,
                        "email": user_email,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except jwt.DecodeError:
            return Response({"detail": "Invalid id_token."}, status=status.HTTP_400_BAD_REQUEST)


class SignupView(APIView):
    """
    사용자 회원가입을 처리하는 API.

    이 API는 사용자로부터 추가적인 회원 정보(닉네임, 성별, 출생연도, 커피 생활 정보,
    선호하는 원두 맛, 커피 자격증 여부)를 받아 유효성을 검사하고 저장합니다.

    Args:
        request: 클라이언트로부터 전달받은 회원가입 데이터 (닉네임, 성별, 출생연도, 커피 생활,
                선호하는 원두 맛, 커피 자격증 여부).

    Returns:
        JSON 응답:
            - 회원가입 성공 시: "회원가입을 성공했습니다." 메시지와 함께 HTTP 200 응답.
            - 유효성 검사 실패 시: 에러 메시지와 함께 HTTP 400 응답.

    담당자: blakej2432
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user_data = {
            "nickname": request.data.get("nickname"),
            "gender": request.data.get("gender"),
            "birth": request.data.get("birth_year"),
        }

        user_serializer = UserSignupSerializer(user, data=user_data, partial=True)
        if not user_serializer.is_valid():
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user_serializer.save()

        coffee_life_data = {choice: choice in request.data.get("coffee_life", []) for choice in UserDetail.COFFEE_LIFE_CHOICES}

        user_detail_data = {
            "coffee_life": coffee_life_data,
            "preferred_bean_taste": request.data.get("preferred_bean_taste", {}),
            "is_certificated": request.data.get("is_certificated", False),
        }
        user_detail, created = UserDetail.objects.get_or_create(user=user)
        user_detail_serializer = UserDetailSignupSerializer(user_detail, data=user_detail_data, partial=True)

        if not user_detail_serializer.is_valid():
            return Response(user_detail_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user_detail_serializer.save()

        return Response({"message": "회원가입을 성공했습니다."}, status=status.HTTP_200_OK)


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


@extend_schema_view(
    get=extend_schema(
        responses=UserProfileSerializer,
        summary="자기 프로필 조회",
        description="""
            현재 로그인한 사용자의 프로필을 조회합니다.

            닉네임, 프로필 이미지, 커피 생활 방식, 팔로워 수, 팔로잉 수, 게시글 수를 반환합니다.
            담당자 : hwstar1204
        """,
        tags=["profile"],
    ),
    patch=extend_schema(
        request=UserUpdateSerializer,
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        summary="자기 프로필 수정",
        description="""
            현재 로그인한 사용자의 프로필을 수정합니다.

            닉네임, 프로필 이미지, 소개, 프로필 링크, 커피 생활 방식, 선호하는 커피 맛, 자격증 여부를 수정합니다.
            담당자 : hwstar1204
        """,
        tags=["profile"],
    ),
)
class MyProfileAPIView(APIView):
    def get(self, request):
        user = request.user
        data = {
            "nickname": user.nickname,
            "profile_image": user.profile_image,
            "coffee_life": user.user_detail.coffee_life,
            "follower_cnt": Relationship.objects.followers(user).count(),
            "following_cnt": Relationship.objects.following(user).count(),
            "post_cnt": user.post_set.count(),
        }

        serializer = UserProfileSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "user not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            fields = ["nickname", "profile_image"]
            for field in fields:
                setattr(user, field, serializer.validated_data.get(field, getattr(user, field)))
            user.save()

            user_detail_data = serializer.validated_data.get("user_detail", None)
            if user_detail_data:
                user_detail, created = UserDetail.objects.get_or_create(user=user)
                fields = ["introduction", "profile_link", "coffee_life", "preferred_bean_taste", "is_certificated"]
                for field in fields:
                    setattr(user_detail, field, user_detail_data.get(field, getattr(user_detail, field)))
                user_detail.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        responses=UserProfileSerializer,
        summary="상대 프로필 조회",
        description="""
            특정 사용자의 프로필을 조회합니다.

            닉네임, 프로필 이미지, 커피 생활 방식, 팔로워 수, 팔로잉 수, 게시글 수를 반환합니다.
            요청한 사용자가 팔로우 중인지 여부도 반환합니다.
            담당자 : hwstar1204
        """,
        tags=["profile"],
    ),
)
class OtherProfileAPIView(APIView):
    def get(self, request, id):
        request_user = request.user
        user = CustomUser.objects.get_user_and_user_detail(id=id)
        data = {
            "nickname": user.nickname,
            "profile_image": user.profile_image,
            "coffee_life": user.user_detail.coffee_life,
            "follower_cnt": Relationship.objects.followers(user).count(),
            "following_cnt": Relationship.objects.following(user).count(),
            "post_cnt": user.post_set.count(),
            "is_user_following": Relationship.objects.check_relationship(request_user, user, "follow"),
        }

        serializer = UserProfileSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter(
                name="type",
                type=str,
                enum=["following", "follower"],
            ),
        ],
        responses={
            200: UserFollowListSerializer,
            400: OpenApiResponse(description="Bad Request"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="자신의 팔로잉/팔로워 프로필 조회",
        description="""
            사용자의 팔로잉/팔로워 리스트를 조회합니다.
            type 파라미터로 팔로잉/팔로워 리스트를 구분합니다.

            담당자 : hwstar1204
        """,
        tags=["follow"],
    )
)
class FollowListAPIView(APIView):
    def get(self, request):
        page = request.query_params.get("page", 1)
        follow_type = request.query_params.get("type")  # 쿼리 파라미터로 type을 받음
        user = request.user

        if follow_type == "following":
            data = get_following_list(user, True)
        elif follow_type == "follower":
            data = get_follower_list(user)
        else:
            return Response({"detail": "Invalid type parameter"}, status=status.HTTP_400_BAD_REQUEST)

        paginator = PageNumberPagination()
        paginator.page_size = 12
        page_obj = paginator.paginate_queryset(data, request)

        serializer = UserFollowListSerializer(page_obj, many=True)
        return paginator.get_paginated_response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter(
                name="type",
                type=str,
                enum=["following", "follower"],
            ),
        ],
        responses={
            200: UserFollowListSerializer,
            400: OpenApiResponse(description="Bad Request"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="사용자의 팔로잉/팔로워 리스트 조회",
        description="""
            특정 사용자의 팔로잉/팔로워 리스트를 조회합니다.
            id 파라미터로 사용자의 id를 받고,type 파라미터로 팔로잉/팔로워 리스트를 구분합니다.

            담당자 : hwstar1204
        """,
        tags=["follow"],
    ),
    post=extend_schema(
        responses=status.HTTP_201_CREATED,
        summary="팔로우",
        description="""
            특정 사용자를 팔로우합니다.
            이미 팔로우 중인 경우 409 CONFLICT

            담당자 : hwstar1204
        """,
        tags=["follow"],
    ),
    delete=extend_schema(
        responses=status.HTTP_200_OK,
        summary="팔로우 취소",
        description="""
            특정 사용자의 언팔로우합니다.
            팔로우 중이 아닌 경우 404 NOT FOUND

            담당자 : hwstar1204
        """,
        tags=["follow"],
    ),
)
class FollowListCreateDeleteAPIView(APIView):
    def get(self, request, id):
        follow_type = request.query_params.get("type")
        user = get_object_or_404(CustomUser, id=id)

        if follow_type == "following":
            data = get_following_list(user, False)
        elif follow_type == "follower":
            data = get_follower_list(user)
        else:
            return Response({"detail": "Invalid type parameter"}, status=status.HTTP_400_BAD_REQUEST)

        paginator = PageNumberPagination()
        paginator.page_size = 12
        page_obj = paginator.paginate_queryset(data, request)

        serializer = UserFollowListSerializer(page_obj, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, id):
        user = request.user
        follow_user = get_object_or_404(CustomUser, id=id)

        relationship, created = Relationship.objects.follow(user, follow_user)
        if not created:
            return Response({"error": "already following"}, status=status.HTTP_409_CONFLICT)
        return Response({"success": "follow"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        following_user = get_object_or_404(CustomUser, id=id)

        relationship, deleted = Relationship.objects.unfollow(user, following_user)
        if not deleted:
            return Response({"error": "not following"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": "unfollow"}, status=status.HTTP_200_OK)


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
            recommend_user_list.append({"user": user, "follower_cnt": Relationship.objects.followers(user).count()})

        serializer = BudyRecommendSerializer(recommend_user_list, many=True)
        category = random_true_category if true_categories else random_category
        response_data = {"users": serializer.data, "category": category}

        return Response(response_data, status=status.HTTP_200_OK)
