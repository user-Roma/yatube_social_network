from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, View
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from .models import Follow, Group, Post, User
from .forms import CommentForm, PostForm


posts_per_page = settings.CUSTOM_SETTINGS['POSTS_PER_PAGE']


class IndexView(ListView):
    """Shows main page of the project"""
    paginate_by = posts_per_page
    template_name = 'posts/index.html'

    def get_queryset(self):
        post = Post.objects.select_related('group').all()
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_timeout'] = 5
        return context


class GroupPostsView(ListView):
    """Shows page filtered according to the post group"""
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
    """Shows author profile page with his posts"""
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


class PostDetailView(DetailView):
    """Shows only selected post"""
    template_name = 'posts/post_detail.html'
    model = Post

    def get_object(self):
        return get_object_or_404(Post, id=self.kwargs['post_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        context['post_count'] = Post.objects.filter(author=post.author).count()
        context['comments'] = post.comments.all()
        context['form'] = CommentForm(self.request.POST or None)
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Creation of new post"""
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
    """Edition of selected post"""
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


class AddCommentView(LoginRequiredMixin, CreateView):
    """Adding a comment to selected post"""
    template_name = 'includes/comment.html'

    def post(self, request, *args, **kwargs):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        form = CommentForm(request.POST or None)
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post.id)


class FollowIndexView(LoginRequiredMixin, ListView):
    """Shows page with posts of authors which you subscribed"""
    paginate_by = posts_per_page
    template_name = 'posts/follow.html'

    def get_queryset(self):
        return Post.objects.select_related(
            'author'
        ).filter(author__following__user=self.request.user)


class ProfileFollowView(LoginRequiredMixin, View):
    """Subscribing for author"""
    def get(self, request, **kwargs):
        user = get_object_or_404(User, username=self.kwargs['username'])
        if user == self.request.user:
            return redirect('posts:profile', username=self.kwargs['username'])
        Follow.objects.get_or_create(user=self.request.user, author=user)
        return redirect('posts:profile', username=self.kwargs['username'])


class ProfileUnfollowView(LoginRequiredMixin, View):
    """Unsubscribing for author"""
    def get(self, request, **kwargs):
        user = get_object_or_404(User, username=self.kwargs['username'])
        get_object_or_404(Follow, user=self.request.user, author=user).delete()
        return redirect('posts:profile', username=self.kwargs['username'])
