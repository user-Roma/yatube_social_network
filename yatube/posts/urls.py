from django.urls import path

from . import views

app_name = 'posts'


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path(
        'profile/<str:username>/',
        views.ProfileView.as_view(),
        name='profile'
    ),
    path(
        'posts/<int:post_id>/',
        views.PostDetailView.as_view(),
        name='post_detail'
    ),
    path(
        'posts/<int:post_id>/comment/',
        views.AddCommentView.as_view(),
        name='add_comment'
    ),
    path('create/', views.PostCreateView.as_view(), name='post_create'),
    path(
        'posts/<int:post_id>/edit/',
        views.PostEditView.as_view(),
        name='post_edit'
    ),
    path(
        'group/<slug:slug>/',
        views.GroupPostsView.as_view(),
        name='group_list'
    ),
    path('follow/', views.FollowIndexView.as_view(), name='follow_index'),
    path(
        'profile/<str:username>/follow/',
        views.ProfileFollowView.as_view(),
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.ProfileUnfollowView.as_view(),
        name='profile_unfollow'
    ),
]
