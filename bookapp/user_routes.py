import re,random,os,requests
from functools import wraps
from flask import render_template, request, redirect, flash,make_response,session,url_for,json
from werkzeug.security import generate_password_hash,check_password_hash
 
from sqlalchemy.sql import text
from bookapp import app, csrf
from bookapp.models import db,Book,User,Reviews,Category,Donation

from bookapp.forms import SignupForm,ProfileForm


def login_required(f):
    @wraps(f)
    def login_decorator(*args,**kwargs):
        if session.get("userid") and session.get("user_loggedin"):
            return  f(*args,**kwargs)
        else:
            flash("Access Denied, Please Login")
            return redirect("/login")
    return login_decorator


@app.route("/register", methods=["POST","GET"])
def register():
    signupform = SignupForm()
    if request.method =="GET":
        return render_template("user/signup.html",signupform =signupform )
    else:
        if signupform.validate_on_submit():
            userpass=request.form.get('password')
            u=User(user_fullname=request.form.get('fullname'),
                   user_email=request.form.get("email"),
                   user_pwd=generate_password_hash(userpass))
            db.session.add(u)
            db.session.commit()
            session['userid']=u.user_id
            session['user_loggedin']=True
            return  redirect ("/dashboard")
        else:
            return render_template ("user/signup.html",signupform=signupform)
        
@app.route("/signout")
def signout():
    if session.get('userid') or session.get('user_loggedin'):
        session.pop('userid',None)
        session.pop('user_loggedin', None)
    return redirect("/")

@app.route("/login", methods=['POST','GET'])
def login():
    if request.method=="GET":
        return render_template("user/loginpage.html")
    else:
        username =request.form.get('email')
        password= request.form.get('password')
        deets =db.session.query(User).filter(User.user_email==username).first()
        if deets:
            hashedpwd =deets.user_pwd
            chk = check_password_hash(hashedpwd,password)
            if chk:
                session['user_loggedin'] = True
                session['userid'] =deets.user_id
                return redirect("/dashboard")
            else:
                flash("Invalid credentials")
                return redirect("/login")
        else:
            flash(" Invalid credentials ")
            return redirect ("/login")

@app.route("/explore", methods=['POST','GET'])
def explore():
    books=db.session.query(Book).filter(Book.book_status=='1').all()
    cats= db.session.query(Category).all()
    return render_template('user/explore.html', books=books)


@app.route('/search/book')
def search_book():
    cate = request.args.get('category')
    title = request.args.get('title')
    search_titile ="%"+title+"%"  #{%%}.format(title)
    # run query
    result = db.session.query(Book).filter(Book.book_catid ==cate).filter
    (Book.book_title.ilike(title)).all()
    
    return 'done'  #go to the explorepage





@app.route("/profile", methods=['POST',"GET"])
@login_required
def profile():
    pform = ProfileForm()
    useronline=session.get('userid')
    userdeets=db.session.query(User).get(useronline)
    if request.method =="GET":
        return render_template("user/profile.html", pform=pform, userdeets=userdeets)
    else:
        if pform.validate_on_submit():
            fullname=request.form.get('fullname')
            picture= request.files.get("pix")
            filename=pform.pix.data.filename
            picture.save("bookapp/static/images/profile"+filename)
            userdeets.user_fullname=fullname
            userdeets.user_pix=filename
            db.session.commit()
            flash("profile updated")
            return redirect ("/dashboard")
        else:
            return render_template("user/profile.html",pform=pform, userdeets=userdeets)



@app.route("/dashboard")
@login_required
def dashboard():
    useronline = session.get('userid')
    userdeets= db.session.query(User).get(useronline)
    return render_template("user/dashboard.html", userdeets=userdeets)



@app.route("/donate",methods=["POST","GET"])
def donation():
    useronline = session.get('userid')
    userdeets = db.session.query(User).get(useronline)
    if request.method =='GET':
        return render_template("user/donation.html",userdeets=userdeets)
    else:
        #retrieve from data
        fullname =request.form.get("fullname")
        email =request.form.get("email")
        amount= request.form.get("amount")
        if request.form.get('userid')=="":
            userid= None
        else:
            userid= request.form.get("userid")

        refno = int(random.random()*100000000)
        #create a new donation instance 
        don = Donation(don_amt=amount,don_userid=userid,don_fullname=fullname,don_email=email, don_refno=refno,don_status='pending' )
        db.session.add(don)
        db.session.commit()
        #save the refno in a sesssion so that we acan retrieve the details on the next page
        session['ref'] = refno
        return redirect("/payment")

@app.route("/payment")
def make_payment():
    userdeets=db.session.query(User).get(session.get('userid'))
    if session.get('ref') !=None:
        ref=session['ref']
        #to do we want to get the details of the transaction and display to the user
        trxdeets = db.session.query(Donation).filter(Donation.don_refno==ref).first()
        return render_template ("user/payment.html",trxdeets=trxdeets,userdeets=userdeets)
    else:
        return redirect("/donate")

@app.route("/paystack", methods=['POST'])
def paystack():
    if session.get('ref') != None:
        ref= session['ref']
        trx= db.session.query(Donation).filter(Donation.don_refno==ref).first()
        email = trx.don_email
        amount= trx.don_amt
        #we want to connect to paystack api
        url="https://api.paystack.co/transaction/initialize"
        headers ={"Content-Type": "application/json","Authorization":"Bearer sk_test_52c50aadab204e5049e257189c70379ba9599a0f"}
        data = {"email":email, "amount":amount *100,"reference":ref}
        response = requests.post(url,headers=headers,data=json.dumps(data))
        rspjson=response.json()
        if rspjson['status'] ==True:
            paygateway =rspjson['data']['authorization_url']
            return redirect(paygateway)
    else:
         return rspjson
    

@app.route("/landing")
def paystack_landing():
    ref=session.get('ref')
    if ref ==None:
        return redirect('/donate')
    else:  #connect to paystack verify
        headers={"Content-Type": "application/json","Authorization":"Bearer sk_test_52c50aadab204e5049e257189c70379ba9599a0f"}
        verifyurl= "https://api.paystack.co/transaction/verify/"+str(ref)
        response =requests.get(verifyurl,headers=headers)
        rspjson =json.loads(response.text)
        if rspjson['status']== True: #payment was successful
            return rspjson
        else:
            return "payment was not successful"









@app.route("/")
def home():
    books =db.session.query(Book).filter(Book.book_status=='1').order_by(Book.book_id.desc()).limit(4).all()
    useronline = session.get('userid')
    #we will have to connect the endpoint http://127.0.0.1:5000/
    userdeets = db.session.query(User).get(useronline)
    books= db.session.query(Book).all()

    headers = {'Content-Type': 'application/json'}
    response = requests.get('http://127.0.0.1:5000/api/v1.0/listall',headers, auth=('bookworm','python'))
    partner_stores = response.json()

    return render_template("user/home.html",books=books,userdeets=userdeets,partner_stores=partner_stores)



@app.route("/reviews/<bookid>")
def reviews(bookid):
    bookdeets = db.session.query(Book).get_or_404(bookid)
    return render_template("user/reviews.html", bookdeets=bookdeets)



@app.route("/submitreview", methods=['POST'])
@login_required
def submit_review():
    title = request.form.get('review_title')
    text = request.form.get('review')
    bookid= request.form.get('bookid')
    useronline = session.get('userid')
    #insert this review
    review= Reviews(rev_text=text,rev_title=title,rev_bookid=bookid,rev_userid=useronline)
    db.session.add(review)
    db.session.commit()
    flash("Thank you, your review has been submitted")
    return  redirect ("/dashboard")







