import db_friends as friends
import db_groups as groups

import psycopg2     # db library
import datetime     # time zone
import pytz
from sqlalchemy import DECIMAL         # time zone
from decimal import Decimal

# Connect to the CHKD Database
curr_time = datetime.datetime.now(pytz.timezone('US/Eastern'))
conn = psycopg2.connect(database="CHKD", user = "postgres", password = "postgres", host = "127.0.0.1", port = "5432")
cur = conn.cursor()

# When finished with db call, close DB connection
def finished():
    conn.close()

# Fill in the blanks if you want to create more users
def newUser():
    full_name = " "
    username = " "
    password = "abc123"
    # Make the Database Call
    cur.execute("INSERT INTO public.user(full_name,username,password, created_at,updated_at) VALUES (%s, %s,%s, %s, %s)",[full_name, username, password, curr_time,curr_time])
    conn.commit()

# Submit Challenge
def newChallenge(user, group, title, description):
    # Gets the user ID
    user_id = findUser(user)

    # Gets the group ID
    group_id = findGroup(group)

    if(group_id > 0 and user_id > 0):
        # Make the Database Call
        cur.execute("INSERT INTO public.challenge (author,description, group_id, challenge_date,title) \
                    VALUES (%s, %s,%s, %s, %s)", [user_id, description, group_id, curr_time, title])
        conn.commit()

# Submit File
def newPost(user, file, challenge_id):
    # Gets the user ID
    userId = findUser(user)
    file = str(file)

    try:
        # Make the Database Call
        cur.execute("INSERT INTO public.post(author,challenge_id,submission,created_at,updated_at) VALUES (%s, %s,%s, %s, %s);",[userId, challenge_id, file, curr_time,curr_time])
        conn.commit()    

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to add post. Try again")
        conn.rollback() 

# Request Member to Join Group
def requestGroupMember(username, group_name):
    # Get IDs
    message = 'Request failed.'
    user_id = int(findUser(username))
    group_id = int(findGroup(group_name))

    # User and Group Exist
    if(user_id > 0 and group_id > 0):
        relationship = groups.getGroupRelationship(user_id,group_id)

        # Does not send request if user is already a member
        if(relationship == 'MEMBER'):
            message = 'User is already a member of this group.'

        # Send request to database
        elif relationship == None:
            result = groups.requestUserToGroup(user_id,group_id,relationship)

            if result == 'SUCCESS':
                return 'You have successfully sent the request for the user to join ' + group_name

    return message
    

def getRelationship(userA,userB):

    if type == 'user':
        userA = int(findUser(userA))
        userB = int(findUser(userB))

    # Database Call
    cur.execute("SELECT relationship FROM public.relation WHERE person_a = %s and person_b = %s \
                UNION \
                SELECT relationship FROM public.relation WHERE person_a = %s and person_b = %s", [userA, userB, userB, userA] )
    relationship = cur.fetchone()
    conn.commit()

    # checks if relationship exists
    if(relationship):
        relationship = relationship[0]
        return relationship
    
    else:
        return None      
    
# Accept Group Request
def acceptGroupRequest(username, group_name):
    # Get IDs
    message = 'Request failed.'
    user_id = int(findUser(username))
    group_id = int(findGroup(group_name))
    if(user_id > 0 and group_id > 0):
        relationship = groups.getGroupRelationship(user_id,group_id)

        # Does not send request if user is already member of group
        if(relationship == 'MEMBER'):
            message = 'You are already a member of this group.'

        # Send request to database (User accepts)
        else:
            result = groups.acceptGroupRequest(user_id,group_id, relationship)
            print("res " + result)
            if result == 'SUCCESS':
                return 'You have successfully joined ' + group_name

    return message

# Decline Group Request
def declineGroup(username, group_name):

    # Get IDs
    message = 'Failed to leave ' + group_name
    user_id = int(findUser(username))
    group_id = int(findGroup(group_name))
    # User and Group Exist
    if(user_id > 0 and group_id > 0):
        relationship = groups.getGroupRelationship(user_id,group_id)
        if(relationship == 'REQUESTED'):
            result = groups.declineGroupRequest(user_id,group_id,relationship)

            if result == 'SUCCESS':
                return 'You have successfully left ' + group_name

    return message

# Request a Friend
def requestFriend(userA, userB):
    message = 'Failed to send request.'
    userint_a = int(findUser(userA)) # requester
    userint_b = int(findUser(userB)) # requestee

    # Check Users Exists // Prevent adding to table with non-existing users
    if(userint_a > 0 and userint_b > 0):
        result = friends.requestFriend(userA, userB)
        if result == 'SUCCESS':
            message = 'A request to ' + userB + ' has been sent.'
    
        else:
            message = result

    return message

def getRelationship(userA,userB):
    userA = int(findUser(userA))
    userB = int(findUser(userB))

    # Database Call
    cur.execute("SELECT relationship FROM public.relation WHERE person_a = %s and person_b = %s or person_a = %s and person_b = %s", [userA, userB, userB, userA] )
    relationship = cur.fetchone()
    conn.commit()

    # checks if relationship exists
    if(relationship):
        relationship = relationship[0]
        return relationship
    
    else:
        return None

# Add a Friend
def addFriend(userA, userB):
    return friends.addFriend(userA, userB)

    

# Decline Friend Request
def declineFriend(userA, userB):

    relationship = getRelationship(userA,userB)

    if relationship == 'REQUESTED':
        # Make the Database Call
        userA = int(findUser(userA))
        userB = int(findUser(userB))
        #cur.execute("DELETE FROM public.relation WHERE p=%s and userB=%s",[userA, userB])
        cur.execute("DELETE FROM public.relation WHERE (person_a=%s and person_B=%s) or (person_A=%s and person_B=%s)",[userA, userB, userB, userA])
        conn.commit()    
        return 'SUCCESS'
    
    # Cannot Decline Friend Request
    else:
        return 'FAILED'


# Remove Existing Friend
def removeFriend(userA, userB):

    relationship = getRelationship(userA,userB)
    print("relation %s" % relationship)
    if relationship == 'FRIEND':
        # Make the Database Call
        userid_A = int(findUser(userA))
        userid_B = int(findUser(userB))
        #print("Removing: %i and %i" % userid_A, userid_B)
        cur.execute("DELETE FROM public.relation WHERE (person_a=%s and person_b=%s) or (person_a=%s and person_b=%s)",[userid_A, userid_B, userid_B, userid_A])
        conn.commit()   
        
        return True
    
    else:
        print("not friends!")
        return False

# Create a Comment
def addComment(post, user, comment):
    # Gets the user ID
    userId = int(findUser(user))

    # Make the Database Call
    cur.execute("INSERT INTO public.comment(post_id,commenter,message, created_at) VALUES (%s, %s, %s, %s)",[post, userId, comment, curr_time])
    conn.commit()

# Creates a new Group
def newGroup(name, owner):
    message = "Failed to create group"

    # Gets the user ID
    userId = int(findUser(owner))
    if(userId < 0):
        return "Error in getting user"

    # Gets the group id
    groupId = int(findGroup(name))
    if(groupId > 0):
        return "This group name is already taken."
    
    # Creates new Group
    result = groups.newGroup(userId, name)

    return result

# User JOINS the group
def addUserToGroup(username, group_name):  
    message = "Failed to join group"
    user_id = int(findUser(username))
    group_id = int(findGroup(group_name))
    if(user_id > 0 and group_id > 0):
        result = groups.addUserToGroup(user_id, group_id)
        if result == 'SUCCESS':
            message = "You have successfully joined the group"

# User LEAVES the group
def removeUserFromGroup(username, group_name):  
    message = "Failed to leave group" 
    user_id = int(findUser(username))
    group_id = int(findGroup(group_name))
    
    if(user_id > 0 and group_id > 0):
        result =   groups.removeUserFromGroup(user_id, group_id)
        if result == 'SUCCESS':
            message = "You have successfully left the group"

    return message

def getUsersInGroup(group_name):
    try:
        cur.execute("SELECT user_id FROM public.group AS user_group \
                    INNER JOIN public.user_list AS user_list \
                    ON user_group.group_id = user_list.group_id \
                    WHERE user_group.group_name = %s", [group_name])
        rows = cur.fetchall()
        if(rows == None):
           return []

        users = []
        # Store Results
        for row in rows:
            user = row[0]

            users.append(user)

        conn.commit()

        return users
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Cannot get users. Try again")
        conn.rollback() 


def deleteGroupExistence(username, group_name):
    message = "Failed to delete group"

    # Gets the user ID
    userId = int(findUser(username))
    if(userId < 0):
        return "Error in getting user"

    # Gets the group id
    groupId = int(findGroup(group_name))
    if(groupId < 0):
        return "Error in getting group"
    
    # Deletes group
    result = groups.deleteGroupExistence(userId, groupId)
    if result == "SUCCESS":
        print("deleted group ", group_name)

    return result


# Request User to Join Group
def requestUserToGroup(username, group_name):   
    message = "Failed to request user to join group"
    user_id = int(findUser(username))
    group_id = int(findGroup(group_name))

    if(user_id > 0 and group_id > 0):
        result =  groups.requestUserToGroup(user_id, group_id)
        if result == 'SUCCESS':
            message = "You have successfully left the group"

    return message

# Lists all group names the user belongs to
def getGroupNamesOfUser(username):
    user_id = int(findUser(username))
    if(user_id > 0):
        return groups.getGroupNamesOfUser(user_id)
    
# Lists all group names the user belongs to
def getPendingGroupNamesOfUser(username):
    user_id = int(findUser(username))
    if(user_id > 0):
        return groups.getPendingGroupNamesOfUser(user_id)
    
# Look for group via name
def findGroup(groupName):
    try:
        cur.execute( "SELECT group_id FROM public.group WHERE group_name = %s", [groupName] )
        groupId = cur.fetchone()
        conn.commit()

        # checks if group exists
        if(groupId):
            groupId = groupId[0]
            return groupId
        
        else:
            return -1

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("The group search failed. Try again")
        conn.rollback() 

# Look for user via username
def findUser(username):
    try:
        cur.execute( "SELECT user_id FROM public.user WHERE username = %s", [username] )
        userId = cur.fetchone()
        conn.commit()

        # checks if user exists
        if(userId):
            userId = userId[0]
            return userId
        
        else:
            return -1

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("The username search failed. Try again")
        conn.rollback() 

# Look for user via id
def findUserWithID(userID):
    try:
        cur.execute( "SELECT username FROM public.user WHERE user_id = %s", [userID] )
        userId = cur.fetchone()
        conn.commit()

        # checks if user exists
        if(userId):
            userId = userId[0]
            return userId
        
        else:
            return -1

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("The userID search failed. Try again")
        conn.rollback() 

# Get Posts by user
def GetPosts(username):
    user_id = int(findUser(username))
    user_posts = []

    try:
        cur.execute( "SELECT post_id FROM public.post WHERE user_id = %s", [user_id] )
        results = cur.fetchall()
        conn.commit()

        # checks if user exists
        if(results == None):
            return
        
        for result in results:
            user_posts.append(result[0])
        
        return user_posts

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to generate feed. Try again")
        conn.rollback() 

# Get List of Friends
def getFriends(username):
    user_id = findUser(username)
    friends = []

    try:
        cur.execute("SELECT username from public.user u \
                    INNER JOIN public.relation f on f.person_a = u.user_id \
                    WHERE f.person_b = %s and f.relationship = 'FRIEND' \
                    union \
                    SELECT username from public.user u \
                    INNER JOIN public.relation f on f.person_b = u.user_id \
                    WHERE f.person_a = %s and f.relationship = 'FRIEND'",
                    [user_id,user_id] )
        
        results = cur.fetchall()
        conn.commit()

        # checks if friends exists
        if(friends == None):
          return
        
        # adds each username to friends list
        for result in results:
          friends.append(result[0])
        
        return friends

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to get list of friends. Try again")
        conn.rollback() 


# Get List of Requests
def getFriendRequests(username):
    user_id = findUser(username)
    requests = []

    try:
        cur.execute("SELECT username from public.user u \
                    INNER JOIN public.relation f on f.person_a = u.user_id \
                    WHERE f.person_b = %s and f.relationship = 'REQUESTED'",
                    [user_id])
        results = cur.fetchall()
        conn.commit()

        # checks if requests exist
        if(results == None):
          return
        
        # adds each username to friends list
        for result in results:
          requests.append(result[0])
        
        return requests

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to obtain list of friend requests. Try again")
        conn.rollback() 

# Login via username and password
def login(username, password):
    try:
        cur.execute( "SELECT user_id FROM public.user WHERE username = %s and password = %s", [username, password] )
        userId = cur.fetchone()
        conn.commit()

        # checks if user exists
        if(userId):
            userId = userId[0]
            return userId
        
        else:
            return -1

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("The username or password you’ve entered is incorrect. Try again")
        conn.rollback() 