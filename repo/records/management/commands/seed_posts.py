from django.core.management.base import BaseCommand
from django_seed import Seed
from faker import Faker

from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord


class Command(BaseCommand):
    help = "게시글 더미 데이터를 생성"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            default=5,
            type=int,
            help="게시글 더미 데이터를 생성할 개수",
        )

    def handle(self, *args, **kwargs):
        number = kwargs["number"]
        seeder = Seed.seeder()
        faker = Faker(locale="ko_KR")
        seeder.add_entity(
            Post,
            number,
            {
                "author": lambda x: faker.random_element(elements=CustomUser.objects.all()),
                "title": lambda x: faker.sentence(),
                "content": lambda x: faker.paragraph(),
                "view_cnt": lambda x: faker.random_int(min=0, max=1000),
                "created_at": lambda x: faker.date_time_this_year(),
                "tag": lambda x: faker.word(),
            },
        )

        inserted_pk = seeder.execute()
        self.stdout.write(self.style.SUCCESS(f"{number}개의 게시글 생성 성공."))

        for pk in inserted_pk[Post]:
            post = Post.objects.get(pk=pk)

            random_tasted_records = TastedRecord.objects.order_by("?")
            tasted_records = random_tasted_records[: faker.random_int(min=0, max=5)]
            post.tasted_records.set(tasted_records)

            random_liked_users = CustomUser.objects.order_by("?")
            liked_users = random_liked_users[: faker.random_int(min=0, max=len(random_liked_users) // 5)]
            post.like_cnt.set(liked_users)

        self.stdout.write(self.style.SUCCESS(f"{number}개의 게시글 좋아요 생성 성공."))
