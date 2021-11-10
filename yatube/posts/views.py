from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
# from django.views.generic import CreateView
# from django.urls import reverse_lazy

from .models import Follow, Group, Post, User
from .forms import CommentForm, PostForm


posts_per_page = settings.CUSTOM_SETTINGS['POSTS_PER_PAGE']


class IndexView(ListView):
    model = Post
    paginate_by = posts_per_page
    template_name = 'posts/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_timeout'] = 20
        return context


class GroupPostsView(ListView):
    paginate_by = posts_per_page
    template_name = 'posts/group_list.html'

    def get_queryset(self):
        self.group = get_object_or_404(Group, slug=self.kwargs['slug'])
        return self.group.posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        return context


class ProfileView(ListView):
    paginate_by = posts_per_page
    template_name = 'posts/profile.html'

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        return self.author.posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = self.author
        context['post_count'] = self.author.posts.all().count()
        context['followers'] = self.author.following.all().count()
        context['following'] = self.author.following.filter(
            user=self.request.user.id
        ).exists()
        return context


# Тут если делать class PostDetail лучше сразу добавить def add_comment внутрь?
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post_count = Post.objects.filter(author=post.author).count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'post_count': post_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)

# Тут выдает ошибку: django.db.utils.IntegrityError:
# NOT NULL constraint failed: posts_post.author_id -
# я не могу понять почему он не подставляет автора,
# попробоавл поставить в моделе Post: author: null=True, тогда работает,
# но создаются посты без автора, код тут:

# class PostCreateView(LoginRequiredMixin, CreateView):
#     template_name = 'posts/create_post.html'
#     model = Post
#     form_class = PostForm

#     def get_success_url(self) -> str:
#         request_user = self.kwargs['username']
#         return reverse_lazy(
#             'posts:post_create',
#             kwargs={'username': request_user}
#         )

# Дайте наводку)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related(
        'author'
    ).filter(author__following__user=request.user)
    paginator = Paginator(post_list, posts_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if user == request.user:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(user=request.user, author=user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    get_object_or_404(Follow, user=request.user, author=user).delete()
    return redirect('posts:profile', username=username)
