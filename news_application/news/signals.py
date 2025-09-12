from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import requests
from requests_oauthlib import OAuth1

from .models import Article, CustomUser, Publisher, Newsletter


@receiver(post_save, sender=Article)
def approve_article(sender, instance, created, **kwargs):
    # Check if the article has just been approved
    if (
        not created
        and instance.approved
        and instance.approved != instance._original_approved
    ):
        author = instance.author
        publisher = instance.publisher

        subscribers_to_author = CustomUser.objects.filter(
            subscriptions_journalists=author
        ).values_list('email', flat=True)

        if publisher:
            subscribers_to_publisher = CustomUser.objects.filter(
                subscriptions_publishers=publisher
            ).values_list('email', flat=True)
            subscribers_emails = list(
                set(
                    list(subscribers_to_author) +
                    list(subscribers_to_publisher)
                )
            )
        else:
            subscribers_emails = list(subscribers_to_author)

        if subscribers_emails:
            subject = f'New Article from {author.username}!'
            message = render_to_string(
                'news/article_email.html',
                {'article': instance}
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = subscribers_emails
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                html_message=message
            )

        try:
            consumer_key = '0IHU2LGnrMS19zYXjWUXiVmCx'
            consumer_secret = (
                'KPuxnc2G1TKFWT7yLKF4vh3FUNmMcqzchdUg2nVI55P2MSEcTy'
            )
            access_token = '1960271448150609920-cwaD31uRAte9M5HfCJqVaND2hEyE9w'
            access_token_secret = (
                'u92WqSTmBMC7by5m0MYQAxogdpZM2dm7tid517lOWdjUn'
            )

            oauth = OAuth1(
                consumer_key,
                client_secret=consumer_secret,
                resource_owner_key=access_token,
                resource_owner_secret=access_token_secret
            )

            api_url = "https://api.x.com/2/tweets"
            post_data = {
                'text': (
                    f"New article from {author.username}: {instance.title} - "
                    + f"Read more @ http://yrdomain.com/articles/{instance.id}"
                )
            }

            response = requests.post(api_url, auth=oauth, json=post_data)

            if response.status_code == 201:
                print(f"Successfully posted to X: {response.json()}")
            else:
                print(f"Failed to post to X: {response.json()}")

        except requests.exceptions.RequestException as e:
            print(f"Error posting to X: {e}")
        except ValueError as e:
            print(f"Error processing response from X: {e}")


@receiver(post_save, sender=Newsletter)
def approve_newsletter(sender, instance, created, **kwargs):
    # Check if the newsletter has just been approved
    if (
        not created
        and instance.approved
        and instance.approved != instance._original_approved
    ):
        author = instance.author
        publisher = instance.publisher

        subscribers_to_author = CustomUser.objects.filter(
            subscriptions_journalists=author
        ).values_list('email', flat=True)

        if publisher:
            subscribers_to_publisher = CustomUser.objects.filter(
                subscriptions_publishers=publisher
            ).values_list('email', flat=True)
            subscribers_emails = list(
                set(
                    list(subscribers_to_author) +
                    list(subscribers_to_publisher)
                )
            )
        else:
            subscribers_emails = list(subscribers_to_author)

        if subscribers_emails:
            try:
                subject = f'New Newsletter from {author.username}!'
                message = render_to_string(
                    'news/newsletter_email.html',
                    {'newsletter': instance}
                )
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = subscribers_emails
                send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    html_message=message
                )
            except (
                smtplib.SMTPException,
                django.core.mail.BadHeaderError
            ) as e:
                print(f"Error sending email for newsletter: {e}")

        try:
            consumer_key = '0IHU2LGnrMS19zYXjWUXiVmCx'
            consumer_secret = (
                'KPuxnc2G1TKFWT7yLKF4vh3FUNmMcqzchdUg2nVI55P2MSEcTy'
            )
            access_token = '1960271448150609920-cwaD31uRAte9M5HfCJqVaND2hEyE9w'
            access_token_secret = (
                'u92WqSTmBMC7by5m0MYQAxogdpZM2dm7tid517lOWdjUn'
            )

            oauth = OAuth1(
                consumer_key,
                client_secret=consumer_secret,
                resource_owner_key=access_token,
                resource_owner_secret=access_token_secret
            )

            api_url = "https://api.x.com/2/tweets"
            post_data = {
                'text': (
                    f"New newsletter from {author.username}: "
                    f"{instance.title} - "
                    f"Read more @ http://yrdomain.com/articles/{instance.id}"
                )
            }

            response = requests.post(api_url, auth=oauth, json=post_data)

            if response.status_code == 201:
                print(f"Successfully posted to X: {response.json()}")
            else:
                print(f"Failed to post to X: {response.json()}")

        except requests.exceptions.RequestException as e:
            print(f"Error posting to X: {e}")
        except ValueError as e:
            print(f"Error processing response from X: {e}")
