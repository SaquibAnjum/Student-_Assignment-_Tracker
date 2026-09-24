from flask import Flask, request
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

client = MongoClient(os.getenv("MONGO_URI"))

db = client["student_db"]
students_collection = db["students"]


# 1. Add Student
@app.post("/students")
def student_detail():

    data = request.json

    if not data.get("name") or not data.get("email") or not data.get("course"):
        return {
            "error": "name, email and course are required"
        }, 400

    existing_student = students_collection.find_one({
        "email": data["email"]
    })

    if existing_student:
        return {
            "error": "Email already exists"
        }, 409

    student = {
        "name": data["name"],
        "email": data["email"],
        "course": data["course"],
        "assignments": []
    }

    result = students_collection.insert_one(student)

    return {
        "message": "Student added successfully",
        "student_id": str(result.inserted_id)
    }, 201


# 2. Get All Students
@app.get("/students")
def get_students():

    students = list(students_collection.find())

    for student in students:
        student["_id"] = str(student["_id"])

    return students


# 3. Add Assignment
@app.post("/students/<student_id>/assignments")
def add_assignment(student_id):

    detail = request.json

    # Validate title
    if not detail.get("title"):
        return {
            "error": "title is required"
        }, 400

    # Validate score
    if "score" not in detail:
        return {
            "error": "score is required"
        }, 400

    score = detail["score"]

    if not isinstance(score, (int, float)) or score < 0 or score > 100:
        return {
            "error": "score must be between 0 and 100"
        }, 400

    # Validate ObjectId
    try:
        student_object_id = ObjectId(student_id)
    except InvalidId:
        return {
            "error": "Invalid student_id"
        }, 400

    # Check student exists
    student = students_collection.find_one({
        "_id": student_object_id
    })

    if not student:
        return {
            "error": "Student not found"
        }, 404

    # Add assignment using $push
    students_collection.update_one(
        {"_id": student_object_id},
        {
            "$push": {
                "assignments": {
                    "title": detail["title"],
                    "score": score
                }
            }
        }
    )

    return {
        "message": "Assignment added successfully"
    }, 200


# 4. Get Top Performers
@app.get("/students/top-performers/<int:score>")
def get_top_performers(score):

    if score < 0 or score > 100:
        return {
            "error": "score must be between 0 and 100"
        }, 400

    students = list(
        students_collection.find({
            "assignments": {
                "$elemMatch": {
                    "score": {
                        "$gte": score
                    }
                }
            }
        })
    )

    for student in students:
        student["_id"] = str(student["_id"])

    return students


if __name__ == "__main__":
    app.run(debug=True)