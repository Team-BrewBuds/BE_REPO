from rest_framework import serializers


class BaseQuerySerializer(serializers.Serializer):
    """기본 추천 검색어 시리얼라이저"""

    q = serializers.CharField(required=True, allow_blank=False)


class BaseSuggestInputSerializer(BaseQuerySerializer):
    """검색어 추천 기본 시리얼라이저"""

    pass


class BuddySuggestInputSerializer(BaseSuggestInputSerializer):
    """사용자 검색어 추천 시리얼라이저"""

    pass


class BeanSuggestInputSerializer(BaseSuggestInputSerializer):
    """원두 검색어 추천 시리얼라이저"""

    pass


class TastedRecordSuggestInputSerializer(BaseSuggestInputSerializer):
    """시음기록 검색어 추천 시리얼라이저"""

    pass


class PostSuggestInputSerializer(BaseSuggestInputSerializer):
    """게시글 검색어 추천 시리얼라이저"""

    pass


class SuggestSerializer(serializers.Serializer):
    """검색어 추천 시리얼라이저"""

    suggestions = serializers.ListField(child=serializers.CharField(), required=True)
