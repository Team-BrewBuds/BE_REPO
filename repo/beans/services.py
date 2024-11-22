from django.db.models import QuerySet

from repo.beans.models import Bean


class BeanService:
    def __init__(self, bean_repository=None):
        self.bean_repository = bean_repository or Bean.objects

    def search_beans_by_name(self, name: str) -> QuerySet[Bean]:
        """원두 이름 검색"""
        if not name:  # 검색어가 없어도 반환
            return self.bean_repository.all()

        return self.bean_repository.filter(name__icontains=name)
