from config.settings._base import env

# Kakao 관련 설정
KAKAO_REST_API_KEY = env.str("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = env.str("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = env.str("KAKAO_REDIRECT_URI")

# naver 관련 설정
NAVER_CLIENT_ID = env.str("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = env.str("NAVER_CLIENT_SECRET")
NAVER_REDIRECT_URI = env.str("NAVER_REDIRECT_URI")


# Kakao 관련 설정
SOCIALACCOUNT_PROVIDERS = {
    "kakao": {
        "APP": {
            "client_id": KAKAO_REST_API_KEY,
            "secret": KAKAO_CLIENT_SECRET,
            "key": "",
        }
    },
    "naver": {
        "APP": {
            "client_id": NAVER_CLIENT_ID,
            "secret": NAVER_CLIENT_SECRET,
            "key": "",
        }
    },
}

LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
