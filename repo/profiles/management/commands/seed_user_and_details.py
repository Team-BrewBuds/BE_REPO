from django.core.management.base import BaseCommand
from django_seed import Seed
from faker import Faker

from repo.interactions.relationship.models import Relationship
from repo.profiles.models import CustomUser, UserDetail


class Command(BaseCommand):
    help = "유저와 유저 상세정보 더미 데이터를 생성"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            default=10,
            type=int,
            help="유저와 유저 상세정보 더미 데이터를 생성할 개수",
        )

    @staticmethod
    def get_random_coffee_life(faker):
        coffee_life_json = UserDetail.default_coffee_life()

        for key in coffee_life_json.keys():
            coffee_life_json[key] = faker.random_element(elements=(True, False))

        return coffee_life_json

    @staticmethod
    def get_random_preferred_taste(faker):
        preferred_taste_json = UserDetail.default_taste()

        for key in preferred_taste_json.keys():
            preferred_taste_json[key] = faker.random_int(min=1, max=5)

        return preferred_taste_json

    def generate_unique_email(self, faker):
        email = faker.email()
        while CustomUser.objects.filter(email=email).exists():
            email = faker.email()
        return email

    def get_nerate_unique_nickname(self, faker):
        nickname = faker.user_name()
        while CustomUser.objects.filter(nickname=nickname).exists():
            nickname = faker.user_name()
        return nickname

    def handle(self, *args, **kwargs):
        number = kwargs["number"]
        seeder = Seed.seeder()
        faker = Faker(locale="ko_KR")

        gender_choices = ["남", "여"]
        login_type_choices = ["naver", "kakao", "apple"]

        seeder.add_entity(
            CustomUser,
            number,
            {
                "nickname": lambda x: self.get_nerate_unique_nickname(faker),
                "gender": lambda x: faker.random_element(elements=gender_choices),
                "birth": lambda x: faker.random_int(min=1970, max=2010),
                "email": lambda x: self.generate_unique_email(faker),
                "login_type": lambda x: faker.random_element(elements=login_type_choices),
                "profile_image": lambda x: faker.image_url(width=360, height=360),
                "social_id": lambda x: faker.random_int(max=9999999),
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                "created_at": lambda x: faker.date_time_this_year(),
            },
        )

        inserted_pks = seeder.execute()

        # UserDetail 생성
        is_certificated_choices = [True, False]

        for user_id in inserted_pks[CustomUser]:
            user = CustomUser.objects.get(pk=user_id)

            UserDetail.objects.create(
                user=user,
                introduction=faker.sentence(),
                profile_link=faker.url(),
                coffee_life=self.get_random_coffee_life(faker),
                preferred_bean_taste=self.get_random_preferred_taste(faker),
                is_certificated=faker.random_element(elements=is_certificated_choices),
            )

        self.stdout.write(self.style.SUCCESS(f"{number}명의 유저와 상세정보 생성 성공."))

        users = CustomUser.objects.filter(pk__in=inserted_pks[CustomUser])

        # 유저간 관계(팔로우,차단) 랜덤 설정
        relationship_type_choices = ["follow", "block"]
        for _ in range(int(number * 1.5)):
            from_user = faker.random_element(users)
            to_user = faker.random_element(users)

            if from_user == to_user:
                continue

            relationship_type = faker.random_element(elements=relationship_type_choices)
            Relationship.objects.get_or_create(from_user=from_user, to_user=to_user, relationship_type=relationship_type)
        self.stdout.write(self.style.SUCCESS("유저간 랜덤 관계(팔로우,차단) 설정 성공."))
