from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    객체에 대한 읽기 권한은 모든 사용자에게 허용하고,
    수정/삭제 권한은 작성자에게만 허용하는 권한 클래스
    """

    @classmethod
    def check_object_permission(cls, request_method: str, user, obj) -> None:
        """
        서비스 레이어에서 사용할 수 있는 권한 검사 메서드

        Args:
            request_method: HTTP 메서드 (GET, POST, PUT, DELETE 등)
            user: 요청한 사용자 객체
            obj: 권한을 검사할 대상 객체

        Raises:
            PermissionDenied: 권한이 없는 경우
        """
        if request_method in permissions.SAFE_METHODS:
            return

        if not (obj.author == user or user.is_staff):
            raise PermissionDenied("Permission denied: not the owner")

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user
