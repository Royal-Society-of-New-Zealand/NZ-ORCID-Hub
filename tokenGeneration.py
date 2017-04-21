from itsdangerous import URLSafeTimedSerializer

from application import app


def generate_confirmation_token(email):
    """Generate Organisation registration confirmation token."""
    serializer = URLSafeTimedSerializer(app.config['TOKEN_SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['TOKEN_PASSWORD_SALT'])


# Token Expiry after 15 days.
def confirm_token(token, expiration=1300000):
    serializer = URLSafeTimedSerializer(app.config['TOKEN_SECRET_KEY'])
    try:
        email = serializer.loads(
            token, salt=app.config['TOKEN_PASSWORD_SALT'], max_age=expiration)
    except:
        return False
    return email
