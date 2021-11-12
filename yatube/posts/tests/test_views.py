import random
import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django import forms

from posts.models import Follow, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()

posts_per_page = settings.CUSTOM_SETTINGS['POSTS_PER_PAGE']

test_crush = '!!! - CRUSHED: '


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = [
            User(username='Terminator'),
            User(username='Terminator II'),
        ]
        User.objects.bulk_create(cls.user)
        cls.groups = [
            Group(
                title='First group',
                slug='first',
                description='First from two'
            ),
            Group(
                title='Second group',
                slug='second',
                description='Second from two'
            ),
        ]
        Group.objects.bulk_create(cls.groups)
        cls.posts = []
        for post in range(1, 8):
            cls.posts.append(
                Post(
                    text=f'Text for post {post}',
                    author=User.objects.get(username='Terminator'),
                    group=Group.objects.get(title='First group')
                )
            )
        for post in range(1, 13):
            cls.posts.append(
                Post(
                    text=f'Text for post 2-{post}',
                    author=User.objects.get(username='Terminator II'),
                    group=Group.objects.get(title='Second group')
                )
            )
        Post.objects.bulk_create(cls.posts)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.user_1 = User.objects.get(username='Terminator')
        self.user_2 = User.objects.get(username='Terminator II')
        self.group_1 = Group.objects.get(title='First group')
        self.group_2 = Group.objects.get(title='Second group')
        self.random_post_user_1 = random.choice(
            Post.objects.filter(author=self.user_1))
        self.random_post_user_2 = random.choice(
            Post.objects.filter(author=self.user_2))
        self.one = 1
        self.last_post = 0
        self.zero = 0
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    def test_pages_uses_correct_templates(self) -> None:
        """URL-address name:namespace uses appropriate template"""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group_1.slug}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user_1.username}):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': random.choice(Post.objects.all()).id}):
                        'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.random_post_user_1.id}):
                        'posts/create_post.html',
        }
        for page_address, template in templates_page_names.items():
            with self.subTest(field=template):
                response = self.authorized_client.get(page_address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'!!! - fail in {template} - {page_address}'
                )
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.random_post_user_2.id}))
        self.assertTemplateNotUsed(
            response,
            'posts/create_post.html',
            '!!! - not only author has access to his post')

    def test_post_detail_shows_correct_context(self) -> None:
        """Template post_detail formed with appropriate context."""
        post_id = 1
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id}))
        field_context = response.context['post']
        post_detail_context = {
            field_context.group.title: self.group_1.title,
            field_context.text: f'Text for post {post_id}',
            field_context.author.username: self.user_1.username,
            response.context.get('post_count'):
                Post.objects.filter(author=self.user_1).count(),
            field_context.id: post_id,
        }
        for field, context in post_detail_context.items():
            with self.subTest(field=field):
                self.assertEqual(field, context)

    def test_post_create_shows_correct_context(self) -> None:
        """Template create_post formed with appropriate context."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField,
        }
        for field, expected_value in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected_value)

    def test_post_create_redirects_after_correct_filling(self):
        """Redirection from post_create works correctly for author."""
        response_create_post = self.authorized_client.post(
            reverse('posts:post_create'),
            {'text': 'Test123', 'group': self.group_1.id},
            follow=True
        )
        self.assertRedirects(response_create_post,
                             f'/profile/{self.user_1.username}/')

    def test_post_edit_shows_correct_context(self) -> None:
        """Template create_post works correctly when user edit it."""
        post_number = self.random_post_user_1.id
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_number})
        )
        self.assertEqual(
            response.context.get('post').text,
            f'Text for post {post_number}')
        self.assertEqual(
            response.context.get('post').group.title,
            self.group_1.title
        )
        self.assertEqual(response.context.get('is_edit'), True)

    def test_post_edit_author_validation(self) -> None:
        """Redirects if user != author"""
        response = self.authorized_client_2.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.random_post_user_1.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND.value)

    def test_post_edit_redirects_author_after_success_post_edit(self) -> None:
        """Redirects author after success post edit"""
        id = self.random_post_user_1.id
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': id}),
            {'text': f'Edited text for post {id}', 'group': self.group_2.id},
            follow=True
        )
        self.assertRedirects(response, f'/posts/{id}/')

    def test_index_page_shows_correct_context(self) -> None:
        """Page Index formed with correct context + paginator"""
        response = self.authorized_client.get(reverse('posts:index'))
        field_context = response.context['page_obj'][self.last_post]
        index_context = {
            field_context.author.username: self.user_2.username,
            field_context.pub_date.strftime("%m/%d/%Y"):
                timezone.now().strftime("%m/%d/%Y"),
            field_context.text: Post.objects.latest('id').text,
            field_context.group.title: self.group_2.title,
            field_context.id: Post.objects.latest('id').id,
        }
        for field, expected_value in index_context.items():
            with self.subTest(field=field):
                self.assertEqual(
                    field,
                    expected_value,
                    f'!!! - CRUSHED: in {field}'
                )

        """Paginator for index pages"""
        self.assertEqual(
            len(response.context['page_obj']),
            posts_per_page,
            '!!! CRUSHED: paginator for Index page'
        )
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            Post.objects.count() - posts_per_page,
            '!!! CRUSHED: paginator for Index 2 page'
        )

    def test_group_list_page_shows_correct_context(self) -> None:
        """Template group_list filters posts according group + paginator"""

        # Checking if amount of group posts equal
        # with amount of posts on group_list page
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_1.slug}))
        self.assertSequenceEqual(
            response.context['page_obj'].object_list,
            Post.objects.filter(group=self.group_1.id),
            '!!! - CRUSHED: group_list is not relevant'
        )

        # Checking context in fields in every
        # post of the group on group_list first page
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_2.slug})
        )

        post_id = Post.objects.filter(group=self.group_2.id).latest('id').id
        for context in response.context['page_obj']:
            post_text_id = context.id - \
                Post.objects.filter(group=self.group_1).count()
            post_context = {
                context.group.title: self.group_2.title,
                context.group.description: self.group_2.description,
                context.group.slug: self.group_2.slug,
                context.author.username: self.user_2.username,
                context.pub_date.strftime("%m/%d/%Y"):
                    timezone.now().strftime("%m/%d/%Y"),
                context.text: f'Text for post 2-{post_text_id}',
                context.id: post_id,
            }
            for field_context, expected_value in post_context.items():
                with self.subTest(field=field_context):
                    self.assertEqual(
                        expected_value,
                        field_context,
                        f'!!! - CRUSHED: in {field_context} -post{context.id}'
                    )
            post_id -= self.one

        """Paginator for group_list pages"""
        self.assertEqual(
            len(response.context['page_obj']),
            posts_per_page,
            '!!! - CRUSHED: in paginator for group_list'
        )
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_2.slug})
            + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            Post.objects.filter(group=self.group_2).count() - posts_per_page,
            '!!! - CRUSHED: in paginator group_list - 2 page'
        )

    def test_profile_page_shows_correct_context(self) -> None:
        """Template profile page filters posts according author + paginator"""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user_1.username}))
        self.assertSequenceEqual(
            response.context['page_obj'].object_list,
            Post.objects.filter(author=self.user_1.id),
            '!!! - CRUSHED: incorrect posts list in Profile'
        )

        post_id = Post.objects.filter(author=self.user_1.id).latest('id').id
        for context in response.context['page_obj']:
            post_context = {
                context.author.username: self.user_1.username,
                context.pub_date.strftime("%m/%d/%Y"):
                    timezone.now().strftime("%m/%d/%Y"),
                context.text: f'Text for post {context.id}',
                context.id: post_id,
            }
            for field_context, expected_value in post_context.items():
                with self.subTest(field=field_context):
                    self.assertEqual(
                        expected_value,
                        field_context,
                        f'!!! - CRUSHED: in {field_context} -post{context.id}'
                    )
            post_id -= self.one

        self.assertEqual(
            response.context['post_count'],
            Post.objects.filter(author=self.user_1.id).count(),
            '!!! - CRUSHED: in author post_count'
        )

        """Paginator for profile page"""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user_2.username}))
        self.assertEqual(
            len(response.context['page_obj']),
            posts_per_page,
            '!!! - CRUSHED: in paginator Profile page'
        )
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user_2.username})
            + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            (Post.objects.filter(author=self.user_2.id).count()
                - posts_per_page),
            '!!! - CRUSHED: in paginator Profile - 2 page'
        )

    def test_new_post_with_group_appears_on_the_other_pages(self) -> None:
        """New post appears on index, group_list, profile pages"""
        self.authorized_client.post(
            reverse('posts:post_create'),
            {'text': 'Test123', 'group': self.group_1.id}
        )

        new_post_id = Post.objects.latest('id').id
        test_post_creation = {
            reverse('posts:index'): Post.objects.get(id=new_post_id),
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}):
                Post.objects.get(id=new_post_id),
            reverse('posts:profile',
                    kwargs={'username': self.user_1.username}):
                Post.objects.get(id=new_post_id),
        }
        for page, test_text in test_post_creation.items():
            with self.subTest(field=page):
                response_new_post_index = self.authorized_client.get(page)
                self.assertIn(
                    test_text,
                    response_new_post_index.context['page_obj'].object_list,
                    f'!!! - CRUSHED: new post lost on {page}'
                )

    def test_new_post_doesnt_appear_in_another_group(self) -> None:
        """New post shouldn't appear in Second Group"""
        self.authorized_client.post(
            reverse('posts:post_create'),
            {'text': 'Test123', 'group': self.group_1.id}
        )
        response_new_post_index = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}))
        self.assertNotIn(
            Post.objects.get(id=Post.objects.latest('id').id),
            response_new_post_index.context['page_obj'].object_list,
            '!!! - CRUSHED: new post - wrong group implementation'
        )

    def test_picture_passed_into_context_of_expected_pages(self) -> None:
        """Picture should appear on index, profile, group_list, post pages"""
        pic = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='pic.gif',
            content=pic,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Test post_create form 123',
            'group': self.group_1.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        new_post_image = Post.objects.latest('id').image
        check_pages = {
            '/': 'page_obj',
            f'/group/{self.group_1.slug}/': 'page_obj',
            f'/profile/{self.user_1.username}/': 'page_obj',
        }
        for page, data in check_pages.items():
            with self.subTest(field=page):
                response = self.authorized_client.get(page)
                page_picture = response.context[data][self.last_post].image
                self.assertEqual(
                    page_picture,
                    new_post_image,
                    f'!!! - CRUSHED: image on {page}'
                )

        self.assertEqual(
            (self.authorized_client.get(
                f'/posts/{Post.objects.latest("id").id}/').
                context['post'].image),
            new_post_image,
            '!!! - CRUSHED: image on post_detail'
        )

    def test_authorized_user_can_follow(self) -> None:
        """Test follow for authorized user"""
        following_start = Follow.objects.filter(user=self.user_1).count()
        response_follow = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user_2}),
            follow=True
        )
        self.assertRedirects(
            response_follow,
            reverse(
                'posts:profile',
                kwargs={'username': self.user_2}
            )
        )

        # User_1 has 0 followings, after following User_2
        # following count should change to 1
        self.assertEqual(
            Follow.objects.filter(user=self.user_1).count(),
            following_start + self.one,
            '!!! - CRUSHED: new follow for user didnt appear in db'
        )

        # Check if user appears in author.following
        self.assertEqual(
            Follow.objects.get(author=self.user_2).user,
            self.user_1,
            test_crush + 'user doesnt following this author'
        )

    def test_authorized_user_can_unfollow(self) -> None:
        """Test unfollow for authorized user"""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user_2}),
            follow=True
        )
        user_follows_count = Follow.objects.filter(user=self.user_1).count()
        response_unfollow = self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_2}),
            follow=True
        )
        self.assertRedirects(
            response_unfollow,
            reverse('posts:profile', kwargs={'username': self.user_2}),
        )
        self.assertNotEqual(
            user_follows_count,
            Follow.objects.filter(user=self.user_1).count(),
            test_crush + 'following didnt break'
        )

        # Try to find deleted follow from user in data base
        try:
            follower = Follow.objects.get(author=self.user_2).user
        except Follow.DoesNotExist:
            follower = None
        self.assertEqual(
            follower,
            None,
            test_crush + 'user STILL following author'
        )

    def test_new_post_on_subscriber_follow_page(self) -> None:
        """New post should appear on subscriber follow page"""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user_2})
        )
        self.authorized_client_2.get(
            '/create/',
            {'text': 'Text only for my subscribers'}
        )
        check_follow = self.authorized_client.get('/follow/')
        author_post = self.authorized_client_2.get(
            reverse('posts:profile', kwargs={'username': self.user_2})
        )
        self.assertIn(
            check_follow.context['page_obj'][self.last_post],
            Post.objects.filter(author=self.user_2)
        )
        self.assertEqual(
            check_follow.context['page_obj'][self.last_post],
            author_post.context['page_obj'][self.last_post]
        )

    def test_new_post_shouldnt_appear_if_not_follow_author(self) -> None:
        """User shouldnt see posts of unfollowing authors"""
        check_follow = self.authorized_client.get('/follow/')
        check_follow_2 = self.authorized_client.get('/follow/')
        self.assertEqual(
            check_follow.content,
            check_follow_2.content,
            test_crush + 'extra object appeared'
        )
        self.assertNotIn(
            Post.objects.get(id=self.random_post_user_2.id),
            check_follow_2.context['page_obj'].object_list,
            test_crush + 'post from unfollowing author finded'
        )
