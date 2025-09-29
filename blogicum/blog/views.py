import datetime as dt

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserChangeForm
from django.core.paginator import Paginator
from django.db import models
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (ListView, CreateView,
                                  DetailView, UpdateView, DeleteView)

from core.constant import PAG
from blog.models import Post, Category

from .forms import AddCommentForm, PostCreateForm
from .models import Comment

User = get_user_model()


def get_posts_query(posts):
    return posts.select_related(
        'author', 'location', 'category'
    ).annotate(
        comment_count=models.Count('commit')
    ).order_by('-pub_date')


filter_posts = {
    'category__is_published': True,
    'is_published': True,
    'pub_date__lte': dt.datetime.now()
}


class ProfileDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = get_posts_query(self.get_object().posts.all())
        paginate_by = Paginator(posts, PAG)
        context['page_obj'] = paginate_by.page(
            self.request.GET.get('page', default=1))
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserChangeForm
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:edit_profile')

    def get_object(self):
        return self.request.user


class PostListView(ListView):
    model = Post
    paginate_by = PAG
    template_name = 'blog/index.html'

    def get_queryset(self):
        return get_posts_query(super().get_queryset()).filter(**filter_posts)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        query = models.Q(author_id=self.request.user.id) | models.Q(
            **filter_posts
        )
        return get_object_or_404(Post, query, id=self.kwargs['post_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AddCommentForm()
        context['comments'] = (
            self.object.commit.select_related('author')
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostCreateForm
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username})


class PostMixin(LoginRequiredMixin):
    model = Post
    form_class = PostCreateForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.id)
        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(PostMixin, UpdateView):
    form_class = PostCreateForm


class PostDeleteView(PostMixin, DeleteView):
    success_url = reverse_lazy('blog:index')


class CommentMixin(LoginRequiredMixin):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', post_id=comment.id)
        return super().dispatch(request, *args, **kwargs)


class CommentUpdateView(CommentMixin, UpdateView):
    form_class = AddCommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    pass


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = AddCommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            id=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class CategoryPostListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True)
        posts = category.post.all()
        return get_posts_query(posts).filter(**filter_posts)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category, slug=self.kwargs['category_slug'])
        return context
