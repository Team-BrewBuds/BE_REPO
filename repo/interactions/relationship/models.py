from django.db import models

from repo.interactions.relationship.managers import RelationshipManager
from repo.profiles.models import CustomUser


class Relationship(models.Model):

    RELATIONSHIP_TYPE_CHOICES = [
        ("follow", "팔로우"),
        ("block", "차단"),
    ]

    from_user = models.ForeignKey(CustomUser, related_name="relationships_from", on_delete=models.CASCADE)
    to_user = models.ForeignKey(CustomUser, related_name="relationships_to", on_delete=models.CASCADE)
    relationship_type = models.CharField(max_length=10, choices=RELATIONSHIP_TYPE_CHOICES, verbose_name="관계 유형")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    objects: RelationshipManager = RelationshipManager()

    def __str__(self):
        return f"{self.from_user.nickname} {self.get_relationship_type_display()} {self.to_user.nickname}"

    class Meta:
        db_table = "relationship"
        verbose_name = "관계"
        verbose_name_plural = "관계"
