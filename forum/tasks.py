from django.utils import timezone
from .models import Post

def update_hot_posts():
    """更新所有帖子的热度分数和热门状态"""
    # 计算所有帖子的热度分数
    for post in Post.objects.all():
        post.calculate_hot_score()
    
    # 更新热门状态
    Post.objects.first().update_hot_status() 