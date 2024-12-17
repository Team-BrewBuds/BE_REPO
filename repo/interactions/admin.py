from django.contrib import admin

from repo.interactions.note.models import Note
from repo.interactions.relationship.models import Relationship

admin.site.register(Relationship)
admin.site.register(Note)
