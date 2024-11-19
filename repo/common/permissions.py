from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    객체에 대한 읽기 권한은 모든 사용자에게 허용하고,
    수정/삭제 권한은 작성자에게만 허용하는 권한 클래스
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user
