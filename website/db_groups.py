import psycopg2     # db library
import datetime     # time zone
import pytz
from sqlalchemy import DECIMAL         # time zone
from decimal import Decimal

import chkd_db as db

# Connect to the CHKD Database
curr_time = datetime.datetime.now(pytz.timezone('US/Eastern'))
conn = psycopg2.connect(database="CHKD", user = "postgres", password = "postgres", host = "127.0.0.1", port = "5432")
cur = conn.cursor()

# When finished with db call, close DB connection
def finished():
    conn.close()


# Creates a new Group
def newGroup(user_id, group_name):
    result = 'Failed to Create Group'
    try:
       # Make the Database Call
        cur.execute("INSERT INTO public.group(group_name,owner, created_at,updated_at) \
                    VALUES (%s, %s, %s, %s)", \
                    [group_name, user_id, curr_time,curr_time])
        conn.commit()
        # Adds owner to the group
        groupId = int(db.findGroup(group_name))
        addOwnerToGroup(user_id, groupId)
        result = 'SUCCESS'
   
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to create group. Try again")
        conn.rollback()

    return result


# Request Member to Join Group
def requestUserToGroup(user_id, group_id,relationship):
    # No requests and not already part of the group
    if(relationship == None):
        relation = "REQUESTED"
        # Make the Database Call
        cur.execute("INSERT INTO public.user_list(group_id,user_id,group_relation) VALUES (%s, %s,%s)",[group_id,user_id, relation])
        conn.commit()
        return 'SUCCESS'
    
    # Failed to send request
    return 'FAILED'


# Accept Group Request
def acceptGroupRequest(user_id, group_id,relationship):
    # Request to Member
    if relationship == 'REQUESTED':
        if(user_id > 0 and group_id > 0):
            cur.execute("UPDATE public.user_list SET group_relation='MEMBER' WHERE user_id=%s and group_id=%s",[user_id, group_id])
            conn.commit()    
            return 'SUCCESS'

    # Failed to accept
    return 'FAILED'
    
# Decline Group Request
def declineGroupRequest(user_id, group_id,relationship):
    if relationship == 'REQUESTED':
        if(user_id > 0 and group_id > 0):
            cur.execute("DELETE FROM public.user_list WHERE user_id=%s and group_id=%s",[user_id, group_id])
            conn.commit()    
            return 'SUCCESS'
    
    # Failed to decline
    return 'FAILED'

# Leave Group
def removeUserFromGroup(userId, groupId):   
    # Call Database
    cur.execute("DELETE FROM public.user_list WHERE user_id = %s and group_id = %s", [userId, groupId])
    conn.commit()

    return 'SUCCESS'

def addOwnerToGroup(userId, groupId):  
    relation = 'MEMBER' 
    # Call Database
    cur.execute("INSERT INTO public.user_list(group_id,user_id,group_relation) VALUES (%s, %s,%s)",[groupId,userId, relation])
    conn.commit()
    return 'SUCCESS'

def addUserToGroup(userId, groupId):  
    relation = 'MEMBER' 
    # Call Database
    cur.execute("UPDATE public.user_list SET group_relation=%s WHERE user_id=%s and group_id=%s",[relation,userId, groupId])
    conn.commit()
    return 'SUCCESS'


def getGroupRelationship(user_id,group_id):
    # Database Call
    cur.execute("SELECT group_relation FROM public.user_list WHERE user_id = %s and group_id = %s", [user_id, group_id] )
    relationship = cur.fetchone()
    conn.commit()

    # checks if relationship exists
    if(relationship):
        relationship = relationship[0]
        return relationship
    
    else:
        return None           
    
# Get List of Groups User Belongs to
def getGroupNamesOfUser(user_id):
    groups = []
    relation = 'MEMBER'
    try:
        cur.execute( "SELECT group_name \
                    FROM public.group AS user_group \
                    INNER JOIN public.user_list AS user_list \
                    ON user_group.group_id = user_list.group_id \
                    WHERE user_list.user_id = %s and (group_relation = %s or group_relation = 'OWNER'", \
                    [user_id,relation] )

        rows = cur.fetchall()

        if(rows == None):
           return groups 

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

# Owner Deletes Group
def deleteGroupExistence(userId, groupId):   

    # Check if user is the OWNER
    owner = getGroupOwner(groupId)

    if(owner == userId):
        # Delete Members from Group and then actual group
        cur.execute("DELETE FROM public.group WHERE group_id = %s", [groupId])
        conn.commit
        return 'SUCCESS'
    
    else:
        return 'FAILED'
    
# Owner Deletes Challenge
def deleteChallenge(userId, groupId, challengeId):   

    # Check if user is the OWNER
    owner = getGroupOwner(groupId)

    if(owner == userId):
        cur.execute("DELETE FROM public.challenge WHERE group_id = %s", [challengeId, challengeId])
        conn.commit
        return 'SUCCESS'

    return 'FAILED'
    

# Get the owner of the group by group id
def getGroupOwner(groupId):   
    try:
        cur.execute("SELECT owner FROM public.group WHERE group_id = %s", [groupId])
        owner = cur.fetchone()
        conn.commit()

        if(owner):
            owner = owner[0]
            return owner
        
        else:
            return None        
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to get owner. Try again")
        conn.rollback()
