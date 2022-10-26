from django.db import models
from django.contrib.auth import get_user_model
from core.models import CreatedModel
from django.db.models import UniqueConstraint


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="title of group",
        help_text="Заголовок группы",
    )
    slug = models.SlugField(
        unique=True, verbose_name="unique adress for group"
    )
    description = models.TextField(verbose_name="group descriptions")

    def __str__(self) -> str:
        return self.title


class Post(models.Model):

    text = models.TextField(verbose_name="blog text", help_text="Текст блога")
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="date of release",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="author of post",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="name of group",
        help_text="Группа, к которой будет относиться пост",
    )
    # Поле для картинки (необязательное)
    image = models.ImageField("Картинка", upload_to="posts/", blank=True)

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self) -> str:
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField()

    class Meta:
        ordering = ["-created"]
        verbose_name = "Комент"
        verbose_name_plural = "Коментарии"

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
    )
    UniqueConstraint(fields=["author"], name="unique_author")
