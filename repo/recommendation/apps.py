from django.apps import AppConfig

from repo.recommendation.loaders import ModelLoader


class RecommendationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "repo.recommendation"

    def ready(self):
        """서버가 시작될 때 머신러닝 모델과 인코더를 미리 로드"""

        ModelLoader.load()
