from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.utils import get_paginated_response_with_class
from repo.interactions.schemas import *
from repo.interactions.serializers import (
    UserBlockListSerializer,
    UserFollowListSerializer,
)
from repo.interactions.services import RelationshipService
from repo.profiles.models import CustomUser


@FollowListSchema.follow_list_schema_view
class FollowListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        self.relationship_service = RelationshipService()

    def get(self, request):
        follow_type = request.query_params.get("type")
        request_user = request.user

        relationships = self.relationship_service.get_user_relationships_by_follow_type(follow_type, request_user)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(relationships, request)

        serializer = UserFollowListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


@FollowListCreateDeleteSchema.follow_list_create_delete_schema_view
class FollowListCreateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        self.relationship_service = RelationshipService()

    def get(self, request, id):
        follow_type = request.query_params.get("type")
        request_user = request.user
        target_user = get_object_or_404(CustomUser, id=id)

        relationships = self.relationship_service.get_user_relationships_by_follow_type(follow_type, request_user, target_user)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(relationships, request)

        serializer = UserFollowListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, id):
        user = request.user
        follow_user = get_object_or_404(CustomUser, id=id)

        relationship, created = self.relationship_service.follow(user, follow_user)
        if not relationship:
            return Response({"error": "user is blocking or blocked"}, status=status.HTTP_403_FORBIDDEN)
        elif not created:
            return Response({"error": "user is already following"}, status=status.HTTP_409_CONFLICT)
        return Response({"success": "follow"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        following_user = get_object_or_404(CustomUser, id=id)

        is_deleted = self.relationship_service.unfollow(user, following_user)
        if not is_deleted:
            return Response({"error": "user is not following"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": "unfollow"}, status=status.HTTP_200_OK)


@BlockListSchema.block_list_schema_view
class BlockListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        self.relationship_service = RelationshipService()

    def get(self, request):
        user = request.user
        queryset = self.relationship_service.get_blocking(user).order_by("-id")
        return get_paginated_response_with_class(request, queryset, UserBlockListSerializer)


@BlockListCreateDeleteSchema.block_list_create_delete_schema_view
class BlockListCreateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self):
        self.relationship_service = RelationshipService()

    def post(self, request, id):
        user = request.user
        target_user = get_object_or_404(CustomUser, id=id)

        relationship, created = self.relationship_service.block(user, target_user)
        if not created:
            return Response({"error": "User is already blocked"}, status=status.HTTP_409_CONFLICT)
        return Response({"success": "block"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        block_user = get_object_or_404(CustomUser, id=id)

        is_deleted = self.relationship_service.unblock(user, block_user)
        if not is_deleted:
            return Response({"error": "User is not blocking"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": "unblock"}, status=status.HTTP_200_OK)
