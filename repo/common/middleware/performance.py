import logging
import time

from django.db import connection

logger = logging.getLogger("performance")

# 공격 시도 경로
ATTACK_PATHS = [
    "/wp-",
    "/xmlrpc.php",
    "/.env",
    "/.git",
    "/phpmyadmin",
    "/pma",
    "/admin.php",
    "/about.php",
    "/phpinfo",
    "/info.php",
    "/.aws",
    "/.docker",
    "/actuator",
    "/config/aws",
    "/.well-known/security.txt",
]

LEGITIMATE_BOT_PATHS = [
    "/robots.txt",
    "/sitemap.xml",
    "/favicon.ico",
]

SUSPICIOUS_PATHS = ATTACK_PATHS + LEGITIMATE_BOT_PATHS

# PHP 파일 확장자
SUSPICIOUS_EXTENSIONS = [".php", ".asp", ".aspx", ".jsp"]


class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        # 의심스러운 경로 체크
        is_suspicious = any(request.path.startswith(path) or path in request.path for path in SUSPICIOUS_PATHS)

        # 의심스러운 확장자 체크
        has_suspicious_ext = any(request.path.endswith(ext) for ext in SUSPICIOUS_EXTENSIONS)

        # 404 응답이면서 의심스러운 경로/확장자는 로깅 제외
        should_skip_log = response.status_code == 404 and (is_suspicious or has_suspicious_ext)

        if not should_skip_log:
            log_message = (
                f"[Performance] "
                f"Method: {request.method} | "
                f"Path: {request.path} | "
                f"Duration: {duration:.4f}s | "
                f"DB Queries: {len(connection.queries)} | "
                f"Status: {response.status_code}"
            )
            logger.info(log_message)

        return response
