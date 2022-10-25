from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        # Создаем авторизованный клиент
        self.guest_client = Client()

    def test_cash_index_page(self):
        """Проверка работы кэша для списка постов"""
        response = self.guest_client.get(reverse("posts:index"))
        first_response = response.content
        self.post.delete()
        response = self.guest_client.get(reverse("posts:index"))
        second_response = response.content
        self.assertEqual(first_response, second_response)
        cache.clear()
        response = self.guest_client.get(reverse("posts:index"))
        third_response = response.content
        self.assertNotEqual(first_response, third_response)
