import pandas as pd
from faker import Faker

from repo.profiles.models import CustomUser, UserDetail


def pre_process_create_user(file_path: str, faker: Faker) -> int:
    # 엑셀 파일 읽기
    df = pd.read_csv(file_path)

    # 작성자 컬럼만 추출
    nicknames = df["작성자"].tolist()

    # 작성자 컬럼에서 중복 제거
    nicknames = list(set(nicknames))

    create_user_cnt = 0
    for nickname in nicknames:
        try:
            CustomUser.objects.get(nickname=nickname)
        except CustomUser.DoesNotExist:
            create_user_and_user_detail(nickname, faker)
            create_user_cnt += 1

    return create_user_cnt


def create_user_and_user_detail(nickname: str, faker: Faker) -> None:
    user = CustomUser.objects.create(
        nickname=nickname,
        gender=faker.random_element(elements=["남", "여"]),
        birth=faker.random_int(min=1970, max=2010),
        email=generate_unique_email(faker),
        login_type=faker.random_element(elements=["naver", "kakao", "apple"]),
    )

    UserDetail.objects.create(
        user=user,
        introduction=faker.sentence(),
        profile_link=faker.url(),
        coffee_life=get_random_coffee_life(faker),
        preferred_bean_taste=get_random_preferred_taste(faker),
        is_certificated=faker.random_element(elements=[True, False]),
    )


def generate_unique_email(faker: Faker) -> str:
    email = faker.email()
    while CustomUser.objects.filter(email=email).exists():
        email = faker.email()
    return email


def get_random_coffee_life(faker: Faker) -> dict:
    coffee_life_json = UserDetail.default_coffee_life()

    for key in coffee_life_json.keys():
        coffee_life_json[key] = faker.random_element(elements=(True, False))

    return coffee_life_json


def get_random_preferred_taste(faker: Faker) -> dict:
    preferred_taste_json = UserDetail.default_taste()

    for key in preferred_taste_json.keys():
        preferred_taste_json[key] = faker.random_int(min=1, max=5)

    return preferred_taste_json
