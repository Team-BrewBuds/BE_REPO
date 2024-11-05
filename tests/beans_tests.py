import pytest

from repo.beans.models import Bean


@pytest.mark.django_db
def test_bean_list_view_bean_ordering_by_name(api_client, create_beans):
    response = api_client.get("/beans/")
    assert sorted(response.data["results"], key=lambda x: x["name"]) == response.data["results"]


@pytest.mark.django_db
def test_bean_list_view_returns_empty_list_when_no_beans(api_client):
    response = api_client.get("/beans/")
    assert len(response.data["results"]) == 0


@pytest.mark.django_db
def test_bean_list_view_returns_paginated_response(api_client, create_beans):
    count = Bean.objects.count()
    page_size = 20

    response = api_client.get("/beans/?page=1")
    assert len(response.data["results"]) == page_size

    response = api_client.get("/beans/?page=2")
    assert len(response.data["results"]) == count - page_size


@pytest.mark.django_db
def test_bean_name_search_view_returns_filtered_results(api_client, create_beans):
    response = api_client.get("/beans/search/?name=Special")
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Special Bean"


@pytest.mark.django_db
def test_bean_name_search_view_returns_all_beans_when_name_not_provided(api_client, create_beans):
    response = api_client.get("/beans/search/")
    assert len(response.data["results"]) == 20


@pytest.mark.django_db
def test_bean_name_search_view_handles_empty_results(api_client):
    response = api_client.get("/beans/search/?name=NonExistentBean")
    assert len(response.data["results"]) == 0
