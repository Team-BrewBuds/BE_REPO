from django.contrib import admin

from repo.profiles.models import UserDetail


class IsCertificatedFilter(admin.SimpleListFilter):
    title = "자격증 여부"
    parameter_name = "is_certificated"

    def lookups(self, request, model_admin):
        return (
            (True, "자격증 있음"),
            (False, "자격증 없음"),
        )

    def queryset(self, request, queryset):
        if self.value() == "True":
            return queryset.filter(is_certificated=True)
        elif self.value() == "False":
            return queryset.filter(is_certificated=False)
        return queryset


class IsCoffeeLifeFilter(admin.SimpleListFilter):
    title = "커피 생활"
    parameter_name = "coffee_life"

    def lookups(self, request, model_admin):
        choices = UserDetail.COFFEE_LIFE_CHOICES
        return [
            (choices[0], "01: 카페 투어"),
            (choices[1], "02: 커피 추출"),
            (choices[2], "03: 커피 공부"),
            (choices[3], "04: 카페 알바"),
            (choices[4], "05: 카페 근무"),
            (choices[5], "06: 카페 운영"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(**{f"coffee_life__{value}": True})
        return queryset


class IsPublicFilter(admin.SimpleListFilter):
    title = "공개 여부"
    parameter_name = "is_private"

    def lookups(self, request, model_admin):
        return (
            (False, "공개"),
            (True, "비공개"),
        )

    def queryset(self, request, queryset):
        if self.value() == "False":
            return queryset.filter(is_private=False)
        elif self.value() == "True":
            return queryset.filter(is_private=True)
        return queryset
