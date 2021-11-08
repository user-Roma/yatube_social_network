from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post


User = get_user_model()


class StaticURLTests(TestCase):
    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK.value,
            '!!! - static home_page'
        )


class PostsURLTests(TestCase):
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
            text='Test text 1 2 3 4 5 6',
            pub_date=None,
            group=cls.group
        )

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='Terminator_II')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.user)
        self.response_guest = self.client.get
        self.response_authorized_client = self.authorized_client.get
        self.response_author = self.author_client.get

    def test_url_exists_at_desired_location(self) -> None:
        """Pages accessible to guest_user/authorized_user/author."""
        posts_pages = {
            'index': self.response_guest('/'),
            'profile': self.response_guest(
                f'/profile/{PostsURLTests.user.username}/'),
            'post_detail': self.response_guest(f'/posts/{self.post.id}/'),
            'group_list': self.response_guest(f'/group/{self.group.slug}/'),
            'authorized_post_create':
                self.response_authorized_client('/create/'),
            'author_post_edit': self.response_author(
                f'/posts/{self.post.id}/edit/'),
        }
        for field, redirect_url in posts_pages.items():
            with self.subTest(field=field):
                self.assertEqual(
                    redirect_url.status_code,
                    HTTPStatus.OK.value,
                    f'!!! - bad URL for {field}'
                )

    def test_url_redirect(self) -> None:
        """Pages redirects guest_user/authorized_user."""
        redirect_pages = {
            'guest_post_create': self.response_guest('/create/'),
            'guest_post_edit': self.response_guest(
                f'/posts/{self.post.id}/edit/'),
            'authorized_post_edit':
                self.response_authorized_client(
                    f'/posts/{self.post.id}/edit/')
        }
        for field, redirect_url in redirect_pages.items():
            with self.subTest(field=field):
                self.assertEqual(
                    redirect_url.status_code,
                    HTTPStatus.FOUND.value,
                    f'!!! - bad redirect form {field}'
                )

    def test_post_create_url_redirects_guest_on_login(self) -> None:
        """Page post_create and post_edit redirects guest to login."""
        guest_redirect_urls = {
            '/auth/login/?next=/create/': '/create/',
            f'/auth/login/?next=/posts/{self.post.id}/edit/':
                f'/posts/{self.post.id}/edit/'
        }
        for redirect_url, url in guest_redirect_urls.items():
            response_guest = self.client.get(url, follow=True)
            self.assertRedirects(
                response_guest,
                redirect_url
            )

    # Может перенести этот тест в test_views?
    def test_post_edit_url_redirects_fake_author_on_post_detail(self) -> None:
        """Page post_edit redirects authorized user on post_detail."""
        response_authorized = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response_authorized,
            f'/posts/{self.post.id}/'
        )

    def test_templates(self) -> None:
        """Urls use appropriate templates."""
        posts_templates = {
            '/': 'posts/index.html',
            f'/profile/{PostsURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html'
        }
        for url, template in posts_templates.items():
            with self.subTest(field=url):
                response = self.response_author(url)
                self.assertTemplateUsed(
                    response,
                    template
                )

    def test_request_to_unexisting_page(self) -> None:
        """Check for 404 error for unexisting page."""
        response = self.response_author('/unexisting_page/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND.value,
            '!!! - MASAKA!')
