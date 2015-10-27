from __future__ import unicode_literals

from django import forms

from .models import Review, Comment, SubmissionMessage, SupportingDocument


class SupportingDocumentCreateForm(forms.ModelForm):

    class Meta:
        model = SupportingDocument
        fields = [
            "document",
            "description",
        ]


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ["comment"]


class ReviewCommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ["text"]


class SubmitterCommentForm(forms.ModelForm):

    class Meta:
        model = SubmissionMessage
        fields = ["message"]
