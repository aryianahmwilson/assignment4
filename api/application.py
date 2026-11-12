from flask import Flask, request, jsonify
from flask_cors import CORS

import flask
from flask import session

import secrets
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, ForeignKey, String

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.secret_key = secrets.token_hex() 

UPLOAD_FOLDER = 'static/images/photos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# SQLite Database creation
Base = declarative_base()

db_name = os.getenv("PHOTO_PORTAL_DB","photosdata.db")
db_url = "sqlite:///" + db_name
engine = create_engine(db_url, future=True, connect_args={'check_same_thread': False})

DBSession = sessionmaker(bind=engine)

# Requirement 1.1
# Add SQLAlchemy object to represent Admin User (refer assignment3)
class AdminUser(Base):
    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)

    def __repr__(self):
        return "<AdminUser(username='%s', password='%s')>" % (
            self.username, self.password)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Requirement 2.1
# Add SQLAlchemy object to represent General User (refer assignment3)
class GeneralUser(Base):
    __tablename__ = 'general'

    id = Column(Integer, primary_key=True)
    gmail = Column(String)

    def __repr__(self):
        return "<GeneralUser(gmail='%s')>" % (
            self.gmail)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Requirement 3.1
# Add SQLAlchemy object to store photos; Add a column to store photo comments 
class Photos(Base):
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    date_taken = Column(String)
    tags = Column(String)
    comments = Column(String)

    def __repr__(self):
        return "<Photos(name='%s', date_taken='%s', tags='%s', comments='%s')>" % (
            self.name, self.date_taken, self.tags, self.comments)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


Base.metadata.create_all(engine)


# Requirement 3.4
@app.route("/api/photos/<photo_name>/comments", methods=["GET"])
def get_photo_comments(photo_name):

   dbsession = DBSession()

   photo = dbsession.query(Photos).filter_by(name=photo_name).first()

   comments = ""

   if photo != None:
       comments = photo.comments

   dbsession.close()
  
   return jsonify({"comments": comments})


# Requirement 3.3: Query the database to return photo metadata (date_taken and tags) for all photos
@app.route("/api/photos", methods=["GET"])
def get_photos():

    dbsession = DBSession()

    #get list of photo objects
    photos = dbsession.query(Photos)

    photo_dicts = []

    for photo in photos:
        photo_dicts.append(photo.as_dict())

    dbsession.close()

    return jsonify({"photos": photo_dicts})


# Requirement 5 -- Add search functionality - Refer to your assignment2 implementation
@app.route("/api/search", methods=["POST"])
def search():

    data = request.get_json()
    searchInput = data.get("query").strip()
    searchSelect = data.get("type")

    matchingPhotos_dict = []

    dbsession = DBSession()

    photos = dbsession.query(Photos)

    for photo in photos:
        if searchSelect == "Name" and searchInput in photo.name:
             matchingPhotos_dict.append(photo.as_dict())
        elif searchSelect == "Date" and searchInput == photo.date_taken:
             matchingPhotos_dict.append(photo.as_dict())
        elif searchSelect == "Tags" and searchInput in photo.tags:
             matchingPhotos_dict.append(photo.as_dict())

    dbsession.close()

   
    return jsonify({"results": matchingPhotos_dict})


@app.route('/api/upload', methods=['POST'])
def upload_photo():
    file = request.files.get('photo_file')
    date_taken = request.form.get('date_taken')
    tags = request.form.get('tags')
    comments = request.form.get('comments')

    # Requirement 3.2

    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    dbsession = DBSession()

    #store photo in database
    photo = Photos(name=file.filename, date_taken=date_taken, tags=tags, comments=comments)

    dbsession.add(photo)
    dbsession.commit()
    dbsession.close()

    # You’d normally save metadata to DB here
    return jsonify({
        'name': file.filename,
        'date_taken': date_taken,
        'tags': tags
    })

# -- Admin user -- 

# Requirement 1.2 - Add a POST call to register an admin user
@app.route("/api/admin", methods=["POST"])
def admin():
    dbsession = DBSession()

    #get new admin's username and password from JSON object
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    #create a new admin object
    admin_user = AdminUser(username=username, password=password)

    dbsession.add(admin_user)
    dbsession.commit()
    dbsession.close()

    return jsonify({"message": "Success", "username": username})


# Requirement 1.3 - Add a GET call to get all registered admin users
@app.route("/api/admin", methods=["GET"])
def get_admins():

    dbsession = DBSession()

    #get all registered admin objects
    admins = dbsession.query(AdminUser)

    admin_dict_list = []

    for admin in admins:

        #add admin dictionaries to admin_dict_list
        admin_dict_list.append(admin.as_dict())

    dbsession.close()

    return jsonify({"admins": admin_dict_list})

# Requirement 1.4 - Complete the adminlogin implementation
@app.route("/api/adminlogin", methods=["POST"])
def admin_login():
    data = request.get_json()
    print("Received:", data)
    username = data.get("name")
    password = data.get("password")
    # Query database to check if username/password exists or  not
    # Replace the below if check with database query

    dbsession = DBSession()

    database_login = dbsession.query(AdminUser).filter_by(password=password, username=username).first()

    dbsession.close()

    if database_login != None:
        flask.session["username"] = username
        return jsonify({"message": "Success", "username": username})
    else:
        return jsonify({"message": "NotFound", "username": username})

# -- General user --

# Requirement 2.2 - Add a POST call to register a general user
@app.route("/api/generaluser", methods=["POST"])
def general():

    dbsession = DBSession()

    #get new general user gmail from JSON object
    data = request.get_json()
    gmail = data.get("gmail")

    #create new general user object 
    general_user = GeneralUser(gmail=gmail)

    dbsession.add(general_user)
    dbsession.commit()
    dbsession.close()

    return jsonify({"message": "Success", "gmail": gmail})



# Requirement 2.3 - Add a GET call to get all registered general users
@app.route("/api/generaluser", methods=["GET"])
def get_general():

    dbsession = DBSession()

    generalUsers = dbsession.query(GeneralUser)

    generalUsers_dict = []

    for user in generalUsers:
        generalUsers_dict.append(user.as_dict())

    dbsession.close()

    return jsonify({"General Users": generalUsers_dict})



# Requirement 2.4 - Complete the generaluserlogin implementation
@app.route("/api/generaluserlogin", methods=["POST"])
def generaluser_login():
    data = request.get_json()
    print("Received:", data)
    username = data.get("gmail")
    # Query database to check if username/password exists or  not
    # Replace the below if check with database query
    # If the generaluser is not present, return NotFound

    dbsession = DBSession()

    database_login = dbsession.query(GeneralUser).filter_by(gmail=username).first()

    dbsession.close()

    if database_login != None:
        flask.session["username"] = username
        return jsonify({"message": "Success", "username": username})
    else:
        return jsonify({"message": "NotFound"})

# Requirement 2.3



@app.route("/api/logout",methods=['POST'])
def logout():
    data = request.get_json()
    print("Received:", data)
    username = data.get("userName")
    user_type = "admin"
    if "gmail.com" in username:
        user_type = "general"

    flask.session.clear()
    return jsonify({"message": "Success", "usertype": user_type})


if __name__ == "__main__":

    app.debug = False
    #app.logger.info('Portal started...')
    app.run(host='0.0.0.0', port=5000)
