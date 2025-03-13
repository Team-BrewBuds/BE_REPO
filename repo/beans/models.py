from django.db import models


class Bean(models.Model):
    bean_type_choices = [("single", "싱글 오리진"), ("blend", "블랜드")]
    roasting_point_choices = list(zip(range(0, 6), range(0, 6)))  # 0~5

    # 필수
    bean_type = models.CharField(max_length=20, choices=bean_type_choices, verbose_name="원두 유형")
    name = models.CharField(max_length=100, verbose_name="원두명")
    origin_country = models.CharField(max_length=100, verbose_name="원산지")
    image_url = models.URLField(null=True, blank=True, verbose_name="공식원두 이미지")

    # 선택
    is_decaf = models.BooleanField(default=False, verbose_name="디카페인")
    extraction = models.CharField(max_length=50, null=True, blank=True, verbose_name="추출 방식")
    roast_point = models.IntegerField(choices=roasting_point_choices, null=True, blank=True, verbose_name="로스팅 포인트")
    process = models.CharField(max_length=50, null=True, blank=True, verbose_name="가공 방식")
    region = models.CharField(max_length=100, null=True, blank=True, verbose_name="지역")
    bev_type = models.BooleanField(default=False, null=True, blank=True, verbose_name="음료 유형")
    roastery = models.CharField(max_length=100, null=True, blank=True, verbose_name="로스터리")
    variety = models.CharField(max_length=100, null=True, blank=True, verbose_name="원두 품종")
    is_user_created = models.BooleanField(default=False, null=True, blank=True, verbose_name="사용자 추가 여부")
    is_official = models.BooleanField(default=False, null=True, blank=True, verbose_name="공식원두 여부")

    def __str__(self):
        return f"{self.id} - {self.name}"

    class Meta:
        db_table = "bean"
        verbose_name = "원두"
        verbose_name_plural = "원두"


class BeanTasteBase(models.Model):
    Taste_point_choices = list(zip(range(0, 6), range(0, 6)))  # 0~5

    flavor = models.TextField(verbose_name="맛")
    body = models.IntegerField(choices=Taste_point_choices, verbose_name="바디감")
    acidity = models.IntegerField(choices=Taste_point_choices, verbose_name="산미")
    bitterness = models.IntegerField(choices=Taste_point_choices, verbose_name="쓴맛")
    sweetness = models.IntegerField(choices=Taste_point_choices, verbose_name="단맛")

    class Meta:
        abstract = True  # 추상 모델 사용


class BeanTaste(BeanTasteBase):
    bean = models.OneToOneField(
        "Bean", on_delete=models.CASCADE, null=True, blank=True, related_name="bean_taste", verbose_name="공식 원두 기본 맛"
    )

    def __str__(self):
        return f"{self.id} - {self.flavor}"

    class Meta:
        db_table = "bean_taste"
        verbose_name = "공식 원두 기본 맛"
        verbose_name_plural = "공식 원두 기본 맛"


class BeanTasteReview(BeanTasteBase):
    star_choices = [(x * 0.5, x * 0.5) for x in range(0, 11)]  # 0~10

    star = models.FloatField(choices=star_choices, verbose_name="별점")
    tasted_at = models.DateField(null=True, blank=True, verbose_name="시음일")
    place = models.CharField(max_length=100, verbose_name="시음 장소")

    def __str__(self):
        return f"bean :{self.flavor} - {self.tasted_at}"

    class Meta:
        db_table = "taste_review"
        verbose_name = "원두 맛&평가"
        verbose_name_plural = "원두 맛&평가"


class NotUsedBean(Bean):
    class Meta:
        proxy = True
        verbose_name = "사용하지 않는 원두"
        verbose_name_plural = "사용하지 않는 원두"
