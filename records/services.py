from itertools import chain
from django.core.paginator import Paginator
from .models import Tasted_Record, Photo
from django.db.models import Prefetch

# TODO : user 인자를 받아서 팔로우한 사용자의 시음 기록만 가져오기(추후 이것으로 변경)
def get_tasted_record_feed(user, page=1):
    following_users = user.following.all()

    followed_records = Tasted_Record.objects.filter(
        user__in=following_users, is_private=False
    ).select_related(
        'user', 'bean', 'taste_and_review'
    ).prefetch_related(
        Prefetch('photo_set', queryset=Photo.objects.only('photo_url'))
    ).order_by('-created_at')

    if not following_users.exists() or followed_records.count() < 10:
        additional_records = Tasted_Record.objects.filter(
            is_private=False
        ).exclude(
            user__in=following_users
        ).select_related(
            'user', 'bean', 'taste_and_review'
        ).prefetch_related(
            Prefetch('photo_set', queryset=Photo.objects.only('photo_url'))
        ).order_by('-created_at')
    else:
        additional_records = Tasted_Record.objects.none()

    all_records = list(chain(followed_records, additional_records))

    paginator = Paginator(all_records, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()

def get_tasted_record_feed2(user, page=1):
    records = Tasted_Record.objects.filter(
         is_private=False
    ).select_related(
        'user', 'bean', 'taste_and_review'
    ).prefetch_related(
        Prefetch('photo_set', queryset=Photo.objects.only('photo_url'))
    ).order_by('-created_at')

    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()

def get_tasted_record_detail(record_id):
    record = Tasted_Record.objects.filter(pk=record_id).select_related(
        'user', 'bean', 'taste_and_review'
    ).prefetch_related(
        Prefetch('photo_set', queryset=Photo.objects.only('photo_url')),
    ).first()

    return record