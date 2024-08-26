from flask_appbuilder.security.sqla.models import User
from sqlalchemy import Column, Integer, ForeignKey, String, Sequence, Table, Text
from sqlalchemy.orm import relationship, backref
from flask_appbuilder import Model

class Myuser(User):
    __tablename__ = 'ab_user'
    contract = Column(String(256))
    iban = Column(String(256))
    working_hours = Column(Integer, nullable=False, default=8)
    hour_rate = Column(Integer)
    team_id = Column(Integer, ForeignKey('ab_user.id'), index=True)
    team = relationship('Myuser', backref=backref('report_to', remote_side='Myuser.id'), primaryjoin='Myuser.id == Myuser.team_id')
    mobile_phone = Column(Integer)
    note = Column(Text)