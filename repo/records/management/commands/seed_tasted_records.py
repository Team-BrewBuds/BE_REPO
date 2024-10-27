from django.core.management.base import BaseCommand
from django_seed import Seed
from faker import Faker

from repo.beans.models import Bean, BeanTasteReview
from repo.profiles.models import CustomUser
from repo.records.models import TastedRecord


class Command(BaseCommand):
    help = "시음기록, 맛&평가 더미 데이터를 생성"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            default=10,
            type=int,
            help="시음기록, 맛&평가더미 데이터를 생성할 개수",
        )

    def handle(self, *args, **kwargs):
        number = kwargs["number"]
        seeder = Seed.seeder()
        faker = Faker(locale="ko_KR")

        # fmt: off
        flavor_choices = [
            "풍부한", "크리미한", "부드러움", "깔끔", "긴 여운", "화사한", "밸런스", "가벼운", "묵직", "산미",
            "상큼", "시트러스", "트로피칼", "베리", "꽃", "허브", "향신료", "주스같은", "차같은", "견과류",
            "고소", "쌉살", "시나몬", "스모키", "곡물", "달콤", "바닐라", "초콜릿", "카라멜"
        ]
        place_choices = ["집", "회사", "친구집", "공원", "도서관", "카페", "커피숍", "커피전문점", "커피마켓", "커피박람회"]

        seeder.add_entity(
            BeanTasteReview,
            number,
            {
                "flavor": lambda x: ",".join(faker.random_elements(elements=flavor_choices, length=3)),
                "body": lambda x: faker.random_int(min=0, max=5),
                "acidity": lambda x: faker.random_int(min=0, max=5),
                "bitterness": lambda x: faker.random_int(min=0, max=5),
                "sweetness": lambda x: faker.random_int(min=0, max=5),
                "star": lambda x: round(faker.pyfloat(left_digits=1, right_digits=1, positive=True, min_value=0.5, max_value=5) * 2) / 2,
                "place": lambda x: faker.random_choices(elements=place_choices, length=1)[0],
                "created_at": lambda x: faker.date_time_this_year(),
            },
        )

        inserted_pks = seeder.execute()
        self.stdout.write(self.style.SUCCESS(f"{number}개의 원두 맛&평가 생성 성공."))

        tasted_records = []
        for pk in inserted_pks[BeanTasteReview]:
            taste_review = BeanTasteReview.objects.get(pk=pk)
            tasted_record = TastedRecord.objects.create(
                author=faker.random_element(elements=CustomUser.objects.all()),  # 랜덤 사용자
                bean=faker.random_element(elements=Bean.objects.all()),  # 랜덤 원두
                taste_review=taste_review,  # 1대1 관계
                content=faker.paragraph(),
                view_cnt=faker.random_int(min=0, max=1000),
                is_private=faker.random_element(elements=(True, False)),
                created_at=faker.date_time_this_year(),
                tag=faker.word(),
            )
            tasted_records.append(tasted_record)

        self.stdout.write(self.style.SUCCESS(f"{number}개의 시음기록 생성 성공."))

        for tasted_record in tasted_records:
            random_liked_users = CustomUser.objects.order_by("?")[:number]
            liked_users = random_liked_users[: faker.random_int(min=0, max=len(random_liked_users) // 5)]
            tasted_record.like_cnt.set(liked_users)

        self.stdout.write(self.style.SUCCESS(f"{number}개의 시음기록 좋아요 생성 성공."))
