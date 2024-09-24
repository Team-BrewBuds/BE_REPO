from django.db import models

class Bean(models.Model):

    bean_type_choices = [
        ('single', '싱글 오리진'),
        ('blend', '블랜드')
    ]
    roasting_point_choices = list(zip(range(0, 6), range(0, 6)))  # 0~5

    # 필수
    bean_id = models.AutoField(primary_key=True)
    bean_type = models.CharField(max_length=20, choices=bean_type_choices,  verbose_name="원두 유형")
    is_decaf = models.BooleanField(default=False, verbose_name="디카페인")
    name = models.CharField(max_length=100, verbose_name="원두명")
    origin_country = models.CharField(max_length=100, verbose_name="원산지")

    # 선택
    extraction = models.CharField(max_length=50, null=True, verbose_name="추출 방식")
    roast_point = models.IntegerField(choices=roasting_point_choices, null=True,  verbose_name="로스팅 포인트")
    process = models.CharField(max_length=50, null=True, verbose_name="가공 방식")
    region = models.CharField(max_length=100, null=True, verbose_name="지역")
    bev_type = models.BooleanField(default=False, null=True, verbose_name="음료 유형")
    roastery = models.CharField(max_length=100, null=True, verbose_name="로스터리")
    variety = models.CharField(max_length=100, null=True, verbose_name="원두 품종")
    is_user_created = models.DateTimeField(default=False, null=True, verbose_name="사용자 추가 여부")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'bean'
        verbose_name = '원두'
        verbose_name_plural = '원두'

class Bean_Taste(models.Model):

    Taste_point_choices = list(zip(range(0, 6), range(0, 6)))  # 0~5

    bean = models.OneToOneField(Bean, on_delete=models.CASCADE, verbose_name="원두")
    taste = models.TextField(verbose_name="맛")
    body = models.IntegerField(choices=Taste_point_choices, verbose_name="바디감")
    acidity = models.IntegerField(choices=Taste_point_choices, verbose_name="산미")
    bitterness = models.IntegerField(choices=Taste_point_choices, verbose_name="쓴맛")
    sweetness = models.IntegerField(choices=Taste_point_choices, verbose_name="단맛")

    def __str__(self):
        return self.bean.name

    class Meta:
        db_table = 'bean_taste'
        verbose_name = '원두 맛'
        verbose_name_plural = '원두 맛'
