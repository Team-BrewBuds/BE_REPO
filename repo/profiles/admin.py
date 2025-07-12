from django.contrib import admin
from django.utils.safestring import mark_safe
from rangefilter.filters import DateRangeFilter, NumericRangeFilter

from repo.common.admin_filters import IsCertificatedFilter, IsCoffeeLifeFilter

from .models import CustomUser, UserDetail


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["id", "nickname", "gender", "birth", "login_type", "email", "created_at", "is_superuser", "is_active", "last_login"]
    list_filter = [
        "gender",
        "login_type",
        "created_at",
        ("created_at", DateRangeFilter),
        "is_superuser",
        "is_staff",
        "is_active",
        "last_login",
        ("birth", NumericRangeFilter),
    ]
    search_fields = ["nickname", "email"]
    actions = ["make_user_admin", "make_user_normal"]

    @admin.action(description="관리자로 수정")
    def make_user_admin(self, request, queryset):
        queryset.update(is_staff=True)
        self.message_user(request, f"{queryset.count()} 명의 사용자가 관리자로 수정되었습니다.")

    @admin.action(description="일반 사용자로 수정")
    def make_user_normal(self, request, queryset):
        queryset.update(is_staff=False)
        self.message_user(request, f"{queryset.count()} 명의 사용자가 일반 사용자로 수정되었습니다.")


@admin.register(UserDetail)
class UserDetailAdmin(admin.ModelAdmin):
    list_display = ["user", "introduction", "get_coffee_life_display", "get_preferred_bean_taste_display", "is_certificated"]
    list_filter = [IsCoffeeLifeFilter, IsCertificatedFilter]
    search_fields = ["user__nickname", "user__email"]

    def get_coffee_life_display(self, obj):
        formatted_choices = {
            "cafe_tour": "카페 투어",
            "coffee_extraction": "커피 추출",
            "coffee_study": "커피 공부",
            "cafe_alba": "카페 알바",
            "cafe_work": "카페 일 경험",
            "cafe_operation": "카페 운영",
        }

        result = []
        for key, label in formatted_choices.items():
            value = obj.coffee_life.get(key, False)
            result.append(f"{label}: {'✔' if value else '✘'}")

        return mark_safe(" | ".join(result))

    def get_preferred_bean_taste_display(self, obj):
        preferred_bean_taste = obj.preferred_bean_taste
        formatted_choices = {"body": "바디", "acidity": "산미", "bitterness": "쓴맛", "sweetness": "단맛"}

        result = []
        for key, label in formatted_choices.items():
            value = preferred_bean_taste.get(key, 3)
            result.append(f"{label}: {value}")

        return mark_safe(" | ".join(result))

    get_coffee_life_display.short_description = "커피 생활"
    get_preferred_bean_taste_display.short_description = "선호하는 원두 맛"
