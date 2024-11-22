from django.db import transaction

from repo.beans.services import BeanService
from repo.records.models import BeanTasteReview, TastedRecord


class TastedRecordService:

    def __init__(self, tasted_record_repository=None):
        self.tasted_record_repository = tasted_record_repository or TastedRecord.objects
        self.bean_service = BeanService()

    @transaction.atomic
    def create(self, user, validated_data):
        """TastedRecord 생성"""

        bean = self.bean_service.create(validated_data["bean"])

        taste_review = BeanTasteReview.objects.create(**validated_data["taste_review"])

        tasted_record = self.tasted_record_repository.create(
            author=user,
            bean=bean,
            taste_review=taste_review,
            content=validated_data["content"],
        )

        photos = validated_data.get("photos", [])
        tasted_record.photo_set.set(photos)

        return tasted_record

    @transaction.atomic
    def update(self, instance, validated_data):
        """TastedRecord 업데이트"""

        if bean_data := validated_data.pop("bean", None):
            bean = self.bean_service.update(bean_data, instance.author)
            instance.bean = bean

        if taste_review_data := validated_data.pop("taste_review", None):
            taste_review, _ = BeanTasteReview.objects.update_or_create(
                id=instance.taste_review_id,
                defaults=taste_review_data,
            )
            instance.taste_review = taste_review

        if photos := validated_data.pop("photos", None):
            instance.photo_set.set(photos)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
