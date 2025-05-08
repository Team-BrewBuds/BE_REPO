import mimetypes
import os
from io import BytesIO

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile
from faker import Faker

from repo.common.bucket import create_unique_filename
from repo.profiles.models import CustomUser, UserDetail
from repo.records.models import Photo, TastedRecord


def pre_process_create_user(file_path: str, faker: Faker, profile_photos_dir_path: str) -> int:
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
            create_user_and_user_detail(nickname, faker, profile_photos_dir_path)
            create_user_cnt += 1

    return create_user_cnt


def create_user_and_user_detail(nickname: str, faker: Faker, profile_photos_dir_path: str) -> None:

    user = CustomUser.objects.create(
        nickname=nickname,
        gender=faker.random_element(elements=["남", "여"]),
        birth=faker.random_int(min=1970, max=2010),
        email=generate_unique_email(faker),
        login_type=faker.random_element(elements=["naver", "kakao", "apple"]),
    )

    upload_profile_photo(profile_photos_dir_path, user)

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


def upload_profile_photo(profile_photos_dir_path: str, user: CustomUser) -> None:
    """프로필 사진 업로드"""
    photo_files = get_photo_file_by_nickname(profile_photos_dir_path, user.nickname)
    save_profile_photos(photo_files, user)


def get_photo_file_by_nickname(photos_dir_path: str, nickname: str) -> list:
    """해당 인덱스의 사진 파일들을 찾아서 반환"""

    photo_files = []

    for file in os.listdir(photos_dir_path):
        # 해당 nickname이 포함된 파일명 찾기
        if nickname not in file:
            continue

        photo_path = os.path.join(photos_dir_path, file)
        if not os.path.isfile(photo_path):
            continue

        try:
            photo_file = create_memory_file(photo_path, file)
            photo_files.append(photo_file)
        except IOError as e:
            print(f"파일 읽기 오류: {photo_path} - {str(e)}")
            continue

    return photo_files


def save_profile_photos(photo_files: list, user: CustomUser) -> None:
    """사진들을 DB에 저장"""
    for i, photo_file in enumerate(photo_files):
        try:
            photo_file.name = create_unique_filename(photo_file.name, is_main=(i == 0))
            user.profile_image = photo_file
            user.save()
        except Exception as e:
            print(f"사진 업로드 오류: {photo_file.name} - {str(e)}")
            continue


def create_memory_file(photo_path: str, filename: str) -> InMemoryUploadedFile:
    """파일을 메모리에 로드하여 Django 파일 객체 생성"""
    with open(photo_path, "rb") as f:
        file_content = BytesIO(f.read())
        content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"

        return InMemoryUploadedFile(file_content, "photo_url", filename, content_type, file_content.getbuffer().nbytes, None)


def save_tasted_record_photos(photo_files: list, tasted_record: TastedRecord) -> None:
    """사진들을 DB에 저장"""
    for i, photo_file in enumerate(photo_files):
        try:
            photo_file.name = create_unique_filename(photo_file.name, is_main=(i == 0))
            photo = Photo(tasted_record=tasted_record, photo_url=photo_file)
            photo.save()
        except Exception as e:
            print(f"사진 업로드 오류: {photo_file.name} - {str(e)}")
            continue
