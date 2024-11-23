import re

from repo.common.exception.exceptions import ValidationException
from repo.profiles.models import CustomUser


class UserValidator:
    """사용자 유효성 검사를 위한 Validator 클래스"""

    @staticmethod
    def validate_nickname(value, instance=None):
        """닉네임 유효성 검사"""

        if not value and value is not None:
            raise ValidationException(
                detail="닉네임은 공백일 수 없습니다.",
                code="nickname_invalid",
            )

        if not re.match(r"^[가-힣a-zA-Z0-9]{2,12}$", value):
            raise ValidationException(
                detail="닉네임은 2 ~ 12자의 한글 영어 또는 숫자만 가능합니다.",
                code="nickname_invalid",
            )

        is_nickname_exists = CustomUser.objects.filter(nickname=value).exclude(pk=instance.pk if instance else None).exists()
        if is_nickname_exists:
            raise ValidationException(
                detail="이미 존재하는 닉네임입니다.",
                code="nickname_invalid",
            )

        return value
