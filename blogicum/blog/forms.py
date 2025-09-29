from django import forms

from .models import Comment, Post


class AddCommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)


class PostCreateForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {'pub_date': forms.DateInput(
            attrs={'type': 'date'}, format='%Y-%m-%d')
        }
        fields = ('title', 'text', 'pub_date', 'location', 'image', 'category')
