bean_info_keys = {
    "원두 유형": "bean_type",
    "원두 이름": "name",
    "원산지": "origin_country",
    "디카페인 여부": "is_decaf",
    "추출 방식": "extraction",
    "로스팅 포인트": "roast_point",
    "가공 방식": "process",
    "생산 지역": "region",
    "음료 유형": "bev_type",
    "로스터리": "roastery",
    "품종": "variety",
    "공식원두 여부": "is_official",
}

bean_taste_review_keys = {
    "맛": "flavor",
    "바디감": "body",
    "산미": "acidity",
    "쓴맛": "bitterness",
    "단맛": "sweetness",
    "별점": "star",
    "시음 날짜": "tasted_at",
    "시음 장소": "place",
}
only_tasted_record_keys = {
    "작성자": "author",
    "시음 내용": "content",
    "태그": "tag",
    "작성 일시": "created_at",
}

full_tasted_record_keys = {
    **bean_taste_review_keys,
    **bean_info_keys,
    **only_tasted_record_keys,
}

post_keys = {"작성 일시": "created_at", "작성자": "author", "주제": "subject", "제목": "title", "내용": "content", "태그": "tag"}
