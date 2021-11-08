from django.contrib.auth import get_user_model
from django.test import TestCase


from posts.models import Group, Post


User = get_user_model()


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='Тестовый Слаг',
            description='Описание тестовой группы'
        )
        cls.group_no_slug = Group.objects.create(
            title='Ж' * 100,
            description='Описание тестовой группы'
        )

    def test_verbose_name(self) -> None:
        """verbose_name is the same as expected."""
        group = GroupModelTest.group
        field_verboses = {
            'title': 'group title',
            'description': 'group description'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name,
                    expected_value,
                    f'!!! - verbose_name in {field}'
                )

    def test_help_text(self) -> None:
        """help_text is the same as expected."""
        group = GroupModelTest.group
        field_help_text = {
            'title': 'Enter the name of the Group',
            'slug': ('Enter the address of the task page: '
                     'any letters will be transcripted to latin, '
                     'use only letters, numbers,'
                     'hyphens and underscores'),
            'description': 'Enter the description of the Group'
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text,
                    expected_value,
                    f'!!! - help_text in {field}'
                )

    def test_slug_converts_from_cyrillic(self) -> None:
        """slug field content converts from cyrillic to latin."""
        group = GroupModelTest.group
        expected_slug = group.slug
        self.assertEqual(
            expected_slug,
            'testovyij-slag',
            '!!! - slug from cyrrilic group.slug'
        )

    def test_text_convert_to_slug(self) -> None:
        """title field content converts to slug."""
        group = GroupModelTest.group_no_slug
        expected_slug = group.slug
        self.assertEqual(
            expected_slug,
            'zh' * 25,
            '!!! - convertation title -> slug'
        )

    def test_tex_slug_max_length_not_exceed(self) -> None:
        """The long slug does not exceed the max_length of the slug field."""
        group = GroupModelTest.group_no_slug
        max_length_slug = group._meta.get_field('slug').max_length
        slug_length = len(group.slug)
        self.assertEqual(
            slug_length,
            max_length_slug,
            '!!! - slug lenght exceeded'
        )


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='Terminator')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='Тестовый Слаг',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 1 2 3 4 5 6',
            pub_date=None,
            group=cls.group,
        )

    def test_verbose_name(self) -> None:
        """verbose_name is the same as expected."""
        post = PostModelTest.post
        field_verboses = {
            'author': 'post author',
            'text': 'post text',
            'pub_date': 'date of publication',
            'group': 'post group'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value,
                    f'!!! - verbose_name in {field}'
                )

    def test_help_text(self) -> None:
        """help_text is the same as expected."""
        post = PostModelTest.post
        field_help_text = {
            'text': 'Write what are you thinking about..',
            'group': 'Select one of the following groups or nothing'
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value,
                    f'!!! - help_text in {field}'
                )

    def test_models_have_correct_object_names(self) -> None:
        """__str__ works correctly"""
        post = PostModelTest.post
        models_name = {
            post.group: post.group.title,
            post: post.text[:15]
        }
        for field, expected_value in models_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    str(field),
                    expected_value,
                    f'!!! - __str__ for {field}'
                )
