from flask_appbuilder.security.sqla.manager import SecurityManager
from .sec_models import Myuser
from .sec_views import MyUserDBModelView

class MySecurityManager(SecurityManager):
    user_model = Myuser
    userdbmodelview = MyUserDBModelView