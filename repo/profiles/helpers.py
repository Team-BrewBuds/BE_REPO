class CoffeeLifeHelper:
    def __init__(self, coffee_life_data):
        """
        coffee_life_data : JSON
        """
        self.coffee_life_data = coffee_life_data

    def update_coffee_life(self, category, value):
        """
        커피 생활의 특정 카테고리의 값을 업데이트합니다.
        :param category: 업데이트할 카테고리 (예: 'cafe_tour', 'coffee_extraction')
        :param value: 업데이트할 값 (True 또는 False)
        """
        if category in self.coffee_life_data:
            self.coffee_life_data[category] = value
        else:
            raise ValueError(f"{category}는 유효한 커피 생활 항목이 아닙니다.")

    def is_active_in_category(self, category):
        """
        특정 커피 생활 카테고리가 활성화되어 있는지 확인합니다.
        :param category: 확인할 카테고리 (예: 'cafe_tour')
        :return: 해당 카테고리가 활성화되어 있으면 True, 그렇지 않으면 False
        """
        return self.coffee_life_data.get(category, False)

    def get_all_categories(self):
        """
        모든 커피 생활 카테고리의 상태를 반환합니다.
        :return: 커피 생활 데이터 (JSON)
        """
        return self.coffee_life_data

    def get_true_categories(self):
        """
        모든 커피 생활 카테고리 중 True인 카테고리를 반환합니다.
        :return: True인 카테고리 리스트
        """
        true_categories = [c for c in self.coffee_life_data if self.coffee_life_data[c]]
        return true_categories


class PreferredBeanTasteHelper:
    def __init__(self, preferred_bean_taste):
        """
        preferred_bean_taste_data : JSON
        """
        self.preferred_bean_taste = preferred_bean_taste

    def update_taste(self, taste_type, value):
        """
        특정 원두 맛의 값을 업데이트합니다.
        :param taste_type: 업데이트할 맛 유형 (예: 'body', 'acidity')
        :param value: 업데이트할 값 (예: 1~5)
        """
        if taste_type in self.preferred_bean_taste:
            self.preferred_bean_taste[taste_type] = value
        else:
            raise ValueError(f"{taste_type}는 유효한 맛 유형이 아닙니다.")

    def get_taste_value(self, taste_type):
        """
        특정 원두 맛 유형의 값을 반환합니다.
        :param taste_type: 확인할 맛 유형 (예: 'body')
        :return: 해당 맛 유형의 값 (1~5)
        """
        return self.preferred_bean_taste.get(taste_type, 3)  # 기본값 3

    def get_all_tastes(self):
        """
        모든 원두 맛 선호도를 반환합니다.
        :return: 원두 맛 데이터 (JSON)
        """
        return self.preferred_bean_taste
