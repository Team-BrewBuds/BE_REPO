from django.contrib import admin

from .models import CustomUser, UserDetail


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["nickname", "email", "gender", "login_type", "created_at", "is_staff"]
    list_filter = ["login_type", "gender", "created_at"]
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


class UserDetailAdmin(admin.ModelAdmin):
    list_display = ["user", "introduction", "is_certificated", "get_coffee_life_display", "get_preferred_bean_taste_display"]
    list_filter = ["is_certificated"]
    search_fields = ["user__nickname", "user__email"]

    def get_coffee_life_display(self, obj):
        coffee_life = obj.coffee_life
        active_choices = [key for key, value in coffee_life.items() if value]
        formatted_choices = {
            "cafe_tour": "카페 투어",
            "coffee_extraction": "커피 추출",
            "coffee_study": "커피 공부",
            "cafe_alba": "카페 알바",
            "cafe_work": "카페 일 경험",
            "cafe_operation": "카페 운영",
        }
        return ", ".join([formatted_choices[choice] for choice in active_choices]) or "-"

    def get_preferred_bean_taste_display(self, obj):
        preferred_bean_taste = obj.preferred_bean_taste
        active_choices = [key for key, value in preferred_bean_taste.items() if value]
        formatted_choices = {"body": "바디", "acidity": "산미", "bitterness": "쓴맛", "sweetness": "단맛"}
        return ", ".join([formatted_choices[choice] for choice in active_choices]) or "-"

    get_coffee_life_display.short_description = "커피 생활"
    get_preferred_bean_taste_display.short_description = "선호하는 원두 맛"


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserDetail, UserDetailAdmin)
