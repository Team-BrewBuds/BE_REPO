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


class IsAuthorOrOwner(permissions.BasePermission):
    """
    삭제 권한
    게시물(게시글, 시음기록)의 작성자 또는 댓글 작성자인경우 삭제 가능
    ex) 게시물 작성자는 자신 및 타인의 댓글도 삭제 가능한 권한
    """

    def has_permission(self, request, view):
        return request.method == "DELETE"

    def has_object_permission(self, request, view, obj):
        return any(
            [
                obj.author and obj.author == request.user,
                obj.post and obj.post.author == request.user,
                obj.tasted_record and obj.tasted_record.author == request.user,
            ]
        )
