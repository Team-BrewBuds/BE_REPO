import os

import joblib
import pandas as pd


class ModelLoader:
    """머신러닝 모델, 인코더, 추천 데이터(recsys_data)를 로드하고 관리하는 클래스"""

    model = None
    mlb_encoder = None
    recsys_data = None

    @classmethod
    def load(cls):
        """모델, 인코더, 추천 데이터 로드"""
        base_dir = os.path.dirname(__file__)
        print("모델, 인코더, 추천 데이터 로드 중...")

        if cls.model is None:
            cls.model = joblib.load(os.path.join(base_dir, "ml/kmeans_model.pkl"))

        if cls.mlb_encoder is None:
            cls.mlb_encoder = joblib.load(os.path.join(base_dir, "ml/mlb_encoder.pkl"))

        recsys_path = os.path.join(base_dir, "ml/recsys_data.csv")
        if cls.recsys_data is None:
            cls.recsys_data = pd.read_csv(recsys_path)
            print(cls.recsys_data.head())

    @classmethod
    def get_model(cls):
        """이미 로드된 모델 반환"""
        if cls.model is None:
            cls.load()
        return cls.model

    @classmethod
    def get_encoder(cls):
        """이미 로드된 인코더 반환"""
        if cls.mlb_encoder is None:
            cls.load()
        return cls.mlb_encoder

    @classmethod
    def get_recsys_data(cls):
        """이미 로드된 추천 데이터 반환"""
        if cls.recsys_data is None:
            cls.load()
        return cls.recsys_data
