import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='Terminator')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test group description'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text 123',
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        cache.clear()
        self.one = 1
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self) -> None:
        """After fill in create_post - new post in database"""
        posts_count = Post.objects.count()
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
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        # Checking if is redirect after creating post
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': PostFormTests.user.username}),
        )

        # Checking if post count increased
        self.assertEqual(
            posts_count + self.one,
            Post.objects.all().count()
        )

        # Checking if new posts with correct data exists
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                author=PostFormTests.user,
                id=Post.objects.latest('id').id,
                image='posts/pic.gif'
            ).exists()
        )

    def test_edit_post(self) -> None:
        """Post edit - updates data in db for this post id"""
        form_data = {
            'text': 'Edited test text 321',
            'group': PostFormTests.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id':
                    PostFormTests.post.id}),
            form_data
        )
        PostFormTests.post.refresh_from_db()
        post_edited_data = {
            PostFormTests.post.text: form_data['text'],
            PostFormTests.group.id: form_data['group'],
        }
        for field, expected_value in post_edited_data.items():
            with self.subTest(field=field):
                self.assertEqual(
                    field,
                    expected_value,
                    '!!! - CRUSHED: in post - data updation'
                )

    def test_guest_create_new_post(self) -> None:
        """Guest shouldn't have rights to create new post"""
        post_count = Post.objects.count()
        self.client.post(
            reverse('posts:post_create'),
            {'text': 'New post by guest', 'group': PostFormTests.group.id}
        )
        self.assertEqual(
            post_count,
            Post.objects.count()
        )

    def text_guest_edit_post(self) -> None:
        """Guest shouldn't have rights to edit posts"""
        form_data = {
            'text': 'New post by guest',
            'group': PostFormTests.group.id,
        }
        self.client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.id}),
            form_data
        )
        post_from_data_base = Post.objects.get(id=PostFormTests.post.id)
        check_data = {
            form_data['text']: post_from_data_base.text,
            form_data['group']: post_from_data_base.group.id,
        }
        for edit_data, expected_data in check_data:
            with self.subTest(field=edit_data):
                self.assertNotEqual(
                    edit_data,
                    expected_data
                )

    def test_guest_comment_post(self) -> None:
        """Guest shouldn't have rights to comment posts"""
        comment_count = PostFormTests.post.comments.count()
        response = self.client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostFormTests.post.id}),
            {'text': 'Test comment'},
            follow=True
        )
        self.assertEqual(
            comment_count,
            PostFormTests.post.comments.count(),
            '!!! - CRASHED: comment from guest appeared!'
        )

        """Guest should be redirected to logina after comment attempt"""
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostFormTests.post.id}/comment/'
        )

    def test_user_can_comment_post(self) -> None:
        comment_count = PostFormTests.post.comments.count()
        """Authorized user can add comments to post"""
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': PostFormTests.post.id}),
            {'text': 'Test comment'},
            follow=True
        )
        self.assertEqual(
            comment_count + self.one,
            Comment.objects.filter(post=PostFormTests.post).count(),
            '!!! - CRUSHED: new comment didnt appeared in data_base'
        )
        self.assertRedirects(
            response,
            f'/posts/{PostFormTests.post.id}/'
        )

        """New comment appeared on post_detail page"""
        response = self.client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostFormTests.post.id})
        )
        self.assertEqual(
            response.context['comments'][0],
            Comment.objects.get(post=PostFormTests.post.id),
            '!!! - CRUSHED: new comment didnt appeared on post_detail'
        )

    def test_xxx_index_page_cache(self) -> None:
        """Test of index_page cache working"""
        index_path = '/'
        response_index_page_1 = self.authorized_client.get(index_path)
        self.authorized_client.post(
            reverse('posts:post_create'),
            {'text': 'Cache cache cache'}
        )
        response_index_page_2 = self.authorized_client.get(index_path)
        self.assertEqual(
            response_index_page_1.content,
            response_index_page_2.content,
            '!!! - CRUSHED: cache doesnt cache'
        )
        cache.clear()
        response_index_page_3 = self.authorized_client.get(index_path)
        self.assertNotEqual(
            response_index_page_2.content,
            response_index_page_3.content,
            '!!! - CRUSHED: check cache or cache time'
        )


class TestPostForm(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.form = PostForm()

    def test_help_texts(self) -> None:
        """Testing help texts for PostForm"""
        help_texts = {
            'text': 'Write what are you thinking about..',
            'group': 'Select one of the following groups or nothing',
            'image': 'This is how I see it',
        }
        for field, expected_help_texts in help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    TestPostForm.form.fields[field].help_text,
                    expected_help_texts,
                    f'!!! - CRUSHED: in help_texts for field {field}'
                )
