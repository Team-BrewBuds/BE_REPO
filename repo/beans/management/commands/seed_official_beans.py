from django.core.management.base import BaseCommand
from django_seed import Seed
from faker import Faker

from repo.beans.models import BeanTaste, OfficialBean


class Command(BaseCommand):
    help = "공식원두 더미 데이터를 생성"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            default=5,
            type=int,
            help="공식원두 더미 데이터를 생성할 개수",
        )

    def handle(self, *args, **kwargs):
        number = kwargs["number"]
        seeder = Seed.seeder()
        faker = Faker(locale="ko_KR")

        # 생성할 데이터 선택지
        extraction_choices = [
            "핸드 드립",
            "에스프레소 머신",
            "커피메이커",
            "모카포트",
            "프렌치프레스",
            "에어로프레스",
            "콜드브루",
        ]
        process_choices = ["내추럴", "워시드", "펄프드 내추럴", "허니", "무산소 발효"]
        variety_choices = ["아라비카", "로부스타", "리베리카"]
        flavor_pool = [
            "신",
            "초콜릿",
            "시트러스",
            "쓴",
            "달콤",
            "견과류",
            "꽃",
            "과일",
            "스파이시",
            "허브",
            "청량감",
            "짙은",
            "풍부한",
            "묵직함",
            "바닐라",
            "카라멜",
            "열대과일",
            "허니",
            "와인",
            "베리",
        ]

        # BeanTaste 데이터 생성
        for _ in range(number):
            random_flavors = faker.random_choices(elements=flavor_pool, length=faker.random_int(min=2, max=4))
            BeanTaste.objects.create(
                acidity=faker.random_int(min=1, max=5),
                body=faker.random_int(min=1, max=5),
                sweetness=faker.random_int(min=1, max=5),
                bitterness=faker.random_int(min=1, max=5),
                flavor=", ".join(random_flavors),
            )

        # OfficialBean 데이터 생성
        seeder.add_entity(
            OfficialBean,
            number,
            {
                "bean_type": lambda x: faker.random_element(elements=("single", "blend")),
                "is_decaf": lambda x: faker.boolean(),
                "name": lambda x: f"{faker.word()} bean",
                "origin_country": lambda x: faker.country(),
                "extraction": lambda x: faker.random_element(elements=extraction_choices),
                "roast_point": lambda x: faker.random_int(min=0, max=5),
                "process": lambda x: faker.random_element(elements=process_choices),
                "region": lambda x: faker.city(),
                "bev_type": lambda x: faker.boolean(),
                "roastery": lambda x: faker.company(),
                "variety": lambda x: faker.random_element(elements=variety_choices),
                "is_user_created": False,
                "bean_taste_id": lambda x: BeanTaste.objects.order_by("?").first().id,  # 랜덤으로 연결된 BeanTaste 선택
            },
        )

        seeder.execute()
        self.stdout.write(self.style.SUCCESS(f"{number}개의 공식원두 생성 성공."))
