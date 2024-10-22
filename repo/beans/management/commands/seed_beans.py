from django.core.management.base import BaseCommand
from django_seed import Seed
from faker import Faker

from repo.beans.models import Bean


class Command(BaseCommand):
    help = "원두 더미 데이터를 생성"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            default=5,
            type=int,
            help="원두 더미 데이터를 생성할 개수",
        )

    def handle(self, *args, **kwargs):
        number = kwargs["number"]
        seeder = Seed.seeder()
        faker = Faker(locale="ko_KR")

        extraction_choices = [
            "핸드 드립",
            "에스프레소 머신" "커피메이커",
            "모카포트",
            "프랜치프레스",
            "에어로프레스",
            "콜드브루",
        ]
        process_choices = ["내추럴", "위시드", "펄프드 내추럴", "허니", "무산소 발효"]

        seeder.add_entity(
            Bean,
            number,
            {
                "bean_type": lambda x: faker.random_element(elements=("single", "blend")),
                "is_decaf": lambda x: faker.random_element(elements=(True, False)),
                "name": lambda x: f"{faker.word()} bean",
                "origin_country": lambda x: faker.country(),
                "extraction": lambda x: faker.random_element(elements=extraction_choices),
                "roast_point": lambda x: faker.random_int(min=0, max=5),
                "process": lambda x: faker.random_element(elements=process_choices),
                "region": lambda x: faker.city(),
                "bev_type": lambda x: faker.random_element(elements=(True, False)),
                "roastery": lambda x: faker.company(),
                "variety": lambda x: faker.random_choices(elements=("아라비카", "로부스타", "리베리카"), length=1)[0],
                # 'is_user_created': faker.random_element(elements=(True, False)),
                "is_user_created": False,
            },
        )

        seeder.execute()
        self.stdout.write(self.style.SUCCESS(f"{number}개의 원두 생성 성공."))
