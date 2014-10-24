from flask.ext.security import UserMixin

class User(UserMixin):
    def __init__(self, imei, name, password, id, active=True):
        self.imei = imei
        self.name = name
        self.password = password
        self.id = id
        self.active = active
        
    def is_active(self):
        return self.active