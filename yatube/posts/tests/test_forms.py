from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from itertools import islice

from ..models import Group, Post, User


class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.user2 = User.objects.create_user(username="NotAuth")

        cls.COUNT_CREATW_POST = 2
        batch_size = 1
        cls.post = (
            Post(
                author=cls.user,
                group=Group.objects.create(
                    title="Тестовая группа %s" % i,
                    slug="test-slug%s" % i,
                    description="Тестовое описание",
                ),
                text="Test %s" % i,
            )
            for i in range(cls.COUNT_CREATW_POST)
        )
        while True:
            batch = list(islice(cls.post, batch_size))
            if not batch:
                break
            Post.objects.bulk_create(batch, batch_size)

    def setUp(self):
        cache.clear()
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
        group_first = Group.objects.first()
        form_data = {
            "text": "Тестовый текст",
            "group": group_first.id,
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
        # group_first = Group.objects.first()
        # group_second = Group.objects.last()
        post = Post.objects.first()
        group = post.group_id
        form_data = {
            "text": "Новый текст",
            "group": group,
        }
        response = self.authorized_client.post(
            reverse("posts:edit", args=[post.id]), data=form_data
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse("posts:post_detail", args=[group])
        )
        new_post = Post.objects.get(id=1).text

        # Проверяем, изменилась ли запись
        self.assertEqual(new_post, "Новый текст")

    def test_create_post_non_authorization_client(self):
        """Создание поста под анонимом
        (кол-во постов БД не должно увеличиться)"""
        post_count = Post.objects.count()
        group_first = Group.objects.first()
        form_data = {
            "text": "Текст, которого не может быть",
            "group": group_first.id,
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
        group_first = Group.objects.first()
        post = Post.objects.first()
        form_data = {
            "text": "Текст, которого не может быть",
            "group": group_first.id,
        }
        response = self.guest_client.post(
            reverse("posts:edit", args=[post.id]), data=form_data
        )
        # Проверяем редирект
        self.assertRedirects(
            response,
            "/auth/login/?next=/posts/" + str(post.id) + "/edit/",
        )
        # Берем 1 запись в БД
        new_post = Post.objects.get(id=1).text

        # Проверяем, изменилась ли запись
        self.assertEqual(new_post, "Test 0")

    def test_edit_post_not_author_client(self):
        """Редактирование не автором
        (пост не должен изменить значения полей)"""
        group_first = Group.objects.first()
        group_second = Group.objects.last()
        post = Post.objects.first()
        form_data = {
            "text": "Текст, которого не может быть",
            "group": group_first.id,
        }
        response = self.not_author.post(
            reverse("posts:edit", args=[post.id]), data=form_data
        )
        # Проверяем редирект
        """self.assertRedirects(
            response,
            "/auth/login/?next=/posts/" + str(self.post.id) + "/edit/",
        )"""
        self.assertRedirects(
            response, reverse("posts:post_detail", args=[group_second.id])
        )
        # Берем 1 запись в БД
        new_post = Post.objects.get(id=1).text

        # Проверяем, изменилась ли запись
        self.assertEqual(new_post, "Test 0")

    def test_edit_group(self):
        """Редактирование с изменением группы"""
        group_last = Group.objects.last()
        # group_first = Group.objects.first()
        post = Post.objects.first()
        form_data = {
            "text": "Тестовый пост",
            "group": group_last.id,
        }
        response = self.author.post(
            reverse("posts:edit", args=[post.id]), data=form_data
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse("posts:post_detail", args=[group_last.id])
        )
        new_post = Post.objects.first().group.title

        # Проверяем, изменилась ли запись
        self.assertEqual(new_post, "Тестовая группа 1")
