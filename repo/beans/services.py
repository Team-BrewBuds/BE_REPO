from typing import Dict

from django.db.models import Avg, Count, FloatField, QuerySet
from django.db.models.functions import Coalesce

from repo.beans.models import Bean, BeanTasteReview
from repo.common.exception.exceptions import NotFoundException
from repo.profiles.services import UserService


class BeanService:

    def __init__(self, bean_repository=None):
        self.bean_repository = bean_repository or Bean.objects
        self.user_service = UserService()

    def check_bean_exists(self, name: str) -> bool:
        """원두 존재 여부 확인"""
        return self.bean_repository.filter(name=name).exists()

    def search_beans_by_name(self, name: str) -> QuerySet[Bean]:
        """원두 이름 검색"""
        if not name:  # 검색어가 없어도 반환
            return self.bean_repository.all()

        return self.bean_repository.filter(name__icontains=name)

    def get_user_saved_beans(self, user_id: int) -> QuerySet[Bean]:
        """
        유저가 찜한 원두 조회 및 통계 정보 반환
        - 평균 평점 계산 (없는 경우 0)
        - 시음기록 수 포함
        """

        if not self.user_service.check_user_exists(user_id):
            raise NotFoundException(detail="유저가 존재하지 않습니다.", code="user_not_found")

        saved_beans = (
            self.bean_repository.filter(note__author_id=user_id)
            .prefetch_related("tastedrecord_set__taste_review")
            .annotate(
                avg_star=Coalesce(Avg("tastedrecord__taste_review__star"), 0, output_field=FloatField()),
                tasted_records_cnt=Count("tastedrecord"),
            )
            .values("id", "name", "origin_country", "roast_point", "avg_star", "tasted_records_cnt")
        )
        return saved_beans

    def create_bean(self, bean_data: Dict) -> Bean:
        """원두 생성"""

        bean, created = self.bean_repository.get_or_create(**bean_data)
        if created:
            # 새로운 원두 데이터는 모두 유저가 생성한 원두
            bean.is_user_created = True
            bean.save()
        return bean


class BeanTasteReviewService:

    def __init__(self, bean_taste_review_repository=None):
        self.bean_taste_review_repository = bean_taste_review_repository or BeanTasteReview.objects

    def create_bean_taste_review(self, bean_taste_review_data: Dict) -> BeanTasteReview:
        """원두 맛&평가 생성"""
        return self.bean_taste_review_repository.create(**bean_taste_review_data)
