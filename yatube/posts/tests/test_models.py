from django.test import TestCase
from django.core.cache import cache

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )

    def setUp(self):
        cache.clear()

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        # Напишите проверку тут
        field_str = {
            self.post.text[:15]: str(self.post),
            self.group.title: str(self.group),
        }
        for expected_object_name, expected in field_str.items():
            self.assertEqual(expected_object_name, expected)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            "text": "blog text",
            "pub_date": "date of release",
            "author": "author of post",
            "group": "name of group",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            "text": "Текст блога",
            "group": "Группа, к которой будет относиться пост",
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value
                )
