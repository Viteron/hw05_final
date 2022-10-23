from gc import unfreeze
from re import template
from django.shortcuts import get_object_or_404, render, redirect
from requests import post
from .models import Follow, Post, Group, User
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

POSTS_PER_PAGE = 10


@cache_page(20)
def index(request):
    tamplate = "posts/index.html"
    post_list = Post.objects.all()
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, tamplate, context)


def group_list(request, slug):
    tamplate = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    title = "Все записи группы"
    context = {
        "group": group,
        "posts": posts,
        "title": title,
        "page_obj": page_obj,
    }
    return render(request, tamplate, context)


def profile(request, username):
    tamplate = "posts/profile.html"
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    following = author.following.exists()
    context = {
        "author": author,
        "posts": posts,
        "page_obj": page_obj,
        "following": following,
    }
    return render(request, tamplate, context)


def post_detail(request, post_id):
    tamplate = "posts/post_detail.html"
    posts = get_object_or_404(Post, id=post_id)
    comments = posts.comments.select_related("author", "post").all()
    form = CommentForm()
    context = {
        "posts": posts,
        "form": form,
        "comments": comments,
    }
    return render(request, tamplate, context)


@login_required
def post_create(request):
    tamplate = "posts/create_post.html"
    author_post = Post(author=request.user)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=author_post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:profile", request.user.username)
    context = {
        "form": form,
    }
    return render(request, tamplate, context)


@login_required
def post_edit(request, post_id):
    tamplate = "posts/create_post.html"
    posts = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=posts
    )
    if request.user != posts.author:
        return redirect("posts:post_detail", post_id)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    context = {"form": form, "is_edit": "is_edit"}
    return render(request, tamplate, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    tamplate = "posts/follow.html"
    return render(request, tamplate, context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    template = "posts:profile"
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect(template, author)


@login_required
def profile_unfollow(request, username):
    """Дизлайк, отписка"""
    template = "posts:follow_index"
    author = get_object_or_404(User, username=username)
    unfollow = Follow.objects.filter(
        user=request.user,
        author=author,
    )
    if unfollow.exists():
        unfollow.delete()
    return redirect(template)
