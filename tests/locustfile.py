from locust import HttpUser, between, task


class BrewBudsUser(HttpUser):
    wait_time = between(1, 3)  # 각 태스크 사이의 대기 시간

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = ""  # 토큰 값 입력

        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        self.page_size = 10
        self.current_page = 1

    @task(1)
    def get_following_user_list(self):
        self.client.get("/records/feed/", params={"feed_type": "following", "page": 1})

    @task(1)
    def get_following_user_list_2(self):
        self.client.get("/records/feed/", params={"feed_type": "following", "page": 2})
