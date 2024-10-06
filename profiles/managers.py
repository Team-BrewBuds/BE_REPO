from django.db import models


class RelationshipManager(models.Manager):
    
    def following(self, user):  # 팔로우한 사용자
        return self.filter(from_user=user, relationship_type="follow")
    
    def followers(self, user):  # 나를 팔로우한 사용자
        return self.filter(to_user=user, relationship_type="follow")
    
    def blocking(self, user):  # 차단한 사용자
        return self.filter(from_user=user, relationship_type="block")
    
    def blocked(self, user):  # 나를 차단한 사용자
        return self.filter(to_user=user, relationship_type="block")
