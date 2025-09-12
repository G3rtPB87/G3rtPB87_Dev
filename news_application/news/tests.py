from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.core import mail
from django.conf import settings

from .models import CustomUser, Publisher, Article, Newsletter


# Test cases for the signals
class TestSignal(TestCase):
    def setUp(self):
        # Set email backend to in-memory for testing
        self.original_email_backend = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = (
            'django.core.mail.backends.locmem.EmailBackend'
        )

        # Create a publisher
        self.publisher = Publisher.objects.create(name='Test Publisher')

        # Create a journalist
        self.journalist = CustomUser.objects.create_user(
            username='test_journalist',
            password='password123',
            role='journalist'
        )

        # Create a reader with a valid email
        self.reader = CustomUser.objects.create_user(
            username='test_reader',
            password='password123',
            email='test@example.com',
            role='reader'
        )
        # Add the subscription to the reader
        self.reader.subscriptions_publishers.add(self.publisher)
        self.reader.subscriptions_journalists.add(self.journalist)

        # Create an unapproved article
        # Ensure _original_approved is set correctly
        self.unapproved_article = Article.objects.create(
            title='Unapproved Article',
            content='Content for unapproved article.',
            author=self.journalist,
            publisher=self.publisher,
            approved=False
        )
        self.unapproved_article._original_approved = False

        # Create an unapproved newsletter
        self.unapproved_newsletter = Newsletter.objects.create(
            title='Unapproved Newsletter',
            content='Content for unapproved newsletter.',
            author=self.journalist,
            publisher=self.publisher,
            approved=False
        )
        self.unapproved_newsletter._original_approved = False

    def tearDown(self):
        # Restore original email backend
        settings.EMAIL_BACKEND = self.original_email_backend


@patch('requests.post')
@patch('news.signals.send_mail')
def test_approve_article_sends_email_and_posts_to_x(
    self, mock_send_mail, mock_requests_post
):
    # Mock the X API response to avoid rate limiting
    mock_requests_post.return_value.status_code = 201
    mock_requests_post.return_value.json.return_value = {'id': 'test123'}

    # Approve the article
    self.unapproved_article.approved = True
    self.unapproved_article.save()

    # Assert that the mocked send_mail function was called
    mock_send_mail.assert_called_once()
    self.assertEqual(len(mail.outbox), 0)

    # Check if API call was made
    mock_requests_post.assert_called_once()
    self.assertIn(
        'New article from test_journalist',
        mock_requests_post.call_args[1]['json']['text']
    )


@patch('requests.post')
@patch('news.signals.send_mail')
def test_approve_newsletter_sends_email_and_posts_to_x(
    self, mock_send_mail, mock_requests_post
):
    # Clear outbox before test
    mail.outbox = []

    # Simulate a successful post to X
    mock_requests_post.return_value.status_code = 201
    mock_requests_post.return_value.json.return_value = {'id': '67890'}

    # Approve the newsletter
    self.unapproved_newsletter.approved = True
    self.unapproved_newsletter.save()

    # Assert that the mocked send_mail function was called
    mock_send_mail.assert_called_once()
    self.assertEqual(len(mail.outbox), 0)

    # Check if API call was made
    mock_requests_post.assert_called_once()
    self.assertIn(
        'New newsletter from test_journalist',
        mock_requests_post.call_args[1]['json']['text']
    )


# Test cases for the API views
class TestSubscribedArticlesView(APITestCase):
    def setUp(self):
        self.url = reverse('subscribed_articles')

        # Create users, publishers, and articles for testing
        self.reader = CustomUser.objects.create_user(
            username='reader_user', password='password123', role='reader'
        )
        self.journalist = CustomUser.objects.create_user(
            username='journalist_user',
            password='password123',
            role='journalist'
        )
        self.publisher = Publisher.objects.create(name='Publisher A')

        self.article1 = Article.objects.create(
            title='Article 1',
            content='Content 1',
            author=self.journalist,
            publisher=self.publisher,
            approved=True
        )

        self.article2 = Article.objects.create(
            title='Article 2',
            content='Content 2',
            author=self.journalist,
            publisher=self.publisher,
            approved=False
        )

    def test_get_subscribed_articles_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_subscribed_articles_authenticated_reader_no_subscriptions(
        self
    ):
        self.client.force_login(self.reader)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_get_subscribed_articles_authenticated_reader_with_subscriptions(
        self
    ):
        self.reader.subscriptions_publishers.add(self.publisher)
        self.client.force_login(self.reader)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Article 1')


class TestSubscribedNewslettersView(APITestCase):
    def setUp(self):
        self.url = reverse('subscribed_newsletters')

        # Create users, publishers, and articles for testing
        self.reader = CustomUser.objects.create_user(
            username='reader_user', password='password123', role='reader'
        )
        self.journalist = CustomUser.objects.create_user(
            username='journalist_user',
            password='password123',
            role='journalist'
        )
        self.publisher = Publisher.objects.create(name='Publisher B')

        self.newsletter1 = Newsletter.objects.create(
            title='Newsletter 1',
            content='Newsletter Content 1',
            author=self.journalist,
            publisher=self.publisher,
            approved=True
        )

        self.newsletter2 = Newsletter.objects.create(
            title='Newsletter 2',
            content='Newsletter Content 2',
            author=self.journalist,
            publisher=self.publisher,
            approved=False
        )

    def test_get_subscribed_newsletters_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_subscribed_newsletters_authenticated_reader_with_subscriptions(
        self
    ):
        self.reader.subscriptions_publishers.add(self.publisher)
        self.client.force_login(self.reader)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Newsletter 1')


# NEW COMPREHENSIVE TEST SUITE
class TestRoleBasedAccess(APITestCase):
    """Test role-based access control for all views"""

    def setUp(self):
        # Create users with different roles
        self.reader = CustomUser.objects.create_user(
            username='reader_test',
            password='password123',
            role='reader',
            email='reader@test.com'
        )
        self.journalist = CustomUser.objects.create_user(
            username='journalist_test',
            password='password123',
            role='journalist'
        )
        self.editor = CustomUser.objects.create_user(
            username='editor_test', password='password123', role='editor'
        )

        # Create test content
        self.publisher = Publisher.objects.create(name='Test Publisher')
        self.article = Article.objects.create(
            title='Test Article', content='Test content',
            author=self.journalist, publisher=self.publisher, approved=False
        )
        self.newsletter = Newsletter.objects.create(
            title='Test Newsletter', content='Test content',
            author=self.journalist, publisher=self.publisher, approved=False
        )

    def test_editor_can_approve_article(self):
        """Test editors can approve articles via API"""
        self.client.force_login(self.editor)
        url = reverse(
            'article_approval',
            kwargs={'article_id': self.article.id}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)

    def test_journalist_cannot_approve_article(self):
        """Test journalists cannot approve articles"""
        self.client.force_login(self.journalist)
        url = reverse(
            'article_approval',
            kwargs={'article_id': self.article.id}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_reader_cannot_approve_article(self):
        """Test readers cannot approve articles"""
        self.client.force_login(self.reader)
        url = reverse(
            'article_approval',
            kwargs={'article_id': self.article.id}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_editor_dashboard_access(self):
        """Test only editors can access editor dashboard"""
        self.client.force_login(self.editor)
        response = self.client.get(reverse('editor_dashboard'))
        self.assertIn(response.status_code, [200, 302])

    def test_non_editor_dashboard_access_denied(self):
        """Test non-editors cannot access editor dashboard"""
        for user in [self.reader, self.journalist]:
            self.client.force_login(user)
            response = self.client.get(reverse('editor_dashboard'))
            self.assertIn(response.status_code, [302, 403])


class TestSubscriptionLogic(APITestCase):
    """Test subscription functionality"""

    def setUp(self):
        self.reader = CustomUser.objects.create_user(
            username='sub_reader',
            password='password123',
            role='reader',
            email='sub@test.com'
        )
        self.journalist = CustomUser.objects.create_user(
            username='sub_journalist',
            password='password123',
            role='journalist'
        )
        self.publisher = Publisher.objects.create(name='Sub Publisher')

        # Create approved content
        self.article = Article.objects.create(
            title='Sub Article', content='Content',
            author=self.journalist, publisher=self.publisher, approved=True
        )
        self.newsletter = Newsletter.objects.create(
            title='Sub Newsletter', content='Content',
            author=self.journalist, publisher=self.publisher, approved=True
        )

    def test_subscribed_content_filtering(self):
        """Test API returns only subscribed content"""
        # Reader subscribes to publisher
        self.reader.subscriptions_publishers.add(self.publisher)
        self.client.force_login(self.reader)

        # Test articles endpoint
        article_response = self.client.get(reverse('subscribed_articles'))
        self.assertEqual(article_response.status_code, 200)
        self.assertEqual(len(article_response.data), 1)
        self.assertEqual(article_response.data[0]['title'], 'Sub Article')

        # Test newsletters endpoint
        newsletter_response = self.client.get(
            reverse('subscribed_newsletters')
        )
        self.assertEqual(newsletter_response.status_code, 200)
        self.assertEqual(len(newsletter_response.data), 1)
        self.assertEqual(
            newsletter_response.data[0]['title'],
            'Sub Newsletter'
        )

    def test_unsubscribed_content_empty(self):
        """Test API returns empty for unsubscribed users"""
        self.client.force_login(self.reader)

        article_response = self.client.get(reverse('subscribed_articles'))
        self.assertEqual(article_response.status_code, 200)
        self.assertEqual(len(article_response.data), 0)


class TestEmailXIntegration(APITestCase):
    """Test email and X integration comprehensively"""

    def setUp(self):
        self.journalist = CustomUser.objects.create_user(
            username='email_journalist',
            password='password123',
            role='journalist'
        )
        self.reader = CustomUser.objects.create_user(
            username='email_reader',
            password='password123',
            role='reader',
            email='reader@test.com'
        )
        self.publisher = Publisher.objects.create(name='Email Publisher')

        # Create unapproved article
        self.article = Article.objects.create(
            title='Email Article', content='Email content',
            author=self.journalist, publisher=self.publisher, approved=False
        )
        self.article._original_approved = False

    @patch('requests.post')
    @patch('news.signals.send_mail')
    def test_approval_sends_email_and_x_post(
        self, mock_send_mail, mock_requests_post
    ):
        """Test approval triggers both email and X post"""
        # Setup mocks
        mock_requests_post.return_value.status_code = 201
        mock_requests_post.return_value.json.return_value = {'id': '123'}

        # Subscribe reader to publisher
        self.reader.subscriptions_publishers.add(self.publisher)

        # Approve the article
        self.article.approved = True
        self.article.save()

        # Check email was sent
        self.assertTrue(mock_send_mail.called)

        # Check X API was called
        self.assertTrue(mock_requests_post.called)

    @patch('requests.post')
    def test_x_api_failure_handling(self, mock_requests_post):
        """Test X API failure doesn't break the application"""
        # Mock API failure
        mock_requests_post.return_value.status_code = 400
        mock_requests_post.return_value.json.return_value = (
            {'error': 'Bad request'}
        )

        # This should not raise an exception
        try:
            self.article.approved = True
            self.article.save()
            success = True
        except requests.RequestException:
            success = False

        self.assertTrue(success)


class TestAPIComprehensive(APITestCase):
    """Comprehensive API testing"""

    def setUp(self):
        self.editor = CustomUser.objects.create_user(
            username='api_editor', password='password123', role='editor'
        )
        self.article = Article.objects.create(
            title='API Article', content='Content',
            author=self.editor, approved=False
        )

    def test_article_approval_api(self):
        """Test article approval API endpoint"""
        self.client.force_login(self.editor)
        url = reverse(
            'article_approval',
            kwargs={'article_id': self.article.id}
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.data)

        # Verify article was approved
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)

    def test_newsletter_approval_api(self):
        """Test newsletter approval API endpoint"""
        newsletter = Newsletter.objects.create(
            title='API Newsletter', content='Content',
            author=self.editor, approved=False
        )

        self.client.force_login(self.editor)
        url = reverse(
            'newsletter_approval',
            kwargs={'newsletter_id': newsletter.id}
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.data)

        # Verify newsletter was approved
        newsletter.refresh_from_db()
        self.assertTrue(newsletter.approved)

    def test_api_method_not_allowed(self):
        """Test API endpoints reject unsupported methods"""
        self.client.force_login(self.editor)

        # Test GET where POST is required for approval endpoints
        article_url = reverse(
            'article_approval',
            kwargs={'article_id': self.article.id}
        )
        response = self.client.get(article_url)
        self.assertEqual(response.status_code, 405)

        # Test POST where GET is required for subscription endpoints
        articles_url = reverse('subscribed_articles')
        response = self.client.post(articles_url)
        self.assertEqual(response.status_code, 405)
