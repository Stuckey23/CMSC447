import psycopg2     # db library
import datetime     # time zone
import pytz
from sqlalchemy import DECIMAL         # time zone
from decimal import Decimal

import chkd_db as db

# Connect to the CHKD Database
curr_time = datetime.datetime.now(pytz.timezone('US/Eastern'))
conn = psycopg2.connect(database="CHKD", user = "postgres", password = "postgres", host = "127.0.0.1", port = "5433")
cur = conn.cursor()

# When finished with db call, close DB connection
def finished():
    conn.close()

# Add a Friend
def addFriend(userA, userB):

    relationship = db.getRelationship(userA,userB)

    if relationship == 'FRIEND':
        return 'You are already friends with this user.'
    
    elif relationship == 'REQUESTED':
        # Make the Database Calls
        userid_A = int(db.findUser(userA))
        userid_B = int(db.findUser(userB))
        cur.execute("UPDATE public.relation SET relationship='FRIEND',created_at=%s WHERE person_a=%s and person_b=%s",[curr_time, userid_A, userid_B])
        conn.commit()    
        return 'You have successfully added ' + userB
    
    # Relationship DOES NOT exist
    else:
        return 'FAILED to add friend'
    

# Request a Friend
def requestFriend(userA, userB):
    relationship = db.getRelationship(userA,userB)

    if(relationship == None):
        userA = int(db.findUser(userA))
        userB = int(db.findUser(userB))
        relation = "REQUESTED"
        # Make the Database Call
        cur.execute("INSERT INTO public.relation(person_a,person_b,relationship,created_at) VALUES (%s, %s,%s, %s)",\
                    [userA, userB, relation,curr_time])
        conn.commit()

        return 'SUCCESS'   

    elif relationship == 'FRIEND': 
        return 'You already are friends with this user.'

    elif relationship == 'REQUESTED':
        return "You have already requested to be friends with this user."

    # Default Result
    return 'Request failed.' 