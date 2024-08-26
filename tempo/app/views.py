from flask import render_template, request, g, redirect, flash, send_file
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi, BaseView, expose, has_access, CompactCRUDMixin
from .models import Author, Book, Project, Projecttask, Deliverable, Timesheet, Task, Comments, Account, Order, Order_revision, Project_status, Invoice
from .sec_models import Myuser
from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterStartsWith, FilterRelationOneToManyEqual, FilterEqual
from flask_appbuilder.actions import action
from . import appbuilder, db, app
import datetime
import csv, random


def get_user():
    return g.user

def today():
    return datetime.datetime.now().strftime('%Y-%m-%d')

def timesheet_update(task):    
    timesheet = db.session.query(Timesheet).filter(Timesheet.date == datetime.datetime.now().strftime('%Y-%m-%d'),
                                              Timesheet.created_by == g.user).first()
    if timesheet:
        task.timesheet = timesheet
    else:
        timesheet = Timesheet(date = datetime.datetime.today(), created_by = g.user)
        task.timesheet = timesheet
    return task
   
class TimesheetOld(BaseView):

    default_view = 'editor'
    
    

    @expose('/editor/', methods=["GET","POST"])
    @has_access
    def editor(self):
        if request.method == "POST":
            print('**** * * * * * * * POST * * * * * * *')
            global_book_object = Book()

            title = request.form["title"]
            author_name = request.form["author"]
            print('**************** ******* SUBMIT ************')

            author_exists = db.session.query(Author).filter(Author.name == author_name).first()
            print(author_exists)
            # check if author already exists in db
            if author_exists:
                author_id = author_exists.id
                book = Book(author_id=author_id, title=title)
                db.session.add(book)
                db.session.commit()
                global_book_object = book
            else:
                author = Author(name=author_name)
                db.session.add(author)
                db.session.commit()

                book = Book(author_id=author.id, title=title)
                db.session.add(book)
                db.session.commit()
                global_book_object = book

            response = f"""
            <tr>
                <td>{title}</td>
                <td>{author_name}</td>
                <td>
                    <button class="btn btn-primary"
                        hx-get="/timesheet/modifier/{global_book_object.id}">
                        Edit Title
                    </button>
                </td>
                <td>
                    <button hx-delete="/timesheet/modifier/{global_book_object.id}"
                        class="btn btn-primary">
                        Delete
                    </button>
                </td>
            </tr>
            """
            return response
        
            
        books = db.session.query(Book, Author).filter(Book.author_id == Author.id).all()
        # do something with param1
        # and return to previous page or index
        self.update_redirect()
        return self.render_template('timesheet.html', books=books)
    
    @expose('/modifier/<int:id>', methods=["DELETE","GET","PUT"]) 
    @has_access 
    def modifier(self,id):
        if request.method == "DELETE":
            book = db.session.query(Book).get(id)
            db.session.delete(book)
            db.session.commit()

            return ""
        elif request.method == "GET":
            book = db.session.query(Book).get(id)
            author = book.author

            response = f"""
        <tr hx-trigger='cancel' class='editing' hx-get="/timesheet/getrow/{id}">
    <td><input name="title" value="{book.title}"/></td>
    <td>{author.name}</td>
    <td>
        <button class="btn btn-primary" hx-get="/timesheet/getrow/{id}">
        Cancel
        </button>
        <button class="btn btn-primary" hx-put="/timesheet/modifier/{id}" hx-include="closest tr">
        Save
        </button>
    </td>
        </tr>
        """
            return response
        
        elif request.method == "PUT":
            db.session.query(Book).filter(Book.id == id).update({"title": request.form["title"]})
            db.session.commit()

            title = request.form["title"]
            book = db.session.query(Book).get(id)
            author = book.author

            response = f"""
            <tr>
                <td>{title}</td>
                <td>{author.name}</td>
                <td>
                    <button class="btn btn-primary"
                        hx-get="/timesheet/modifier/{id}">
                        Edit Title
                    </button>
                </td>
                <td>
                    <button hx-delete="/timesheet/modifier/{id}"
                        class="btn btn-primary">
                        Delete
                    </button>
                </td>
            </tr>
            """
            return response
            
            
        book = db.session.query(Book).get(id)
        author = book.author

        response = f"""
        <tr hx-trigger='cancel' class='editing' hx-get="/timesheet/getrow/{id}">
    <td><input name="title" value="{book.title}"/></td>
    <td>{author.name}</td>
    <td>
        <button class="btn btn-primary" hx-get="/timesheet/getrow/{id}">
        Cancel
        </button>
        <button class="btn btn-primary" hx-put="/timesheet/modifier/{id}" hx-include="closest tr">
        Save
        </button>
    </td>
        </tr>
        """
        return response
    
    @expose('/getrow/<int:id>') 
    @has_access
    def getrow(self,id):
        book = db.session.query(Book).get(id)
        author = book.author

        response = f"""
        <tr>
            <td>{book.title}</td>
            <td>{author.name}</td>
            <td>
                <button class="btn btn-primary"
                    hx-get="/timesheet/modifier/{id}">
                    Edit Title
                </button>
            </td>
            <td>
                <button hx-delete="/timesheet/modifier/{id}"
                    class="btn btn-primary">
                    Delete
                </button>
            </td>
        </tr>
        """
        return response
        
class Ts(BaseView):
    default_view = 'main'

    @expose('/main/', methods=["GET","POST"])
    @has_access
    def main(self):
        projects = db.session.query(Project).all()
    
        self.update_redirect()
        return self.render_template('ts3.html', projects=projects)

    @expose('/projecttask/<int:id>', methods=["GET","POST"])
    @has_access
    def ts_active(self, id):
        # automatic leave - set end last task
        last_task = db.session.query(Task).filter(
            Task.created_by_fk == g.user.id,
            Task.start != None
        ).order_by(Task.created_on.desc()).first()
        
        if last_task and last_task.end is None:
            last_task.end = datetime.datetime.now()
            last_task.duration = (last_task.end - last_task.start).total_seconds()
            last_task = timesheet_update(last_task)
        db.session.commit()
        
        # internal project task 
        
        projects = db.session.query(Project).all()
    
        self.update_redirect()
        return self.render_template('ts_active.html', projects=projects, projecttask_id=id)

    @expose('deliverable/pending/', methods=["GET","POST"])
    @has_access
    def pending_deliverables(self):
        name = request.form['name']
        projecttask_id = request.form['projecttask_id']
        deliverables = db.session.query(Deliverable).filter(Deliverable.name.like('%'+name+'%'),
                                                      Deliverable.completed == False,
                                                      Deliverable.projecttask_id == projecttask_id).all()
        self.update_redirect()
        return self.render_template('pending_deliverables.html', deliverables=deliverables)
        
    @expose('deliverable/new/', methods=["GET","POST"])
    @has_access
    def new_deliverable(self):
        name = request.form['name']
        projecttask_id = request.form['projecttask_id']
        # look for the deliverbale and incompleted tasks
        deliverable = db.session.query(Deliverable).filter(
            Deliverable.name == name,
            Deliverable.projecttask_id == projecttask_id).order_by(Deliverable.created_on.desc()).first()
        
        if deliverable and deliverable.completed:
            deliverables = db.session.query(Deliverable).filter(
            Deliverable.name == name,
            Deliverable.projecttask_id == projecttask_id).all()
            self.update_redirect()
            return self.render_template('new_deliverable.html',
                                        new_deliverable = deliverable, 
                                        deliverables = deliverables,
                                        task_active = 0)
            
        # if the deliverable exist create a nue rev
        if deliverable:
            new_deliverable = Deliverable(name = deliverable.name,
                                          projecttask = deliverable.projecttask,
                                          duration = deliverable.duration,
                                          revision = deliverable.revision +1,
                                          
                                          )
            for task in deliverable.Tasks:
                if task.completed == False:
                    new_task = Task(name=task.name, 
                                    description=task.description,
                                    completed = task.completed,
                                    deliverable_id= new_deliverable.id)
                    #new_task.Comments = task.Comments
                    db.session.add(new_task)
            db.session.add(new_deliverable)
            
                    
            db.session.commit()
            # else create a new deliverable with predefined task
        else:
            new_deliverable = Deliverable(name = name, projecttask_id=projecttask_id)
            db.session.add(new_deliverable)
            db.session.commit()
            projecttask = db.session.query(Projecttask).get(projecttask_id)
            
            for task in projecttask.Tasks:
                new_task = Task(name=task.name, 
                                description=task.description,
                                deliverable_id= new_deliverable.id)
                db.session.add(new_task)
                
            db.session.commit()
        
        # ** ordinare i task
        task_list = db.session.query(Task).filter(
            Task.deliverable_id == new_deliverable.id).all()
        task_active = 0
        for task in task_list:
            print(task.completed)
            if task.completed == False:
                task_active = task.id
                task.start = datetime.datetime.now()
                db.session.commit()
                break
        
        # complete list with tasks for all the revisions
        
        deliverables = db.session.query(Deliverable).filter(
            Deliverable.name == name,
            Deliverable.projecttask_id == projecttask_id).all()
        self.update_redirect()
        print('********** ***** Deliverable len', len(deliverables))
        return self.render_template('new_deliverable.html', 
                                    deliverables=deliverables,
                                    new_deliverable=new_deliverable,
                                    task_active=task_active) 
        

    @expose('task/update/', methods=["GET","POST"])
    @has_access
    def task_update(self):
        deliverable_id = request.form['deliverable_id']
        task_id = request.form['id']
        deliverable = db.session.query(Deliverable).get(deliverable_id)
        task = db.session.query(Task).get(task_id)
        task.completed = True
        task.end = datetime.datetime.now()
        task.duration = (task.end - task.start).total_seconds()
        task = timesheet_update(task)
        db.session.commit()
        task_list = db.session.query(Task).filter(
            Task.deliverable_id == deliverable_id).order_by(Task.id.asc()).all()
        task_active = 0
        for task in task_list:
            if task.completed == False:
                task_active = task.id
                task.start = datetime.datetime.now()
                db.session.commit()
                
                break
        if task_active == 0:
            deliverable.completed = True
            db.session.commit()
            
        self.update_redirect()
        return self.render_template('new_deliverable.html', 
                                    deliverable=deliverable,
                                    task_active=task_active)
    
    @expose('task/completed/<int:id>', methods=["GET","POST"])
    @has_access
    def task_completed(self,id):
        
        task = db.session.query(Task).get(id)
        
        task.completed = True
        task.end = datetime.datetime.now()
        task.duration = (task.end - task.start).total_seconds()
        task = timesheet_update(task)
        db.session.commit()
        task_list = db.session.query(Task).filter(
            Task.deliverable_id == task.deliverable_id).all()
        task_active = 0
        for task in task_list:
            if task.completed == False:
                task_active = task.id
                task.start = datetime.datetime.now()
                db.session.commit()         
                break
         
        deliverables = db.session.query(Deliverable).filter(
                Deliverable.name == task.deliverable.name,
                Deliverable.projecttask_id == task.deliverable.projecttask_id
            ).all()
           
        if task_active == 0:
            # task.deliverable.completed = True
            # coplete all the revisions for this deliverable | no pending anymore
            for deliverble in deliverables:
                deliverble.completed = True
            db.session.commit()
        
        
        self.update_redirect()
        return self.render_template('new_deliverable.html',
                                    deliverables = deliverables, 
                                    new_deliverable=task.deliverable,
                                    task_active=task_active)

    @expose('/task/new/comment/<int:id>', methods=["GET","POST"])
    @has_access
    def task_new_comment(self, id):
        text = request.form['text']
        new_comment = Comments(task_id = id, text = text)
        db.session.add(new_comment)
        db.session.commit()
        #task_comments = db.session.query(Comments).filter(Comments.task_id == id).all()
    
        self.update_redirect()
        return self.render_template('task_new_comment.html', comment=new_comment)
    
    @expose('/task/list/comment/', methods=["GET","POST"])
    @has_access
    def task_comment(self, id):
        text = request.form['text']
        new_comment = Comments(task_id = id, text = text)
        db.session.add(new_comment)
        db.session.commit()
        task_comments = db.session.query(Comments).filter(Comments.task_id == id).all()
    
        self.update_redirect()
        return self.render_template('task_comments.html', task_comments=task_comments)
    
    @expose('projecttask/pause/', methods=["GET","POST"])
    @has_access
    def new_pause(self):
        
        # automatic leave - set end last task
        last_task = db.session.query(Task).filter(
            Task.created_by_fk == g.user.id,
            Task.start != None
        ).order_by(Task.created_on.desc()).first()
        
        if last_task and last_task.end is None:
            last_task.end = datetime.datetime.now()
            last_task.duration = (last_task.end - last_task.start).total_seconds()
            last_task = timesheet_update(last_task)
        db.session.commit()
        
        # pause    
        p_task = Task(
            start = datetime.datetime.now(),
            name = 'Pause')
        
        db.session.add(p_task)
        db.session.commit()
        
        self.update_redirect()
        return self.render_template('pause.html')


def projecttask_leave():
    # automatic leave - set end last task
    print('******************* automatic leave - set end last task *****************')
    last_task = db.session.query(Task).filter(
        Task.created_by_fk == g.user.id,
        Task.start != None
    ).order_by(Task.start.desc()).first()
    print(last_task.name, last_task.deliverable, last_task.id, last_task.end)
     
    if last_task and last_task.end is None:
        print('Last Task:', last_task.id)
        last_task.end = datetime.datetime.now()
        last_task.duration = (last_task.end - last_task.start).total_seconds()
        last_task = timesheet_update(last_task)
        print('')
        print('////////////// LAST TASK ////////////////////////////')
        print('Last Task', last_task.name, last_task.deliverable,'duration:', last_task.duration,'completed:', last_task.completed,'timesheet', last_task.timesheet_id)
        print('')
    
    
    print('')
    print('//////    END LAST TASK ///////////////')
    print('')
    db.session.commit()

class Isa(BaseView):
    default_view = 'ts' 

    @expose('/ts/')
    @has_access
    def ts(self): 
        user = get_user()
        projects = db.session.query(Project).all()
        days_back = 7
        last_timesheets = db.session.query(Timesheet).filter(
            Timesheet.created_by_fk == user.id
        ).order_by(Timesheet.date.desc()).limit(days_back).all()
        
        date_list = [x.date.strftime('%A %d %B, %Y') for x in last_timesheets]
        working_time = [int(Ts.seconds())/3600 for Ts in last_timesheets]
        work_hours = [8-x for x in working_time]
        
        self.update_redirect()
        return self.render_template('isa/base.html', projects=projects,
                                    labels = date_list,
                                    value1_data = working_time,
                                    value2_data  = work_hours)
    
    
    @expose('/projecttask/<int:id>', methods=['GET'])
    @has_access
    def projecttask(self,id):
        projecttask_leave()
        projects = db.session.query(Project).all()
        
        self.update_redirect()
        return self.render_template('isa/projecttask.html',
                                    id=id,
                                    projects=projects)

    @expose('/projecttask/timesheet/<int:prjtask_id>', methods=["GET","POST"])
    @has_access
    def projecttask_timesheet(self, prjtask_id):
        # spostare tutto in projecttask?
        timesheet = db.session.query(Timesheet).filter(Timesheet.date == datetime.datetime.now().strftime('%Y-%m-%d'),
                                              Timesheet.created_by == g.user
                                              ).first()
        if timesheet:
            
            tasks = db.session.query(Task).join(Deliverable).filter(
                Task.timesheet_id == timesheet.id,
                Deliverable.projecttask_id == prjtask_id
                
            ).all()
            
            
            if tasks:
                
                tot_seconds = sum(task.duration for task in tasks)
                seconds = datetime.timedelta(seconds=tot_seconds).seconds
                time = str(datetime.timedelta(seconds=seconds))
                return time + ' (' + str(len(tasks)) + ')'
            
        return 'ND'
    
    
    @expose('search/form/<int:prjtask_id>', methods=["GET","POST"])
    @has_access
    def search_form(self, prjtask_id):
        
            
        projecttask = db.session.query(Projecttask).get(prjtask_id)
        self.update_redirect()
        return self.render_template('isa/search_form.html', projecttask=projecttask)
    
    
    @expose('search/pending/', methods=["GET","POST"])
    @has_access
    def search_pending(self):
        print(request.view_args)
        name = request.form['name']
        projecttask_id = request.form['projecttask_id']
        # tasks1 = db.session.query(Task).filter(Task.created_by_fk == 1).paginate(page=2, per_page=5)
        deliverables = db.session.query(Deliverable).filter(Deliverable.name.like('%'+name+'%'),
                                                    Deliverable.completed == False,
                                                    Deliverable.projecttask_id == projecttask_id).order_by(
                                                    Deliverable.created_on.desc()).all()
        self.update_redirect()
        return self.render_template('isa/pending.html', 
                                    deliverables=deliverables,
                                    search_deliverable = name)
    
    # PENDING PAGINATION
    @expose('search/pending2/<int:page>', methods=["GET","POST"])
    @has_access
    def search_pending(self,page):
        print(request.view_args)
        name = request.form['name']
        page = page
        projecttask_id = request.form['projecttask_id']
        # tasks1 = db.session.query(Task).filter(Task.created_by_fk == 1).paginate(page=2, per_page=5)
        d_page = db.session.query(Deliverable).filter(Deliverable.name.like('%'+name+'%'),
                                                    Deliverable.completed == False,
                                                    Deliverable.projecttask_id == projecttask_id).order_by(
                                                    Deliverable.created_on.desc()).paginate(page, per_page=10)
        self.update_redirect()
        return self.render_template('isa/pending2.html', 
                                    d_page=d_page,
                                    search_deliverable = name,
                                    projecttask_id=projecttask_id
                                    )

    @expose('deliverable/new/', methods=["GET","POST"])
    @has_access
    def new_deliverable(self): 
        projecttask_leave() 
        name = request.form['name']
        
        projecttask_id = request.form['projecttask_id']
        
        # cerca l'ultima rev per il deliverable
        deliverable = db.session.query(Deliverable).filter(
            Deliverable.name == name,
            Deliverable.projecttask_id == projecttask_id
            ).order_by(Deliverable.revision.desc()).first()
        
        # se il deliverable è completed
        if deliverable and deliverable.completed:
            return self.render_template('isa/deliverable2.html', 
                                        deliverable = deliverable)
        
        # se il deliverable non è completed crea una nuova revisione
        elif deliverable and deliverable.completed == False:
            new_deliverable = Deliverable(
                name = name,
                projecttask_id = projecttask_id,
                revision = deliverable.revision +1
                )
            db.session.add(new_deliverable)
            db.session.flush()
            
            tasks = db.session.query(Task).filter(
            Task.deliverable_id == deliverable.id).all()
        
            for task in tasks:
                new_task = Task(
                    deliverable_id = new_deliverable.id,
                    description = task.description,
                    name = task.name,
                    input_required = task.input_required,
                    completed = task.completed
                )
                db.session.add(new_task)
        # altrimenti crea un nuovo deliverable    
        else:
            
            new_deliverable = Deliverable(
                name = name,
                projecttask_id = projecttask_id                
            )
            db.session.add(new_deliverable)
            db.session.flush()
            tasks = db.session.query(Task).filter(
            Task.projecttask_id == projecttask_id).all()

            for task in tasks:
                new_task = Task(
                    deliverable_id = new_deliverable.id,
                    description = task.description,
                    name = task.name,
                    input_required = task.input_required
                )
                db.session.add(new_task)
        
        
        db.session.commit()
        
        # Task Active
        task_list = db.session.query(Task).filter(
            Task.deliverable_id == new_deliverable.id).all()
        
        task_active = 0
        for task in task_list:
            
            if task.completed == False:
                task_active = task.id
                task.start = datetime.datetime.now()
                
                db.session.commit()
                break
        
        return self.render_template('isa/deliverable2.html', 
                                    deliverable = new_deliverable,
                                    task_active = task_active,
                                    task_list=task_list)
            
     # pending se no input required   
         
    @expose('task/completed/<int:id>', methods=["GET","POST"])
    @has_access
    def task_completed(self,id):
        session = db.session
        task = session.query(Task).get(id)
        deliverable = session.query(Deliverable).get(task.deliverable.id)
        print('')
        print(task.name, task.deliverable ,task.deliverable.id ,'*-----*  ----++++-++-+-+ HERE ****************')
        print(len(deliverable.name.splitlines()))
        print('=', task.input_required)
        print('=')
        
        
        
        
        
        #batch di deliverable
        
        if len(deliverable.name.splitlines()) > 1:
            print('*----*--**-**- TASK BATCH *-*---////////////////')
            # definisci la durata di ogni task
            task.end = datetime.datetime.now()
            task.duration = (task.end - task.start).total_seconds()
            task_time_media = task.duration / len(deliverable.name.splitlines())
            print('*----*--**-**- TASK Input *-*---////////////////', 'INPUT:', task.input_required, 'END')
            # task semplice - crea deliverable e task per ogni deliverable nel batch
            if task.input_required == '':
                # per ogni deliverable nel batch
                print('*----*--**-**- TASK NO INPUT REQUIRED *-*---////////////////')
                deliverables = deliverable.name.splitlines()
                for deliv in deliverables:
                    new_deliverable = session.query(Deliverable).filter(
                        deliverable.name == deliv
                    ).order_by(Deliverable.created_on.desc()).first()
                    
                    if not new_deliverable:
                        new_deliverable = Deliverable(
                            name = deliv,
                            projecttask_id = deliverable.projecttask_id                
                        )
                        session.add(new_deliverable)
                        session.commit()
                    
                    new_task = Task(
                        deliverable_id = new_deliverable.id,
                        description = task.description,
                        name = task.name,
                        start = task.start,
                        input_required = task.input_required,
                        completed = True,
                        end = task.end,
                        duration = task_time_media
                    )
                    session.add(new_task)
                    session.flush()
                    new_task = timesheet_update(new_task)
                    session.commit()
                
            else:
                # task input required: crea un task per ogni input    
                for k,v in request.form.items():
                    new_deliverable = session.query(Deliverable).filter(
                        deliverable.name == k
                    ).order_by(Deliverable.created_on.desc()).first()
                    
                    if not new_deliverable:
                        new_deliverable = Deliverable(
                            name = k.split('_')[2],
                            projecttask_id = deliverable.projecttask_id                
                        )
                        session.add(new_deliverable)
                        session.commit()
                    
                    new_task = Task(
                        deliverable_id = new_deliverable.id,
                        description = task.description,
                        name = task.name,
                        start = task.start,
                        input_required = v,
                        completed = True,
                        end = task.end,
                        duration = task_time_media
                    )
                    session.add(new_task)
                    session.flush()
                    new_task = timesheet_update(new_task)
                    session.commit()
            
            task_comments = session.query(Comments).filter(
                Comments.task_id == task.id,
            ).all()
            for comment in task_comments:
                comment.task_id = new_task.id
                
            session.delete(task)    
            session.commit()
            
            
                 
        # unico deliverable
        elif task.input_required and len(deliverable.name.splitlines()) == 1:
            print('*-----* 2  ----++++-++-+-+ HERE ****************')
            input_required = request.form['input_required_'+ deliverable.name]
            task.input_required = input_required
            task.completed = True
            task.end = datetime.datetime.now()
            task.duration = (task.end - task.start).total_seconds()
            task = timesheet_update(task)
        else:
                
            task.completed = True
            task.end = datetime.datetime.now()
            task.duration = (task.end - task.start).total_seconds()
            task = timesheet_update(task)
        
        session.commit()
        
        # Next Task Active
        task_list = session.query(Task).filter(
            Task.deliverable_id == deliverable.id).all()
        
        task_active = 0
        for task in task_list:
            if task.completed == False:
                task_active = task.id
                task.start = datetime.datetime.now()
                session.commit()         
                break
        
        if task_active == 0:
            if len(deliverable.name.splitlines()) >1 :
                # complete all the revisions for all the deliverables | no pending anymore
                for k,v in request.form.items():
                    deliverables = session.query(Deliverable).filter(
                        Deliverable.name == k,
                        Deliverable.projecttask_id == task.deliverable.projecttask_id    
                                                ).all()
                    for deliv in deliverables:
                        deliv.completed = True
                 
                # delete master deliverable and tasks
                '''
                task_to_del = session.query(Task).join(Deliverable).filter(Deliverable.name == deliverable.name).all()
                for x in task_to_del:
                    session.query(Task).filter(Task.id == x.id).delete()
                session.commit()
                '''
                session.query(Deliverable).filter(Deliverable.name == deliverable.name).delete()
                print('*---+++++++++++ Deliverable:', deliverable, deliverable.id, 'DELETED' )
                session.commit()
                return '<h1> Batch Completed </h1>'
                    
            # complete all the revisions for this deliverable | no pending anymore
            else:
                deliverables = session.query(Deliverable).filter(
                Deliverable.name == task.deliverable.name,
                Deliverable.projecttask_id == task.deliverable.projecttask_id    
                                                ).all()
                for deliverble in deliverables:
                    deliverble.completed = True
                
                
                
            
        session.commit()
        
        
        self.update_redirect()
        return self.render_template('isa/deliverable2.html',
                                    #deliverables = deliverables,
                                    #comments = comments, 
                                    deliverable = task.deliverable,
                                    task_active = task_active)
        
    @expose('/comments/<int:id>', methods=["GET","POST"])
    @has_access
    def comments(self, id):
        task = db.session.query(Task).get(id)
        
        if request.method == 'POST':
            text = request.form['text']
            new_comment = Comments(task_id = id, text = text)
            db.session.add(new_comment)
            db.session.commit()
            
        comments = db.session.query(Comments).join(Task, Deliverable).filter(
            Deliverable.name == task.deliverable.name,
            Deliverable.projecttask_id == task.deliverable.projecttask_id
        ).order_by(Comments.created_on.desc()).all()
        return self.render_template('isa/comments.html', 
                                    comments=comments,
                                    task=task)
    @expose('/workingtime/')
    @has_access
    def workingtime(self):
        timesheet = db.session.query(Timesheet).filter(
            Timesheet.created_by == g.user,
            Timesheet.date == datetime.datetime.now().strftime('%Y-%m-%d')  
        ).first()
        if timesheet:
            return '<i class="fa fa-clock-o fs-4" aria-hidden="true"></i>' + timesheet.time()
        return '0:00:00'
    
    
    @expose('/working_quotes/')
    def working_quotes(self):
        filename = 'app/static/csv/work_quotes/work_quotes.csv'
        with open(filename) as f:
            reader = csv.reader(f)
            chosen_row = random.choice(list(reader))[0]
            #quote = chosen_row.encode('raw_unicode_escape','unicode-escape')
            return u"{}".format(chosen_row)
    
    


  



class TaskPredefinedView(ModelView): 
    datamodel = SQLAInterface(Task) 
    list_columns = ['name','description','projecttask', 'input_required']
    add_columns = ['name','description','projecttask', 'input_required']
    show_columns = ['name','description','projecttask', 'input_required','created_by','created_on','changed_by','changed_on']
    edit_columns = ['name','description','projecttask','input_required']
    base_filters = [['deliverable', FilterRelationOneToManyEqual, 'None']]
    
    list_title = 'CheckList Task | List'
    add_title = 'CheckList Task | Add'
    edit_title = 'CheckList Task | Edit'
    show_title = 'CheckList Task | Sow'
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())
       

class ProjectTaskView(ModelView):
    datamodel = SQLAInterface(Projecttask) 
    list_columns = ['name', 'order', 'users']
    show_columns = ['name', 'order','description', 'est_seconds','hour_rate','billable', 'users','created_by','created_on','changed_by','changed_on']
    add_columns = ['name', 'order','description', 'est_seconds','hour_rate','billable', 'users']
    edit_columns = ['name', 'order','description', 'est_seconds','hour_rate','billable', 'users']
    
    related_views = [TaskPredefinedView]  
    
    list_title = 'Project Task | List'
    add_title = 'Project Task | Add'
    edit_title = 'Project Task | Edit'
    show_title = 'Project Task | Sow'
    
    show_template = 'appbuilder/general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())
    
    @action("assign_to_all","Assign to all Users","Do you really want to assign this Project Task to All Users?","fa-rocket", single=False   )
    def assign_to_all(self, items):
        users = db.session.query(Myuser).all()
        if users:
            for item in items:
                item.users = users
                
            db.session.commit()
        
        self.update_redirect()
        return redirect(self.get_redirect())



class DeliverableView(ModelView):
    datamodel = SQLAInterface(Deliverable) 
    list_columns = ['name', 'revision', 'projecttask','duration' ,'completed']
    add_columns = ['name', 'revision', 'projecttask', 'duration', 'completed', 'billed']
    edit_columns = ['name', 'revision', 'projecttask', 'duration', 'completed', 'billed']
    show_columns = ['name', 'revision', 'projecttask', 'duration', 'completed', 'billed','created_by','created_on','changed_by','changed_on']
    
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())
    
    @action("load_deliverables","Load All Deliverables","Do you really want to Load all the deliverables from approved Timesheets to this SAL?","fa-rocket", single=False   )
    def load_deliverables(self, items):
        for item in items:
            deliverables = db.session.query(Deliverable).join(Projecttask, Project).filter(
                Project.id == item.order_revision.order.project.id,
                Deliverable.completed == True,
                Deliverable.billed == False,
                Deliverable.created_on.between(item.start, item.end)).all()
            
            if deliverables:
                for deliverable in deliverables:
                    #item.seconds += deliverable.duration
                    deliverable.project_status_id = item.id
                    deliverable.billed == True
            
        db.session.commit()
        return redirect(self.get_redirect()) 

class InvoiceView(ModelView):
    datamodel = SQLAInterface(Invoice) 
    list_columns = ['id','amount','approved_on','billed','paid']
    add_columns = ['amount','approved_on','billed','paid','note']
    edit_columns = ['amount','approved_on','billed','paid','note']
    show_columns = ['amount','approved_on','billed','paid','note','created_by','created_on','changed_by','changed_on']
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect()) 

from .helpers import to_csv
class ProjectStatusView(ModelView):
    datamodel = SQLAInterface(Project_status)  
    list_columns = ['id', 'order_revision', 'task_time','est_time','amount', 'approved', 'approved_on','deliverables_count', 'changed_on']
    add_columns = ['order_revision', 'start','end', 'approved', 'approved_on']
    edit_columns = ['order_revision', 'start','end', 'approved', 'approved_on']
    show_columns = ['order_revision', 'start','end','task_time', 'approved', 'approved_on','created_by','created_on','changed_by','changed_on']
    
    related_views = [DeliverableView, InvoiceView]
    
    show_template = 'appbuilder/general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())
    
    @action(name="downlad_sal", text= "Download CSV", icon= "fa-rocket", multiple=False)
    def download_sal(self, items):
        self.update_redirect()
        csv_file = to_csv()
        #return send_file('./static/downloads/output.csv', as_attachment=True, download_name='sal.csv')
        return csv_file
 
class OrderRevisionView(ModelView):
    datamodel = SQLAInterface(Order_revision) 
    list_columns = ['id', 'order','revision','hours', 'amount', 'due_date']
    add_columns = [ 'order','revision','hours', 'amount', 'due_date']
    edit_columns = [ 'order','revision','hours', 'amount', 'due_date']
    show_columns = [ 'order','revision','hours', 'amount', 'due_date','created_by','created_on','changed_by','changed_on']
    
    related_views = [ProjectStatusView]
    show_template = 'appbuilder/general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'
    
    list_title = 'Order Revision | List'
    add_title = 'Order Revision | Add'
    edit_title = 'Order Revision | Edit'
    show_title = 'Order Revision | Sow'
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())  
  
class OrderView(ModelView):
    datamodel = SQLAInterface(Order) 
    list_columns = ['name', 'project']
    add_columns = ['name', 'project', 'payment_days', 'pending_deliverable']
    edit_columns = ['name', 'project', 'payment_days', 'pending_deliverable']
    show_columns = ['name', 'project', 'payment_days', 'pending_deliverable','amount','total_hours','created_by','created_on','changed_by','changed_on'] 
    
    related_views = [OrderRevisionView, ProjectTaskView]
    
    show_template = 'appbuilder/general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'
    
    label_columns = {
        'amount': 'Total amount',
        'total_hours': 'Total hours'  
    }
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect()) 

class ProjectView(ModelView):
    datamodel = SQLAInterface(Project) 
    list_columns = ['name', 'account']
    add_columns = ['name', 'account']
    show_columns = ['name', 'account','created_by','created_on','changed_by','changed_on']
    edit_columns = ['name', 'account']
    
    related_views = [OrderView]
    
    show_template = 'appbuilder/general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())

class AccountView(ModelView):
    datamodel = SQLAInterface(Account) 
    list_columns = ['name','Projects']
    add_columns = ['name']
    edit_columns = ['name']
    show_columns = ['name','created_by','created_on','changed_by','changed_on']
    
    related_views = [ProjectView]
    
    show_template = 'appbuilder/general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'
    
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect()) 


def today():
    return datetime.datetime.today().strftime('%Y-%m-%d')

class TaskView(ModelView):
    datamodel = SQLAInterface(Task) 
    list_columns = ['deliverable.projecttask.order.project','deliverable.projecttask','name', 'deliverable', 'time','input_required', 'completed']
    add_columns = ['name', 'deliverable', 'timesheet', 'projecttask', 'duration', 'completed']
    base_filters = [['projecttask', FilterRelationOneToManyEqual, 'None']]
    
    label_columns = {
        'deliverable.projecttask.order.project': 'Project',
        'deliverable.projecttask': 'Task',
        'completed':'Status', 
        'name': 'Step'
         
        
    }
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False) 
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())
    


class TimesheetView(ModelView):
    datamodel = SQLAInterface(Timesheet)
    base_order = ('date','desc')
    list_columns = ['date_cs','time','created_by', 'approved']
    add_columns = ['date', 'approved']
    show_columns = ['id','date_cs','time','created_by', 'approved'] 
    related_views = [TaskView]  
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())
    
    @action("approved_to_sal","Approve to SAL","Do you really want to approve this Timesheets to SAL?","fa-rocket", single=False   )
    def approved_to_sal(self, items):
        for item in items:
            item.approved = True
            
        db.session.commit()
        
        self.update_redirect()
        return redirect(self.get_redirect())
    
class CommentsView(ModelView):
    datamodel = SQLAInterface(Comments)
    list_columns = ['id', 'task', 'text']
    add_columns = ['task', 'text'] 
    
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())

class MyTaskView(ModelView):
    datamodel = SQLAInterface(Task) 
    list_columns = ['id','name', 'deliverable', 'timesheet', 'deliverable.projecttask','task_start','task_end', 'time', 'completed']
    add_columns = ['name', 'deliverable', 'timesheet', 'duration', 'completed']
    base_filters = [['projecttask', FilterRelationOneToManyEqual, 'None'],
                    ['created_by', FilterEqualFunction, get_user]]
    
class MyTimesheetView(ModelView):
    datamodel = SQLAInterface(Timesheet)
    base_order = ('date','desc')
    list_columns = ['date_cs','time','created_by', 'approved']
    show_columns = ['date', 'approved'] 
    
    base_permissions = ['can_show', 'can_list']
    base_filters = [['created_by', FilterEqualFunction, get_user]]
    
    related_views = [MyTaskView] 
    show_template = 'appbuilder/general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'
    
    
appbuilder.add_view(Isa, "ISA Timesheet", category='ISA')
#appbuilder.add_link('ISA Timesheet','/isa/main', category='ISA') 
appbuilder.add_view(ProjectView, "Projects", category='Management') 
appbuilder.add_view_no_menu(ProjectTaskView) 
#appbuilder.add_view(ProjectTaskView, "Project Task", category='Management') 
appbuilder.add_view(TaskPredefinedView, "Task Predefined", category='Management')
appbuilder.add_view(TimesheetView, "Timesheet", category='Management')
appbuilder.add_view(DeliverableView, "Deliverable", category='Management') 
appbuilder.add_view(TaskView, "Task", category='Management')
appbuilder.add_view(CommentsView, "Comments", category='Management')

appbuilder.add_view(AccountView, "Account", category='Finance')
appbuilder.add_view(OrderView, "Order", category='Finance')
appbuilder.add_view(OrderRevisionView, "Order Revision", category='Finance')
appbuilder.add_view(ProjectStatusView, "SAL", category='Finance')
appbuilder.add_view(InvoiceView, "Invoice", category='Finance')

appbuilder.add_view(MyTaskView, "Task", category='User')
appbuilder.add_view(MyTimesheetView, "Timesheet", category='User')

#appbuilder.add_view(Ts, "Main", category='My View') 
#appbuilder.add_view(TimesheetOld, "Editor", category='My View')    
#appbuilder.add_link("Submit", href='/timesheet/editor/submit', category='My View')

"""
    Create your Model based REST API::

    class MyModelApi(ModelRestApi):
        datamodel = SQLAInterface(MyModel)

    appbuilder.add_api(MyModelApi)


    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(
        MyModelView,
        "My View",
        icon="fa-folder-open-o",
        category="My Category",
        category_icon='fa-envelope'
    )
"""

"""
    Application wide 404 error handler
"""


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


db.create_all()
from .helpers import init_task, to_csv, gen_task, repair_task
#init_task() 
#to_csv()
#gen_task()
#repair_task() 