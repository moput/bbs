import os
import django
import random
from datetime import datetime, timedelta

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bbs.settings')
django.setup()

from forum.models import User, Post
from django.utils import timezone

# 获取或创建测试用户
def get_or_create_test_user():
    try:
        user = User.objects.get(username='test_user')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test123',
            nickname='测试用户'
        )
    return user

# 帖子内容
posts_data = [
    {
        'title': '新学期开始了，大家有什么计划吗？',
        'content': '新学期新气象，希望大家都能制定好学习计划，取得好成绩！'
    },
    {
        'title': '图书馆自习室开放时间调整通知',
        'content': '从下周一开始，图书馆自习室开放时间调整为早上7点到晚上10点，请大家注意。'
    },
    {
        'title': '校园美食推荐',
        'content': '今天在二食堂发现了一家新开的麻辣烫，味道很不错，推荐大家去尝尝！'
    },
    {
        'title': '寻找一起打篮球的小伙伴',
        'content': '本人热爱篮球，想找一些志同道合的朋友一起打球，每周六下午有空。'
    },
    {
        'title': '关于选课的一些建议',
        'content': '分享一些选课经验，希望对学弟学妹们有所帮助。'
    },
    {
        'title': '校园二手交易',
        'content': '出售二手自行车，九成新，价格面议，有意者请联系。'
    },
    {
        'title': '社团招新啦！',
        'content': '摄影社团开始招新，欢迎对摄影感兴趣的同学加入！'
    },
    {
        'title': '期末考试复习资料分享',
        'content': '整理了一些高数复习资料，有需要的同学可以联系我。'
    },
    {
        'title': '校园周边美食探店',
        'content': '分享几家学校周边好吃又实惠的餐厅，欢迎大家补充！'
    },
    {
        'title': '寻找考研研友',
        'content': '准备考研的同学可以一起组队学习，互相监督，共同进步！'
    }
]

def create_posts():
    user = get_or_create_test_user()
    
    # 创建帖子
    for i, post_data in enumerate(posts_data):
        # 设置不同的发布时间，从最近到较远
        created_at = timezone.now() - timedelta(days=i*2)
        
        post = Post.objects.create(
            title=post_data['title'],
            content=post_data['content'],
            author=user,
            created_at=created_at,
            views=random.randint(50, 500),
            likes=random.randint(10, 100),
            is_hot=random.choice([True, False])
        )
        print(f'Created post: {post.title}')

if __name__ == '__main__':
    create_posts() 