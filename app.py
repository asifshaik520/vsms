from flask import Flask,flash,redirect,render_template,url_for,request,jsonify,session,abort
from flask_session import Session  
import mysql.connector
from flask_mysqldb import MySQL
from datetime import date
from datetime import datetime
from sdmail import sendmail
from tokenreset import token
from itsdangerous import URLSafeTimedSerializer
from key import *
from stoken1 import token1
app=Flask(__name__)
app.secret_key='hello'
app.config['SESSION_TYPE'] = 'filesystem'
# app.config['MYSQL_HOST'] ='localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD']='admin'
# app.config['MYSQL_DB']='vehicle_service'
# mysql=MySQL(app)
mydb=mysql.connector.connect(host="localhost",user='root',password='admin',db='vehicle_mang_sys_flask')
Session(app)
@app.route('/')
def welcome():
    return render_template('welcome.html')
#=========================================customer login and register
@app.route('/clogin',methods=['GET','POST'])
def clogin():
    if session.get('customers'):
        return redirect(url_for('customer_dashboard'))
    if request.method=='POST':
        username=request.form['id1']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from customers where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['customers']=username
            return redirect(url_for("customer_dashboard"))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')
@app.route('/homepage')
def home():
    if session.get('customers'):
        return "customer login"
    else:
        return redirect(url_for('clogin'))
@app.route('/cregistration',methods=['GET','POST'])
def cregistration():
    if request.method=='POST':
        id1=request.form['username']
        email=request.form['email']
        phnumber=request.form['phone_number']
        password=request.form['password']
        address=request.form['address']
        #ccode=request.form['ccode']
        # code="codegnan@9"
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from customers where username=%s',[id1])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from customers where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('registration.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('registration.html')
        
        data={'username':id1,'password':password,'email':email,'phone_number':phnumber,'address':address}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('aconfirm',token=token(data,salt),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('clogin'))

    return render_template('registration.html')
@app.route('/aconfirm/<token>')
def aconfirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
      
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        id1=data['username']
        cursor.execute('select count(*) from customers where username=%s',[id1])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('clogin'))
        else:
            cursor.execute('INSERT INTO customers (username, password, email, phone_number, address) VALUES (%s, %s, %s, %s, %s)',[data['username'], data['password'], data['email'], data['phone_number'], data['address']])

            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('clogin'))
@app.route('/forget',methods=['GET','POST'])
def uforgot():
    if request.method=='POST':
        id1=request.form['id1']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from customers where username=%s',[id1])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mydb.cursor(buffered=True)

            cursor.execute('SELECT email  from customers where username=%s',[id1])
            email=cursor.fetchone()[0]
            cursor.close()
            subject='Forget Password'
            confirm_link=url_for('ureset',token=token(id1,salt=salt2),_external=True)
            body=f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('clogin'))
        else:
            flash('Invalid username id')
            return render_template('forgot.html')
    return render_template('forgot.html')


@app.route('/reset/<token>',methods=['GET','POST'])
def ureset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        id1=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update  customers set password=%s where username=%s',[newpassword,id1])
                mydb.commit()
                flash('Reset Successful')
                return redirect(url_for('clogin'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
                
        return render_template('newpassword.html')

#=============================== customer service request
@app.route('/service_request',methods=['GET','POST'])
def service_request():
    if session.get('customers'):
        k=session['customers']
        #print('---------------',k)
        if request.method == 'POST':
            vehicle_category = request.form['vehicle_category']
            vehicle_number = request.form['vehicle_number']
            vehicle_model = request.form['vehicle_model']
            problem_description = request.form['problem_description']
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select customer_id from customers where username=%s',(session['customers'],))
            cust_id= cursor.fetchone()[0]
            cursor.execute('select  email from customers where username =%s',(session['customers'],))
            email = cursor.fetchone()[0]
            cursor.execute("INSERT INTO service_requests (customer_id, vehicle_category, vehicle_number, vehicle_model, problem_description, status) VALUES (%s,%s, %s, %s, %s, %s)",
                        (cust_id,vehicle_category, vehicle_number, vehicle_model, problem_description, 'Pending'))
            mydb.commit()
            cursor.close()
            subject="vehicle service request"
            body=f"{vehicle_number} of your vehicle service request has submitted successfully"
            sendmail(to=email,subject=subject,body=body)
            flash('Service request submitted successfully.')

            return redirect(url_for('customer_dashboard'))

        return render_template('customer_service_request.html')
    else:
        return redirect(url_for("clogin"))
#============================== customer dashboard
@app.route('/customer_dashboard')
def customer_dashboard():
    if session.get('customers'):
    
        return render_template('customer_dashboard.html') 
    else:
        return redirect(url_for('clogin'))
#===========customer view his requests
@app.route('/view_requests')
def view_requests():
    if session.get('customers'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select customer_id from customers where username=%s',(session['customers'],))
        customerid = cursor.fetchone()[0]
        cursor.execute("SELECT sr.request_id, c.customer_id, c.username,c.email,c.phone_number, sr.vehicle_number, sr.vehicle_model, sr.vehicle_category, sr.problem_description, sr.status, sr.cost, sr.date_requested FROM service_requests sr JOIN customers c ON sr.customer_id = c.customer_id WHERE sr.customer_id = %s",(customerid,))
        view = cursor.fetchall()
        return render_template('view_requests.html',view=view) 
    return redirect(url_for('clogin'))  
#===================================mechanic dasboard
#=======================mechani signup and applying for a job
@app.route('/mlogin',methods=['GET','POST'])
def mlogin():
    if session.get('mechanic'):
        return redirect(url_for('mechanic_dashboard'))
    if request.method=='POST':
        username=request.form['id1']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from mechanics where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['mechanic']=username
            return redirect(url_for("mechanic_dashboard"))
        else:
            flash('Invalid username or password')
            return render_template('mechanic_login.html')
    return render_template('mechanic_login.html')
@app.route('/mlogout')
def mlogout():
    if session.get('mechanic'):
        session.pop('mechanic')
        flash('Successfully loged out')
        return redirect(url_for('mlogin'))
    else:
        return redirect(url_for('mlogin'))

@app.route('/mregistration',methods=['GET','POST'])
def mregistration():
    if request.method=='POST':
        id1=request.form['username']
        email=request.form['email']
        phnumber=request.form['phone_number']
        password=request.form['password']
        address=request.form['address']
        skills=request.form['skills']
        #ccode=request.form['ccode']
        # code="codegnan@9"
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from mechanics where username=%s',[id1])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from mechanics where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('mechanic_application.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('mechanic_application.html')
        
        data1={'username':id1,'password':password,'email':email,'phone_number':phnumber,'address':address,'skills':skills}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('mconfirm',token=token1(data1,salt),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('mlogin'))

    return render_template('mechanic_application.html')
@app.route('/mconfirm/<token>')
def mconfirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
      
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        id1=data['username']
        cursor.execute('select count(*) from mechanics where username=%s',[id1])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('mlogin'))
        else:
            cursor.execute('INSERT INTO mechanics (username, password, email, phone_number, address,skills,status) VALUES (%s, %s, %s, %s, %s,%s,%s)',[data['username'], data['password'], data['email'], data['phone_number'], data['address'],data['skills'],'pending'])

            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('mlogin'))
            #return redirect(url_for('clogin'))
@app.route('/mforget',methods=['GET','POST'])
def mforgot():
    if request.method=='POST':
        id1=request.form['id1']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from mechanics where username=%s',[id1])
        count=cursor.fetchone()[0]
        cursor.close()
        print('================',count)
        if count==1:
            cursor=mydb.cursor(buffered=True)

            cursor.execute('SELECT email  from mechanics where username=%s',[id1])
            email=cursor.fetchone()[0]
            cursor.close()
            subject='Forget Password'
            confirm_link=url_for('mreset',token=token1(id1,salt=salt2),_external=True)
            body=f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('mlogin'))
        else:
            flash('Invalid username id')
            return render_template('forgot.html')
    return render_template('forgot.html')


@app.route('/mreset/<token>',methods=['GET','POST'])
def mreset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        id1=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update  mechanics set password=%s where username=%s',[newpassword,id1])
                mydb.commit()
                flash('Reset Successful')
                return redirect(url_for('mlogin'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')


#==============mechanic dashboard
@app.route('/mechanic_dashboard')
def mechanic_dashboard():
    if session.get('mechanic'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select mechanic_id from mechanics where username=%s',(session['mechanic'],))
        mechanicid = cursor.fetchone()[0]
        cursor.execute("select * from mechanics WHERE mechanic_id = %s",(mechanicid,))
        view = cursor.fetchall()
        return render_template('mechanic_dashboard.html',view=view) 
    return redirect(url_for('mlogin'))  


#======================================Admin dashboard  
   
#=================admin login 
@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        email=request.form['email']
        code = request.form['code']
        if email == "admin@codegnan.com" and  code == "admin@123":
            session['admin']="admin@123"
            return redirect(url_for('admin_dashboard'))
        else:
            flash("unauthorized access")
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('admin'):
        return render_template('admin_dashboard.html')
    else:
        return redirect(url_for('admin_login'))
@app.route('/alogout')
def alogout():
    if session.get('admin'):
        session.pop('admin')
        flash('successfully log out')
        return render_template('admin_login.html')
    else:
        return redirect(url_for('admin_login'))
#==================admin view the requested customer services pending
@app.route('/cust_pending_req',methods=['GET','POST'])
def customer_pending():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)      
        cursor.execute("SELECT sr.request_id, c.customer_id, c.username,c.email,c.phone_number, sr.vehicle_number, sr.vehicle_model, sr.vehicle_category, sr.problem_description, sr.status, sr.cost, sr.date_requested, c.date_registered FROM service_requests sr JOIN customers c ON sr.customer_id = c.customer_id WHERE sr.status = 'Pending'")
        pending_requests = cursor.fetchall()
        cursor.close()
    
        return render_template('cust_pending_req.html', requests=pending_requests)
    else:
        return redirect(url_for('admin_login'))
#============================update request
@app.route('/update_status/<int:request_id>', methods=['POST'])
def update_status(request_id):
    if session.get('admin'):
        new_status = request.form['status']
        cursor = mydb.cursor(buffered=True)
        try:
            cursor.execute("UPDATE service_requests SET status = %s WHERE request_id = %s", (new_status, request_id))
            mydb.commit()
            
            cursor.execute('SELECT customer_id, vehicle_number, date_requested FROM service_requests WHERE request_id = %s', (request_id,))
            cid = cursor.fetchone()
            if cid:
                cursor.execute('SELECT email FROM customers WHERE customer_id = %s', (cid[0],))
                email = cursor.fetchone()[0]
                subject = "Vehicle Service Request"
                body = f"The status of your vehicle service request for vehicle number {cid[1]} is {new_status}. Date requested: {cid[2]}"
                sendmail(to=email, subject=subject, body=body)
            cursor.close()
            flash('Status updated successfully.')
        except Exception as e:
            mydb.rollback()
            flash(f"An error occurred: {e}")
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

#=================== admin view accepted service requests
@app.route('/cust_accepted_req', methods=['GET', 'POST'])
def customer_accepted():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute("""
            SELECT sr.request_id, c.customer_id, c.username, c.email, c.phone_number, 
                   sr.vehicle_number, sr.vehicle_model, sr.vehicle_category, 
                   sr.problem_description, sr.status, sr.cost, sr.date_requested, 
                   c.date_registered 
            FROM service_requests sr 
            JOIN customers c ON sr.customer_id = c.customer_id 
            WHERE sr.status = 'Accept'
        """)
        accept_requests = cursor.fetchall()
        cursor.close()
        return render_template('cust_accepted_req.html', requests=accept_requests)
    return redirect(url_for('admin_login'))

#=================== admin rejected service requests
@app.route('/cust_reject_req', methods=['GET', 'POST'])
def customer_rejected():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute("""
            SELECT sr.request_id, c.customer_id, c.username, c.email, c.phone_number, 
                   sr.vehicle_number, sr.vehicle_model, sr.vehicle_category, 
                   sr.problem_description, sr.status, sr.cost, sr.date_requested, 
                   c.date_registered 
            FROM service_requests sr 
            JOIN customers c ON sr.customer_id = c.customer_id 
            WHERE sr.status = 'Reject'
        """)
        reject_requests = cursor.fetchall()
        cursor.close()
        return render_template('cust_rejected_req.html', requests=reject_requests)
    return redirect(url_for('admin_login'))

#=================== admin view completed service requests
@app.route('/cust_completed_req', methods=['GET', 'POST'])
def customer_completed():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute("""
            SELECT sr.request_id, c.customer_id, c.username, c.email, c.phone_number, 
                   sr.vehicle_number, sr.vehicle_model, sr.vehicle_category, 
                   sr.problem_description, sr.status, sr.cost, sr.date_requested, 
                   c.date_registered 
            FROM service_requests sr 
            JOIN customers c ON sr.customer_id = c.customer_id 
            WHERE sr.status = 'Completed'
        """)
        completed_requests = cursor.fetchall()
        cursor.close()
        return render_template('cust_completed_req.html', requests=completed_requests)
    return redirect(url_for('admin_login'))

#================== update cost
@app.route('/update_cost/<int:request_id>', methods=['POST'])
def update_cost(request_id):
    if session.get('admin'):
        new_cost = request.form['cost']
        cursor = mydb.cursor(buffered=True)
        
        cursor.execute("UPDATE service_requests SET cost = %s WHERE request_id = %s", (new_cost, request_id))
        mydb.commit()
        cursor.execute('select customer_id,vehicle_number,date_requested from service_requests where request_id = %s',[request_id])
        cid = cursor.fetchone()
        cursor.execute('select  email from customers where  customer_id=%s',[cid[0]])
        email = cursor.fetchone()[0]
        subject="vehicle service request"
        body=f"{cid[1]} of your vehicle service request is accepted the cost is {new_cost} - date of requested {cid[2]}"
        sendmail(to=email,subject=subject,body=body)
        cursor.close()
        flash('Cost updated successfully.')
        return redirect(url_for('view_requests'))
    
    return redirect(url_for('admin_login'))
#==================admin view the requested mechanic applications pending
@app.route('/mech_pending',methods=['GET','POST'])
def mechanic_pending():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)      
        cursor.execute("select * from mechanics where status='pending'")
        pending_requests = cursor.fetchall()
        cursor.close()
        
        return render_template('mechanic_pending.html', requests=pending_requests)
    return redirect(url_for('admin_login'))
#============================update mechanic job request
from flask import request, session, flash, redirect, url_for
# Ensure `sendmail` and `mydb` are properly imported or defined
# from your application context

@app.route('/update_job/<int:request_id>', methods=['GET', 'POST'])
def update_job(request_id):
    if session.get('admin'):
        new_status = request.form['status']
        cursor = mydb.cursor(buffered=True)
        
        try:
            # Update the status of the mechanic
            cursor.execute("UPDATE mechanics SET status = %s WHERE mechanic_id = %s", (new_status, request_id))
            mydb.commit()

            # Fetch email and username of the mechanic
            cursor.execute('SELECT email, username FROM mechanics WHERE mechanic_id = %s', (request_id,))
            email_data = cursor.fetchone()

            if email_data:
                email, username = email_data
                subject = "Vehicle Service Request"
                body = f"{username}, your job application status is {new_status}"
                sendmail(to=email, subject=subject, body=body)
                flash('Service request submitted and email sent successfully.')
            else:
                flash('Mechanic not found.')

        except Exception as e:
            flash('An error occurred while updating the job status.')
            # Optionally log the error or handle it
        finally:
            cursor.close()
        
        flash('Status updated successfully.')
        return redirect(url_for('admin_dashboard'))
    
    return redirect(url_for('admin_login'))

#=============================accepted mechanic job
@app.route('/mech_accepted',methods=['GET','POST'])
def mechanic_accepted():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)      
        cursor.execute("select * from mechanics where status='approved'")
        accept_requests = cursor.fetchall()
        cursor.close()
    
        return render_template('mechanic_accept.html', requests=accept_requests)
    return redirect(url_for('admin_login'))
#=============================== rejected mechanic job
@app.route('/mech_reject',methods=['GET','POST'])
def mechanic_rejected():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)      
        cursor.execute("select * from mechanics where status='rejected'")
        reject_requests = cursor.fetchall()
        cursor.close()
        
        return render_template('mechanic_rejected.html', requests=reject_requests)
    return redirect(url_for('admin_login'))
#customer logout
@app.route('/clogout')
def clogout():
    if session.get('customers'):
        session.pop('customers')
        flash('Successfully loged out')
        return redirect(url_for('clogin'))
    else:
        return redirect(url_for('clogin'))
#============================ contact us
@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        number = request.form['number']
        subject = request.form['subject']
        message = request.form['message']
        
        try:
            # Insert the contact message into the database
            cur = mydb.cursor(buffered=True)
            query = "INSERT INTO contact_us (name, email, number, subject, message) VALUES (%s, %s, %s, %s, %s)"
            values = (name, email, number, subject, message)
            cur.execute(query, values)
            mydb.commit()
            cur.close()
            flash('Your message has been sent successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
            mydb.rollback()
        return redirect('/contact_us')
    
    return render_template('contact_us.html')
#======================read conmtact us
@app.route('/view_contact_messages')
def view_contact_messages():
    if session.get('admin'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute("SELECT * FROM contact_us")
        messages = cursor.fetchall()
        cursor.close()
        return render_template('view_contactus_messages.html',messages=messages)
    return redirect(url_for('admin_login'))


































app.run(use_reloader=True,debug=True)

