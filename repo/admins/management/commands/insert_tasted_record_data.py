import os
from datetime import datetime

import pandas as pd
from django.core.management.base import BaseCommand
from faker import Faker

from repo.admins.keys import (
    bean_info_keys,
    bean_taste_review_keys,
    full_tasted_record_keys,
    only_tasted_record_keys,
)
from repo.admins.utils import (
    create_memory_file,
    pre_process_create_user,
    save_tasted_record_photos,
)
from repo.beans.models import Bean, BeanTasteReview
from repo.common.bucket import delete_photos
from repo.profiles.models import CustomUser
from repo.records.models import TastedRecord

DATETIME_NOW = datetime.now()
FILE_PATH = ""  # 시음기록 데이터 파일 경로
PHOTOS_DIR_PATH = ""  # 시음기록 사진 데이터 파일 경로

BEAN_TYPE = {"싱글 오리진": "single", "블렌드": "blend"}
BEV_TYPE = {"콜드": True, "핫": False}


class Command(BaseCommand):
    help = "시음기록 더미 데이터를 생성"

    def handle(self, *args, **kwargs):
        faker = Faker(locale="ko_KR")

        # 2. csv 데이터 전처리
        df = pd.read_csv(FILE_PATH)

        # 1. 작성자 생성 (없으면 미리 생성)
        create_user_cnt = pre_process_create_user(FILE_PATH, faker)

        # 5. 시음기록 생성  (1+2+3+4 조합을 사용해서 생성)
        tasted_record_cnt = create_tasted_record(df[full_tasted_record_keys.keys()])

        self.stdout.write(self.style.SUCCESS(f"{create_user_cnt}명의 작성자 생성 성공."))
        self.stdout.write(self.style.SUCCESS(f"{tasted_record_cnt}개의 시음기록 생성 성공."))


def create_tasted_record(df: pd.DataFrame) -> int:
    """시음기록 데이터 생성"""

    for idx, row in df.iterrows():
        if idx == 1:
            break

        # 0. 작성자 데이터 생성
        user = CustomUser.objects.get(nickname=row["작성자"])

        # 1. 원두 데이터 생성
        bean = create_bean(row[bean_info_keys.keys()])

        # 2. 원두 리뷰 데이터 생성
        taste_review = create_taste_review(row[bean_taste_review_keys.keys()])

        # 3. 시음기록 데이터 생성 (1+2+3 조합)
        only_tasted_record = row[only_tasted_record_keys.keys()]

        tasted_record = TastedRecord.objects.create(
            author=user,
            bean=bean,
            taste_review=taste_review,
            content=only_tasted_record["시음 내용"],
            tag=only_tasted_record["태그"],
            is_private=False,
        )

        # 4. 시음기록 사진 생성 및 연결
        result = upload_photos(PHOTOS_DIR_PATH, idx + 1, tasted_record)
        if result:
            print(f"시음기록 {idx+1} 사진 업로드 성공")
        else:
            print(f"시음기록 {idx+1} 사진 업로드 실패")
            tr = TastedRecord.objects.get(id=tasted_record.id)
            tr.delete()
    return idx


def create_bean(df: pd.DataFrame):
    """원두 데이터 생성"""

    bean_data = {
        "bean_type": BEAN_TYPE[df["원두 유형"]],
        "name": df["원두 이름"],
        "origin_country": df["원산지"],
        "is_decaf": df["디카페인 여부"],
        "extraction": df["추출 방식"],
        "roast_point": df["로스팅 포인트"],
        "process": df["가공 방식"],
        "region": df["생산 지역"],
        "bev_type": BEV_TYPE[df["음료 유형"]],
        "roastery": df["로스터리"],
        "variety": df["품종"],
        "is_official": df["공식원두 여부"],
    }

    bean = Bean.objects.filter(**bean_data).first()
    if not bean:
        bean = Bean.objects.create(**bean_data)

    return bean


def create_taste_review(df: pd.DataFrame):
    """원두 리뷰 데이터 생성"""
    taste_review = BeanTasteReview.objects.create(
        flavor=df["맛"],
        body=df["바디감"],
        acidity=df["산미"],
        bitterness=df["쓴맛"],
        sweetness=df["단맛"],
        star=df["별점"],
        tasted_at=df["시음 날짜"],
        place=df["시음 장소"],
    )
    return taste_review


def upload_photos(photos_dir_path: str, idx: int, tasted_record: TastedRecord) -> bool:
    """시음기록 사진 데이터 생성

    Args:
        photos_dir_path: 사진 디렉토리 경로
        idx: 시음기록 인덱스
        tasted_record: 시음기록 객체

    Returns:
        bool: 사진 업로드 성공 여부
    """
    if not os.path.exists(photos_dir_path):
        raise FileNotFoundError(f"사진 디렉토리를 찾을 수 없습니다: {photos_dir_path}")

    try:
        photo_files = get_photo_files_by_idx(photos_dir_path, idx)
        if not photo_files:
            print(f"경고: review_{idx}_에 해당하는 사진을 찾을 수 없습니다.")
            return False

        # 파일명 기준으로 정렬 (숫자만 추출하여 정렬)
        photo_files.sort(key=lambda x: int(x.name.split("_")[-1].split(".")[0]))

        # 사진 업로드 및 TastedRecord와 연결
        save_tasted_record_photos(photo_files, tasted_record)
        return True

    except Exception as e:
        delete_photos(tasted_record)
        print(f"사진 업로드 중 오류 발생: {str(e)}")
        return False


def get_photo_files_by_idx(photos_dir_path: str, idx: int) -> list:
    """해당 인덱스의 사진 파일들을 찾아서 반환"""
    photo_files = []

    for file in os.listdir(photos_dir_path):
        # review_1_1.jpg 형식의 파일명 패턴 매칭
        if not file.startswith(f"review_{idx}_"):
            continue

        photo_path = os.path.join(photos_dir_path, file)
        if not os.path.isfile(photo_path):
            continue

        try:
            num = file.split("_")[-1].split(".")[0]
            photo_file = create_memory_file(photo_path, f"review_{idx}_{num}.jpg")
            photo_files.append(photo_file)
        except IOError as e:
            print(f"파일 읽기 오류: {photo_path} - {str(e)}")
            continue

    return photo_files
