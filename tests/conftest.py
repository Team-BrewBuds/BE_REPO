import pytest
from rest_framework.test import APIClient

from beans.models import Bean, Bean_Taste_Review
from profiles.models import User
from records.models import Post, Tasted_Record, Comment, Note


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create(
        nickname="testuser",
        login_type="naver",
        profile_image="http://example.com/profile.jpg"
    )


@pytest.fixture
def bean():
    return Bean.objects.create(
        name="Test Bean",
        bean_type="single",
        is_decaf=False,
        origin_country="Test origin Country",
        extraction="Espresso",
        roast_point=3,
        process="Washed",
        region="Yirgacheffe",
        bev_type=True,
        roastery="Test Roastery",
        variety="Heirloom",
    )   


@pytest.fixture
def bean_taste_review():
    return Bean_Taste_Review.objects.create(
        flavor="Test Flavor",
        body=3,
        acidity=3,
        bitterness=3,
        sweetness=3,
        star=3,
        place="Test Place"
    )


@pytest.fixture
def tasted_record(user, bean, bean_taste_review):

    return Tasted_Record.objects.create(
        user=user,
        bean=bean,
        taste_and_review=bean_taste_review,
        content="Test Content",
        tag="tags"
    )


@pytest.fixture
def post(user, tasted_record):
    return Post.objects.create(
        user=user,
        title="Test Post",
        content="Test Content",
        subject="Test Subject",
        tag="Test Tag",
        tasted_record=tasted_record
    )


@pytest.fixture
def post_comment(user, post):
    return Comment(
        user=user,
        post=post,
        content="Test Post Comment!"
    )

@pytest.fixture
def tasted_record_comment(user, tasted_record):
    return Comment(
        user=user,
        tasted_record=tasted_record,
        content="Test Tasted_Record Comment!"
    )

@pytest.fixture
def post_note(user, post):
    note = Note.objects.create(user=user, post=post)
    return note


@pytest.fixture
def tasted_record_note(user, tasted_record):
    note = Note.objects.create(user=user, tasted_record=tasted_record)
    return note
