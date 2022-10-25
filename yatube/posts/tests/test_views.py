from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Group, Post, User


class PostPagesTests(TestCase):
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
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            "posts/index.html": reverse("posts:index"),
            "posts/group_list.html": reverse(
                "posts:list", kwargs={"slug": "test-slug"}
            ),
            "posts/profile.html": reverse(
                "posts:profile", kwargs={"username": "auth"}
            ),
            "posts/post_detail.html": reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            ),
            "posts/create_post.html": reverse(
                "posts:edit", kwargs={"post_id": self.post.id}
            ),
            "core/404.html": reverse(
                "posts:profile", kwargs={"username": "NotfoundUser"}
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:index"))
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object.author.username, "auth")
        self.assertEqual(first_object.text, "Тестовый пост")
        self.assertEqual(first_object.group.title, "Тестовая группа")

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:list", kwargs={"slug": "test-slug"})
        )
        first_page_object = response.context["page_obj"][0]
        self.assertEqual(first_page_object.text, "Тестовый пост")
        self.assertEqual(first_page_object.group.title, "Тестовая группа")
        self.assertEqual(first_page_object.author.username, "auth")
        self.assertIsInstance(response.context["group"], Group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": "auth"})
        )
        first_page_object = response.context["page_obj"][0]
        first_post_object = response.context["posts"][0]
        autor_context = response.context["author"]
        self.assertEqual(autor_context.username, "auth")
        self.assertIsInstance(first_post_object, Post)
        self.assertEqual(first_page_object.text, "Тестовый пост")

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertIsInstance(response.context["posts"], Post)

    def test_posts_edit_page_show_correct_context(self):
        """Шаблон posts_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:edit", kwargs={"post_id": self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_create_page_show_correct_context(self):
        """Шаблон posts_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)
