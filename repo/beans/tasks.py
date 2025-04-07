from datetime import timedelta

from celery import shared_task
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone

from repo.beans.serializers import BeanRankingSerializer
from repo.records.models import TastedRecord

CACHE_TTL = 60 * 60 * 24 * 7  # 1주일
TOP_BEAN_RANK_COUNT = 10


@shared_task(name="repo.beans.tasks.cache_top_beans", bind=True, default_retry_delay=10, max_retries=3)
def cache_top_beans(self):
    try:
        one_week_ago = timezone.now() - timedelta(days=7)

        top_beans = (
            TastedRecord.objects.filter(created_at__gte=one_week_ago, bean__is_official=True)  # 공식 원두만
            .select_related("bean")
            .values("bean_id", "bean__name")
            .annotate(record_count=Count("id"))
            .order_by("-record_count")[:TOP_BEAN_RANK_COUNT]
        )

        serialized_beans = BeanRankingSerializer(top_beans, many=True).data
        cache.set("top_beans:weekly", serialized_beans, timeout=CACHE_TTL)
        print("Top beans cached successfully.")
    except Exception as e:
        print(f"Failed to cache top beans: {str(e)}")
        raise
