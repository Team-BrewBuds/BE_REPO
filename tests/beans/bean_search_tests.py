import pytest
from rest_framework import status

from tests.factorys import BeanFactory

pytestmark = pytest.mark.django_db


class TestBeanNameSearchView:
    """
    원두 이름 검색 API 테스트
    작성한 테스트 케이스
    - [일반] 원두 이름 검색 성공 테스트
    - [일반] 원두 이름 검색 결과가 없는 경우 테스트
    - [일반] 원두 이름 검색 이름 순 정렬 테스트
    """

    def test_get_bean_name_search_success(self, api_client):
        """
        원두 이름 검색 성공 테스트
        """
        # Given
        BeanFactory(name="과테말라 내추럴")
        BeanFactory(name="에티오피아 구지 기계사")
        BeanFactory(name="콜롬비아 핑크 버번")

        search_name = "과테말라"

        url = f"/beans/search/?name={search_name}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "과테말라 내추럴"

    def test_get_bean_name_search_empty(self, api_client):
        """
        원두 이름 검색 결과가 없는 경우 테스트
        """
        # Given
        BeanFactory(name="과테말라 내추럴")
        BeanFactory(name="에티오피아 구지 기계사")
        BeanFactory(name="콜롬비아 핑크 버번")

        search_name = "케냐 AA"

        url = f"/beans/search/?name={search_name}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_get_bean_name_search_order_by_name(self, api_client):
        """
        원두 이름 검색 성공 테스트
        """

        # Given
        BeanFactory(name="에티오피아 구지 기계사")
        BeanFactory(name="에티오피아 예가체프 코체레")
        BeanFactory(name="과테말라 내추럴")

        search_name = "에티오피아"

        url = f"/beans/search/?name={search_name}"

        # When
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert response.data["results"][0]["name"] == "에티오피아 구지 기계사"
        assert response.data["results"][1]["name"] == "에티오피아 예가체프 코체레"
