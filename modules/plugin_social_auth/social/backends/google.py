"""
Google OpenId, OAuth2, OAuth1, Google+ Sign-in backends, docs at:
    http://psa.matiasaguirre.net/docs/backends/google.html
"""
from requests import HTTPError

from social.backends.open_id import OpenIdAuth
from social.backends.oauth import BaseOAuth2, BaseOAuth1
from social.exceptions import AuthMissingParameter, AuthCanceled


class BaseGoogleAuth(object):
    def get_user_id(self, details, response):
        """Use google email as unique id"""
        if self.setting('USE_UNIQUE_USER_ID', False):
            return response['id']
        else:
            return details['email']

    def get_user_details(self, response):
        """Return user details from Orkut account"""
        email = response.get('email', '')
        return {'username': email.split('@', 1)[0],
                'email': email,
                'fullname': response.get('name', ''),
                'first_name': response.get('given_name', ''),
                'last_name': response.get('family_name', '')}


class BaseGoogleOAuth2API(BaseGoogleAuth):
    def user_data(self, access_token, *args, **kwargs):
        """Return user data from Google API"""
        return self.get_json(
            'https://www.googleapis.com/oauth2/v1/userinfo',
            params={'access_token': access_token, 'alt': 'json'}
        )


class GoogleOAuth2(BaseGoogleOAuth2API, BaseOAuth2):
    """Google OAuth2 authentication backend"""
    name = 'google-oauth2'
    REDIRECT_STATE = False
    AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/auth'
    ACCESS_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REVOKE_TOKEN_URL = 'https://accounts.google.com/o/oauth2/revoke'
    REVOKE_TOKEN_METHOD = 'GET'
    DEFAULT_SCOPE = ['https://www.googleapis.com/auth/userinfo.email',
                     'https://www.googleapis.com/auth/userinfo.profile']
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('expires_in', 'expires'),
        ('token_type', 'token_type', True)
    ]

    def revoke_token_params(self, token, uid):
        return {'token': token}

    def revoke_token_headers(self, token, uid):
        return {'Content-type': 'application/json'}


class GooglePlusAuth(BaseGoogleOAuth2API, BaseOAuth2):
    name = 'google-plus'
    REDIRECT_STATE = False
    STATE_PARAMETER = False
    ACCESS_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REVOKE_TOKEN_URL = 'https://accounts.google.com/o/oauth2/revoke'
    REVOKE_TOKEN_METHOD = 'GET'
    DEFAULT_SCOPE = ['https://www.googleapis.com/auth/plus.login',
                     'https://www.googleapis.com/auth/userinfo.email',
                     'https://www.googleapis.com/auth/userinfo.profile']
    EXTRA_DATA = [
        ('id', 'user_id'),
        ('refresh_token', 'refresh_token', True),
        ('expires_in', 'expires'),
        ('access_type', 'access_type', True),
        ('code', 'code')
    ]

    def auth_complete_params(self, state=None):
        params = super(GooglePlusAuth, self).auth_complete_params(state)
        params['redirect_uri'] = 'postmessage'
        return params

    def auth_complete(self, *args, **kwargs):
        token = self.data.get('access_token')
        if not token:
            raise AuthMissingParameter(self, 'access_token')

        self.process_error(self.get_json(
            'https://www.googleapis.com/oauth2/v1/tokeninfo',
            params={'access_token': token}
        ))

        try:
            response = self.request_access_token(
                self.ACCESS_TOKEN_URL,
                data=self.auth_complete_params(),
                headers=self.auth_headers(),
                method=self.ACCESS_TOKEN_METHOD
            )
        except HTTPError as err:
            if err.response.status_code == 400:
                raise AuthCanceled(self)
            else:
                raise
        self.process_error(response)
        return self.do_auth(response['access_token'], response=response,
                            *args, **kwargs)


class GoogleOAuth(BaseGoogleAuth, BaseOAuth1):
    """Google OAuth authorization mechanism"""
    name = 'google-oauth'
    AUTHORIZATION_URL = 'https://www.google.com/accounts/OAuthAuthorizeToken'
    REQUEST_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetRequestToken'
    ACCESS_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetAccessToken'
    DEFAULT_SCOPE = ['https://www.googleapis.com/auth/userinfo#email']

    def user_data(self, access_token, *args, **kwargs):
        """Return user data from Google API"""
        return self.get_querystring(
            'https://www.googleapis.com/userinfo/email',
            auth=self.oauth_auth(access_token)
        )

    def get_key_and_secret(self):
        """Return Google OAuth Consumer Key and Consumer Secret pair, uses
        anonymous by default, beware that this marks the application as not
        registered and a security badge is displayed on authorization page.
        http://code.google.com/apis/accounts/docs/OAuth_ref.html#SigningOAuth
        """
        key_secret = super(GoogleOAuth, self).get_key_and_secret()
        if key_secret == (None, None):
            key_secret = ('anonymous', 'anonymous')
        return key_secret


class GoogleOpenId(OpenIdAuth):
    name = 'google'
    URL = 'https://www.google.com/accounts/o8/id'

    def get_user_id(self, details, response):
        """
        Return user unique id provided by service. For google user email
        is unique enought to flag a single user. Email comes from schema:
        http://axschema.org/contact/email
        """
        return details['email']
