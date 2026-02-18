from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads the access token from an HTTP-only cookie
    instead of the Authorization header.
    Falls back to the default header-based authentication if no cookie is found.
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get('access_token')

        if raw_token is None:
            return super().authenticate(request)

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
