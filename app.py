from flask import Flask, render_template
from flask_cors import CORS
import cv2
import numpy as np
import face_recognition
import os
import datetime
import mysql.connector
import glob

app = Flask(__name__)
CORS(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

path = 'imageAttendance'  # folder where all the images of registered students are saved
images = []
classnames = []
classUniqId = []  # List that stores Unique Id of student
classname = []  # List that stores Names of Student
myList = os.listdir(path)

for cls in myList:
    curImg = cv2.imread(f'{path}/{cls}')
    images.append(curImg)
    classnames.append(os.path.splitext(cls)[0])

for name in classnames:
    data = name.split(" ", 1)
    classUniqId.append(data[0])  # separating id and name from photo name
    classname.append(data[1])


def markAttendance(name):  # Function to mark attendance in database
    conn = mysql.connector.connect(host="localhost", user='root', passwd='', database="mysql")  # connecting to MySql
    cursor = conn.cursor()
    nowd = datetime.datetime.now()  # recording the current time
    dtStringY = nowd.strftime("%D %H:%M:%S")
    dtString = dtStringY.split(" ")  # splitting the string
    sql = ("INSERT INTO attendance (Name, Date, Time) "  # Inserting date time and name in sql database
           "VALUES (%s,%s,%s)")
    d = (name, dtString[0], dtString[1])
    cursor.execute(sql, d)
    conn.commit()


def getDetails(name):  # Function to fetch the details from database
    mydb = mysql.connector.connect(host="localhost", user="root", passwd="", database="studentdb")  # connecting to database
    mycursor = mydb.cursor()
    mycursor.execute("Select * from studentdetails")
    myresult = mycursor.fetchall()  # fetching all rows of the table
    for row in myresult:
        if name in row[1]:  # if name is in row then return that row
            return row


encodeListKnown = []  # List of List to store the encoding values
with open("encoding.txt", "r") as f:  # Reading the encoding text file
    while True:
        lines = f.readline()
        if lines == '':
            break
        encode = []
        encode.append(float(lines))
        for i in range(127):
            lines = f.readline()
            encode.append(float(lines))
        encodeListKnown.append(encode)


@app.route("/")
def hello_world():
    while True:
        row = None
        img_dir = 'uploads'  # Folder where the Live Scanned Picture will get uploaded
        data_path = os.path.join(img_dir, '*g')
        files = glob.glob(data_path)

        if not files:
            print("No image found in uploads folder.")
            return render_template("NoRecord.html")

        for i in files:
            img = cv2.imread(i)  # reading the image
            if img is None:
                print(f"Unable to read image: {i}")
                return render_template("NoRecord.html")

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurr = face_recognition.face_locations(imgS)
        encodeCurr = face_recognition.face_encodings(imgS, faceCurr)

        if not encodeCurr:
            print("No face found in the uploaded image.")
            return render_template("NoRecord.html")

        for enf, floc in zip(encodeCurr, faceCurr):
            matches = face_recognition.compare_faces(encodeListKnown, enf)
            faceDis = face_recognition.face_distance(encodeListKnown, enf)

            print(f"Face distances: {faceDis}")

            if len(matches) > 0 and np.min(faceDis) < 0.5100000000000000:  # Check if valid match exists within threshold
                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:  # Ensure the match is valid
                    if matchIndex < len(classname):  # Validate index
                        name = classname[matchIndex].upper()
                        print(f"Match found: {name}")

                        row = getDetails(name)  # calling the getDetails and markAttendance functions
                        markAttendance(name)
                    else:
                        print(f"MatchIndex {matchIndex} is out of bounds for classname.")

        if row:
            print(f"Details found: {row}")
            return render_template("MainPage.html", data=row)  # if person is registered then displaying the main page
        else:
            print("No record found in the database.")
            return render_template("NoRecord.html")  # else asking the admin to get the student registered


app.run("localhost", port=5000, debug=True)
