#####################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
import datetime

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass
 
@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form('password') == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
                <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'></input>
                <input type='password' name='password' id='password' placeholder='password'></input>
                <input type='submit' name='submit'></input>
                </form></br>
            <a href='/'>Home</a>
               '''
    email = flask.request.form['email']
    cursor = conn.cursor()
    #check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0] )
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user) #okay login in user
            return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file
        return "<a href='/login'>Try again</a>\
            </br><a href='/register'>or make an account</a>"
            
@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier

@app.route("/register", methods=['GET'])
def register():
    supress = request.values.get("supress")
    print('supress', supress)
    if supress is None:
        return render_template('register.html', supress=None)
    else:
        return render_template('register.html', supress='NotNone')

# this method allows a user to make an account as well as throws and exepction if the email used to make a new account is already being utilized.
@app.route("/register", methods=['POST'])
def register_user():
    
    cursor = conn.cursor()
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    hometown = request.form.get('hometown')
    gender = request.form.get('gender')
    gender = str(gender)
    email=request.form.get('email')
    password=request.form.get('password')
        
    test = isEmailUnique(email)
    if test:
        print(cursor.execute("INSERT INTO Users (first_name, last_name, email, hometown, gender, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')".format(first_name, last_name, email, hometown, gender, password)))
        conn.commit()
            #log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name= first_name, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register', supress='No'))




############################# GETTER FUCNTIONS #####################################

# this function allows for us to access the Users Photos
def getUsersPhotos(UID):
	cursor = conn.cursor()
	cursor.execute("SELECT data_1, UPHID, caption FROM Photos WHERE UID = {0}".format(UID))
	return cursor.fetchall()
    #NOTE return a list of tuples, [(imgdata, pid, caption), ...]
    
# this function allows for us to access the all Photos uploaded.
def getAllPhotos():
    cursor = conn.cursor()
    cursor.execute("SELECT data_1, caption, UPHID FROM Photos")
    return cursor.fetchall()
    
# def getUsersPhotosFromUID(UID):
#     cursor = conn.cursor()
#     cursor.execute("SELECT data_1, AID, UID, caption FROM Albums WHERE UID = '{0}'".format(UID))
#     return cursor.fetchall()

 # this function allows for us to access the Users Album
def getUsersAlbumsFromUID(UID):
    cursor = conn.cursor()
    cursor.execute("SELECT albumname, AID, UID FROM Albums WHERE UID = {0}".format(UID))
    return cursor.fetchall()

def getUserAIDfromUID(UID):
    cursor = conn.cursor()
    cursor.execute("SELECT AID FROM Albums WHERE UID = {0} ".format(UID))
    return cursor.fetchall()

def getUsersPhotosinAlbumfromUID(UID):
    cursor = conn.cursor()
    cursor.execute("SELECT AID, UID FROM Photos".format(UID))
    return cursor.fetchall()

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT UID  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def getUserHometown(UID):
    cursor = conn.cursor()
    cursor.execute("Select hometown From Users WHERE UID = {0}".format(UID))
    return cursor.fetchone()[0]

def getUserfirst_name(UID):
    cursor = conn.cursor()
    cursor.execute("Select first_name From Users WHERE UID = {0}".format(UID))
    return cursor.fetchone()[0]

def getUserlast_name(UID):
    cursor = conn.cursor()
    cursor.execute("Select last_name From Users WHERE UID = '{0}'".format(UID))
    return cursor.fetchone()[0]

def getUserGender(UID):
    cursor = conn.cursor()
    cursor.execute("Select gender From Users WHERE UID = '{0}'".format(UID))
    return cursor.fetchone()[0]

def getUserDOB(UID):
    cursor = conn.cursor()
    cursor.execute("Select DOB from Users WHERE UID = '{0}'".format(UID))
    return cursor.fetchone()[0]

def getUPHID (data_1):
    cursor = conn.cursor()
    cursor.execute("Select UPHID from Photos WHERE data_1 = {0}".format(data_1))
    return cursor.fetchone()[0]

def getCaption(UPHID):
    cursor = conn.cursor()
    cursor.execute("Select caption from Photos WHERE UPHID = {0}".format(UPHID))
    return cursor.fetchall()

def getUPHIDFromUID(UID, AID):
    cursor = conn.cursor()
    cursor.execute("Select UPHID from Photos WHERE UID = {0} AND AID = {1}".format(UID, AID))
    return cursor.fetchall()

def getUsersTags(UID):
    cursor = conn.cursor()
    cursor.execute("Select word from Tags WHERE UID = {0}".format(UID))
    return cursor.fetchall()
    
def getAID(UID):
    cursor = conn.cursor()
    cursor.execute("Select AID from Albums WHERE UID = {0}".format(UID))
    return cursor.fetchone()[0]

def getAlbums(UID):
    cursor = conn.cursor()
    cursor.execute("SELECT AID, ablumname FROM Albums WHERE UID = {0}".format(UID))
    return cursor.fetchall()
    
def getUserPhotos(UID):
    cursor = conn.cursor()
    cursor.execute("SELECT UPHID, data_1, caption FROM Photos WHERE UID = {0}".format(UID))
    return cursor.fetchall()
    
def getGender(UID):
    cursor = conn.cursor()
    cursor.execute("SELECT gender FROM Users WHERE UID ={0}".format(UID))
    return cursor.fetchone()[0]

def getAllComment():
    cursor = conn.cursor()
    cursor.execute("SELECT UPHID, texts, UID, date_left FROM Comments")
    return cursor.fetchall()

#def getPictureComment(UPHID):
#    cursor = conn.cursor()
#    cursor.execute("SELECT texts, caption FROM Comments, Photos WHERE Photos.UPHID = Comments.UPHID ".format(UPHID))
#    return cursor.fetchall()
    
#def getPictureComment(UID):
#    cursor = conn.cursor()
#    cursor.execute("SELECT texts, UPHID FROM Comments WHERE Photos.UID = Comments.UID ".format(UPHID))
#    return cursor.fetchall()


#################################### ROUTING FUNCTIONS #####################################

# this method maps to the proile page of a user.
@app.route('/profile')
@flask_login.login_required
def protected():
    UID = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", hometown=getUserHometown(UID), DOB=getUserDOB(UID),  gender=getUserGender(UID), first_name=getUserfirst_name(UID), last_name=getUserlast_name(UID), photos = getAllPhotos(),base64=base64)
    
    
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', '', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# this method routes to the upload page where a user can upload a photo.
@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		UID = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (data_1, UID, caption) VALUES (%s, %s, %s )''', (photo_data, UID, caption))
		conn.commit()
		return render_template('photos.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(UID), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code



# this methods connects us to our create album page. (GET)
@app.route('/album', methods = ['GET'])
@flask_login.login_required
def create_album():
    supress = request.values.get("supress")
    if supress:
        return render_template('/album.html')
    else:
        return render_template('/album.html',supress = 'True')
        
# this methods connects us to our create album page. (POST)
@app.route('/album', methods=['POST'])
def albumCreated():
    try:
#    # in this method we need to include all of the attributes that are assigned to albums
#    if request.method == 'POST':
        createAlbum = request.form.get('createAlbum')
        picInAlbum = request.form.get('picInAlbum')
        UID = getUserIdFromEmail(flask_login.current_user.id)
        AID = getUserAIDfromUID(UID)
        DOC = datetime.datetime.now().date()
        DOC1 = DOC.strftime('%Y-%m-%d %H:%M:%S')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Photos (UID, AID, data_1) VALUES ({0}, {1}, '{2}')".format(UID, AID, picInAlbum))
        cursor.execute("INSERT INTO Albums (UID, albumname, DOC) VALUES ({0}, '{1}', '{2}')".format(UID, createAlbum, DOC1))
        conn.commit()
    except:
        return flask.redirect(flask.url_for('album.html', supress = 'No', name=flask_login.current_user.id, album=AID, base64=base64))
        
@app.route('/albumPOST', methods=['POST'])
def albumPOST():
        UID = getUserIdFromEmail(flask_login.current_user.id)
        DOC = datetime.datetime.now().date()

        DOC1 = DOC.strftime('%Y-%m-%d %H:%M:%S')
        print(UID)
        albumNAME = request.form.get('createAlbum')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Albums (UID, albumname, DOC) VALUES ({0}, '{1}', '{2}')".format(UID, albumNAME, DOC1))
        conn.commit()
        return render_template('albumPOST.html', album = getUsersAlbumsFromUID(UID))
             
              
    # cursor = conn.cursor()
    # cursor.execute("SELECT albumname, AID, UID FROM Albums WHERE UID = '{0}'".format(UID))
    # return cursor.fetchall()

## this method connects us to our search page.
#@app.route('/search', methods = ['GET'])
#def search():
#    return render_template('search.html')

# this method connects us to our page that allows us to create tags.
@app.route('/tag', methods = ['GET'])
@flask_login.login_required
def tag():
    return render_template('tag.html')
    
# this method connects us to our page that allows us to look at tags.
@app.route('/viewTag', methods = ['GET'])
@flask_login.login_required
def viewTag():
    return render_template('viewTag.html')
    
# this method connects us to our page that allows us to look at our tagged photos.
@app.route('/taggedPhotos', methods = ['GET'])
def taggedPhotos():
    return render_template('taggedPhotos.html')

# this method connects us to our page that allows us to remove a tag from a selected picture.
@app.route('/removedTags', methods = ['GET'])
@flask_login.login_required
def removedTag():
    return render_template('removedTags.html')

# this method connects us to our page that allows us search for tags and displays photos with searched tag.
@app.route('/searchTagged', methods = ['GET'])
def searchTagged():
    return render_template('searchTagged.html')
    # TODO: we are going to have to make another error throwing page that says there are no photos for a searched tag.

    
# this method connects us to our page that lets us like pictures.
@app.route('/likePhoto', methods = ['GET'])
@flask_login.login_required
def likePhoto():
  comments = getAllComment()
  photos = getAllPhotos()
  likes = []
  for l in likes:
    UPHID = request.form.get('UPHID')
    like = request.form.get('like')
    likes.append(like)
  return render_template('likePhoto.html', photos = photos, base64 = base64, likes = likes, comments = comments)
@app.route('/likePhoto', methods = ['POST'])
def likedPhotos():
  comments = getAllComment()
  UPHID = request.form.get('UPHID')
  UID = getUserIdFromEmail(flask_login.current_user.id)
  cursor = conn.cursor()
  cursor.execute("INSERT INTO Likes (UID,UPHID) VALUES ({0}, {1})".format(UID,UPHID))
  conn.commit()
  return flask.redirect(flask.url_for('yourLikedPhotos'))
#this method connects us to our page that shows all of the picture that have been liked.
@app.route('/listOfLikes', methods = ['GET'])
@flask_login.login_required
def yourLikedPhotos():
  comments = getAllComment()
  photos= getAllPhotos()
  UID = getUserIdFromEmail(flask_login.current_user.id)
  UPHID = request.form.get('UPHID')
  cursor = conn.cursor()
  cursor.execute("INSERT INTO Likes (UID,UPHID) VALUES ({0}, {1})".format(UID,UPHID))
  conn.commit()
  return render_template('listOfLikes.html',photos=photos, base64=base64, comments=comments)

# this method connects us to our page that shows us our friends and friend suggestions.
@app.route('/friends', methods = ['GET'])
@flask_login.login_required
def addFriends():
    return render_template('friends.html')

# this method connects us to our page that shows all of the picture that have been liked.
# @app.route('/listOfLikes', methods = ['GET'])
# @flask_login.login_required
# def likedPhotos():
#     return render_template('listOfLikes.html')

@app.route('/comment', methods = ['GET'])
def getComment():
  supress = request.args.get("supress")
  print(supress)
  if supress == 'True':
    UID = getUserIdFromEmail(flask_login.current_user.id)
    text = getAllComment(UID)  # trying to grab the text from the user here
    print(text)
    return render_template('/comment.html', photos=getAllPhotos(), base64=base64, text=text, flag = '123')
  else:
    return render_template('/comment.html', photos=getAllPhotos(), base64=base64, flag = None)

# this method connects us to browse the comment page for everyone to see.
@app.route('/comment', methods = ['POST'])
def postComment():
#  try:
    texts = request.form.get('comment')
    UID = getUserIdFromEmail(flask_login.current_user.id)
    date = datetime.datetime.now().date()
    date_left = date.strftime('%Y-%m-%d %H:%M:%S')
    UPHID = request.form.get('UPHID')
    print('tests', UPHID, 'texts')
#    print(texts, UID, date_left, UPHID)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Comments (texts, UID, date_left, UPHID) VALUES ('{0}', {1}, '{2}', {3})".format(texts, UID, date_left, UPHID))
    conn.commit()
    return flask.redirect(flask.url_for('showAllComments'))
#  except:
#    print('we have some error')
#    return flask.redirect(flask.url_for('getComment', supress = 'True'))
# def getCommentsByUPHID(UPHID):
#     cursor = conn.cursor()
#     cursor.execute("SELECT texts, caption FROM Comments, Photos WHERE Photos.UPHID = Comments.UPHID ".format(UPHID))
#     return cursor.fetchall()
    
def getCommentsn():
    cursor = conn.cursor()
    cursor.execute("SELECT texts, UPHID FROM Comments ".format())
    return cursor.fetchall()

@app.route('/allComments', methods=['GET'])
def showAllComments():
    photos = getAllPhotos()
    commentslist = []
    for p in photos:
        UPHID = request.form.get('UPHID')
        comments = getCommentsn()
        commentslist.append(comments)
        #   get comments for every photo
        # SQL: for loop : for p in photos
        #    query comment using pid
        #   get a list of tuple for this photo
        # do untill get all comments for every photo
        # pass to html
        UID = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('/allComments.html', photos=photos, base64=base64, commentslist=commentslist)

@app.route('/allComments', methods=['POST'])
def allComments():
    texts = request.form.get('text')
    UID = getUserIdFromEmail(flask_login.current_user.id)
    date = datetime.datetime.now().date()
    date_left = date.strftime('%Y-%m-%d %H:%M:%S')
    UPHID = request.form.get('UPHID')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Comments (texts, UID, date_left, UPHID) VALUES ('{0}', {1}, '{2}', {3})".format(texts, UID, date_left, UPHID))
    conn.commit()
    return render_template('allComments.html', photos=getAllPhotos(), base64=base64, texts=texts)




# # this method connects us to browse the pictures that were commented.
# @app.route('/commentAction', methods = ['GET'])
# @flask_login.login_required
# def commentAction():
#     return render_template('commentAction.html')


# TODO: REDOOOOOOOOOOOOOOOOOOOOOOOO to connect to the correct page!! We need to connect this to the album page after a user selects one of their albums, they can view the photos inside.
## this method connects us to browse albums page.
#@app.route('/displayCreatedAlbums', methods = ['GET'])
#@flask_login.login_required
#def browse_albums():
#    return render_template('displayCreatedAlbums.html')

# this method connects us to browse which pictures we would like to add to an Album.

# @app.route('/toDelete/<UPHID>', methods=['POST', 'GET'])
# @flask_login.login_required
# def delete_picture(UPHID):
#     UID = getUserIdFromEmail(flask_login.current_user.id)
#     print(UID)
#     cursor.execute('''DELETE FROM Photos WHERE UID = {0} AND UPHID = {1}  '''.format(UID, UPHID))
#     return render_template('hello.html', name = flask_login.current_user.id, pics = UPHID, messaged = "Photo was Successfully Deleted!" ,base64=base64)

# @app.route("/deletePhoto", methods = ["GET"])
# @flask_login.login_required
# def willDelete():
#     UID = getUserIdFromEmail(flask_login.current_user.id)
#     photos = getUserPhotos(UID)
#     return render_template('deletePhoto.html', photos = photos, base64=base64)


# cursor.execute("INSERT INTO Likes (UID,UPHID) VALUES ({0}, {1})".format(UID,UPHID))

@app.route('/willAddto/<AID>', methods=['GET', 'POST'])
@flask_login.login_required
def add_picture(AID):
    UID = getUserIdFromEmail(flask_login.current_user.id)
    AID = getUserAIDfromUID(UID)
    UPHID = getUPHIDFromUID(UID, AID)
    cursor.execute("INSERT INTO Photos (AID, UID, UPHID) VALUES ({0}, {1}, {2} ) ".format(AID, UID, UPHID))
    cursor.execute("INSERT INTO Albums (AID, UID) VALUES ({0}, {1} ) ".format(AID, UID))
    return render_template('hello.html', name = flask_login.current_user.id, messagea = "Album successfully Added!", base64=base64)


@app.route('/selectPhotosforAlbum', methods = ['GET'])
@flask_login.login_required
def whichPicforAlbum():
    UID = getUserIdFromEmail(flask_login.current_user.id)
    photos = getUsersPhotos(UID)
    # UPHID = request.form.get('UPHID')
    return render_template('selectPhotosforAlbum.html', album = getUsersAlbumsFromUID(UID), photos = photos, base64 = base64) #album = albumname, AID, UID
    
# this method connects us to our browse albums page.
@app.route('/myAlbums', methods = ['GET'])
@flask_login.login_required
def viewMyAlbums():
    UID = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('myAlbums.html', albums = getUsersAlbumsFromUID(UID), photoExist = getUsersPhotosinAlbumfromUID(UID))
    
# this method connects us to our browse photos page.
@app.route('/photos', methods = ['GET'])
def browse_photos():
    return render_template('photos.html', photos=getAllPhotos(), base64=base64)


# this method connects us to our browse photos page.
@app.route('/hello', methods = ['GET'])
@flask_login.login_required
def home_button():
    return render_template('hello.html',comments=getAllComment())


# functions to delete photos
@app.route('/toDelete/<UPHID>', methods=['POST', 'GET'])
@flask_login.login_required
def delete_picture(UPHID):
    UID = getUserIdFromEmail(flask_login.current_user.id)
    print(UID)
    cursor.execute('''DELETE FROM Photos WHERE UID = {0} AND UPHID = {1}  '''.format(UID, UPHID))
    return render_template('hello.html', name = flask_login.current_user.id, pics = UPHID, messaged = "Photo was Successfully Deleted!" ,base64=base64)

@app.route("/deletePhoto", methods = ["GET"])
@flask_login.login_required
def willDelete():
    UID = getUserIdFromEmail(flask_login.current_user.id)
    photos = getUserPhotos(UID)
    return render_template('deletePhoto.html', photos = photos, base64=base64)


# functions to delete albums

def getUsersPhotosinAlbumfromAID(AID):
    cursor = conn.cursor()
    cursor.execute("SELECT data_1 FROM Photos WHERE AID = {0}".format(AID))
    return cursor.fetchall()


@app.route('/willDelete/<AID>', methods=['POST', 'GET'])
@flask_login.login_required
def delete_album(AID):
    UID = getUserIdFromEmail(flask_login.current_user.id)
    # UPHID = getUPHIDFromUID(UID, AID)
    # photosinalbum = getUsersPhotosinAlbumfromAID(AID)
    cursor.execute("DELETE FROM Albums WHERE UID = {0} AND AID = {1}".format(UID, AID))
    # if photosinalbum:
    #     cursor.execute("DELETE CASCADE FROM Photos WHERE AID = {0} AND UPHID = {1}").format(AID, UPHID)
    return render_template('hello.html', name = flask_login.current_user.id, messaged = "Album was successfully deleted!" ,base64=base64)

@app.route("/deleteAlbum", methods = ["GET"])
@flask_login.login_required
def album2Delete():
    UID = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('deleteAlbum.html', albums = getUsersAlbumsFromUID(UID), base64=base64)


@app.route('/willDisplay/<AID>', methods=['POST', 'GET'])
@flask_login.login_required
def display_album(AID):
    UID = getUserIdFromEmail(flask_login.current_user.id)
    # UPHID = getUPHIDFromUID(UID, AID)
    # photosinalbum = getUsersPhotosinAlbumfromAID(AID)
    cursor.execute("SELECT data_1 FROM Photos WHERE UID = {0} AND AID = {1}".format(UID, AID))
    # if photosinalbum:
    #     cursor.execute("DELETE CASCADE FROM Photos WHERE AID = {0} AND UPHID = {1}").format(AID, UPHID)
    return render_template('displayCreatedAlbum.html', name = flask_login.current_user.id, base64=base64, photoExist = getUsersPhotosinAlbumfromUID(UID))

@app.route("/myAlbums", methods = ["GET"])
@flask_login.login_required
def album2Display():
    UID = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('myAlbums.html', albums = getUsersAlbumsFromUID(UID), base64=base64)

# AName AID UID
#default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welcome to Photoshare',photos=getAllPhotos(),base64=base64)
    
if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)


