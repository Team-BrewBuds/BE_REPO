import pytest
from rest_framework import status

from tests.factorys import BeanFactory

pytestmark = pytest.mark.django_db


class TestBeanNameListView:
    """
    원두 리스트 조회 API 테스트
    작성한 테스트 케이스
    - [일반] 원두 리스트 조회 성공 테스트
    - [일반] 원두 빈 리스트 조회 성공 테스트
    - [정렬] 원두 리스트 이름 순 정렬 테스트
    """

    def test_get_bean_list_success(self, api_client):
        """
        원두 리스트 조회 성공 테스트
        """
        # Given
        BeanFactory.create_batch(10)

        url = "/beans/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def test_get_bean_list_empty(self, api_client):
        """
        원두 빈 리스트 조회 성공 테스트
        """
        # Given
        url = "/beans/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_get_bean_list_order_by_name(self, api_client):
        """
        원두 리스트 이름 순 정렬 테스트
        """
        # Given
        BeanFactory(name="과테말라 내추럴")
        BeanFactory(name="에티오피아 구지 기계사")
        BeanFactory(name="콜롬비아 핑크 버번")

        url = "/beans/"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == "과테말라 내추럴"
        assert response.data["results"][1]["name"] == "에티오피아 구지 기계사"
        assert response.data["results"][2]["name"] == "콜롬비아 핑크 버번"
