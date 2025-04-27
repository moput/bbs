from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import User, Post, Comment, Like, Message as MessageModel
from .forms import UserRegistrationForm, PostForm, CommentForm
import json
import random
import string
from django.db import models

def send_verification_email(user):
    """发送验证邮件"""
    subject = '校园论坛邮箱验证'
    message = f'''
    您好，{user.nickname or user.username}！
    
    感谢您注册校园论坛，您的验证码是：{user.verification_code}
    验证码将在30分钟后过期。
    
    如果这不是您的操作，请忽略此邮件。
    '''
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        verification_code = request.POST.get('verification_code')
        
        # 验证密码是否匹配
        if password != password2:
            return redirect('forum:register')
            
        # 验证验证码
        session_code = request.session.get('verification_code')
        session_email = request.session.get('verification_email')
        session_time = request.session.get('verification_code_time')
        
        if not session_code or not session_email or not session_time:
            return redirect('forum:register')
            
        if email != session_email:
            return redirect('forum:register')
            
        if verification_code != session_code:
            return redirect('forum:register')
            
        # 检查验证码是否过期（10分钟）
        if timezone.now().timestamp() - session_time > 600:
            return redirect('forum:register')
            
        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            return redirect('forum:register')
            
        # 创建用户
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                email_verified=True  # 因为已经验证过验证码，所以直接设置为已验证
            )
            return redirect('forum:login')
        except Exception as e:
            return redirect('forum:register')
            
    return render(request, 'forum/register.html')

def verify_email(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        code = request.POST.get('verification_code')
        if code == user.verification_code:
            if timezone.now() <= user.verification_code_expires:
                user.email_verified = True
                user.save()
                login(request, user)
                return redirect('forum:index')
            else:
                return redirect('forum:verify_email', user_id=user.id)
        else:
            return redirect('forum:verify_email', user_id=user.id)
    
    return render(request, 'forum/verify_email.html', {'user': user})

def resend_verification_code(request, user_id):
    user = get_object_or_404(User, id=user_id)
    verification_code = user.generate_verification_code()
    send_verification_email(user)
    return redirect('forum:verify_email', user_id=user.id)

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            if user.is_active:
                login(request, user)
                # 如果是管理员，跳转到管理页面
                if user.is_staff or user.is_superuser:
                    return redirect('admin:index')
                return redirect('forum:index')
            else:
                return redirect('forum:login')
        else:
            return redirect('forum:login')
    
    return render(request, 'forum/login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('forum:index')

def index(request):
    """首页视图"""
    # 更新所有帖子的热门状态
    if Post.objects.exists():
        Post.objects.first().update_hot_status()
    
    posts = Post.objects.all().order_by('-created_at')
    hot_posts = Post.objects.filter(is_hot=True).order_by('-hot_score')[:5]
    
    # 设置每页显示8个帖子
    paginator = Paginator(posts, 8)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'forum/index.html', {
        'posts': posts,
        'hot_posts': hot_posts
    })

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('forum:post_detail', post.id)
    else:
        form = PostForm()
    return render(request, 'forum/create_post.html', {'form': form})

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.views += 1
    post.save()
    post.calculate_hot_score()  # 更新热度分数
    
    comments = Comment.objects.filter(post=post, parent=None)
    form = CommentForm()
    
    # 检查用户是否已经点赞
    is_liked = False
    if request.user.is_authenticated:
        is_liked = Like.objects.filter(post=post, user=request.user).exists()
    
    return render(request, 'forum/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'is_liked': is_liked
    })

@login_required
@require_POST
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        
        # 创建评论消息
        MessageModel.objects.create(
            sender=request.user,
            receiver=post.author,
            message_type='comment',
            content=f'评论了你的帖子《{post.title}》：{comment.content[:50]}',
            post=post,
            comment=comment
        )
        
        post.calculate_hot_score()  # 更新热度分数
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'})

@login_required
@require_POST
def like_post(request, post_id):
    """点赞功能"""
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        like.delete()
        # 确保点赞数不会小于0
        if post.likes > 0:
            post.likes -= 1
        is_liked = False
    else:
        post.likes += 1
        is_liked = True
        # 创建点赞消息
        MessageModel.objects.create(
            sender=request.user,
            receiver=post.author,
            message_type='like',
            content=f'点赞了你的帖子《{post.title}》',
            post=post
        )
    
    post.save()
    post.calculate_hot_score()  # 更新热度分数
    return JsonResponse({
        'status': 'success',
        'likes': post.likes,
        'is_liked': is_liked
    })

@require_POST
def send_verification_code(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'status': 'error', 'message': '邮箱不能为空'})
            
        # 检查邮箱是否已被注册
        if User.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': '该邮箱已被注册'})
            
        # 生成验证码
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # 发送验证邮件
        subject = '校园论坛注册验证码'
        message = f'''
        您好！

        您的注册验证码是：{verification_code}
        验证码将在10分钟内有效。

        如果这不是您的操作，请忽略此邮件。
        '''
        
        # 使用HTML格式发送邮件
        html_message = f'''
        <html>
            <body>
                <p>您好！</p>
                <p>您的注册验证码是：<strong>{verification_code}</strong></p>
                <p>验证码将在10分钟内有效。</p>
                <p>如果这不是您的操作，请忽略此邮件。</p>
            </body>
        </html>
        '''
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
            html_message=html_message
        )
        
        # 将验证码保存到session中
        request.session['verification_code'] = verification_code
        request.session['verification_email'] = email
        request.session['verification_code_time'] = timezone.now().timestamp()
        
        return JsonResponse({'status': 'success', 'message': '验证码已发送'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@require_POST
def send_reset_password_code(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'status': 'error', 'message': '邮箱不能为空'})
            
        # 检查邮箱是否已注册
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '该邮箱未注册'})
            
        # 生成验证码
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # 发送验证邮件
        subject = '校园论坛密码重置验证码'
        message = f'''
        您好！

        您的密码重置验证码是：{verification_code}
        验证码将在10分钟内有效。

        如果这不是您的操作，请忽略此邮件。
        '''
        
        html_message = f'''
        <html>
            <body>
                <p>您好！</p>
                <p>您的密码重置验证码是：<strong>{verification_code}</strong></p>
                <p>验证码将在10分钟内有效。</p>
                <p>如果这不是您的操作，请忽略此邮件。</p>
            </body>
        </html>
        '''
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
            html_message=html_message
        )
        
        # 将验证码保存到session中
        request.session['reset_password_code'] = verification_code
        request.session['reset_password_email'] = email
        request.session['reset_password_time'] = timezone.now().timestamp()
        
        return JsonResponse({'status': 'success', 'message': '验证码已发送'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        verification_code = request.POST.get('verification_code')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # 验证密码是否匹配
        if new_password != confirm_password:
            return redirect('forum:forgot_password')
            
        # 验证验证码
        session_code = request.session.get('reset_password_code')
        session_email = request.session.get('reset_password_email')
        session_time = request.session.get('reset_password_time')
        
        if not session_code or not session_email or not session_time:
            return redirect('forum:forgot_password')
            
        if email != session_email:
            return redirect('forum:forgot_password')
            
        if verification_code != session_code:
            return redirect('forum:forgot_password')
            
        # 检查验证码是否过期（10分钟）
        if timezone.now().timestamp() - session_time > 600:
            return redirect('forum:forgot_password')
            
        # 更新密码
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save(update_fields=['password'])  # 只更新密码字段
            
            # 清除session中的验证码信息
            del request.session['reset_password_code']
            del request.session['reset_password_email']
            del request.session['reset_password_time']
            
            return redirect('forum:login')
        except User.DoesNotExist:
            return redirect('forum:forgot_password')
        except Exception as e:
            return redirect('forum:forgot_password')
            
    return render(request, 'forum/forgot_password.html')

@login_required
def my_comments(request):
    """显示用户的所有评论"""
    comments = Comment.objects.filter(author=request.user).order_by('-created_at')
    paginator = Paginator(comments, 10)  # 每页显示10条评论
    page = request.GET.get('page')
    comments = paginator.get_page(page)
    return render(request, 'forum/my_comments.html', {'comments': comments})

@login_required
def my_likes(request):
    """显示用户点赞的所有帖子"""
    likes = Like.objects.filter(user=request.user).order_by('-id')
    paginator = Paginator(likes, 10)  # 每页显示10条点赞
    page = request.GET.get('page')
    likes = paginator.get_page(page)
    return render(request, 'forum/my_likes.html', {'likes': likes})

@login_required
def my_posts(request):
    """显示用户发布的所有帖子"""
    posts = Post.objects.filter(author=request.user).order_by('-created_at')
    paginator = Paginator(posts, 10)  # 每页显示10条帖子
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    return render(request, 'forum/my_posts.html', {'posts': posts})

@login_required
def delete_post(request, post_id):
    """删除帖子"""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('forum:post_detail', post_id=post_id)
    
    post.delete()
    return redirect('forum:index')

@login_required
def delete_comment(request, comment_id):
    """删除评论"""
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return redirect('forum:post_detail', post_id=comment.post.id)
    
    post_id = comment.post.id
    comment.delete()
    return redirect('forum:post_detail', post_id=post_id)

@login_required
def user_messages(request):
    """显示用户的所有消息"""
    user_messages_list = MessageModel.objects.filter(receiver=request.user).order_by('-created_at')
    paginator = Paginator(user_messages_list, 10)  # 每页显示10条消息
    page = request.GET.get('page')
    user_messages_list = paginator.get_page(page)
    
    # 将所有消息标记为已读
    MessageModel.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
    
    return render(request, 'forum/messages.html', {'messages': user_messages_list})

# @login_required
# def chat(request, user_id):
#     """显示与特定用户的聊天界面"""
#     other_user = get_object_or_404(User, id=user_id)
#     messages = MessageModel.objects.filter(
#         models.Q(sender=request.user, receiver=other_user) |
#         models.Q(sender=other_user, receiver=request.user)
#     ).order_by('created_at')
    
#     return render(request, 'forum/chat.html', {
#         'other_user': other_user,
#         'messages': messages
#     })

# @login_required
# @require_POST
# def send_chat_message(request, user_id):
#     """发送聊天消息"""
#     other_user = get_object_or_404(User, id=user_id)
#     content = request.POST.get('content')
    
#     if content:
#         MessageModel.objects.create(
#             sender=request.user,
#             receiver=other_user,
#             message_type='chat',
#             content=content
#         )
#         messages.success(request, '消息发送成功')
    
#     return redirect('forum:chat', user_id=user_id)

def search(request):
    """搜索帖子"""
    query = request.GET.get('q', '')
    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).order_by('-created_at')
    else:
        posts = Post.objects.none()
    
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'forum/search_results.html', {
        'posts': posts,
        'query': query
    })

@login_required
def profile(request):
    """用户个人资料页面"""
    user = request.user
    posts = Post.objects.filter(author=user).order_by('-created_at')[:5]
    comments = Comment.objects.filter(author=user).order_by('-created_at')[:5]
    likes = Like.objects.filter(user=user).order_by('-created_at')[:5]
    
    return render(request, 'forum/profile.html', {
        'user': user,
        'posts': posts,
        'comments': comments,
        'likes': likes
    })

