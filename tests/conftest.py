import pytest
from rest_framework.test import APIClient

from beans.models import Bean, Bean_Taste_Review
from profiles.models import User, Relationship
from records.models import Post, Tasted_Record, Comment, Note


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create(
        nickname="testuser",
        login_type="naver",
        email='user@example.com',
        profile_image="http://example.com/profile.jpg"
    )

@pytest.fixture
def following_user(user):
    user2 = User.objects.create(
        nickname="testuser2",
        login_type="kakao",
        email='following_user@example.com',
        profile_image="http://example.com/profile.jpg"
    )

    Relationship.custom_objects.create(
        from_user=user2,
        to_user=user,
        relationship_type="follow"
    )

    return user2



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
def multiple_tasted_records(user, bean):
    records = []
    for i in range(5):
        bean_taste_review = Bean_Taste_Review.objects.create(
            flavor=f"Test Flavor {i}",
            body=3,
            acidity=3,
            bitterness=3,
            sweetness=3,
            star=3,
            place=f"Test Place {i}"
        )
        record = Tasted_Record.objects.create(
            user=user,
            bean=bean,
            taste_and_review=bean_taste_review,
            content=f"Test Content {i}",
            tag=f"tags_{i}"
        )
        records.append(record)
    return records


@pytest.fixture
def multiple_posts(user, multiple_tasted_records):
    posts = []
    for i, tasted_record in enumerate(multiple_tasted_records):
        post = Post.objects.create(
            user=user,
            title=f"Test Post {i}",
            content=f"Test Content {i}",
            subject=f"Test Subject {i}",
            tag=f"Test Tag {i}",
            tasted_record=tasted_record
        )
        posts.append(post)
    return posts


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
