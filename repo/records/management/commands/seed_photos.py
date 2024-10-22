from django.core.management.base import BaseCommand
from django_seed import Seed
from faker import Faker

from repo.records.models import Photo, Post, TastedRecord


class Command(BaseCommand):
    help = "사진 더미 데이터를 생성"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            default=10,
            type=int,
            help="사진 더미 데이터를 생성할 개수",
        )

    def handle(self, *args, **kwargs):
        number = kwargs["number"]
        seeder = Seed.seeder()
        faker = Faker()

        for _ in range(number):
            if faker.boolean():  # 게시글, 시음 기록 사진 랜덤 구별 생성
                # 게시글 사진 생성
                seeder.add_entity(
                    Photo,
                    1,
                    {
                        "post": lambda x: faker.random_element(elements=Post.objects.all()),
                        "tasted_record": None,
                        "photo_url": lambda x: faker.image_url(width=360, height=360),
                        "created_at": lambda x: faker.date_time_this_year(),
                    },
                )
            else:
                # 시음기록 사진 생성
                seeder.add_entity(
                    Photo,
                    1,
                    {
                        "post": None,
                        "tasted_record": lambda x: faker.random_element(elements=TastedRecord.objects.all()),
                        "photo_url": lambda x: faker.image_url(width=360, height=360),
                        "created_at": lambda x: faker.date_time_this_year(),
                    },
                )

        seeder.execute()
        self.stdout.write(self.style.SUCCESS(f"{number}개의 사진 생성 성공."))
