from django.db import transaction
from django.db.models import Count, Prefetch

from repo.beans.services import BeanService
from repo.profiles.services import UserService
from repo.records.models import BeanTasteReview, Photo, TastedRecord


class TastedRecordService:

    def __init__(self, tasted_record_repository=None):
        self.tasted_record_repository = tasted_record_repository or TastedRecord.objects
        self.bean_service = BeanService()
        self.user_service = UserService()

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

    def get_record_detail(self, pk):
        return (
            TastedRecord.objects.select_related("author", "bean", "taste_review")
            .prefetch_related(
                Prefetch("photo_set", queryset=Photo.objects.only("photo_url")),
            )
            .get(pk=pk)
        )

    def get_user_tasted_records(self, user_id):
        user = self.user_service.get_user_by_id(user_id)
        return (
            user.tastedrecord_set.select_related("bean", "taste_review")
            .prefetch_related("like_cnt", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .only("id", "bean__name", "taste_review__star", "created_at", "like_cnt")
            .annotate(
                likes=Count("like_cnt", distinct=True),
            )
        )
