from datetime import datetime

import pandas as pd
from django.core.management.base import BaseCommand
from faker import Faker

from repo.admins.utils import (
    create_user_and_user_detail,
    pre_process_create_user,
)
from repo.profiles.models import CustomUser
from repo.records.models import Post

DATETIME_NOW = datetime.now()
FILE_PATH = ""  # 게시글 데이터 파일 경로
PROFILE_PHOTOS_DIR_PATH = ""  # 프로필 사진 데이터 파일 경로
POST_SUBJECT_CHOICES = {v: k for k, v in Post.SUBJECT_TYPE_CHOICES}


class Command(BaseCommand):
    help = "게시글 더미 데이터를 생성"

    def handle(self, *args, **kwargs):
        faker = Faker(locale="ko_KR")

        # 1. 작성자 생성 (없으면 미리 생성)
        create_user_cnt = pre_process_create_user(FILE_PATH, faker, PROFILE_PHOTOS_DIR_PATH)

        # 2. 게시글 생성
        post_cnt = create_post(FILE_PATH, faker)

        self.stdout.write(self.style.SUCCESS(f"{create_user_cnt}명의 작성자 생성 성공."))
        self.stdout.write(self.style.SUCCESS(f"{post_cnt}개의 게시글 생성 성공."))


def create_post(file_path: str, faker: Faker) -> int:
    df = pd.read_csv(file_path)

    posts = []
    for _, row in df.iterrows():
        try:
            author = CustomUser.objects.get(nickname=row["작성자"])
        except CustomUser.DoesNotExist:
            author = create_user_and_user_detail(row["작성자"], faker, PROFILE_PHOTOS_DIR_PATH)

        posts.append(
            Post(
                author=author,
                subject=POST_SUBJECT_CHOICES[row["주제"]],
                title=row["제목"],
                content=row["내용"],
                tag=row["태그"],
            )
        )

    Post.objects.bulk_create(posts)
    return len(posts)
