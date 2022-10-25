from django.test import TestCase, Client
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
        cls.url_post_edit = "/posts/1/edit/"
        cls.url_create_post = "posts/create_post.html"
        cls.url_create = "/create/"

    def setUp(self):
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username="HasNoName")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем автора
        self.author = Client()
        # Авторизуем автора
        self.author.force_login(StaticURLTests.user)

    # Проверяем общедоступные страницы
    def test_home_url_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        TEMPLATE_URLS = {
            "posts/group_list.html": "/group/test-slug/",
            "posts/profile.html": "/profile/auth/",
            "posts/index.html": "/",
            "posts/post_detail.html": "/posts/1/",
        }
        for template, address in TEMPLATE_URLS.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    # Проверяем  доступ автору к редактрированию
    def test_autor_edit(self):
        """Страница редактирования поста"""
        response = self.author.get(self.url_post_edit)
        self.assertTemplateUsed(response, self.url_create_post)

    # Проверяем досуп авторизовоному пользователю к созданиею поста
    def test_create_post(self):
        """Страница создания нового поста"""
        response = self.authorized_client.get(self.url_create)
        self.assertTemplateUsed(response, self.url_create_post)

    # Проверка ошибки при вызове несуществующей страницы
    def test_non_existent_page(self):
        """Не существующая страница"""
        response = self.guest_client.get("/unexistent-page/")
        self.assertEqual(response.status_code, 404)
