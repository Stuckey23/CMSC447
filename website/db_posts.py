import psycopg2     # db library
import datetime     # time zone
import pytz

import chkd_db as db

# Connect to the CHKD Database
curr_time = datetime.datetime.now(pytz.timezone('US/Eastern'))
conn = psycopg2.connect(database="CHKD", user = "postgres", password = "postgres", host = "127.0.0.1", port = "5433")
cur = conn.cursor()

# When finished with db call, close DB connection
def finished():
    conn.close()

# Get List of Posts by CHALLENGE
def getPostsByChallenge(challenge_id):
    submissions = []
    comments = []

    try:
        cur.execute("SELECT p.post_id, author, points, submission \
                    from public.post p  \
                    WHERE p.challenge_id = %s" , [challenge_id])
        allPosts = cur.fetchall()
        conn.commit()

        if(allPosts == None):
           return submissions 

        # Store Result
        for post in allPosts:
            print(post)
            post_id = post[0]
            author_id = post[1]
            points = post[2]
            submission = post[3]
            comments = getCommentsByPost(post_id)    # array where comment[comment_id, commenter, message]

            # stores in submissions array 
            submissions.append([post_id, author_id, points, submission, comments])
        
        # 2d array of post/task submissions and its 2d array of comment info
        return submissions
            
        '''
        Output? 
        comments = getCommentsByPost(post_id)
        submissionFile = File(submission, points, comments)
        newSubmission = Submission(author_id, post_id, submissionFile)
        
        # Add formatted results to list of posts
        #submissions.append(newSubmission)
        '''

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Cannot get list of posts from this challenge. Try again")
        conn.rollback() 


# Get List of CHALLENGES by group
def getChallengesByGroup(group_name):
    group_id = db.findGroup(group_name)
    challenges = []

    try:
        print("gid %s" % group_id)
        cur.execute("SELECT challenge_id, title, description \
                    from public.challenge  \
                    WHERE group_id = %s" , [group_id])
        quests = cur.fetchall()
        conn.commit()

        #return submissions
        if(quests == None):
           return challenges 
        
        else:
            return quests # 2d array returned basically looking like quest[challenge_id, title, description]

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Cannot get list of challenges from this group. Try again")
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
    print("I'm trying sir")
    result = 'FAILED'
    try:
        # See if there is already a reaction by the user to the post
        curr_reaction = getReaction(post_id,reactor_id)
        
        if curr_reaction == None:
            # Make the Database Call
            cur.execute("INSERT INTO public.reaction(post_id, reaction ,reactor,updated_at) VALUES (%s, %s, %s, %s)", \
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
        
            comments = cur.fetchall()
            conn.commit()

            newComments = []
            for comment in comments:
                comment = list(comment)
                comment[1] = db.findUserWithID(comment[1])
                newComments.append(comment)

            
                


            return newComments
            #   Returns 2d array where each row contains
            #   comment_id = row[0]
            #   commenter = row[1]
            #   message = row[2]

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        print("Cannot get list of comments from this post. Try again")
        conn.rollback() 

    return comments