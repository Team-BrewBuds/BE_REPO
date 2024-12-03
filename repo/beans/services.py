from typing import Dict

from django.db.models import Avg, Count, FloatField, QuerySet
from django.db.models.functions import Coalesce

from repo.beans.models import Bean
from repo.common.exception.exceptions import NotFoundException
from repo.profiles.models import CustomUser
from repo.profiles.services import UserService


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
            .values("id", "name", "origin_country", "roast_point", "avg_star", "tasted_records_cnt")
        )
        return saved_beans

    def create(self, bean_data: Dict) -> Bean:
        """원두 생성"""

        bean, created = Bean.objects.get_or_create(**bean_data)
        if created:
            # 새로운 원두 데이터는 모두 유저가 생성한 원두
            bean.is_user_created = True
            bean.save()
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
