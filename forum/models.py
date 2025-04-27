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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    views = models.PositiveIntegerField(default=0, verbose_name='浏览量')
    likes = models.PositiveIntegerField(default=0, verbose_name='点赞数')
    is_hot = models.BooleanField(default=False, verbose_name='是否热门')
    hot_score = models.FloatField(default=0)  # 热度分数

    def calculate_hot_score(self):
        """计算帖子热度分数"""
        # 浏览量权重 0.3
        views_score = self.views * 0.3
        # 点赞数权重 0.4
        likes_score = self.likes * 0.4
        # 评论数权重 0.3
        comments_score = Comment.objects.filter(post=self).count() * 0.3
        # 时间衰减因子 (24小时内的帖子获得额外加分)
        time_factor = 1.0
        if (timezone.now() - self.created_at).total_seconds() < 86400:  # 24小时
            time_factor = 1.5
        
        # 计算最终热度分数
        self.hot_score = (views_score + likes_score + comments_score) * time_factor
        self.save()

    def update_hot_status(self):
        """更新帖子热门状态"""
        # 获取所有帖子并按热度排序
        all_posts = Post.objects.all().order_by('-hot_score')
        if not all_posts.exists():
            return
        
        # 取前10%的帖子作为热门帖子，但至少保证有1个
        hot_count = max(1, int(all_posts.count() * 0.1))
        hot_posts = all_posts[:hot_count]
        
        # 更新所有帖子的热门状态
        Post.objects.all().update(is_hot=False)
        hot_posts.update(is_hot=True)

    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title

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
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='comment', verbose_name='消息类型')
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

