import random

import factory
from factory.django import DjangoModelFactory
from faker import Faker

from repo.beans.models import Bean, BeanTasteReview
from repo.interactions.note.models import Note
from repo.interactions.relationship.models import Relationship
from repo.profiles.models import CustomUser, UserDetail
from repo.records.models import Comment, Photo, Post, Report, TastedRecord

fake = Faker("ko_KR")


class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    nickname = factory.Sequence(lambda n: f"유저{n}")
    gender = factory.Iterator(["남", "여"])
    birth = factory.LazyFunction(lambda: fake.random_int(min=1970, max=2005))
    login_type = factory.Iterator(["kakao", "naver", "apple"])
    profile_image = factory.django.ImageField()
    social_id = factory.Sequence(lambda n: n)
    is_active = True


class UserDetailFactory(DjangoModelFactory):
    class Meta:
        model = UserDetail

    user = factory.SubFactory(CustomUserFactory)
    introduction = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    profile_link = factory.LazyFunction(lambda: fake.url())
    coffee_life = factory.Dict(
        {
            "cafe_tour": factory.Faker("boolean"),
            "coffee_extraction": factory.Faker("boolean"),
            "coffee_study": factory.Faker("boolean"),
            "cafe_alba": factory.Faker("boolean"),
            "cafe_work": factory.Faker("boolean"),
            "cafe_operation": factory.Faker("boolean"),
        }
    )
    preferred_bean_taste = factory.Dict(
        {
            "body": factory.LazyFunction(lambda: fake.random_int(min=1, max=5)),
            "acidity": factory.LazyFunction(lambda: fake.random_int(min=1, max=5)),
            "bitterness": factory.LazyFunction(lambda: fake.random_int(min=1, max=5)),
            "sweetness": factory.LazyFunction(lambda: fake.random_int(min=1, max=5)),
        }
    )
    is_certificated = factory.Faker("boolean")


class RelationshipFactory(DjangoModelFactory):
    class Meta:
        model = Relationship

    from_user = factory.SubFactory(CustomUserFactory)
    to_user = factory.SubFactory(CustomUserFactory)
    relationship_type = factory.Iterator(["follow", "block"])
    created_at = factory.Faker("date_time_this_year")


class BeanFactory(DjangoModelFactory):
    class Meta:
        model = Bean

    bean_type = factory.Iterator(["single", "blend"])
    is_decaf = factory.Faker("boolean")
    name = factory.LazyFunction(lambda: f"{fake.word()} 커피")
    origin_country = factory.Faker("country")
    extraction = factory.Iterator(["핸드드립", "에스프레소", "콜드브루", "프렌치프레스"])
    roast_point = factory.LazyFunction(lambda: fake.random_int(min=1, max=5))
    process = factory.Iterator(["워시드", "내추럴", "허니", "펄프드내추럴"])
    region = factory.Faker("city")
    roastery = factory.Faker("company")
    variety = factory.Iterator(["아라비카", "로부스타", "리베리카"])
    is_user_created = factory.Faker("boolean")


class BeanTasteReviewFactory(DjangoModelFactory):
    class Meta:
        model = BeanTasteReview

    flavor = factory.LazyFunction(lambda: ",".join(fake.words(3)))
    body = factory.LazyFunction(lambda: fake.random_int(min=1, max=5))
    acidity = factory.LazyFunction(lambda: fake.random_int(min=1, max=5))
    bitterness = factory.LazyFunction(lambda: fake.random_int(min=1, max=5))
    sweetness = factory.LazyFunction(lambda: fake.random_int(min=1, max=5))
    star = factory.LazyFunction(lambda: round(fake.random.uniform(0.5, 5.0) * 2) / 2)
    place = factory.Iterator(["집", "카페", "회사", "도서관"])
    created_at = factory.Faker("date_time_this_year")


class TastedRecordFactory(DjangoModelFactory):
    class Meta:
        model = TastedRecord
        skip_postgeneration_save = True

    author = factory.SubFactory(CustomUserFactory)
    bean = factory.SubFactory(BeanFactory)
    taste_review = factory.SubFactory(BeanTasteReviewFactory)
    content = factory.LazyFunction(lambda: fake.text())
    view_cnt = factory.LazyFunction(lambda: fake.random_int(min=0, max=1000))
    is_private = factory.Faker("boolean")
    created_at = factory.Faker("date_time_this_year")
    tag = factory.LazyFunction(lambda: ",".join(fake.words(3)))

    @factory.post_generation
    def like_cnt(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                self.like_cnt.add(user)
        else:
            for _ in range(random.randint(0, 10)):
                self.like_cnt.add(CustomUserFactory())


class PostFactory(DjangoModelFactory):
    class Meta:
        model = Post
        skip_postgeneration_save = True

    author = factory.SubFactory(CustomUserFactory)
    title = factory.LazyFunction(lambda: fake.sentence())
    content = factory.LazyFunction(lambda: fake.text())
    subject = factory.Iterator(["normal", "cafe", "bean", "info", "question", "worry", "gear"])
    view_cnt = factory.LazyFunction(lambda: fake.random_int(min=0, max=1000))
    created_at = factory.Faker("date_time_this_year")
    tag = factory.LazyFunction(lambda: ",".join(fake.words(3)))

    @factory.post_generation
    def tasted_records(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tasted_record in extracted:
                self.tasted_records.add(tasted_record)


class PhotoFactory(DjangoModelFactory):
    class Meta:
        model = Photo
        skip_postgeneration_save = True

    photo_url = factory.django.ImageField()
    created_at = factory.Faker("date_time_this_year")
    post = None
    tasted_record = None

    @factory.post_generation
    def post_or_tasted_record(self, create, _, **kwargs):
        if not create:
            return

        if random.choice([True, False]):
            self.post = PostFactory()
        else:
            self.tasted_record = TastedRecordFactory()


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment
        skip_postgeneration_save = True

    author = factory.SubFactory(CustomUserFactory)
    content = factory.LazyFunction(lambda: fake.text())
    is_deleted = factory.Faker("boolean")
    created_at = factory.Faker("date_time_this_year")
    post = None
    tasted_record = None

    @factory.post_generation
    def post_or_tasted_record(self, create, _, **kwargs):
        if not create:
            return

        if random.choice([True, False]):
            self.post = PostFactory()
        else:
            self.tasted_record = TastedRecordFactory()


class NoteFactory(DjangoModelFactory):
    class Meta:
        model = Note
        skip_postgeneration_save = True

    author = factory.SubFactory(CustomUserFactory)
    created_at = factory.Faker("date_time_this_year")
    post = None
    tasted_record = None
    bean = None

    @factory.post_generation
    def related_object(self, create, extracted, **kwargs):
        if not create:
            return

        choice = random.choice(["post", "tasted_record", "bean"])
        if choice == "post":
            self.post = PostFactory()
        elif choice == "tasted_record":
            self.tasted_record = TastedRecordFactory()
        else:
            self.bean = BeanFactory()


class ReportFactory(DjangoModelFactory):
    class Meta:
        model = Report

    author = factory.SubFactory(CustomUserFactory)
    object_type = factory.Iterator(["post", "comment", "tasted_record"])
    reason = factory.LazyFunction(lambda: fake.text())
    status = factory.Iterator(["pending", "processing", "completed"])
    created_at = factory.Faker("date_time_this_year")
    object_id = None

    @factory.post_generation
    def set_object_id(self, create, _, **kwargs):
        if not create:
            return

        if self.object_type == "post":
            self.object_id = PostFactory().id
        elif self.object_type == "comment":
            self.object_id = CommentFactory().id
        else:
            self.object_id = TastedRecordFactory().id


class ContentObjectFactory:
    @staticmethod
    def create_content_object(object_type):
        if object_type == "post":
            return PostFactory()
        elif object_type == "tasted_record":
            return TastedRecordFactory()
        elif object_type == "comment":
            return CommentFactory()
