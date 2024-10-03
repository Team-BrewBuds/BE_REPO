from django.db import models
from django.apps import apps
from django.shortcuts import get_object_or_404


class NoteManagers(models.Manager):

    model_map = {
        "post": "records.Post",
        "tasted_record": "records.Tasted_Record",
        "bean": "beans.Bean"
    }

    def get_notes_for_user_and_object(self, user, object_type, object_id):
        model = self._get_model(object_type)
        obj = get_object_or_404(model, pk=object_id)
        notes = obj.note_set.filter(user=user).order_by("-created_at")
        return notes

    def create_note_for_object(self, user, object_type, object_id):
        model = self._get_model(object_type)
        obj = get_object_or_404(model, pk=object_id)
        # 올바른 필드에 객체를 설정
        if object_type == 'post':
            note = self.model(user=user, post=obj)
        elif object_type == 'tasted_record':
            note = self.model(user=user, tasted_record=obj)
        elif object_type == 'bean':
            note = self.model(user=user, bean=obj)
        else:
            raise ValueError("Invalid object_type")
        note.save()
        return note
    
    def _get_model(self, object_type):
        model_path = self.model_map.get(object_type)
        app_label, model_name = model_path.split(".")
        return apps.get_model(app_label,model_name)
    