from django.test import TestCase, Client


class BasicTestCase(TestCase):
    def test_index(self):
        # A really simple test to validate that the environment is working.
        c = Client()
        response = c.get("/")
        assert response.status_code == 200
