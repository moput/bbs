from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/comment/', views.create_comment, name='create_comment'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('verify-email/<int:user_id>/', views.verify_email, name='verify_email'),
    path('resend-verification/<int:user_id>/', views.resend_verification_code, name='resend_verification_code'),
    path('send-verification-code/', views.send_verification_code, name='send_verification_code'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('send-reset-password-code/', views.send_reset_password_code, name='send_reset_password_code'),
    path('my-comments/', views.my_comments, name='my_comments'),
    path('my-likes/', views.my_likes, name='my_likes'),
    path('my-posts/', views.my_posts, name='my_posts'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('messages/', views.user_messages, name='messages'),
    path('search/', views.search, name='search'),
    path('profile/', views.profile, name='profile'),
] 