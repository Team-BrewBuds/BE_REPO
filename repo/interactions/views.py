from django.shortcuts import get_object_or_404
from rest_framework import status
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
        return get_paginated_response_with_class(request, relationships, UserFollowListSerializer)


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
        return get_paginated_response_with_class(request, relationships, UserFollowListSerializer)

    def post(self, request, id):
        user = request.user
        follow_user = get_object_or_404(CustomUser, id=id)

        self.relationship_service.follow(user, follow_user)
        return Response({"success": "follow"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        following_user = get_object_or_404(CustomUser, id=id)

        self.relationship_service.unfollow(user, following_user)
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

        self.relationship_service.block(user, target_user)
        return Response({"success": "block"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        block_user = get_object_or_404(CustomUser, id=id)

        self.relationship_service.unblock(user, block_user)
        return Response({"success": "unblock"}, status=status.HTTP_200_OK)
