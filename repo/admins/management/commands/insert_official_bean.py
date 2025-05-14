import pandas as pd
from django.core.management.base import BaseCommand

from repo.admins.keys import bean_taste_keys, is_official_keys
from repo.admins.management.commands.insert_tasted_record_data import BEAN_TYPE
from repo.beans.models import Bean, BeanTaste

FILE_PATH = ""  # 공식 원두 데이터 파일 경로


class Command(BaseCommand):
    help = "공식 원두 데이터를 생성"

    def handle(self, *args, **kwargs):
        df = pd.read_csv(FILE_PATH)

        for _, row in df.iterrows():
            bean = self.create_bean(row)
            bean_taste = self.create_bean_taste(row, bean)

        self.stdout.write(self.style.SUCCESS("공식 원두 데이터 생성 완료"))

    def create_bean(self, row: pd.Series) -> Bean:
        bean_data = {key: row[value] for value, key in is_official_keys.items() if value in row and pd.notna(row[value])}
        bean_data["bean_type"] = BEAN_TYPE[bean_data["bean_type"]]
        bean_data["is_official"] = True
        bean = Bean.objects.create(**bean_data)
        return bean

    def create_bean_taste(self, row: pd.Series, bean: Bean) -> BeanTaste:
        bean_taste_data = {key: row[value] or None for value, key in bean_taste_keys.items()}
        bean_taste_data["bean"] = bean
        bean_taste = BeanTaste.objects.create(**bean_taste_data)
        return bean_taste
