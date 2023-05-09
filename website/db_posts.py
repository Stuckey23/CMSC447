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


# Get List of Posts by CHALLENGE
def getPostsByChallenge(challenge):

    submissions = []
    comments = []

    try:
        cur.execute("SELECT p.post_id, author, points, submission \
                    from public.post p  \
                    WHERE p.challenge_id = %s" , [challenge])
        allPosts = cur.fetchall()

        if(allPosts == None):
           return submissions 

        # Store Result
        for post in allPosts:
            post_id = post[0]
            author_id = post[1]
            points = post[2]
            submission = post[3]
            
            '''
            comments = getCommentsByPost(post_id)
            submissionFile = File(submission, points, comments)
            newSubmission = Submission(author_id, post_id, submissionFile)
            '''
            # Add formatted results to list of posts
            submissions.append(newSubmission)

        conn.commit()
        return submissions

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Cannot get list of posts from this challenge. Try again")
        conn.rollback() 
  
def getReaction(post_id, reactor_id):
    try:
        # Make the Database Call
        cur.execute("SELECT reaction FROM public.reaction WHERE post_id = %s and reactor = %s", [post_id,reactor_id])
        conn.commit()
        reaction = cur.fetchone()
        conn.commit()

        if(reaction):
            reaction = reaction[0]
            return reaction
        
        else:
            return None     

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to get reaction from post. Try again")
        conn.rollback()    

# UPVOTE or DOWNVOTE Post
def reactToPost(post_id, reactor_id,reaction):
    result = 'FAILED'
    try:
        # See if there is already a reaction by the user to the post
        curr_reaction = getReaction(post_id,reactor_id)
        
        if curr_reaction == None:
            # Make the Database Call
            cur.execute("INSERT INTO public.reaction(post_id, reaction ,reactor,updated_at) VALUES (%s, %s,%s, %s, %s)", \
                        [post_id, reaction, reactor_id, curr_time])
            conn.commit()

            # Update Points on Post
            updatePoints(post_id)

            # DONE
            result = 'SUCCESS'

        # User has already reacted to post
        else:
             # Update Points on Post
            cur.execute("UPDATE public.reaction SET reaction = %s WHERE post_id = %s", [reaction, post_id])
            conn.commit()

            # Update Points on Post
            updatePoints(post_id)

            # DONE
            result = 'SUCCESS'

   
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to upvote post. Try again")
        conn.rollback()

    # Get out...
    return result

def updatePoints(post_id):
    result = 'FAILED"'
    try:
        # Get sum of reactions to post
        cur.execute("SELECT SUM(reaction) FROM public.reaction WHERE post_id = %s", [post_id])
        points = cur.fetchone()

        if(points):
            points = int(points[0])

        else:
            points = 0     
        
        # Actually update the points on the post
        cur.execute("UPDATE public.post SET points = %s WHERE post_id = %s", [points, post_id])
        conn.commit()

        # DONE
        result = 'SUCCESS'

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to update points on post. Try again")
        conn.rollback()
    
    return result


# Create a Comment
def insertComment(post_id, user_id, comment):
    try:
        # Make the Database Call
        cur.execute("INSERT INTO public.comment(post_id,commenter,message, created_at) VALUES (%s, %s, %s, %s)",[post_id, user_id, comment, curr_time])
        conn.commit()

        # DONE
        return 'SUCCESS'

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to upvote post. Try again")
        conn.rollback()
        return 'FAILED'

# Create/Add new challenge
def addChallenge(user_id, group_id, title, description):
    try:
        # Make the Database Call
        cur.execute("INSERT INTO public.challenge (author,description, group_id, challenge_date,title) \
                    VALUES (%s, %s,%s, %s, %s)", [user_id, description, group_id, curr_time, title])
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to create new challenge. Try again")
        conn.rollback()

# Remove Posts 
def removePost(post_id):
    try:
        # Make the Database Call
        cur.execute("DELETE FROM public.post WHERE post_id=%s",[post_id])
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to remove post. Try again")
        conn.rollback()

# Remove Quest 
def removeChallenge(challenge_id):
    try:
        # Make the Database Call
        cur.execute("DELETE FROM public.challenge WHERE challenge_id=%s",[challenge_id])
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Failed to remove challenge. Try again")
        conn.rollback()

def getCommentsByPost(post_id):
    comments = []
    try :
            cur.execute("select comment_id, commenter, message \
                    from public.comment c \
                    where c.post_id = %s", [post_id])
        
            rows = cur.fetchall()
            conn.commit()

            if(rows == None):
                return comments 

            # Store Results
            for row in rows:
                comment_id = row[0]
                commenter = row[1]
                message = row[3]

                # Add formatted results to list of posts
                newComment = Comment(comment_id, commenter, message)
                comments.append(newComment)

            return comments

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Cannot get list of comments from this post. Try again")
        conn.rollback() 

    return comments