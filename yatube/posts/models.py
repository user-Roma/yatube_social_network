from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel
from core.context_processors.pytils.templatetags.pytils_translit import slugify

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='Enter the name of the Group',
        verbose_name='group title'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        allow_unicode=True,
        help_text=('Enter the address of the task page: '
                   'any letters will be transcripted to latin, '
                   'use only letters, numbers,'
                   'hyphens and underscores'
                   )
    )
    description = models.TextField(
        help_text='Enter the description of the Group',
        verbose_name='group description'
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.slug)
        if not self.slug:
            self.slug = slugify(self.title)[:50]
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        help_text='Write what are you thinking about..',
        verbose_name='post text'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='date of publication'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='post author'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        help_text='Select one of the following groups or nothing',
        verbose_name='post group'
    )
    image = models.ImageField(
        'picture',
        upload_to='posts/',
        blank=True,
        null=True,
        help_text='This is how I see it'
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'post'
        verbose_name_plural = 'posts'

    def __str__(self) -> str:
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='comment author'
    )
    text = models.TextField(
        help_text='Write your comment here',
        verbose_name='comment text'
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'comment'
        verbose_name_plural = 'comments'

    def __str__(self) -> str:
        return self.text[:15]


class Follow(CreatedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow'
            )
        ]

    def __str__(self) -> str:
        return 'Follow / Unfolow'
