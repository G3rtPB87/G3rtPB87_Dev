from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser, Article, Publisher, Newsletter


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    publishers = forms.ModelMultipleChoiceField(
        queryset=Publisher.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Affiliated Publishers (for Editors/Journalists)"
    )

    # ADD SUBSCRIPTION FIELDS FOR READERS
    subscriptions_publishers = forms.ModelMultipleChoiceField(
        queryset=Publisher.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Subscribe to Publishers (for Readers)"
    )

    subscriptions_journalists = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role='journalist'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Subscribe to Journalists (for Readers)"
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'role',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    (
                        (
                            'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm '
                            'focus:outline-none focus:ring-gray-500 '
                            'focus:border-gray-500'
                        )
                    )
                )
            })
        self.fields['role'].help_text = 'Select a role for the new user.'

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        if role:
            role_lower = role.lower()

            # Clear fields based on role
            if role_lower == 'reader':
                # Clear publisher affiliations for readers
                cleaned_data['publishers'] = []

            elif role_lower in ['editor', 'journalist']:
                # Clear subscription fields for editors/journalists
                cleaned_data['subscriptions_publishers'] = []
                cleaned_data['subscriptions_journalists'] = []

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()

            # Handle publishers for editors/journalists
            publishers = self.cleaned_data.get('publishers')
            if publishers and user.role:
                role_lower = user.role.lower()
                if role_lower == 'editor':
                    user.publishers_editor.set(publishers)
                elif role_lower == 'journalist':
                    user.publishers_journalist.set(publishers)

            # Handle subscriptions for readers
            if user.role and user.role.lower() == 'reader':
                subscriptions_publishers = self.cleaned_data.get(
                    'subscriptions_publishers'
                )
                subscriptions_journalists = self.cleaned_data.get(
                    'subscriptions_journalists'
                )

                if subscriptions_publishers:
                    user.subscriptions_publishers.set(subscriptions_publishers)

                if subscriptions_journalists:
                    user.subscriptions_journalists.set(
                        subscriptions_journalists
                    )

        return user


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'publisher']
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'w-full px-3 py-2 border rounded-md'}
            ),
            'content': forms.Textarea(
                attrs={'class': 'w-full px-3 py-2 border rounded-md'}
            ),
            'publisher': forms.Select(
                attrs={'class': 'w-full px-3 py-2 border rounded-md'}
            ),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['title', 'content', 'publisher']
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'w-full px-3 py-2 border rounded-md'}
            ),
            'content': forms.Textarea(
                attrs={'class': 'w-full px-3 py-2 border rounded-md'}
            ),
            'publisher': forms.Select(
                attrs={'class': 'w-full px-3 py-2 border rounded-md'}
            ),
        }


class PublisherForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ['name']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'w-full px-3 py-2 border rounded-md'}
            ),
        }
