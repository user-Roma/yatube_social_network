from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, View
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView

from .models import Follow, Group, Post, User
from .forms import CommentForm, PostForm


posts_per_page = settings.CUSTOM_SETTINGS['POSTS_PER_PAGE']

# Indexpage - странно работает переход по страницам,
# почемуто срабатывает в рандомном порядке,
# в терминале пишет, что перешел,код 200, а в браузере ничего не происходит


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


# Еше не придумал как реализовать
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


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = 'posts/create_post.html'
    model = Post
    form_class = PostForm

    def get_success_url(self) -> str:
        request_user = self.request.user.username
        return reverse_lazy(
            'posts:profile',
            kwargs={'username': request_user}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostEditView(LoginRequiredMixin, UpdateView):
    template_name = 'posts/create_post.html'
    model = Post
    form_class = PostForm

    def get_object(self):
        return get_object_or_404(Post, id=self.kwargs['post_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def get_success_url(self) -> str:
        post = self.get_object()
        return reverse_lazy(
            'posts:post_detail',
            kwargs={'post_id': post.id}
        )

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.request.user != post.author:
            return redirect(
                'posts:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)


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


class FollowIndexView(LoginRequiredMixin, ListView):
    paginate_by = posts_per_page
    template_name = 'posts/follow.html'

    def get_queryset(self):
        return Post.objects.select_related(
            'author'
        ).filter(author__following__user=self.request.user)


# в чем тут может быть проблема? в моих тестах отдает оишибки
class ProfileFollowView(LoginRequiredMixin, View):
    def get(self, request, **kwargs):
        user = get_object_or_404(User, username=self.kwargs['username'])
        if user == self.request.user:
            return redirect('posts:profile', username=self.kwargs['username'])
        Follow.objects.get_or_create(user=self.request.user, author=user)
        return redirect('posts:profile', username=self.kwargs['username'])


# в чем тут может быть проблема? в моих тестах отдает оишибки
class ProfileUnfollowView(LoginRequiredMixin, View):
    def get(self, request, **kwargs):
        user = get_object_or_404(User, username=self.kwargs['username'])
        get_object_or_404(Follow, user=self.request.user, author=user).delete()
        return redirect('posts:profile', username=self.kwargs['username'])
