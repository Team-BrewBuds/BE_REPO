from collections import Counter, defaultdict
from datetime import datetime

import jwt
import requests
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.naver import views as naver_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count, F
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from repo.beans.models import Bean
from repo.beans.services import BeanService
from repo.common.utils import get_first_photo_url, get_paginated_response_with_class
from repo.interactions.note.models import Note
from repo.profiles.models import CustomUser, UserDetail
from repo.profiles.schemas import *
from repo.profiles.serializers import (
    PrefCountrySerializer,
    PrefFlavorSerializer,
    PrefPostSerializer,
    PrefSavedBeanSerializer,
    PrefStarSerializer,
    PrefSummarySerializer,
    PrefTastedRecordSerializer,
    UserDetailSignupSerializer,
    UserProfileSerializer,
    UserSignupSerializer,
    UserUpdateSerializer,
)
from repo.profiles.services import UserService
from repo.records.models import Post, TastedRecord
from repo.records.serializers import UserNoteSerializer

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
                    "access": access_token,
                    "refresh": str(refresh),
                    "user": {
                        "pk": user.pk,
                        "email": user_email,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except jwt.DecodeError:
            return Response({"detail": "Invalid id_token."}, status=status.HTTP_400_BAD_REQUEST)


class CheckNicknameView(APIView):
    """
    사용자의 nickname이 저장되었는지 확인하는 API
    Args:
        request: 클라이언트 요청.
    Returns:
        JSON 응답: 사용자 nickname 저장 여부.
    담당자: blakej2432
    """

    # permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.nickname:
            return Response({"nickname_saved": True, "nickname": user.nickname}, status=200)
        else:
            return Response(status=204)


class DuplicateNicknameCheckView(APIView):
    """
    닉네임 중복 여부 확인 API
    Args:
        request: 사용자가 입력한 닉네임(?nickname=new_user123)을 받아 중복 여부 확인
    Returns:
        JSON 응답:
            - 닉네임이 사용 가능하면 {"is_available": true}
            - 닉네임이 중복되면 {"is_available": false, "message": "이미 사용 중인 닉네임입니다."}
    담당자: blakej2432
    """

    def get(self, request):
        nickname = request.GET.get("nickname", "").strip()

        if not nickname:
            return Response({"error": "닉네임을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        is_available = not CustomUser.objects.filter(nickname=nickname).exists()

        if is_available:
            return Response({"is_available": True}, status=status.HTTP_200_OK)
        else:
            return Response({"is_available": False, "message": "이미 사용 중인 닉네임입니다."}, status=status.HTTP_200_OK)


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


@ProfileSchema.my_profile_schema_view
class MyProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        self.user_service = UserService()

    def get(self, request):
        user = request.user
        profile = self.user_service.get_user_profile(user)

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request):
        user = request.user
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user_validated_data = serializer.validated_data
        self.user_service.update_user(user, user_validated_data)

        serializer = UserUpdateSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({"message": "계정이 성공적으로 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)


@OtherProfileSchema.other_proflie_schema_view
class OtherProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        self.user_service = UserService()

    def get(self, request, id):
        user_id = request.user.id
        other_user_id = id
        data = self.user_service.get_other_user_profile(user_id, other_user_id)

        serializer = UserProfileSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@UserNoteSchema.user_note_schema_view
class UserNoteAPIView(APIView):
    def get(self, request, id):
        user = get_object_or_404(CustomUser, id=id)
        notes = user.note_set.filter(bean__isnull=True).select_related("post", "tasted_record")

        notes_with_photos = []
        for note in notes:
            note.photo_url = get_first_photo_url(note.post if note.post else note.tasted_record)
            notes_with_photos.append(note)

        return get_paginated_response_with_class(request, notes_with_photos, UserNoteSerializer)


class PrefSummaryView(APIView):
    """
    활동요약 API
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user_stats = (
            CustomUser.objects.filter(id=user_id)
            .annotate(tasted_record_cnt=Count("tastedrecord"), post_cnt=Count("post"), saved_notes_cnt=Count("note", distinct=True))
            .first()
        )

        bean_service = BeanService()
        saved_beans_cnt = bean_service.get_user_saved(user_id).count()

        serializer = PrefSummarySerializer(user_stats)
        response_data = serializer.data
        response_data["saved_beans_cnt"] = saved_beans_cnt

        return Response(response_data, status=status.HTTP_200_OK)


class PrefCalendarAPIView(APIView):
    """
    활동 캘린더 API
    - 특정 유저의 특정 월 시음 기록을 날짜별로 그룹화하여 반환
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        now = datetime.now()
        year = int(request.query_params.get("year", now.year))
        month = int(request.query_params.get("month", now.month))
        activity_type = request.query_params.get("type", "tasted_record")

        user = get_object_or_404(CustomUser, id=user_id)

        search_result = defaultdict(list)
        category = "tasted_record"

        if activity_type == "tasted_record":
            records = (
                TastedRecord.objects.filter(author=user, created_at__year=year, created_at__month=month)
                .annotate(
                    created_date=TruncDate("created_at"),
                    total_count=Count("id"),
                    star=F("taste_review__star"),
                    flavor=F("taste_review__flavor"),
                )
                .order_by("created_date")
            )

            serializer = PrefTastedRecordSerializer(records, many=True)

            for record in serializer.data:
                search_result[record["created_date"]].append(record)

            category = "tasted_record"

        elif activity_type == "post":
            posts = (
                Post.objects.filter(author=user, created_at__year=year, created_at__month=month)
                .annotate(created_date=TruncDate("created_at"))
                .order_by("created_date")
            )

            serializer = PrefPostSerializer(posts, many=True)

            for post in serializer.data:
                search_result[post["created_date"]].append(post)

            category = "post"

        elif activity_type == "saved_bean":
            saved_beans = (
                Bean.objects.filter(note__author=user, note__created_at__year=year, note__created_at__month=month)
                .annotate(
                    created_date=TruncDate("note__created_at"),
                    avg_star=Avg("tastedrecord__taste_review__star", default=0),
                )
                .distinct()
                .order_by("created_date")
            )

            serializer = PrefSavedBeanSerializer(saved_beans, many=True)

            for saved_bean in serializer.data:
                search_result[saved_bean["created_date"]].append(saved_bean)

            category = "saved_bean"

        elif activity_type == "saved_note":
            search_result = defaultdict(lambda: defaultdict(list))
            saved_notes = (
                Note.objects.filter(author=user, created_at__year=year, created_at__month=month)
                .annotate(note_date=TruncDate("created_at"))
                .values("id", "note_date", "tasted_record_id", "post_id")
            )

            tasted_record_ids = [note["tasted_record_id"] for note in saved_notes if note["tasted_record_id"]]
            post_ids = [note["post_id"] for note in saved_notes if note["post_id"]]
            note_dates = {note["tasted_record_id"]: note["note_date"] for note in saved_notes if note["tasted_record_id"]}
            note_dates.update({note["post_id"]: note["note_date"] for note in saved_notes if note["post_id"]})

            saved_tasted_records = (
                TastedRecord.objects.filter(id__in=tasted_record_ids)
                .annotate(
                    created_date=TruncDate("created_at"),
                    total_count=Count("id"),
                    star=F("taste_review__star"),
                    flavor=F("taste_review__flavor"),
                )
                .order_by("created_date")
            )
            tr_serializer = PrefTastedRecordSerializer(saved_tasted_records, many=True)
            for record in tr_serializer.data:
                note_date = str(note_dates.get(record["id"], "unknown"))
                record["note_date"] = note_date
                search_result["tasted_record"][note_date].append(record)

            saved_posts = Post.objects.filter(id__in=post_ids).annotate(created_date=TruncDate("created_at")).order_by("created_date")
            post_serializer = PrefPostSerializer(saved_posts, many=True)
            for post in post_serializer.data:
                note_date = str(note_dates.get(post["id"], "unknown"))
                post["note_date"] = note_date
                search_result["post"][note_date].append(post)

            category = "saved_note"

        response_data = {
            f"{category}": search_result,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class PrefStarAPIView(APIView):
    """
    유저의 별점 분포 API
    """

    # permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)

        star_distribution_query = (
            TastedRecord.objects.filter(author=user).values(star=F("taste_review__star")).annotate(count=Count("id")).order_by("star")
        )

        avg_star = TastedRecord.objects.filter(author=user).aggregate(avg_star=Avg("taste_review__star"))["avg_star"]
        avg_star = round(avg_star, 1) if avg_star is not None else 0

        total_ratings = TastedRecord.objects.filter(author=user).count()

        most_common_star = None
        if star_distribution_query:
            most_common_star = max(star_distribution_query, key=lambda x: x["count"])["star"]

        stars = {round(i * 0.5, 1): 0 for i in range(1, 11)}

        for entry in star_distribution_query:
            stars[entry["star"]] = entry["count"]

        serializer = PrefStarSerializer(
            data={"star_distribution": stars, "most_common_star": most_common_star, "avg_star": avg_star, "total_ratings": total_ratings}
        )
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)


class PrefFlavorAPIView(APIView):
    """
    유저의 선호하는 맛 API
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        self.bean_service = BeanService()

    def get(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)

        records = TastedRecord.objects.filter(author=user).select_related("taste_review")

        if not records.exists():
            return Response({"top_flavors": []})

        flavors = records.values_list("taste_review__flavor", flat=True)
        top_flavors = self.bean_service.get_flavor_percentages(flavors)

        serializer = PrefFlavorSerializer(data={"top_flavors": top_flavors})
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)


class PrefCountryAPIView(APIView):
    """
    유저의 선호하는 원산지 API
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        records = TastedRecord.objects.filter(author=user).select_related("bean")

        if not records.exists():
            return Response({"top_origins": []})

        origins = [origin for origin in records.values_list("bean__origin_country", flat=True) if origin]
        origin_counter = Counter(origins)

        total_origin_count = sum(origin_counter.values())

        top_origins = [
            {"origin": origin, "percentage": round((count / total_origin_count) * 100, 2)}
            for origin, count in origin_counter.most_common(5)
        ]

        serializer = PrefCountrySerializer(data={"top_origins": top_origins})
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)


class UserAccountInfoView(APIView):
    """
    사용자 계정 정보 조회 API

    - 가입일 (YYYY년 MM월 DD일)
    - 가입 기간 (000일째)
    - 로그인 유형 변환
    - 성별 변환
    - 태어난 연도
    """

    def get(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)

        # 가입일 변환 (변환 없이 그대로 사용)
        joined_date_str = user.created_at.strftime("%Y년 %m월 %d일")

        # 가입 기간 계산 (오늘 날짜 - 가입일)
        today = datetime.now().date()
        days_since_joined = (today - user.created_at.date()).days
        joined_duration = f"{days_since_joined}일째"

        login_type = dict(CustomUser.login_type_choices).get(user.login_type, "알 수 없음")
        gender = dict(CustomUser.gender_choices).get(user.gender, "미입력")
        birth_year = user.birth if user.birth else "미입력"

        data = {
            "가입일": joined_date_str,
            "가입기간": joined_duration,
            "로그인 유형": login_type,
            "성별": gender,
            "태어난 연도": birth_year,
        }

        return Response(data, status=status.HTTP_200_OK)
