from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.user2 = User.objects.create_user(username="NotAuth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.group2 = Group.objects.create(
            title="Группа №2",
            slug="test-slug2",
            description="Дополнительная группа для проверки",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
        )
        cls.post2 = Post.objects.create(
            author=cls.user,
            text="Тестовый 2 пост",
            group=cls.group2,
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем автора
        self.author = Client()
        # Авторизуем автора
        self.author.force_login(self.user)
        # Создаем не автора
        self.not_author = Client()
        self.not_author.force_login(self.user2)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст",
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse("posts:profile", args=[self.user])
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_edit_post_and_check_edit_in_base(self):
        """Проверка изменений поста после валидации и изменение в БД"""
        form_data = {
            "text": "Новый текст",
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse("posts:edit", args=[self.post.id]), data=form_data
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse("posts:post_detail", args=[self.group.id])
        )
        new_post = Post.objects.get(id=1).text

        # Проверяем, изменилась ли запись
        self.assertEqual(new_post, "Новый текст")

    def test_create_post_non_authorization_client(self):
        """Создание поста под анонимом
        (кол-во постов БД не должно увеличиться)"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Текст, которого не может быть",
            "group": self.group.id,
        }
        response = self.guest_client.post(
            reverse("posts:post_create"), data=form_data
        )
        # Проверяем редирект
        self.assertRedirects(response, "/auth/login/?next=/create/")
        # Проверяем неизменность числа постов
        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_post_non_authorization_client(self):
        """Редактирование под анонимом
        (пост не должен изменить значения полей)"""
        form_data = {
            "text": "Текст, которого не может быть",
            "group": self.group.id,
        }
        response = self.guest_client.post(
            reverse("posts:edit", args=[self.post.id]), data=form_data
        )
        # Проверяем редирект
        self.assertRedirects(
            response,
            "/auth/login/?next=/posts/" + str(self.post.id) + "/edit/",
        )
        # Берем 1 запись в БД
        new_post = Post.objects.get(id=1).text

        # Проверяем, изменилась ли запись
        self.assertEqual(new_post, "Тестовый пост")

    def test_edit_post_not_author_client(self):
        """Редактирование не автором
        (пост не должен изменить значения полей)"""
        form_data = {
            "text": "Текст, которого не может быть",
            "group": self.group.id,
        }
        response = self.not_author.post(
            reverse("posts:edit", args=[self.post.id]), data=form_data
        )
        # Проверяем редирект
        """self.assertRedirects(
            response,
            "/auth/login/?next=/posts/" + str(self.post.id) + "/edit/",
        )"""
        self.assertRedirects(
            response, reverse("posts:post_detail", args=[self.group.id])
        )
        # Берем 1 запись в БД
        new_post = Post.objects.get(id=1).text

        # Проверяем, изменилась ли запись
        self.assertEqual(new_post, "Тестовый пост")

    def test_edit_group(self):
        """Редактирование с изменением группы"""
        form_data = {
            "text": "Тестовый пост",
            "group": self.group2.id,
        }
        response = self.author.post(
            reverse("posts:edit", args=[self.post.id]), data=form_data
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse("posts:post_detail", args=[self.group.id])
        )
        new_post = Post.objects.get(id=1).group.title

        # Проверяем, изменилась ли запись
        self.assertEqual(new_post, "Группа №2")
