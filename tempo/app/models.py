from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from flask_appbuilder.filemanager import ImageManager 
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, DateTime, Text, Table, func, Float
from sqlalchemy.orm import relationship
from .sec_models import Myuser
from flask_appbuilder.models.decorators import renders
from markupsafe import Markup
from sqlalchemy.orm import session
from flask import g, url_for

def get_user_id():
    return g.user.id





"""

You can use the extra Flask-AppBuilder fields and Mixin's

AuditMixin will add automatic timestamp of created and modified by who


To ADD.

Deliverable Status - Pending - Rejected - Canceled -  


"""
class Author(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    '''
    def __repr__(self):
        return '<Author: {}>'.format(self.books)
    '''      
class Book(Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(50))
    author_id = Column(Integer, ForeignKey('author.id'))
    author = relationship(Author, backref='Books', )

 

import datetime
def today():
    return datetime.datetime.today().strftime('%Y-%m-%d')

def date_csm(date):
    return date.strftime('%d-%m-%Y %H:%M:%S')

class Account(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    
    def __repr__(self):
        return self.name
    

class Project(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    account = relationship(Account, backref='Projects')
    def __repr__(self):
        return self.name
    
    @renders('created_on_custom')
    def created_on_custom(self):
    # will render this columns as bold on ListWidget
        return Markup('<b>' + self.created_on.strftime('%A %d %B, %Y') + '</b>')
    
class Order(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship(Project, backref='Orders')
    payment_days = Column(Integer, nullable=False)
    pending_deliverable = Column(Boolean, default=False)
    
    note = Column(Text)
    
    def __repr__(self):
        return self.name + ' | ' + self.project.name + ' for ' + str(self.project.account)
    
    def amount(self): 
        return sum(Revision.amount for Revision in self.Revisions)
    
    def amount_q(self):
        return session.query(func.sum(Order_revision.amount)).filter(Order_revision.order_id == self.id).all()
    
    
    def total_hours(self):
        return sum(Revision.hours for Revision in self.Revisions)
    
    def due_date(self):
        due_date = session.query(Order_revision).filter(
            Order_revision.order_id == self.id).order_by(
                Order_revision.due_date.desc().first())
        return due_date.strftime('%A %d %B, %Y')
    
class Order_revision(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('order.id'))
    order = relationship(Order, backref='Revisions')
    revision = Column(String(50))
    hours = Column(Integer)
    amount = Column(Integer)
    due_date = Column(Date)
    note = Column(Text)
    def __repr__(self):
        return self.order.name + ' | ' + str(self.revision)

class Project_status(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    start = Column(Date)
    end = Column(Date)
    order_revision_id = Column(Integer, ForeignKey('order_revision.id'))
    order_revision = relationship(Order_revision, backref='PSRs')
    seconds = Column(Integer)
    amount = Column(Integer)
    approved = Column(Boolean, default=False)
    approved_on = Column(Date)
    
    def __repr__(self):
        return 'SAL ' + str(self.id)
    
    def deliverables_count(self):
        return len(self.Deliverables) 
    
    def task_time(self):         
        tot_seconds = sum((task.duration for deliverable in self.Deliverables for task in deliverable.Tasks))
        
        seconds = datetime.timedelta(seconds=tot_seconds).seconds
        return str(datetime.timedelta(seconds=seconds))
    
    def est_time(self):         
        tot_seconds = sum((deliverable.projecttask.est_seconds for deliverable in self.Deliverables))
        
        seconds = datetime.timedelta(seconds=tot_seconds).seconds
        return str(datetime.timedelta(seconds=seconds))
    
     
class Invoice(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    project_status_id = Column(Integer, ForeignKey('project_status.id'))
    project_status = relationship(Project_status, backref='Invoices')
    approved = Column(Boolean, default=True)
    approved_on = Column(Date)
    billed = Column(Boolean, default=True)
    billed_on = Column(Date)
    paid = Column(Boolean, default=True)
    paid_on = Column(Date)
    note = Column(Text)
    
    def __repr__(self):
        return 'Invoice ' + str(self.id)
    
    def due_date(self):
        return self.billed_on + datetime.timedelta(days=self.order_revision.order.payment_days)
    
    
class Timesheet(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    date = Column(Date, default=today, nullable=False)
    project_status_id = Column(Integer, ForeignKey('project_status.id'))
    project_status = relationship(Project_status, backref='Timesheets')
    approved = Column(Boolean, default=False)
    def __repr__(self):
        return 'TS'+ str(self.id) + " | " + str(self.date)
    
    @renders('date')
    def date_cs(self):
    # will render this columns as bold on ListWidget
        return Markup('<b>' + self.date.strftime('%A %d %B, %Y') + '</b>')
    
    def time(self): 
        tot_seconds = sum(Task.duration for Task in self.Tasks)
        seconds = datetime.timedelta(seconds=tot_seconds).seconds
        return str(datetime.timedelta(seconds=seconds))
    
    def seconds(self): 
        tot_seconds = sum(Task.duration for Task in self.Tasks)
        seconds = datetime.timedelta(seconds=tot_seconds).seconds
        return seconds


assoc_users_prjtasks = Table('users_prjtasks', Model.metadata,
                                      Column('id', Integer, primary_key=True),
                                      Column('user_id', Integer, ForeignKey('ab_user.id')),
                                      Column('prjtask_id', Integer, ForeignKey('projecttask.id'))
)



class Projecttask(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    #project_id = Column(Integer, ForeignKey('project.id'))
    #project = relationship(Project, backref='ProjectTasks')
    order_id = Column(Integer, ForeignKey('order.id'))
    order = relationship(Order, backref='ProjectTasks')
    est_seconds = Column(Integer, default=0)
    hour_rate = Column(Float, default=0)
    #reject_restart = Column(Boolean, default=True)
    billable = Column(Boolean, default=True)
    users = relationship('Myuser', secondary=assoc_users_prjtasks, backref='ProjectTasks')
    def __repr__(self):
        return self.order.project.name +" | " + self.name 
    
    def est_min(self):
        return self.est_seconds/60


      
class Deliverable(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    projecttask_id = Column(Integer, ForeignKey('projecttask.id'))
    projecttask = relationship(Projecttask, backref='Deliverables')
    timesheet_id = Column(Integer, ForeignKey('timesheet.id'))
    timesheet = relationship(Timesheet, backref='Deliverables')
    project_status_id = Column(Integer, ForeignKey('project_status.id'))
    project_status = relationship(Project_status, backref='Deliverables')
    duration = Column(Integer)
    revision = Column(Integer, default=1, nullable=False)
    completed = Column(Boolean, default=False)
    inputs = Column(Text)
    billed = Column(Boolean, default=False)
    def __repr__(self):
        return self.name + " Rev " + str(self.revision)      
    
    @renders('duration')
    def time(self): 
        tot_seconds = self.duration
        seconds = datetime.timedelta(seconds=tot_seconds).seconds
        return str(datetime.timedelta(seconds=seconds))

'''
example of group_contact function to concatenate tasks input into deliverable when completed.
db.session.query(
   Class.class_id,
   Class.class_name,
   func.group_concat(User.user_fistName.distinct()),
   func.group_concat(Course.course_name.distinct())
   ).filter(Class.courses, User.classes).group_by(Class.class_id)

'''
class Task(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    timesheet_id = Column(Integer, ForeignKey('timesheet.id'))
    timesheet = relationship(Timesheet, backref='Tasks')
    deliverable_id = Column(Integer, ForeignKey('deliverable.id'))
    deliverable = relationship(Deliverable, backref='Tasks')
    projecttask_id = Column(Integer, ForeignKey('projecttask.id'))
    projecttask = relationship(Projecttask, backref='Tasks')
    start = Column(DateTime)
    end = Column(DateTime)
    duration = Column(Integer)
    input_required = Column(String(100))
    completed = Column(Boolean, default=False)
    photo = Column(ImageColumn(size=(300, 300, True), thumbnail_size=(30, 30, True)))
    '''
    def photo_img(self):
        im = ImageManager()
        if self.photo:
            return Markup('<a href="' + url_for('PersonModelView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="' + im.get_url(self.photo) +\
              '" alt="Photo" class="img-rounded img-responsive"></a>')
        else:
            return Markup('<a href="' + url_for('PersonModelView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="//:0" alt="Photo" class="img-responsive"></a>')

    def photo_img_thumbnail(self):
        im = ImageManager()
        if self.photo:
            return Markup('<a href="' + url_for('PersonModelView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="' + im.get_url_thumbnail(self.photo) +\
              '" alt="Photo" class="img-rounded img-responsive"></a>')
        else:
            return Markup('<a href="' + url_for('PersonModelView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="//:0" alt="Photo" class="img-responsive"></a>')
    '''
    def __repr__(self):
        return str(id) + self.name 
    '''
    @renders('duration')
    def time(self): 
        tot_seconds = self.duration
        seconds = datetime.timedelta(seconds=tot_seconds).seconds
        return str(datetime.timedelta(seconds=seconds))
    '''
    
    
    @renders('start')
    def task_start(self):
        return date_csm(self.start)
    
    @renders('end')
    def task_end(self):
        return date_csm(self.end)

class Step(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    position = Column(Integer, nullable=False, default=0, unique=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    projecttask_id = Column(Integer, ForeignKey('projecttask.id'))
    projecttask = relationship(Projecttask, backref='Steps')
    input_required = Column(String(100)) 
    completed = Column(Boolean, default=False)
    photo = Column(ImageColumn(size=(1800, 900, True), thumbnail_size=(64, 48, True)))

    def img_url(self): 
        im = ImageManager()
        if self.photo: 
            return Markup('<img class="imgx" src="' + im.get_url(self.photo) +\
              '" alt="Photo" class="screenshot img-rounded img-responsive" style="margin-right: auto;margin-left: auto;display: block;">') 
        else:
            return Markup('<a href="' + url_for('StepView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="//:0" alt="Photo" class="img-responsive"></a>')

    
    def photo_img(self): 
        im = ImageManager()
        if self.photo:
            return Markup('<a href="' + url_for('StepView.show',pk=str(self.id)) +\
             '" class="screenshot"><img src="' + im.get_url(self.photo) +\
              '" alt="Photo" class="screenshot img-rounded img-responsive" style="margin-right: auto;margin-left: auto;display: block;"></a>') 
        else:
            return Markup('<a href="' + url_for('StepView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="//:0" alt="Photo" class="img-responsive"></a>')

    def photo_img_thumbnail(self):
        im = ImageManager()
        if self.photo:
            return Markup('<a href="' + url_for('StepView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="' + im.get_url_thumbnail(self.photo) +\
              '" alt="Photo" class="img-rounded img-responsive"></a>')
        else:
            return Markup('<a href="' + url_for('StepView.show',pk=str(self.id)) +\
             '" class="thumbnail"><img src="//:0" alt="Photo" class="img-responsive"></a>')
    
    def __repr__(self):
        return str(id) + self.name 
        
class Typeoffwork(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    note = Column(Text)
    
class Dayoffwork(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    start = Column(Date, nullable = False)
    end = Column(Date, nullable = False)
    note = Column(Text)
    typeoffwork_id = Column(Integer, ForeignKey('typeoffwork.id'), nullable=False)
    typeoffwork = relationship(Typeoffwork, backref='DaysOff')
    approved = Column(Boolean, default=False)    
    

class Timeoffwork(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable = False)
    hours = Column(Float, nullable=False)
    note = Column(Text)
    typeoffwork_id = Column(Integer, ForeignKey('typeoffwork.id'), nullable=False)
    typeoffwork = relationship(Typeoffwork, backref='TimeOff')
    approved = Column(Boolean, default=False)      

class Comments(Model, AuditMixin):
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    task_id = Column(Integer, ForeignKey('task.id'))
    task = relationship(Task, backref='Comments')
    
    
# Rejected
# Il task può essere rejected
# Il deliverable con Task rejected è pending e rejected
# il del rejected può o meno essere addebitato con una percentuale X del tempo totale
# batch di deliverable con input diversi

# GAIA  
    