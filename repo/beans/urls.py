from django.urls import path

from repo.beans.views import *

urlpatterns = [
    path('', BeanNameListView.as_view(), name='bean_list'),
    path('search/', BeanNameSearchView.as_view(), name='bean_search'),
]
