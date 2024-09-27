from rest_framework import serializers
from .models import Bean, Bean_Taste, Bean_Taste_Review 

class BeanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bean
        fields = '__all__'

class BeanTasteAndReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bean_Taste_Review
        fields = '__all__'
