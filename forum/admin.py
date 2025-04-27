from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Post, Comment, Like, Message

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'nickname', 'email_verified', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'email_verified', 'date_joined')
    search_fields = ('username', 'email', 'nickname')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('nickname', 'email', 'avatar')}),
        ('验证信息', {'fields': ('email_verified', 'verification_code', 'verification_code_expires')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'views', 'likes', 'is_hot')
    list_filter = ('is_hot', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'author', 'post', 'created_at', 'parent')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'post__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'message_type', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'content')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
