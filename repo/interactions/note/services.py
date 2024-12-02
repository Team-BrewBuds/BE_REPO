from django.db.models import OuterRef

from repo.beans.models import Bean
from repo.common.exception.exceptions import ConflictException, NotFoundException
from repo.records.models import Post, TastedRecord

from .models import Note


class NoteService:
    def __init__(self, note_repo=Note.objects):
        self.note_repo = note_repo

    def is_existing_note(self, user, object_type, object_id):
        return self.note_repo.filter(author=user, **{f"{object_type}__id": object_id}).exists()

    def _get_instance(self, object_type, object_id):
        model_map = {"post": Post, "tasted_record": TastedRecord, "bean": Bean}
        return model_map[object_type].objects.get(id=object_id)

    def create(self, user, object_type, object_id):
        if self.is_existing_note(user, object_type, object_id):
            raise ConflictException(detail="Note already exists", code="note_exists")

        instance = self._get_instance(object_type, object_id)
        note = self.note_repo.create(author=user, **{f"{object_type}": instance})
        return note

    def delete(self, user, object_type, object_id):
        instance = self._get_instance(object_type, object_id)
        note = self.note_repo.filter(author=user, **{f"{object_type}": instance}).first()

        if not note:
            raise NotFoundException(detail="Note not found", code="note_not_found")

        note.delete()
        return note

    def get_note_subquery_for_post(self, user):
        return self.note_repo.filter(author=user, post_id=OuterRef("pk"))

    def get_note_subquery_for_tasted_record(self, user):
        return self.note_repo.filter(author=user, tasted_record_id=OuterRef("pk"))
