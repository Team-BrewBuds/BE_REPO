from django.core.management.base import BaseCommand
from django_seed import Seed
from faker import Faker

from repo.profiles.models import CustomUser
from repo.records.models import Comment, Post, TastedRecord


class Command(BaseCommand):
    help = "댓글 더미 데이터를 생성"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            default=10,
            type=int,
            help="댓글 더미 데이터를 생성할 개수",
        )

    def handle(self, *args, **kwargs):
        number = kwargs["number"]
        seeder = Seed.seeder()
        faker = Faker(locale="ko_KR")

        # 댓글 생성, 대댓글 무작위로 추가
        comments = []

        for _ in range(number // 2):
            # 무작위로 post 또는 tasted_record에 연결
            if faker.boolean():
                post = faker.random_element(elements=Post.objects.all())
                tasted_record = None
            else:
                post = None
                tasted_record = faker.random_element(elements=TastedRecord.objects.all())

            # 부모 댓글 생성
            parent_comment = Comment.objects.create(
                parent=None,
                author=faker.random_element(elements=CustomUser.objects.all()),
                post=post,
                tasted_record=tasted_record,
                content=faker.paragraph(),
                created_at=faker.date_time_this_year(),
            )
            comments.append(parent_comment)

            # 자식 댓글(대댓글) 생성 (깊이는 1로 제한)
            if faker.boolean():
                child_comment = Comment.objects.create(
                    parent=parent_comment,  # 부모 댓글과 연결
                    author=faker.random_element(elements=CustomUser.objects.all()),
                    post=post,
                    tasted_record=tasted_record,
                    content=faker.paragraph(),
                    created_at=faker.date_time_this_year(),
                )
                comments.append(child_comment)

        self.stdout.write(self.style.SUCCESS(f"{len(comments)}개의 댓글(대댓글 포함) 생성 성공."))

        for comment in comments:
            # 무작위로 좋아요 누르기
            if faker.boolean():
                random_liked_users = CustomUser.objects.order_by("?")
                liked_users = random_liked_users[: faker.random_int(min=0, max=len(random_liked_users) // 5)]
                comment.like_cnt.set(liked_users)
        self.stdout.write(self.style.SUCCESS("댓글 좋아요 생성 성공."))
