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
    cur.execute("INSERT INTO public.user(full_name,username,password, created_at,updated_at) VALUES (%s, %s,'%s, %s, %s)",[full_name, username, password, curr_time,curr_time])
    conn.commit()

# Submit File
def newChallenge(user, group, title, description):
    # Gets the user ID
    user_id = findUser(user)

    # Gets the group ID
    group_id = findGroup(group)

    # Make the Database Call
    cur.execute("INSERT INTO public.challenge(author, group, title, description, challenge_date) VALUES (%s, %s,'%s, %s, %s)",[user_id, group_id, title, description, curr_time])
    conn.commit()    


# Submit File
def newPost(user, file, challenge_id):
    # Gets the user ID
    userId = findUser(user)

    # Make the Database Call
    cur.execute("INSERT INTO public.post(author,challenge_id,submission,created_at,updated_at) VALUES (%s, %s,'%s, %s, %s)",[userId, challenge_id, file, curr_time,curr_time])
    conn.commit()    

# Request a Friend
def requestFriend(userA, userB):
    relation = "REQUESTED"
    userA = findUser(userA)
    userB = findUser(userB)
    
    # Make the Database Call
    cur.execute("INSERT INTO public.relation(personA,personB,relationship,created_at) VALUES (%s, %s,'%s, %s, %s)",[userA, userB, relation,curr_time])
    conn.commit()  

def getRelationship(userA,userB):
    userA = findUser(userA)
    userB = findUser(userB)

    # Database Call
    cur.execute("SELECT relationship FROM public.relation WHERE personA = %s and personB = %s", [userA,userB] )
    relationship = cur.fetchone()
    conn.commit()

    return relationship

# Add a Friend
def addFriend(userA, userB):
    userA = findUser(userA)
    userB = findUser(userB)
    relationship = getRelationship(userA,userB)

    if relationship == 'FRIENDS':
        return 0
    
    elif relationship == 'REQUESTED':
        # Make the Database Call
        cur.execute("UPDATE public.relation SET relationship='FRIENDS',created_at=%s WHERE userA=%s and userB=%s",[curr_time, userA, userB])
        conn.commit()    
        return 1
    
    # Relationship DOES NOT exist
    else:
        return -1

# Remove a Friend
def removeFriend(userA, userB):
    userA = findUser(userA)
    userB = findUser(userB)
    relationship = getRelationship(userA,userB)

    if relationship == 'FRIENDS':
        # Make the Database Call
        cur.execute("DELETE FROM public.relation WHERE userA=%s and userB=%s",[userA, userB])
        conn.commit()    
        return True
    
    else:
        return False

# Create a Comment
def addComment(post, user, comment):
    # Gets the user ID
    userId = findUser(user)

    # Make the Database Call
    cur.execute("INSERT INTO public.comment(post_id,commenter,message, created_at) VALUES (%s, %s, %s, %s)",[post, userId, comment, curr_time])
    conn.commit()

# Creates a new Group
def newGroup(name, owner):
    # Gets the user ID
    userId = findUser(owner)
    # Make the Database Call
    cur.execute("INSERT INTO public.group(group_name,owner, created_at,updated_at) VALUES (%s, %s, %s, %s)",[name, userId, curr_time,curr_time])

    # Adds owner to the group
    groupId = findGroup(name)
    addUserToGroup(userId, groupId)
    conn.commit()

def addUserToGroup(user, groupName):
    # Gets the user ID and group ID
    userId = findUser(user)
    groupId = findGroup(groupName)
    # Call Database
    cur.execute("INSERT INTO public.user_list(group_id,user_id) VALUES (%s, %s)",[int(groupId), int(userId)])
    conn.commit()

# Lists all group names the user belongs to
def getGroupNamesOfUser(user):
    userId = findUser(user)
    groups = []
    try:
        cur.execute( "SELECT group_name \
                    FROM public.group AS user_group \
                    INNER JOIN public.user_list AS user_list \
                    ON user_group.group_id = user_list.group_id \
                    WHERE user_list.user_id = %s", [int(userId)] )
        rows = cur.fetchall()

        # Store Results
        for row in rows:
            group_name = row[0]
            groups.append(group_name)

        conn.commit()
        return groups

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Cannot display groups. Try again")
        conn.rollback() 

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