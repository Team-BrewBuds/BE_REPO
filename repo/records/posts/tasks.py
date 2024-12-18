from datetime import timedelta

from celery import shared_task
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone

from repo.records.models import Post
from repo.records.posts.serializers import TopPostSerializer

# from django.utils.log import get_logger
# logger = get_logger(__name__)

subjects = ["normal", "cafe", "bean", "info", "question", "worry", "gear"]
CACHE_TTL = 60 * 60 * 24 * 7  # 1주일
TOP_POST_COUNT = 60


@shared_task(name="repo.records.posts.tasks.cache_top_posts", bind=True, default_retry_delay=10, max_retries=3)
def cache_top_posts(self):
    try:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        base_query = (
            Post.objects.filter(created_at__range=(start_date, end_date))
            .select_related("author")
            .annotate(
                likes=Count("like_cnt", distinct=True),
                comments=Count("comment", distinct=True),
            )
        )

        # 전체 주제
        cache_key = "top_posts::weekly"
        posts = base_query.order_by("-view_cnt")[:TOP_POST_COUNT]
        serialized_posts = TopPostSerializer(posts, many=True).data
        cache.set(cache_key, serialized_posts, timeout=CACHE_TTL)

        # 각 주제
        for subject in subjects:
            posts = base_query.filter(subject=subject).order_by("-view_cnt")[:TOP_POST_COUNT]
            serialized_posts = TopPostSerializer(posts, many=True).data
            cache_key = f"top_posts:{subject}:weekly"
            cache.set(cache_key, serialized_posts, timeout=CACHE_TTL)
            print(f"{subject} 주제 인기 게시글 상위 60개 캐싱 완료")

        print("Top posts cache updated successfully")
    except Exception as e:
        print(f"Failed to update top posts cache: {str(e)}")
        raise
