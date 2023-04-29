# Database Libraries
import chkd_db
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



# Create Postgres Database Engine
engine = sqlalchemy.create_engine('postgresql://postgres:postgres@localhost:5432/CHKD')

video_formats = [".mp4", ".webm"] # hardcoded video formats
image_formats = [".jpg", ".png", "jpeg", ".gif",".bmp"] # hardcoded image formats
audio_formats = [".mp3", ".m4a", ".wav"] # hardcoded audio formats

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

        # ADD FRIENDS
        # userA = session.get("user")
        #result = chkd_db.addFriend(userA, userB)
        #if result == 0:
        #   flash("You already are friends with this user.")
        #elif result == 1:
        #   do something to update screen to reflect changes (add them to the list)
        #   flash("You are now friends with this user.")
        #else:
        #   flash("Something went wrong.")

#root of the website folder
root_path = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nerf'
app.config['MEDIA_FOLDER'] = 'static\media'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

#gets quest creation info
class QuestForm(FlaskForm):
    quest = StringField('quest', widget = TextArea(), validators=[DataRequired(), Length(max= 500)])
    rules = StringField('rules', widget = TextArea(), validators=[DataRequired(), Length(max= 500)])

#gets quest submission
class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

#get login info
class LoginForm(FlaskForm):
    name = StringField('username', validators=[DataRequired(), Length(max= 30)])
    password = StringField('password', validators=[DataRequired(), Length(max= 30)])
    login = SubmitField("Login")

#stores group info
class Groups():
    def __init__(self, users, id):
        self.users = users
        self.id = id
        self.quest = ""
        self.rules = ""
    def add_quest(self, quest, rules):
        self.quest = quest
        self.rules = rules 

class Submission():
    def __init__(self, user, file):
        self.user = user
        self.file = file
        self.votes = 0
    def upvote(self):
        self.votes += 1
    def downvote(self):
        self.votes -=1

    
# def getGroups():
#     groups = [
#         {"name": "The Blue Boys", "hasNotification": False, "completedTasks": 2, "totalTasks": 5, "totalMembers": 6, "isMember": True},
#         {"name": "The Blue Boys", "hasNotification": True, "completedTasks": 1, "totalTasks": 3, "totalMembers": 12, "isMember": True},
#         {"name": "The Blue Boys", "hasNotification": False, "completedTasks": 11, "totalTasks": 12, "totalMembers": 3, "isMember": True},
#         {"name": "The Blue Boys", "hasNotification": False, "completedTasks": 2, "totalTasks": 5, "totalMembers": 6, "isMember": False}
#     ]
#     return groups

# def getFriends():
#     friends = [
#         {"name": "ThwompFriend12", "isFriend": True},
#         {"name": "ToothStealer", "isFriend": False}
#     ]
#     return friends

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
temp_submissions = []  #temp array to all quest submissions
temp_group = Groups("none", 0)#temp group fo testing


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
        user_id = chkd_db.login(username, password)

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
    
#home page
@app.route('/home', methods=['GET',"POST"])
def home():
    #check that the user actually sigined in and didn't manually type the url
    if "user" in session:
        quest_check = 0 #checks if a quest has been made yet
        if(temp_group.quest != ""):
            quest_check = 1
        if request.method == "POST":
            if(quest_check):
                return redirect(url_for('upload', group = temp_group.id))
            else:
                return redirect(url_for('create'))
    else: return redirect(url_for('login'))         
    return render_template('index.html', quest_check = quest_check, user = session["user"], groups=groups, friends=friends)


#/create, collects text information to create a task
#returns the upload page after any text is sumbitted
@app.route('/create', methods=['GET', 'Post'])
def create():
    #create the quest
    form = QuestForm()
    if request.method == "POST":
        # Kyle
        quest = form.quest.data # First grab the file
        rules = form.rules.data
        temp_group.add_quest(quest, rules)

        # Get the USER ID and GROUP ID

        # Get the input from user
        title = str(form.quest.data)
        description = str(form.rules.data)
    
        # Call to Database
        #chkd_db.newChallenge(user, title, description, group)
        
        return redirect(url_for('upload', group = temp_group.id))
    return render_template("create.html", form = form, groups=groups, friends=friends)

#/upload/<group> uploads files from the websever to the database, given the group number
#returns redirect to watch page to veiw the submissions
@app.route('/upload/<group>', methods=["GET", "POST"])
def upload(group):
    file_num = len(os.listdir(os.path.join(root_path, app.config['MEDIA_FOLDER']))) 
    quest_msg = temp_group.quest
    rules_msg = temp_group.rules
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data # First grab the file
        #save the file to (file location of root + file in root + file name)
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['MEDIA_FOLDER'],secure_filename(str(file_num) + file.filename))) # Then save the file
       
        #update the fake databse
        sub =Submission(session["user"], file.filename)
        temp_submissions.append(sub)

        # Update the Database
        file = form.file.data # First grab the file
        user = session["user"]
        challenge_id = 1

        # Call to Database
        chkd_db.newPost(user, file, challenge_id)

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
    if request.method == "POST":
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
        #load next media file
        return redirect(url_for('watch', curr=curr))
    # Load the webpage
    else:
            return  render_template('watch.html', user = temp_submissions[curr].user, filename = temp_submissions[curr].file, user_input = img_name, media = mediaType(img_name), curr = curr, files = folder_len, groups=groups, friends=friends)
    

 #/results, webpage to viww the top upvoted
 #this is not fully coded yet
@app.route('/results', methods=['GET', 'POST'])
def results():
    unsorted = []
    winner_index = 0

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
    return  render_template('results.html', user =user_name, file = file_name, user_input = img_name, media = mediaType(img_name), votes = num_votes, groups=groups, friends=friends)       



if __name__ == '__main__':
    '''
    #Uncomment if you want everyone on your local network to connect!
    #This will work on eduroam or umbc vistor for a class demonstration 
    #your new url will be given in the terminal
    print(socket.gethostbyname(socket.gethostname()))
    app.run(debug=True, host = "0.0.0.0", port = 25565)
    '''
    app.run(debug=True)
    #chkd_db.finished()