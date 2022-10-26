from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from itertools import islice

from ..models import Group, Post, Follow, User


class FollowingTests(TestCase):
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
        self.second_author = Client()
        self.second_author.force_login(self.user2)

    def test_autoriz_user_following(self):
        """Проверка подписки пользователя на других"""
        count_follow = Follow.objects.count()
        post = Post.objects.first()
        tamplate_follow = "posts:profile_follow"
        self.second_author.get(
            reverse(tamplate_follow, kwargs={"username": post.author})
        )
        # проверяем подписку
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(Follow.objects.last().author, post.author)
        self.assertEqual(Follow.objects.last().user, self.user2)

    def test_autoriz_user_unfollowing(self):
        """Проверка отписки пользователя от автора"""
        tamplate_unfollow = "posts:profile_unfollow"
        count_follow = Follow.objects.count()
        post = Post.objects.first()
        self.second_author.get(
            reverse(tamplate_unfollow, kwargs={"username": post.author})
        )
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_new_post_in_follow_list(self):
        """Проверка что пост не появился у того, кто не подписан"""
        post = Post.objects.first()
        cache.clear()
        another_user = User.objects.create(username="NoName")
        self.authorized_client.force_login(another_user)
        response_another_follower = self.authorized_client.get(
            reverse("posts:follow_index")
        )
        self.assertNotIn(post, response_another_follower.context["page_obj"])
