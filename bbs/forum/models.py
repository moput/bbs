from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string

class User(AbstractUser):
    """自定义用户模型"""
    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', verbose_name='头像')
    email = models.EmailField(unique=True, verbose_name='邮箱')
    email_verified = models.BooleanField(default=False, verbose_name='邮箱已验证')
    verification_code = models.CharField(max_length=6, blank=True, verbose_name='验证码')
    verification_code_expires = models.DateTimeField(null=True, blank=True, verbose_name='验证码过期时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def generate_verification_code(self):
        """生成6位随机验证码"""
        self.verification_code = ''.join(random.choices(string.digits, k=6))
        self.verification_code_expires = timezone.now() + timezone.timedelta(minutes=30)
        self.save()
        return self.verification_code

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name

class Post(models.Model):
    """帖子模型"""
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name='作者')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    views = models.PositiveIntegerField(default=0, verbose_name='浏览量')
    likes = models.PositiveIntegerField(default=0, verbose_name='点赞数')
    is_hot = models.BooleanField(default=False, verbose_name='是否热门')

    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

class Comment(models.Model):
    """评论模型"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='帖子')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name='作者')
    content = models.TextField(verbose_name='内容')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name='父评论')

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = verbose_name
        ordering = ['created_at']

class Like(models.Model):
    """点赞模型"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes', verbose_name='帖子')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_likes', verbose_name='用户')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '点赞'
        verbose_name_plural = verbose_name
        unique_together = ('post', 'user')

class Message(models.Model):
    """消息模型"""
    MESSAGE_TYPES = (
        ('like', '点赞'),
        ('comment', '评论'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name='发送者')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', verbose_name='接收者')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, verbose_name='消息类型')
    content = models.TextField(verbose_name='内容')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, verbose_name='相关帖子')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, verbose_name='相关评论')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '消息'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_message_type_display()} from {self.sender.username} to {self.receiver.username}"

