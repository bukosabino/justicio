import locust


class ApiUser(locust.HttpUser):
    wait_time = locust.constant_pacing(1)
    input_data = (
        "¿Es de aplicación la ley de garantía integral de la libertad sexual a niños (varones) menores de edad "
        "víctimas de violencias sexuales o solo a niñas y mujeres?"
    )

    def health_check(self):
        self.client.get("/healthcheck")

    def endpoint404(self):
        with self.client.get(
            "/url_does_not_exist", catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()


class ApiAsyncUser(ApiUser):

    url = "/aqa"

    @locust.task
    def aqa(self):
        self.client.get(self.url, json=self.input_data)


class ApiSyncUser(ApiUser):

    url = "/qa"

    @locust.task
    def qa(self):
        self.client.get(self.url, json=self.input_data)
