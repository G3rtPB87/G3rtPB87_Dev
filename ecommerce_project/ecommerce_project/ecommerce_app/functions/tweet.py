import json
import requests
from requests_oauthlib import OAuth1Session


class Tweet:
    """
    A class to handle Twitter API authentication and tweeting.
    """
    # Replace with your actual consumer key and secret
    CONSUMER_KEY = 'uAiFNzMYrQ9OrgQtXfCSIQdyQ'
    CONSUMER_SECRET = 'nOPVkJX0QfrY6QLoIyp5mvzbjYyjtJakpJBgnt9msU3Oasxwnk'

    # The singleton instance
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print('Creating the Tweet object')
            cls._instance = super(Tweet, cls).__new__(cls)
            cls._instance.authenticate()
        return cls._instance

    def authenticate(self):
        """
        Authenticates the application with the Twitter API.
        """
        # Get request token
        # The URL has been updated from 'twitter.com' to 'x.com'
        request_token_url = (
            "https://api.x.com/oauth/request_token"
            "?oauth_callback=oob"
            "&x_auth_access_type=write"
        )
        oauth = OAuth1Session(
            self.CONSUMER_KEY,
            client_secret=self.CONSUMER_SECRET
        )
        try:
            fetch_response = oauth.fetch_request_token(request_token_url)
        except ValueError:
            print(
                "There may have been an issue with the consumer_key or "
                "consumer_secret you entered."
            )
            return

        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")
        print("Got OAuth token: %s" % resource_owner_key)

        # Get authorization
        # The URL has been updated from 'twitter.com' to 'x.com'
        base_authorization_url = "https://api.x.com/oauth/authorize"
        authorization_url = oauth.authorization_url(base_authorization_url)
        print("Please go here and authorize: %s" % authorization_url)
        verifier = input("Paste the PIN here: ")

        # Get the access token
        # The URL has been updated from 'twitter.com' to 'x.com'
        access_token_url = "https://api.x.com/oauth/access_token"
        oauth = OAuth1Session(
            self.CONSUMER_KEY,
            client_secret=self.CONSUMER_SECRET,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )
        oauth_tokens = oauth.fetch_access_token(access_token_url)
        access_token = oauth_tokens["oauth_token"]
        access_token_secret = oauth_tokens["oauth_token_secret"]

        # Make the request
        self.oauth = OAuth1Session(
            self.CONSUMER_KEY,
            client_secret=self.CONSUMER_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        print("Authentication successful!")

    def make_tweet(self, tweet_text):
        """
        Sends a tweet to the Twitter API.
        """
        if not hasattr(self, 'oauth'):
            raise ValueError('Authentication failed!')

        # The URL has been updated from 'twitter.com' to 'x.com'
        response = self.oauth.post(
            "https://api.x.com/2/tweets",
            json={"text": tweet_text},
        )

        if response.status_code != 201:
            raise requests.exceptions.HTTPError(
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )

        json_response = response.json()
        print(json.dumps(json_response, indent=4, sort_keys=True))
