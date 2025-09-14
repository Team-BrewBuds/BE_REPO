import logging
from collections import Counter
from typing import Dict

from django.core.cache import cache
from django.db.models import Avg, Count, FloatField, QuerySet
from django.db.models.functions import Coalesce
from django.utils import timezone
from redis.exceptions import ConnectionError

from repo.beans.models import Bean
from repo.beans.tasks import TOP_BEAN_RANK_COUNT, cache_top_beans
from repo.common.exception.exceptions import NotFoundException
from repo.profiles.models import CustomUser
from repo.profiles.services import UserService
from repo.records.models import TastedRecord

logger = logging.getLogger(__name__)


class BeanService:

    def __init__(self):
        self.user_service = UserService()

    def exists_by_name(self, name: str) -> bool:
        """원두 존재 여부 확인"""
        return Bean.objects.filter(name=name).exists()

    def exists_by_data(self, bean_data: Dict) -> bool:
        """원두 존재 여부 확인"""
        return Bean.objects.filter(**bean_data).exists()

    def search_by_name(self, name: str) -> QuerySet[Bean]:
        """원두 이름 검색"""
        if not name:  # 검색어가 없어도 반환
            return Bean.objects.all()

        return Bean.objects.filter(name__icontains=name)

    def get_user_saved(self, user_id: int) -> QuerySet[Bean]:
        """
        유저가 찜한 원두 조회 및 통계 정보 반환
        - 평균 평점 계산 (없는 경우 0)
        - 시음기록 수 포함
        """

        if not self.user_service.check_user_exists(user_id):
            raise NotFoundException(detail="유저가 존재하지 않습니다.", code="user_not_found")

        saved_beans = (
            Bean.objects.filter(note__author_id=user_id)
            .prefetch_related("tastedrecord_set__taste_review")
            .annotate(
                avg_star=Coalesce(Avg("tastedrecord__taste_review__star"), 0, output_field=FloatField()),
                tasted_records_cnt=Count("tastedrecord"),
            )
            .values("id", "name", "origin_country", "roast_point", "bean_type", "avg_star", "tasted_records_cnt")
        )
        return saved_beans

    def create(self, bean_data: Dict) -> Bean:
        """원두 생성"""

        bean = Bean.objects.filter(**bean_data).first()
        if not bean:
            bean = Bean.objects.create(**bean_data)
        return bean

    def update(self, bean_data: Dict, user: CustomUser) -> Bean:
        """원두 데이터 수정"""

        if user.is_staff:
            # 관리자만 원두 데이터 수정 가능
            return Bean.objects.update(**bean_data)
        else:
            # 사용자는 원두 데이터를 직접 수정할 수 없고 조회 또는 생성만 가능함
            return self.get_or_create(bean_data)

    def get_or_create(self, bean_data: Dict) -> Bean:
        """원두 조회 또는 생성"""

        if self.exists_by_data(bean_data):
            return Bean.objects.get(**bean_data)
        else:
            return self.create(bean_data)

    @staticmethod
    def get_flavor_percentages(flavors: list[str], limit: int = None) -> list[dict[str, str | int]]:
        split_flavors = []
        for flavor_str in flavors:
            if flavor_str:
                fs = [i.strip() for i in flavor_str.split(",")]
                split_flavors.extend(fs)  # 쉼표 기준 맛 분리

        flavor_counter = Counter(split_flavors)
        flavor_items = flavor_counter.most_common(limit)

        if limit:
            total_flavor_count = sum(count for _, count in flavor_items)
        else:
            total_flavor_count = flavor_counter.total()

        top_flavors = []
        for flavor, count in flavor_items:
            percent = round((count / total_flavor_count) * 100)
            top_flavors.append({"flavor": flavor, "percentage": percent})

        total_percent = sum(flavor["percentage"] for flavor in top_flavors)
        if total_percent != 100:
            diff = 100 - total_percent
            top_flavors[0]["percentage"] += diff

        return top_flavors


class BeanRankingService:
    def __init__(self):
        self.cache_key = "top_beans:weekly"

    def get_top_weekly_beans(self):
        """레디스 기반 상위 원두 반환. 없을 시 DB 직접 조회."""
        try:
            cached_data = cache.get(self.cache_key)

            if not cached_data:
                cache_top_beans.delay()
                return self._get_top_beans_from_db()

            return cached_data
        except ConnectionError as e:
            logger.error(f"Redis 연결 실패 bean_list: {str(e)}", exc_info=True)
            return self._get_top_beans_from_db()

    def _get_top_beans_from_db(self):
        """레디스 실패 시 직접 DB에서 조회"""
        one_week_ago = timezone.now() - timezone.timedelta(days=7)

        top_beans = (
            TastedRecord.objects.filter(created_at__gte=one_week_ago, bean__is_official=True)
            .select_related("bean")
            .values("bean_id", "bean__name", "bean__bean_type", "bean__roast_point")
            .annotate(record_count=Count("id"))
            .order_by("-record_count")[:TOP_BEAN_RANK_COUNT]
        )

        return top_beans
