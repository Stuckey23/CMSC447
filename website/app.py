# Database Libraries
import chkd_db as database
import sqlalchemy

from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from wtforms.widgets import TextArea
from werkzeug.utils import secure_filename
from flask_wtf.file import FileField, FileAllowed
import os
from wtforms.validators import InputRequired, DataRequired, Length
import socket


#changed port number
# Create Postgres Database Engine
engine = sqlalchemy.create_engine('postgresql://postgres:postgres@localhost:5433/CHKD')

video_formats = [".mp4", ".webm"] # hardcoded video formats
image_formats = [".jpg", ".png", "jpeg", ".gif",".bmp"] # hardcoded image formats
audio_formats = [".mp3", ".m4a", ".wav"] # hardcoded audio formats



#root of the website folder
root_path = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
# following string is stored in cookies
app.config['SECRET_KEY'] = 'nerf'

app.config['MEDIA_FOLDER'] = 'static\media'
# 10 mb content length
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

#gets quest creation info
class QuestForm(FlaskForm):
    quest = StringField('quest', widget = TextArea(), validators=[DataRequired(), Length(max= 500)])
    rules = StringField('rules', widget = TextArea(), validators=[DataRequired(), Length(max= 500)])

class CommentForm(FlaskForm):
    comment = StringField('comment', widget = TextArea(), validators=[Length(max= 500)])


#gets quest submission
class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

#get login info
class LoginForm(FlaskForm):
    name = StringField('name', validators=[DataRequired(), Length(max= 30)])
    password = StringField('password', validators=[DataRequired(), Length(max= 30)])
    login = SubmitField("Login")

#stores group info
class Groups():
    def __init__(self, users, id):
        self.users = users
        self.id = id
        self.quest = ""
        self.rules = ""
        self.submissions = []
    def add_quest(self, quest, rules):
        self.quest = quest
        self.rules = rules
    def add_submission(self, submission):
        self.submissions.append(submission)

class Submission():
    def __init__(self, user, file):
        self.user = user
        self.file = file
        self.votes = 0
        self.comments = []
    def upvote(self):
        self.votes += 1
    def downvote(self):
        self.votes -=1
    def commnet(self, input):
        self.comments.append(input)
    
# Hard coded groups and friends. This eventually needs to come from the database
groups = [
    {"name": "The Blue Boys", "hasNotification": False, "completedTasks": 2, "totalTasks": 5, "totalMembers": 6, "isMember": True},
    {"name": "The Whalers", "hasNotification": True, "completedTasks": 1, "totalTasks": 3, "totalMembers": 12, "isMember": True},
    {"name": "Team 3: Best!", "hasNotification": False, "completedTasks": 11, "totalTasks": 12, "totalMembers": 3, "isMember": True},
    {"name": "Gang X", "hasNotification": False, "completedTasks": 2, "totalTasks": 5, "totalMembers": 6, "isMember": False}
]

friends = [
    {"name": "ThwompFriend12", "isFriend": True},
    {"name": "ToothStealer", "isFriend": False}
]

# submissions = [
#     {"user":"stuckey", "filename":"media/SS1.png", "mediaType": 1},
#     {"user":"stuckey", "filename":"media/SS2.png", "mediaType": 1}
# ]

submissions = []


tasks = [
    {"id": 0, "title": "Drop the ball from the furthest height", "rules": "Only 1 drop allowed", "submissions":submissions},
    {"id": 1, "title": "Make the funniest face", "rules": "Must be your face", "submissions": submissions}
]

#tasks = []



# def getFriends():
#     friends = [
#         {"name": "ThwompFriend12", "isFriend": True},
#         {"name": "ToothStealer", "isFriend": False}
#     ]
#     return friends

    
# Hard coded groups and friends. This eventually needs to come from the database
groups = [
    {"name": "The Blue Boys", "hasNotification": False, "completedTasks": 2, "totalTasks": 5, "totalMembers": 6, "isMember": True},
    {"name": "The Whalers", "hasNotification": True, "completedTasks": 1, "totalTasks": 3, "totalMembers": 12, "isMember": True},
    {"name": "Team 3: Best!", "hasNotification": False, "completedTasks": 11, "totalTasks": 12, "totalMembers": 3, "isMember": True},
    {"name": "Gang X", "hasNotification": False, "completedTasks": 2, "totalTasks": 5, "totalMembers": 6, "isMember": False}
]

friends = [
    {"name": "ThwompFriend12", "isFriend": True},
    {"name": "ToothStealer", "isFriend": False}
]

# submissions = [
#     {"user":"stuckey", "filename":"media/SS1.png", "mediaType": 1},
#     {"user":"stuckey", "filename":"media/SS2.png", "mediaType": 1}
# ]

submissions = []


tasks = [
    {"id": 0, "title": "Drop the ball from the furthest height", "rules": "Only 1 drop allowed", "submissions":submissions},
    {"id": 1, "title": "Make the funniest face", "rules": "Must be your face", "submissions": submissions}
]

#tasks = []



#FAKE DATABSE!
#This is here beacause I havent connected the website to the data base yet
temp_submissions = []  #temp array to all quest submissions
temp_group = Groups("none", 0)#temp group fo testing


#mediaType(), given an image name checks what type of media was uploaded
#returns an int 1-image, 2-video, 3-audio
def mediaType(img_name):
    if any(word in img_name for word in image_formats):
        media_type = 1 # image 
    elif any(word in img_name for word in video_formats):
        media_type = 2 # video
    elif any(word in img_name for word in audio_formats):
        media_type = 3 # audio
    else:
        media_type = 0 # unsupported media format
    return media_type

#FAKE DATABSE!
#This is here beacause I havent connected the website to the data base yet
temp_submissions = []  #temp list to all quest submissions  
temp_group = Groups("none", 0)#temp group fo testing

# post means user input
# get means get from server

# first thing after main
#creates the website on localhost:5000
@app.route('/', methods=['GET',"POST"])

#login page
@app.route('/login', methods=['GET',"POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        # Get the input from user
        username = str(form.name.data)
        password = str(form.password.data)

        # Call to Database
        user_id = database.login(username, password)

        # User login failed
        if(user_id == -1):
            flash("The username or password you’ve entered is incorrect. Try again")
            print("Fail")
        
        # User login success!
        else:
            session["user"] = username

            # Go to home page
            session.pop('_flashes',None)
            return redirect(url_for('home'))
        
    # Close out of DB after using DB / webapp
    return(render_template('login.html', form = form))

def handleHome(request):
    functions = {
        "newSubmission": newSubmission,
        "viewSubmission": viewSubmission,
        "newQuest": createQuest
    }

    if request.method == "POST":
        formType = request.form.get('formType')
        if formType == "home":
            return functions[request.form.get('button')](request.form.get('value'))

def newSubmission(arg):
    return redirect(url_for('upload', group = arg))

def viewSubmission(arg):
    return redirect(url_for('watch', curr = 0))

def createQuest(arg):
    return redirect(url_for('create'))
    

def handleSidebar(request):
    functions = {
        "acceptFriend": acceptFriendRequest, 
        "declineFriend": declineFriendRequest, 
        "requestFriend": requestFriend,
        "removeFriend": removeFriend,
        "acceptGroup": acceptGroup,
        "declineGroup": declineGroup,
        "newGroup": newGroup,
        "log-out": logOut
        }
    
    if request.method == "POST":
        formType = request.form.get('formType')
        if formType == "sidebar":
            return functions[request.form.get('button')](request.form.get('value'))
    
def acceptFriendRequest(arg):
    friendName = arg
    username = session["user"]
    print("%s accepted %s's friend request" % (username, friendName))
    #database.addFriend(friendName, username)
    return

def declineFriendRequest(arg):
    friendName = arg
    username = session["user"]
    print("%s declined %s's friend request" % (username, friendName))
    return

def requestFriend(arg):
    requesteeName = arg
    requesterName = session["user"]
    print("%s sent a friend requet to %s" % (requesterName, requesteeName))
    #database.requestFriend(requesteeName, requesterName)
    return

def removeFriend(arg):
    userA = session["user"]
    userB = arg
    print("%s removed %s as a friend" % (userA, userB))
    #database.removeFriend(userA, userB)
    return

def acceptGroup(arg):
    username = session["user"]
    groupName = arg
    print("%s joined the group: %s" % (username, groupName))
    #database.addUserToGroup(username, groupName)
    return

def declineGroup(arg):
    return

def newGroup(arg):
    groupName = arg
    username = session["user"]
    print("%s created group: %s" % (username, groupName))
    #database.newGroup(groupName, username)
    return

def logOut(arg):
    session.clear()
    print("User logged out")
    return redirect(url_for('login')) 




def validateUser():
    if "user" in session:
        return None
    else: return redirect(url_for('login'))         


#home page
@app.route('/home', methods=['GET',"POST"])
def home():
    #check that the user actually sigined in and didn't manually type the url
    results = validateUser()
    if results != None:
        return results
    
    # Sees if anything was pressed in sidebar, handles it
    results = handleSidebar(request)
    if results != None:
        return results
    
    results = handleHome(request)
    if results != None:
        return results
    
    questExists = len(tasks)
    

    return render_template('index.html', questExists = questExists, user = session["user"], currGroup = temp_group.id, groups=groups, friends=friends, tasks=tasks)


#/create, collects text information to create a task
#returns the upload page after any text is sumbitted
@app.route('/create', methods=['GET', 'Post'])
def create():
    form = QuestForm()

    #check that the user actually sigined in and didn't manually type the url
    results = validateUser()
    if results != None:
        return results
    
    # Sees if anything was pressed in sidebar, handles it
    results = handleSidebar(request)
    if results != None:
        return results
    
    formType = request.form.get('formType')
    if request.method == "POST" and formType != "sidebar":
        quest = form.quest.data # First grab the file
        rules = form.rules.data
        tasks.append({"id": len(tasks), "title": quest, "rules": rules, "submissions":submissions})
        return redirect(url_for('upload', group = len(tasks) - 1))
    return render_template("create.html", form = form, groups=groups, friends=friends)

#/upload/<group> uploads files from the websever to the database, given the group number
#returns redirect to watch page to veiw the submissions
@app.route('/upload/<group>', methods=["GET", "POST"])
def upload(group):
    form = UploadFileForm()
    file_num = len(os.listdir(os.path.join(root_path, app.config['MEDIA_FOLDER']))) 
    
    quest_msg = tasks[int(group)].get("title")
    rules_msg = tasks[int(group)].get("rules")
    #check that the user actually sigined in and didn't manually type the url
    results = validateUser()
    if results != None:
        return results
    
    # Sees if anything was pressed in sidebar, handles it
    results = handleSidebar(request)
    if results != None:
        return results
    
    formType = request.form.get('formType')
    if request.method == "POST" and formType != "sidebar":
        if form.validate_on_submit():
            file = form.file.data # First grab the file
            #save the file to (file location of root + file in root + file name)
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['MEDIA_FOLDER'],secure_filename(str(file_num) + file.filename))) # Then save the file
            #update the fake databse
            sub =Submission(session["user"], file.filename)
            temp_submissions.append(sub)
            return redirect(url_for('watch', curr = 0))
    return render_template('upload.html', form=form, quest = quest_msg, rules =rules_msg, groups=groups, friends=friends)
           

#/watch/<curr> creates webpage to veiw the actual submissions, curr is the submission
#returns the next or previous submission, or redirects to the voting page
@app.route('/watch/<curr>', methods=['GET', 'POST'])
def watch(curr):
    curr = int(curr)
    folder_len = len(os.listdir(os.path.join(root_path, app.config['MEDIA_FOLDER']))) -1
    img_name = 'media/' + os.listdir(os.path.join(root_path, app.config['MEDIA_FOLDER']))[curr]
    #check what button is pressed
    #check that the user actually sigined in and didn't manually type the url
    results = validateUser()
    if results != None:
        return results
    
    # Sees if anything was pressed in sidebar, handles it
    results = handleSidebar(request)
    if results != None:
        return results
    
    formType = request.form.get('formType')
    if request.method == "POST" and formType != "sidebar":
        button = request.form["submit_button"]
        if(button == "NEXT"):
            if curr == folder_len:
                print(folder_len)
            else:
                curr += 1
        if(button == "PREV"):
            if curr == 0:
                print("No previous files")
            else:
                curr -= 1
        if(button == "NEW"):
            return redirect(url_for('upload', group = temp_group.id))
        if(button == "UP"):
            temp_submissions[curr].upvote()
            print("Current vote counter:")
            print(temp_submissions[curr].votes)
            return redirect(url_for('results'))
        if(button == "Log-out"):
            session.clear()
            return redirect(url_for('login')) 
        #load next media file
        return redirect(url_for('watch', curr=curr))
    # Load the webpage
    else:
            return  render_template('watch.html', user = temp_submissions[curr].user, filename = temp_submissions[curr].file, user_input = img_name, media = mediaType(img_name), curr = curr, files = folder_len, groups=groups, friends=friends)
    

 #/results, webpage to veiw the top upvoted
 #this is not fully coded yet
@app.route('/results', methods=['GET', 'POST'])
def results():
    if "user" in session:
        unsorted = []
        winner_index = 0
        #This is a really bad way to get the top voted
        folder_len = len(os.listdir(os.path.join(root_path, app.config['MEDIA_FOLDER'])))
        print("This is the current "+ str(folder_len))
        for votes in range(folder_len):
            unsorted.append((temp_submissions[votes].votes))
        num_votes  = max(unsorted)

        for votes in range(folder_len):
            if temp_submissions[votes].votes == num_votes:
                winner_index = votes

        user_name = temp_submissions[winner_index].user
        file_name = temp_submissions[winner_index].file
        img_name = 'media/' + os.listdir(os.path.join(root_path, app.config['MEDIA_FOLDER']))[winner_index]
        print(img_name)
        print(winner_index)
        if request.method == "POST":
            return redirect(url_for('home'))

    else: return redirect(url_for('login'))
    return  render_template('results.html', user =user_name, file = file_name, user_input = img_name, media = mediaType(img_name), votes = num_votes, groups=groups, friends=friends)       



if __name__ == '__main__':
    #Uncomment if you want everyone on your local network to connect!
    #This will work on eduroam or umbc vistor for a class demostration 
    #your new url will be given in the termianl
    '''
    print(socket.gethostbyname(socket.gethostname()))
    app.run(debug=True, host = "0.0.0.0", port = 25565)
    '''
    app.run(debug=True)
    #database.finished()