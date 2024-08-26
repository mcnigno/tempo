from . import db
from .models import Account, Project, Order, Order_revision, Projecttask, Task
from sqlalchemy import func, select

def init_task():
    account = Account(name = 'Technip', created_by_fk = 1, changed_by_fk = 1)
    borouge = Project(name = 'Borouge', account = account, created_by_fk = 1, changed_by_fk = 1)
    rotterdam = Project(name = 'Rotterdam', account = account, created_by_fk = 1, changed_by_fk = 1)
    prjt1 = Projecttask(name = 'Vendor Incoming ', project = borouge, created_by_fk = 1, changed_by_fk = 1)
    prjt2 = Projecttask(name = 'Vendor Outgoing ', project = borouge, created_by_fk = 1, changed_by_fk = 1)
    prjt3 = Projecttask(name = 'Comments ', project = borouge, created_by_fk = 1, changed_by_fk = 1)
    prjt4 = Projecttask(name = 'Comments ', project = rotterdam, created_by_fk = 1, changed_by_fk = 1)
    
    def_prjt1 = Task(name= '01 Predefined Task for this Project Task', projecttask= prjt1, created_by_fk = 1, changed_by_fk = 1)
    def_prjt2 = Task(name= '02 Predefined Task for this Project Task', projecttask= prjt1, created_by_fk = 1, changed_by_fk = 1)
    db.session.add(def_prjt1)
    db.session.add(def_prjt2)
    db.session.add(prjt3)
    db.session.add(prjt4)
    
    
    db.session.commit()

import os
from flask import send_file, url_for
import datetime
from datetime import timedelta
def repair_task():
    tasks = db.session.query(Task).all()
    for task in tasks:
        task.changed_by_fk = '1' 
        task.duration = 150
        task.start = datetime.datetime.now()
        task.end = datetime.datetime.now()
    db.session.commit()

def gen_task():
    for n in range(10000):
        print('Task',n)
        tsk = Task(name= 'Test Task ' + str(n), 
                   created_by_fk = 1, 
                   changed_by_fk = 1,
                   start = datetime.datetime.now(),
                   end = datetime.datetime.now(),
                   duration = 150)
        
        db.session.add(tsk)
    db.session.commit()
def to_csv():
        
    # MySQL connection information
    mysql_host = 'your_host'
    mysql_user = 'root'
    mysql_password = 'lollipop300777'
    mysql_database = 'isa'

    # Define your SQL query
    sql_query = "SELECT * FROM Task"
    
    '''
    # query for sal
    
    * aggiungere lo user del commento e gli user che hanno lavorato i task
    * prevedere la possibilità di avere questo formato per user
    * fare il trim del nome del deliverable
    * considerare inclusione pending
    *  
    
    select isa.projecttask.name as activity, isa.deliverable.name as deliverable, sum(isa.task.duration) as duration, group_concat(isa.comments.text) as note
    from isa.task

    join isa.deliverable on isa.task.deliverable_id = isa.deliverable.id
    join isa.projecttask on isa.deliverable.projecttask_id = isa.projecttask.id
    left join isa.comments on isa.task.id = isa.comments.task_id

    WHERE startDate BETWEEN '2013-03-12 00:00:00' AND '2013-03-12 23:59:59'
    AND endDate BETWEEN '2013-03-12 00:00:00' AND '2013-03-12 23:59:59'
  
    group by isa.projecttask.name, isa.deliverable.name
    '''

    # Define the output CSV file path
    output_csv_file = 'app/static/downloads/output.csv' 

    # Use the mysqldump command to execute the query and save the result as a CSV file
    #command = f"mysql -h {mysql_host} -u {mysql_user} -p{mysql_password} {mysql_database} -e \"{sql_query}\" > {output_csv_file}"
    command = f"mysql -u {mysql_user} -p{mysql_password} {mysql_database} -e \"{sql_query}\" > {output_csv_file}"
    
    # Execute the command
    os.system(command)

    print(f"Query result has been saved to {output_csv_file}")
    return send_file('./static/downloads/output.csv', as_attachment=True, download_name='sal.csv')


