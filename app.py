from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import random

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/hospital"
mongo = PyMongo(app)

def initialize_doctors():
    if mongo.db.doctors.count_documents({}) == 0:
        doctors = [{"name": f"Doc-{i+1}", "available": True} for i in range(5)]  # 5 doctors
        mongo.db.doctors.insert_many(doctors)
initialize_doctors()
@app.route("/add_patient", methods=["POST"])
def add_patient():
    name = request.form["name"]
    condition = request.form["condition"]
    doctor = mongo.db.doctors.find_one({"available": True})
    if doctor:
        mongo.db.doctors.update_one({"_id": doctor["_id"]}, {"$set": {"available": False}})  # Mark as busy
        assigned_doctor = doctor["name"]
    else:
        assigned_doctor = "Waiting for doctor"
    patient = {"name": name, "condition": condition, "bed": None, "doctor": assigned_doctor}
    mongo.db.patients.insert_one(patient)
    return jsonify({"message": f"{name} added to OPD under {assigned_doctor}!"})
@app.route("/release_bed", methods=["POST"])
def release_bed():
    name = request.form["name"]
    patient = mongo.db.patients.find_one({"name": name})
    if patient and patient["bed"]:
        mongo.db.beds.update_one({"bed_id": patient["bed"]}, {"$set": {"occupied": False}})
        mongo.db.patients.update_one({"name": name}, {"$set": {"bed": None}})
    if patient and patient["doctor"] != "Waiting for doctor":
        mongo.db.doctors.update_one({"name": patient["doctor"]}, {"$set": {"available": True}})  
    return jsonify({"message": f"{name} has been discharged and {patient['doctor']} is now available!"})
@app.route("/status", methods=["GET"])
def status():
    queue = list(mongo.db.patients.find({"bed": None}, {"_id": 0}))
    beds = list(mongo.db.beds.find({}, {"_id": 0}))
    patients = list(mongo.db.patients.find({}, {"_id": 0}))
    doctors = list(mongo.db.doctors.find({}, {"_id": 0}))

    return jsonify({"queue": queue, "beds": beds, "patients": patients, "doctors": doctors})

if __name__ == "__main__":
    app.run(debug=True)