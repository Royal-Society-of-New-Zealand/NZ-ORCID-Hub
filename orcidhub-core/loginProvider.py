from application import login_manager
from functools import wraps
from flask_login import current_user
from model import OrcidUser
from model import UserRole

def login_required(role=[UserRole.ANY]):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):

            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            urole = OrcidUser.query.filter_by(email=current_user.get_id()).first().get_urole()
            if ((urole not in role) and (UserRole.ANY not in role)):
                return login_manager.unauthorized()
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

@login_manager.user_loader
def load_user(user_id):
    from model import OrcidUser
    return OrcidUser.query.filter_by(email=user_id).first()
