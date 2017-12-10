from flask import render_template, request, redirect, session, abort
from app import app
from .forms import LoginForm, RegisterForm, EventDetailForm
from .models import User, Event
import os
from pprint import pprint


@app.route('/home')
def home():
    if 'userid' in session:
        userid = session['userid']
        events = User(userid).get_following_events()
        creator_name_list = {}
        for e in events:
            creator_id = e[6]
            if creator_id not in creator_name_list:
                creator = User(creator_id).find()
                creator_name_list[creator_id] = creator[1]
        return render_template('home.html', user=userid, username=session['username'], event_list=events,
                               creators=creator_name_list)
    return redirect('/login')


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'userid' in session:
        return redirect('/home')
    form = LoginForm()
    if form.validate_on_submit():
        user = User().authenticate(form.email.data, form.password.data)
        if user is not None:
            session['userid'] = user[0]
            session['username'] = user[1]
            return redirect('/home')
        return redirect('/login')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if 'userid' in session:
        session.pop('userid')
        session.pop('username')
    return redirect('/login')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        userid = User().create(form.email.data, form.password.data, form.username.data)
        if userid is not None:
            session['userid'] = userid
            session['username'] = form.username.data
            return redirect('/home')
        return redirect('/signup')

    return render_template('signup.html', form=form)


@app.route('/profile/<int:userid>')
def profile(userid):
    if 'userid' not in session:
        return redirect('/login')
    user = User(userid).find()
    if user is None:
        return abort(404)
    events_created = User(userid).get_events_created()
    events_participated = User(userid).get_events_participated()
    creator_name_list = {}
    for e in events_participated:
        creator_id = e[6]
        if creator_id not in creator_name_list:
            creator = User(creator_id).find()
            creator_name_list[creator_id] = creator[1]

    return render_template('profile.html', current_user=session['userid'], user_profile=user,
                           event_created=events_created, events_participated=events_participated,
                           creators=creator_name_list, user=userid, username=session['username'])


@app.route('/register/<int:eventid>')
def register(eventid):
    if 'userid' not in session:
        return redirect('/login')
    userid = session['userid']
    if User(userid).register(eventid) is True:
        return redirect('/profile/%d' % userid)
    return redirect('/home')


@app.route('/event_detail/<int:eventid>', methods=['GET', 'POST'])
def event_detail(eventid):
    if 'userid' not in session:
        return redirect('/login')
    event = Event(eventid).find()
    if event is None:
        return abort(404)
    registered = User(session['userid']).check_register(event[0])
    participants = Event(eventid).get_participants()
    comments = Event(eventid).get_comments()
    return render_template('event_detail.html', event=event, user=session['userid'], username=session['username'],
                           participants=participants, registered=registered, comments=comments)


@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'userid' not in session:
        return redirect('/login')
    form = EventDetailForm()
    userid = session['userid']

    if form.validate_on_submit():
        start_time = form.start_date.data
        end_time = form.end_date.data
        eventid = Event().create(session['userid'], form.name.data, form.description.data, form.location.data,
                                 start_time, end_time)
        # TODO: cannot upload
        # if request.files:
        #     file = request.files['file']
        #     if file:
        #         splitlist = file.filename.split('.')
        #         file_format = splitlist[-1]
        #         file.filename = str(eventid) + '.' + file_format
        #         file.save(os.path.join(app.config['EVENT_PICTURE'], file.filename))
        return redirect('/profile/%d' % session['userid'])

    return render_template('create_event.html', form=form, user=userid, username=session['username'])


@app.route('/add_friend', methods=['GET', 'POST'])
def add_friend():
    if 'userid' not in session:
        return redirect('/login')
    userid = session['userid']
    userinfo = request.form['userinfo']
    userlist = User().search_user(userinfo)
    userlist = list(userlist)
    for i in range(len(userlist)):
        if User(userid).check_follow(userlist[i][0]):
            userlist[i] += (1,)
        else:
            userlist[i] += (0,)
    return render_template('add_friend.html', userlist=userlist, user=userid, username=session['username'])


@app.route('/add/<int:userid>')
def add(userid):
    if 'userid' not in session:
        return redirect('/login')
    if User(session['userid']).follow(userid):
        return redirect('/show_friends')
    return redirect('/home')


@app.route('/show_friends')
def show_friends():
    if 'userid' not in session:
        return redirect('/login')
    userid = session['userid']
    followers = User(userid).get_followers()
    followings = User(userid).get_followings()
    return render_template('show_friends.html', followers=followers, followings=followings, user=userid,
                           username=session['username'])


@app.route('/change_profile', methods=['GET', 'POST'])
def change_profile():
    userid = session['userid']
    # picture = request.files['picture']
    # if picture:
    #     picture.save(os.path.join(app.config['UPLOAD_FOLDER'], picture.filename))
    return render_template('change_profile.html', user=userid, username=session['username'])


@app.route('/add_comment/<int:eventid>', methods=['GET', 'POST'])
def add_comment(eventid):
    if 'userid' not in session:
        return redirect('/login')
    userid = session['userid']
    comment = request.form['comment']
    if comment:
        User(userid).post_comment(eventid, comment)
    return redirect('/event_detail/%d' % eventid)


# @app.route('/really_change', methods=['GET', 'POST'])
# def really_change():
#     userid = session['userid']
#     if request.method == "POST":
#         file = request.files['file']
#         pprint(request.files)
#         if file:
#             file.save(os.path.join(app.config['EVENT_PICTURE'], file.filename))
#     return render_template('change_profile.html', user=userid, username=session['username'])
