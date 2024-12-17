from django.core.management.base import BaseCommand
from faker import Faker

from repo.beans.models import Bean
from repo.interactions.note.models import Note
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord


class Command(BaseCommand):
    help = "사용자가 저장한 노트 더미 데이터를 생성"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            default=10,
            type=int,
            help="사용자가 저장한 노트 데이터를 생성할 개수 (number * 3)",
        )

    def handle(self, *args, **kwargs):
        number = kwargs["number"]
        faker = Faker(locale="ko_KR")

        # post와 연결된 노트 생성
        for _ in range(number // 5):
            Note.objects.create(
                author=faker.random_element(elements=CustomUser.objects.all()),
                post=faker.random_element(elements=Post.objects.all()),
                tasted_record=None,
                bean=None,
                created_at=faker.date_time_this_year(),
            )

        # tasted_record와 연결된 노트 생성
        for _ in range(number // 5):
            Note.objects.create(
                author=faker.random_element(elements=CustomUser.objects.all()),
                post=None,
                tasted_record=faker.random_element(elements=TastedRecord.objects.all()),
                bean=None,
                created_at=faker.date_time_this_year(),
            )

        # bean과 연결된 노트 생성
        for _ in range(number // 5):
            Note.objects.create(
                author=faker.random_element(elements=CustomUser.objects.all()),
                post=None,
                tasted_record=None,
                bean=faker.random_element(elements=Bean.objects.all()),
                created_at=faker.date_time_this_year(),
            )

        # 총 생성된 노트의 개수를 출력
        self.stdout.write(self.style.SUCCESS(f"{(number // 5) * 3}개의 저장한 노트 생성 성공."))
