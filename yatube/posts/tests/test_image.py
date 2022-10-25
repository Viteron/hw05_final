from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.core.cache import cache
import shutil
import tempfile
from django.conf import settings

from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="test_user")
        cls.group = Group.objects.create(
            title="Тестовая группа", slug="test-slug"
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            group=cls.group,
            author=cls.user,
            image=cls.uploaded,
        )

    def setUp(self):
        cache.clear()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_home_page_image_context(self):
        """Проверка передачи картинки в контекст на главной странице"""
        cache.clear()
        response = self.authorized_client.get(reverse("posts:index"))
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object.image, ImageTests.post.image)

    def test_profile_page_image_context(self):
        """Проверка передачи картинки в контекст на странице profile"""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": "test_user"})
        )
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object.image, ImageTests.post.image)

    def test_group_list_page_image_correct_context(self):
        """Проверка передачи картинки в контекст на странице group_list"""
        response = self.authorized_client.get(
            reverse("posts:list", kwargs={"slug": "test-slug"})
        )
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object.image, ImageTests.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Проверка передачи картинки в контекст на странице post_detail"""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(
            response.context["posts"].image, ImageTests.post.image
        )

    def test_post_create_with_image_in_DB(self):
        """Проверка создания поста с картинокой в БД"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст2",
            "group": self.group.id,
            "image": ImageTests.post.image,
        }
        self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_create_comment_non_authorization_client(self):
        """Создание коментария под анонимом
        (кол-во коментов в БД не должно увеличиться)"""
        comment_count = Comment.objects.count()
        form_data = {
            "comment": "Текст, которого не может быть",
        }
        response = self.guest_client.post(
            reverse("posts:add_comment", args=[self.post.id]), data=form_data
        )
        # Проверяем редирект
        self.assertRedirects(response, "/auth/login/?next=/posts/1/comment/")
        # Проверяем неизменность числа постов
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        comment_count = Comment.objects.count()
        form_data = {
            "text": "Новый комент",
        }
        response = self.authorized_client.post(
            reverse("posts:add_comment", args=[self.post.id]), data=form_data
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse("posts:post_detail", args=[self.post.id])
        )
        # Проверяем, увеличилось ли число коментов
        self.assertEqual(Comment.objects.count(), comment_count + 1)

        new_comment = Comment.objects.get(id=1).text
        # Проверяем, появился ли комент
        self.assertEqual(new_comment, "Новый комент")
