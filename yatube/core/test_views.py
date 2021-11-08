from http import HTTPStatus

from django.test import TestCase


class TestCoreViews(TestCase):
    def test_404_view(self) -> None:
        """Check if correct user see correct page with 404"""
        response = self.client.get('/unexpected-page/')
        self.assertTemplateUsed(response, 'core/404.html')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
