from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count

# Create your views here.

def post_list (request, tag_slug=None) :
    post_list = Post.published.all()
    tag = None
    if tag_slug :
        tag = get_object_or_404(Tag, slug= tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    all_tags = Tag.objects.all()
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page',1)
    posts = paginator.page(page_number)
    return render(request,'blog/post/list.html', {'posts': posts, 'tag': tag, 'all_tags': all_tags})

def post_detail(request, year, month, day, post) :
    post = get_object_or_404(Post, status= Post.Status.PUBLISHED,
        slug=post, publish__year=year, publish__month=month, publish__day=day)
    comments = post.comments.filter(activate= True)
    form = CommentForm()
    all_tags = Tag.objects.all()
    post_tags_ids = post.tags.values_list('id', flat= True)
    similar_post = Post.published.filter(tags__in=post_tags_ids).exclude(id= post.id)
    similar_post= similar_post.annotate(same_tags= Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request, 'blog/post/detail.html', {'post' : post, 'comments': comments, 'form': form, 'all_tags': all_tags, 'similar_post':similar_post})

def post_share(request , post_id) :
    post = get_object_or_404(Post, status= Post.Status.PUBLISHED, id=post_id)
    sent = False
    if request.method == 'POST' :
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url} \n\n {cd['name']}\'s comments: {cd['comment']}"
            send_mail(subject, message, cd['email'], ['mohy.website@gmail.com'])
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})

@require_POST
def post_comment(request, post_id):
    post= get_object_or_404(Post, status= Post.Status.PUBLISHED, id=post_id)
    comment = None 
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post= post
        comment.save()
    return render(request, 'blog/post/comment.html',{'post': post, 'form': form, 'comment': comment})