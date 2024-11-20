import logging
import time

from django.db import connection

logger = logging.getLogger("performance")


class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        if request.path.startswith("/"):
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
