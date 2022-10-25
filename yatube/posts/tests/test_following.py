from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post, Follow, User


class FollowingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.user2 = User.objects.create_user(username="SecondAuth")
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
        self.second_author = Client()
        self.second_author.force_login(self.user2)

    def tearDown(self):
        cache.clear()

    def test_autoriz_user_following(self):
        """Проверка подписки пользователя на других"""
        count_follow = Follow.objects.count()
        tamplate_follow = "posts:profile_follow"
        self.second_author.get(
            reverse(tamplate_follow, kwargs={"username": self.post.author})
        )
        # проверяем подписку
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(Follow.objects.last().author, self.post.author)
        self.assertEqual(Follow.objects.last().user, self.user2)
        # проверяем отписку

    def test_autoriz_user_unfollowing(self):
        """Проверка отписки пользователя от автора"""
        tamplate_unfollow = "posts:profile_unfollow"
        count_follow = Follow.objects.count()
        self.second_author.get(
            reverse(tamplate_unfollow, kwargs={"username": self.post.author})
        )
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_new_post_in_follow_list(self):
        cache.clear()
        """Проверка появления новой записи в ленте подписок"""
        self.second_author.get(
            reverse(
                "posts:profile_follow", kwargs={"username": self.post.author}
            )
        )
        response = self.second_author.get(reverse("posts:follow_index"))
        page_object = response.context["page_obj"][0]
        self.assertEqual(page_object, self.post)
        # Проверка что нет других записей
        self.assertNotEqual(page_object, self.post2)
