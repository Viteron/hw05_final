from django.test import TestCase, Client, override_settings
from django.urls import reverse
from itertools import islice
from django.core.cache import cache


from ..models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

        cls.COUNT_CREATW_POST = 101
        cls.COUNT_POST_IN_PAGE = 10

        cls.count_page = cls.COUNT_CREATW_POST // cls.COUNT_POST_IN_PAGE
        cls.count_post_in_last_page = cls.COUNT_CREATW_POST - (
            cls.COUNT_POST_IN_PAGE * cls.count_page
        )
        cls.last_page = cls.count_page + 1
        batch_size = 1
        cls.post = (
            Post(author=cls.user, group=cls.group, text="Test %s" % i)
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

    def test_index_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице
        равно задонному числу на одной странице."""
        cache.clear()
        response = self.client.get(reverse("posts:index"))
        self.assertEqual(
            len(response.context["page_obj"]), self.COUNT_POST_IN_PAGE
        )

    def test_index_second_page_contains_three_records(self):
        """Проверка постов на последней странице"""
        response = self.client.get(
            reverse("posts:index") + "?page=" + str(self.last_page)
        )
        self.assertEqual(
            len(response.context["page_obj"]), self.count_post_in_last_page
        )

    def test_group_list_first_page_contains_ten_records(self):
        """Проверка отображения постов по группам"""
        response = self.client.get(
            reverse("posts:list", kwargs={"slug": "test-slug"})
        )
        self.assertEqual(
            len(response.context["page_obj"]), self.COUNT_POST_IN_PAGE
        )

    def test_group_list_second_page_contains_three_records(self):
        """Проверка последней страницы в группах"""
        response = self.client.get(
            reverse("posts:list", kwargs={"slug": "test-slug"})
            + "?page="
            + str(self.last_page)
        )
        self.assertEqual(
            len(response.context["page_obj"]), self.count_post_in_last_page
        )

    def test_profile_first_page_contains_ten_records(self):
        """Проверка постов на 1 странице профайла"""
        response = self.client.get(
            reverse("posts:profile", kwargs={"username": "auth"})
        )
        self.assertEqual(
            len(response.context["page_obj"]), self.COUNT_POST_IN_PAGE
        )

    def test_profile_second_page_contains_three_records(self):
        """Проверка последней страницы профайла"""
        response = self.client.get(
            reverse("posts:profile", kwargs={"username": "auth"})
            + "?page="
            + str(self.last_page)
        )
        self.assertEqual(
            len(response.context["page_obj"]), self.count_post_in_last_page
        )
