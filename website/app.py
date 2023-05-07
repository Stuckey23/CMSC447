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
import shutil
from wtforms.validators import InputRequired, DataRequired, Length
import socket


#changed port number
# Create Postgres Database Engine
engine = sqlalchemy.create_engine('postgresql://postgres:postgres@localhost:5432/CHKD')

video_formats = [".mp4", ".webm"] # hardcoded video formats
image_formats = [".jpg", ".png", "jpeg", ".gif",".bmp"] # hardcoded image formats
audio_formats = [".mp3", ".m4a", ".wav"] # hardcoded audio formats
#testing
# Hard coded groups and friends. This eventually needs to come from the database
groups = []

        # ADD FRIENDS
        # userA = session.get("user")
        #result = database.addFriend(userA, userB)
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
# following string is stored in cookies
app.config['SECRET_KEY'] = 'nerf'


app.config['MEDIA_FOLDER'] = 'static\media'
app.config['OLD_FOLDER'] = 'static\old'

#clear out the media file
if(os.path.exists(os.path.join(root_path, app.config['MEDIA_FOLDER']))):
    os.rename(os.path.join(root_path, app.config['MEDIA_FOLDER']), os.path.join(root_path, app.config['OLD_FOLDER']))
    shutil.rmtree(os.path.join(root_path, app.config['OLD_FOLDER']))
os.mkdir(os.path.join(root_path, app.config['MEDIA_FOLDER']))

# 10 mb content length
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

#gets quest creation info
class QuestForm(FlaskForm):
    quest = StringField('quest', widget = TextArea(), validators=[DataRequired(), Length(max= 500)])
    rules = StringField('rules', widget = TextArea(), validators=[DataRequired(), Length(max= 500)])

class NewGroupForm(FlaskForm):
    groupName = StringField('groupName', widget = TextArea(), validators=[DataRequired(), Length(max= 20)])

class NewFriendForm(FlaskForm):
    friendName = StringField('friendName', widget = TextArea(), validators=[DataRequired(), Length(max= 20)])

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
# {"id": 0, "name": "The Blue Boys", "hasNotification": False, "completedTasks": 2, "totalTasks": 5, "totalMembers": 6, "isMember": True, "tasks": tasks},

class Groups():
    def __init__(self, users, id):
        self.users = users #users in the group will be added later
        self.id = id       #group id
        self.name = "group" + str(id) 
        self.tasks = []    #lists of all tasks 
        self.memberStatus = "OWNER"
        #creates group folder nside of media
        self.group_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['MEDIA_FOLDER'],secure_filename(str(id)))
        #self.group_path = os.path.join(app.config['MEDIA_FOLDER'], str(id))
        if(not os.path.exists(self.group_path)):
            os.mkdir(self.group_path)

    def set_name(self, newName):
        self.name = newName

    def set_tasks(self, tasks):
        self.tasks = tasks

    def toDictionary(self):
        dict = {"id": self.id, "name": self.name, "tasks": self.tasks, "obj": self, "memberStatus": self.memberStatus}
        return dict
    
    def add_task(self, quest, rules):
        submissions = []
        self.tasks.append({"id": len(self.tasks), "title": quest, "rules": rules, "submissions":submissions})
        #creates task folder inside of group folder
        task_path = os.path.join(self.group_path, str(len(self.tasks) -1))
        if(not os.path.exists(task_path)):
           os.mkdir(task_path)
        return True

    def add_submission(self, submission):
        #get the right task folder
        task_path = os.path.join(self.group_path, str(submission.task))
        #get the media file number
        file_num = len(self.tasks[submission.task].get("submissions"))
        #create new name to prevent error / hacks
        file_name = secure_filename(str(file_num) + submission.file.filename)
        #save media file to the folder
        file_path = os.path.join(task_path,file_name)
        submission.file.save(file_path)
        #save the new name needed to display images in flask!
        submission.setname(file_name)
        #add submission to submissions list 
        self.tasks[submission.task].get("submissions").append(submission)

class Submission():
    def __init__(self, user, task, file):
        self.user = user
        self.task = task
        self.file = file
        self.filename = ""
        self.votes = 0
        self.comments = []
    def setname(self, name):
        self.filename = name
    def getname(self):
        return self.filename

    def upvote(self):
        self.votes += 1
    def downvote(self):
        self.votes -=1
    def commnet(self, input):
        self.comments.append(input)
    

friends = [
    {"name": "ThwompFriend12", "isFriend": True},
    {"name": "ToothStealer", "isFriend": False}
]



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
temp_groups = []    #temp list of all groups  
temp_group = Groups("none", 0)#temp group fo testing
temp_groups.append(temp_group)


def handleHome(request):
    functions = {
        "newSubmission": newSubmission,
        "viewSubmission": viewSubmission,
        "newQuest": createQuest,
        #"viewResults": viewResults #currently not implemented
    }

    if request.method == "POST":
        formType = request.form.get('formType')
        if formType == "home":
            #print("PLEASE WORK")
            #print(request.form.get('group'))
            return functions[request.form.get('button')](request.form.get('group'), (request.form.get('task')))

def newSubmission(group, task):
    #groups is hard coded in html since we cant switch groups yet

    return redirect(url_for('upload', group = int(group), task = int(task)))

def viewSubmission(group, task):
    
    if len(groups[int(group)].tasks[int(task)].get("submissions")) == 0:
        flash("No Submissions have be uploaded to that task yet")
        return
    return redirect(url_for('watch', curr =0, group = int(group), task = int(task),))

def createQuest(group, task):
    
    return redirect(url_for('create', group = group))
    

def handleSidebar(request):
    functions = {
        "acceptFriend": acceptFriendRequest, 
        "declineFriend": declineFriendRequest, 
        "requestFriend": requestFriend,
        "removeFriend": removeFriend,
        "acceptGroup": acceptGroup,
        "declineGroup": declineGroup,
        "newGroup": newGroup,
        "deleteGroup": deleteGroup,
        "log-out": logOut,
        "groupSelect": groupSelect
        }
    
    if request.method == "POST":
        formType = request.form.get('formType')
        if formType == "sidebar":
            
            return functions[request.form.get('button')](request.form.get('value'))
    
def acceptFriendRequest(arg):
    friendName = arg
    username = session["user"]
    print("%s accepted %s's friend request" % (username, friendName))
    database.addFriend(friendName, username)
    return redirect(url_for('home', group = 0))

def declineFriendRequest(arg):
    friendName = arg
    username = session["user"]
    database.declineFriend(username, friendName)
    print("%s declined %s's friend request" % (username, friendName))
    return redirect(url_for('home', group = 0))

def requestFriend(arg):
    return redirect(url_for('addFriend'))
    # requesteeName = arg
    # requesterName = session["user"]
    # print("%s sent a friend requet to %s" % (requesterName, requesteeName))
    # #database.requestFriend(requesteeName, requesterName)
    return

def removeFriend(arg):
    userA = session["user"]
    userB = arg
    print("%s removed %s as a friend" % (userA, userB))
    database.removeFriend(userA, userB)
    return redirect(url_for('home', group = 0))

def acceptGroup(arg):
    username = session["user"]
    groupName = arg
    print("%s joined the group: %s" % (username, groupName))
    #database.addUserToGroup(username, groupName)
    return redirect(url_for('home', group = 0))

def declineGroup(arg):
    return

def newGroup(arg):
    return redirect(url_for('groupCreation'))

def deleteGroup(arg):
    username = session["user"]
    groupName = arg
    database.deleteGroupExistence(username, groupName)
    return redirect(url_for('home', group = 0))
    #print("res", database.deleteGroupExistence(username, groupName))
    

def logOut(arg):
    session.clear()
    print("User logged out")
    return redirect(url_for('login')) 

def groupSelect(arg):
    return redirect(url_for('home', group = arg))

def getGroup(id):
    for group in groups:
        if group.id == int(id):
            return group
    return None


def validateUser():
    if "user" in session:
        return None
    else: return redirect(url_for('login'))    

def formGroupsFromDB(username):
    groupNames = database.getGroupNamesOfUser(username)
    print("%s has groups %s" % (username, groupNames))
    groups.clear()
    for name in groupNames:
        newGroup = Groups("None", len(groups))
        newGroup.set_name(name)
        # eventually pull tasks from database
        newGroup.set_tasks([])
        #newGroup = newGroup.toDictionary()
        #newGroup.set_tasks()
        groups.append(newGroup)
        print("adding group! %s" % newGroup.name)

    #print(groups)
    return groups     

def formFriendsFromDB(username):
    friendNames = database.getFriends(username)
    friends.clear()
    for name in friendNames:
        friends.append({
            "name": name,
            "isFriend": True
        })

    pendingNames = database.getFriendRequests(username)
    for name in pendingNames:
        #print("appending ", name)
        friends.append({
            "name": name,
            "isFriend": False
        })
    
        
        #print("friend! %s" % frinewGroup.get("name"))

    #print(groups)
    #print("testing ", database.findUser("erinm5"))
    #print("testing ", database.getFriendRequests(username))
    return friends

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

            # Go to home page first group is 0
            session.pop('_flashes',None)
            return redirect(url_for('home', group = 0))
        
    # Close out of DB after using DB / webapp
    return(render_template('login.html', form = form))

#home page
@app.route('/home/<group>', methods=['GET',"POST"])
def home(group):
    user = session["user"]
    # Gets a list of groups a user is in
    groups = formGroupsFromDB(user)
    friends = formFriendsFromDB(user)

    #print("g1", groups)


    group = int(group)
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
    
    theGroup = getGroup(group)
    
    tasks = []
    #tasks = theGroup.tasks
    #print("tasks ", tasks)
    questExists = len(tasks)
    
    return render_template('index.html', questExists = questExists, user = user,  groups= groups, friends=friends, tasks=tasks, group = getGroup(group))

@app.route('/group_create', methods=['GET', 'POST'])
def groupCreation():
    user = session["user"]
    # Gets a list of groups a user is in
    groups = formGroupsFromDB(user)
    friends = formFriendsFromDB(user)

    #check that the user actually sigined in and didn't manually type the url
    results = validateUser()
    if results != None:
        return results
    
    # Sees if anything was pressed in sidebar, handles it
    results = handleSidebar(request)
    if results != None:
        return results
    

    form = NewGroupForm()
    formType = request.form.get('formType')
    if request.method == "POST" and formType != "sidebar":
        groupName = form.groupName.data # First grab the file
        username = session["user"]

        # Creates a new group
        result = database.newGroup(groupName, username)

        if(result == 'SUCCESS'):
            group = Groups(username, len(groups))
            group.set_name(groupName)
            groups.append(group)

            print("%s created group: %s" % (username, groupName))
            return redirect(url_for('home', group = len(groups) - 1))
        
        # Group name taken
        else:
            flash(result)
            # Need to return to previous page but flash the message somehow.
        
    return render_template("newGroup.html", form = form, user = user, groups=groups, friends=friends)

@app.route('/add_friend', methods=['GET', 'POST'])
def addFriend():
    user = session["user"]
    # Gets a list of groups a user is in
    groups = formGroupsFromDB(user)
    friends = formFriendsFromDB(user)

    #check that the user actually sigined in and didn't manually type the url
    results = validateUser()
    if results != None:
        return results
    
    # Sees if anything was pressed in sidebar, handles it
    results = handleSidebar(request)
    if results != None:
        return results
    
    form = NewFriendForm()
    formType = request.form.get('formType')
    if request.method == "POST" and formType != "sidebar":
        
        # Get usernames
        username = session["user"]
        friendName = form.friendName.data

        # Check if trying to add self
        if friendName == username:
            flash("Hey! You cannot add your self!")

        # Check if user exists
        else:
            friendID = database.findUser(friendName)
            #print(friendID)
            
            # User does not exist
            if friendID == -1:
                print("not found")
                flash("That user doesn't exist! :()")
        
            # Send the request
            else:
                result = database.requestFriend(username, friendName)
                flash(result)
                return redirect(url_for('home', group = 0))
            
        
        


        # groupName = form.groupName.data # First grab the file
        # username = session["user"]
        # #creat a new group
        # group = Groups(username, len(temp_groups))
        # group.set_name(groupName)
        # temp_groups.append(group)
        # print("%s created group: %s" % (username, groupName))
        
    return render_template("newFriend.html", form = form, groups=groups, friends=friends)


#/create, collects text information to create a task
#returns the upload page after any text is sumbitted
@app.route('/create/<group>', methods=['GET', 'Post'])
def create(group):
    group = int(group)
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
        #create new submission
        #print("herezzz ", groups[group].add_task(quest, rules))
        #uncomment
        groups[group].add_task(quest, rules)


        #tasks.append({"id": len(tasks), "title": quest, "rules": rules, "submissions":submissions})
        
        # add quest to group here

        # Get the input from user
        user = session["user"]
        #group = 'EVERYONE' # get the group -- need to find way to get the group name

    
        # Call to Database
        #database.newChallenge(user, group, quest, rules)
        
        #return redirect(url_for('upload', group = temp_group.id))
        return redirect(url_for('home', group = group))
    return render_template("create.html", form = form, groups=groups, friends=friends)

#/upload/<group> uploads files from the websever to the database, given the group number
#returns redirect to watch page to veiw the submissions
@app.route('/upload/<group>/<task>', methods=["GET", "POST"])
def upload(group, task):
    group = int(group)
    task = int(task)
    form = UploadFileForm()
    file_num = len(os.listdir(os.path.join(root_path, app.config['MEDIA_FOLDER']))) 
    
    quest_msg = temp_groups[group].tasks[task].get("title")
    rules_msg = temp_groups[group].tasks[task].get("rules")
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
            sub = Submission(session["user"] , task, file)
            
            #update the fake databse
            temp_groups[group].add_submission(sub)
            #temp_submissions.append(sub)

        # Update the Database
        submissionFile = root_path + 'static\\media\\' + secure_filename(str(file_num) + file.filename)
        user = session["user"]
        challenge_id = 1

        # Call to Database
        #database.newPost(user, submissionFile, challenge_id)

        return redirect(url_for('watch', curr = 0, group = group, task = task))
    return render_template('upload.html', form=form, quest = quest_msg, rules =rules_msg, groups=groups, friends=friends)
           

#/watch/<curr> creates webpage to veiw the actual submissions, curr is the submission
#returns the next or previous submission, or redirects to the voting page
@app.route('/watch/<curr>/<group>/<task>', methods=['GET', 'POST'])
def watch(curr, group, task):
    group = int(group)
    task = int(task)
    form = CommentForm()
    curr = int(curr)
    #this is the original unmodifed file name
    filename = temp_groups[group].tasks[task].get("submissions")[curr].file.filename

   
    user = temp_groups[group].tasks[task].get("submissions")[curr].user
    folder_len = len(temp_groups[group].tasks[task].get("submissions")) -1
    secure_name = temp_groups[group].tasks[task].get("submissions")[curr].getname()
    img_name = 'media/' + str(group) + '/' + str(task) + '/' + secure_name


    #print(img_name)
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
        if(button == "UP"):
            temp_groups[group].tasks[task].get("submissions")[curr].upvote
            #temp_submissions[curr].upvote()
            print("Current vote counter:")
            
            return redirect(url_for('home', group = 0))
        if(button == "Log-out"):
            session.clear()
            return redirect(url_for('login')) 
        if(button == "SUBMIT"):
                print(form.comment.data)
                temp_groups[group].tasks[task].get("submissions")[curr].commnet(form.comment.data)
                #temp_submissions[curr].commnet(form.comment.data)

        #load next media file
        return redirect(url_for('watch', curr=curr, group = group, task = task))
    # Load the webpage
    else:
            return  render_template('watch.html', user = user, filename = filename, user_input = img_name, media = mediaType(img_name), curr = curr, files = folder_len, groups=groups, friends=friends, comments = temp_groups[group].tasks[task].get("submissions")[curr].comments, form = form)
    

 #/results, webpage to view the top upvoted
 #this is not fully coded yet
@app.route('/results/<group>/<task>', methods=['GET', 'POST'])
def results(group, task):
    pass
    # group = int(group)
    # task = int(task)
    # if "user" in session:
    #     unsorted = []
    #     winner_index = 0
    #     #This is a really bad way to get the top voted
    #     folder_len = len(os.listdir(os.path.join(root_path, app.config['MEDIA_FOLDER'])))
    #     print("This is the current "+ str(folder_len))
    #     for votes in range(folder_len):
    #         unsorted.append((temp_submissions[votes].votes))
    #     num_votes  = max(unsorted)

    #     for votes in range(folder_len):
    #         if temp_submissions[votes].votes == num_votes:
    #             winner_index = votes

    #     user_name = temp_submissions[winner_index].user
    #     file_name = temp_submissions[winner_index].file
    #     img_name = 'media/' + os.listdir(os.path.join(root_path, app.config['MEDIA_FOLDER']))[winner_index]
    #     print(img_name)
    #     print(winner_index)
    #     if request.method == "POST":
    #         return redirect(url_for('home', group = 0))

    # else: return redirect(url_for('login'))
    # return  render_template('results.html', user =user_name, file = file_name, user_input = img_name, media = mediaType(img_name), votes = num_votes, groups=temp_groups, friends=friends)       

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