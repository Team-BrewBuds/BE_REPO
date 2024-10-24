from django.db import transaction

from ..models import Bean, BeanTasteReview


def update_bean(instance, bean_data):
    """Bean 데이터를 업데이트하거나 생성"""
    if bean_data:
        if instance.bean:
            for attr, value in bean_data.items():
                setattr(instance.bean, attr, value)
            instance.bean.save()
        else:
            instance.bean = Bean.objects.create(**bean_data)


def update_taste_review(instance, taste_review_data):
    """TasteReview 데이터를 업데이트하거나 생성"""
    if taste_review_data:
        if instance.taste_review:
            for attr, value in taste_review_data.items():
                setattr(instance.taste_review, attr, value)
            instance.taste_review.save()
        else:
            instance.taste_review = BeanTasteReview.objects.create(**taste_review_data)


def update_photos(instance, photos):
    instance.photo_set.set(photos)


def update_other_fields(instance, validated_data):
    """나머지 필드를 업데이트"""
    for attr, value in validated_data.items():
        setattr(instance, attr, value)
    instance.save()


@transaction.atomic
def update_tasted_record(instance, validated_data):
    """TastedRecord 객체를 트랜잭션으로 업데이트"""
    update_bean(instance, validated_data.pop("bean", None))
    update_taste_review(instance, validated_data.pop("taste_review", None))
    update_photos(instance, validated_data.pop("photos", []))
    update_other_fields(instance, validated_data)
    instance.save()
    return instance
