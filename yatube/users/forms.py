from django.contrib.auth.forms import UserCreationForm
from posts.models import User


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")
        help_texts = "form for registration new users"
