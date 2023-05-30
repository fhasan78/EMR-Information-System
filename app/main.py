from typing import Annotated
from typing import List, Dict, Optional

from fastapi import FastAPI, File, UploadFile

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/patients/file")   
async def readPatientsFromFile(fileName: Annotated[UploadFile, File(description="A file read as UploadFile")] | None = None):
    """
    Reads patient data from a plaintext file.

    fileName: The name of the file to read patient data from.
    Returns a dictionary of patient IDs, where each patient has a list of visits.
    The dictionary has the following structure:
    {
        patientId (int): [
            [date (str), temperature (float), heart rate (int), respiratory rate (int), systolic blood pressure (int), diastolic blood pressure (int), oxygen saturation (int)],
            [date (str), temperature (float), heart rate (int), respiratory rate (int), systolic blood pressure (int), diastolic blood pressure (int), oxygen saturation (int)],
            ...
        ],
        patientId (int): [
            [date (str), temperature (float), heart rate (int), respiratory rate (int), systolic blood pressure (int), diastolic blood pressure (int), oxygen saturation (int)],
            ...
        ],
        ...
    }
    """
    patients = {}
    try:
        patient_file = open(fileName, "r")
        # loop through file line by line
        for line in patient_file:
            try:
                data = line.rstrip().split(",")
                numFields = len(data) # variable with number of fields
                # if number of fields is incorrect in any line, that line is skipped
                if numFields != 8:
                    raise ValueError("Invalid number of fields " + str(numFields) + " in line: "+ str(line))
                else:
                    # Checking if the data is valid, if any of the data is invalid or an error occurs, the function skips to the next line and continues reading
                    # check if date is valid
                    if int(data[1].split("-")[0]) <= 1900 or int(data[1].split("-")[1]) not in range(1,13) or int(data[1].split("-")[2]) not in range(1,32):
                        raise ValueError("Invalid date. Please enter a valid date.")
                    # check if temperature is valid
                    elif 35 <= float(data[2]) >= 42:
                        raise ValueError("Invalid temperature value (" + str(data[2]) + ") in line: " + str(line))
                    # check if heart rate is valid
                    elif int(data[3]) not in range(30, 181):
                        raise ValueError("Invalid heart rate value (" + str(data[3]) + ") in line: " + str(line))
                    # check if respiratory rate is valid 
                    elif int(data[4]) not in range(5, 41):
                        raise ValueError("Invalid respiratory rate value (" + str(data[4]) + ") in line: " + str(line))
                    # check if systolic blood pressure is valid
                    elif int(data[5]) not in range(70, 201):
                        raise ValueError("Invalid systolic blood pressure value (" + str(data[5]) + ") in line: " + str(line))
                    # check if diastolic blood pressure is valid
                    elif int(data[6]) not in range(40, 121):
                        raise ValueError("Invalid diastolic blood pressure value (" + str(data[6]) + ") in line: " + str(line))
                    # check if oxygen saturation is valid
                    elif int(data[7]) not in range(70, 101):
                        raise ValueError("Invalid oxygen saturation value (" + str(data[7]) + ") in line: " + str(line))
                    # if no error occurred proceed by adding the value to the patients dictionary 
                    # check if any previous data is saved for patient 
                    elif int(data[0]) in patients:
                        patients[int(data[0])].append([str(data[1]), float(data[2]), int(data[3]), int(data[4]), int(data[5]), int(data[6]), int(data[7])])
                    # if not add id in patients dictionary 
                    else:
                        patients[int(data[0])] = [[str(data[1]), float(data[2]), int(data[3]), int(data[4]), int(data[5]), int(data[6]), int(data[7])]]
            except ValueError as e:
                print(e)
                pass
            # if any exception occurs during reading the file, skip the line and continue reading
            except Exception as e:
                print("An unexpected error occurred while reading the file.")
                pass       
    # if file is not found, exit program
    except IOError : 
        print("The file '" + str(fileName) + "' could not be found.")
        exit()
    # close file after reading it 
    finally:
        patient_file.close()
    return patients

@app.get("/patients/{patient_id}")
def displayPatientData(patients, patientId: int | None = 0):
    """
    Displays patient data for a given patient ID.

    patients: A dictionary of patient dictionaries, where each patient has a list of visits.
    patientId: The ID of the patient to display data for. If 0, data for all patients will be displayed.
    """
    # if patient id is 0, print data for all patients
    if patientId == 0:
        # loop through patients in the patients dictionary
        for patient in patients:
            patient_data = patients[patient]
            print("Patient ID: {}".format(patient))
            for visit in patient_data:
                print(" Visit Date:", visit[0])
                print("  Temperature:", "%.2f" % visit[1], "C")
                print("  Heart Rate:", "%d" % visit[2], "bpm")
                print("  Respiratory Rate:", "%d" % visit[3], "bpm")
                print("  Systolic Blood Pressure:", "%d" % visit[4], "mmHg")
                print("  Diastolic Blood Pressure:", "%d" % visit[5], "mmHg")
                print("  Oxygen Saturation:", "%d" % visit[6], "%")
    # patient is specified here so print inforamtion for one patient only
    elif patientId in patients:
        patient_data = patients[patientId]
        print("Patient ID: {}".format(patientId))
        for visit in patient_data:
            print(" Visit Date:", visit[0])
            print("  Temperature:", "%.2f" % visit[1], "C")
            print("  Heart Rate:", "%d" % visit[2], "bpm")
            print("  Respiratory Rate:", "%d" % visit[3], "bpm")
            print("  Systolic Blood Pressure:", "%d" % visit[4], "mmHg")
            print("  Diastolic Blood Pressure:", "%d" % visit[5], "mmHg")
            print("  Oxygen Saturation:", "%d" % visit[6], "%")
    # if patient was not found and is not 0, print a error message
    else:
        print("Patient with ID {} not found.".format(patientId))

@app.get("/patients/stats/{patient_id}")
def displayStats(patients, patientId: int | None = 0):
    """
    Prints the average of each vital sign for all patients or for the specified patient.

    patients: A dictionary of patient IDs, where each patient has a list of visits.
    patientId: The ID of the patient to display vital signs for. If 0, vital signs will be displayed for all patients.
    """
    if type(patients) == dict:
        try:
            if int(patientId) == 0:
                # declaring and initializing variables to store in order to get the average for each vital sign
                temp_sum = 0
                heart_sum = 0
                res_sum = 0
                sys_blood_sum = 0
                dias_blood_sum = 0
                oxygen_sum = 0
                num_visits = 0 # number of visits in total for all patients
                for patient in patients:
                    patient_data = patients[patient]
                    num_visits = num_visits + len(patient_data)
                    for visit in patient_data:
                        # get the sum of each of the following
                        temp_sum = temp_sum + visit[1]
                        heart_sum = heart_sum + visit[2]
                        res_sum = res_sum + visit[3]
                        sys_blood_sum = sys_blood_sum + visit[4]
                        dias_blood_sum = dias_blood_sum + visit[5]
                        oxygen_sum = oxygen_sum + visit[6]
                print("Vital Signs for All Patients: ")
                print("  Average temperature:", "%.2f" % (temp_sum / num_visits), "C")
                print("  Average heart rate:", "%.2f" % (heart_sum / num_visits), "bpm")
                print("  Average respiratory rate:", "%.2f" % (res_sum / num_visits), "bpm")
                print("  Average systolic blood pressure:", "%.2f" % (sys_blood_sum / num_visits), "mmHg")
                print("  Average diastolic blood pressure:", "%.2f" % (dias_blood_sum / num_visits), "mmHg")
                print("  Average oxygen saturation:", "%.2f" % (oxygen_sum / num_visits), "%")
            elif int(patientId) > 0:
                if patientId in patients:
                    patient_data = patients[patientId]
                    num_visits = len(patient_data)
                    # declaring and initializing variables to store in order to get the average for each vital sign
                    temp_sum = 0
                    heart_sum = 0
                    res_sum = 0
                    sys_blood_sum = 0
                    dias_blood_sum = 0
                    oxygen_sum = 0
                    for visit in patient_data:
                        temp_sum = temp_sum + visit[1]
                        heart_sum = heart_sum + visit[2]
                        res_sum = res_sum + visit[3]
                        sys_blood_sum = sys_blood_sum + visit[4]
                        dias_blood_sum = dias_blood_sum + visit[5]
                        oxygen_sum = oxygen_sum + visit[6]
                        
                    print("Vital Signs for Patient {}:".format(patientId))
                    print("  Average temperature:", "%.2f" % (temp_sum / num_visits), "C")
                    print("  Average heart rate:", "%.2f" % (heart_sum / num_visits), "bpm")
                    print("  Average respiratory rate:", "%.2f" % (res_sum / num_visits), "bpm")
                    print("  Average systolic blood pressure:", "%.2f" % (sys_blood_sum / num_visits), "mmHg")
                    print("  Average diastolic blood pressure:", "%.2f" % (dias_blood_sum / num_visits), "mmHg")
                    print("  Average oxygen saturation:", "%.2f" % (oxygen_sum / num_visits), "%")
                else:
                    print("No data found for patient with ID {}.".format(patientId))
        except ValueError:
            print("Error: 'patientId' should be an integer.")
    else:
        print("Error: 'patients' should be a dictionary.")

@app.post("/patients/")
def addPatientData(patients, patientId: int, date: str, temp: float, hr: int, rr: int, sbp: int, dbp: int, spo2: int, fileName: str):
    """
    Adds new patient data to the patient list.

    patients: The dictionary of patient IDs, where each patient has a list of visits, to add data to.
    patientId: The ID of the patient to add data for.
    date: The date of the patient visit in the format 'yyyy-mm-dd'.
    temp: The patient's body temperature.
    hr: The patient's heart rate.
    rr: The patient's respiratory rate.
    sbp: The patient's systolic blood pressure.
    dbp: The patient's diastolic blood pressure.
    spo2: The patient's oxygen saturation level.
    fileName: The name of the file to append new data to.
    """
    try:
        patient_file = open(fileName, "a")
        # check if date is in correct format
        if len(date) != 10 or date[4] != "-" or date[7] != "-":
            raise ValueError("Invalid date format. Please enter a date in the format 'yyyy-mm-dd'.")
        # check if date is valid
    
        elif int(date.split("-")[0]) <= 1900 or int(date.split("-")[1]) not in range(1,13) or int(date.split("-")[2]) not in range(1,32):
            raise ValueError("Invalid date. Please enter a valid date.")
        # check if temperature is valid
        elif 35 <= float(temp) >= 42:
            raise ValueError("Invalid temperature. Please enter a temperature between 35.0 and 42.0 Celsius.")
        # check if heart rate is valid
        elif int(hr) not in range(30, 181):
            raise ValueError("Invalid heart rate. Please enter a heart rate between 30 and 180 bpm.")
        # check if respiratory rate is valid 
        elif int(rr) not in range(5, 41):
            raise ValueError("Invalid respiratory rate. Please enter a respiratory rate between 5 and 40 bpm.")
        # check if systolic blood pressure is valid
        elif int(sbp) not in range(70, 201):
            raise ValueError("Invalid systolic blood pressure. Please enter a systolic blood pressure between 70 and 200 mmHg.")
        # check if diastolic blood pressure is valid
        elif int(dbp) not in range(40, 121):
            raise ValueError("Invalid diastolic blood pressure. Please enter a diastolic blood pressure between 40 and 120 mmHg.")
        # check if oxygen saturation is valid
        elif int(spo2) not in range(70, 101):
            raise ValueError("Invalid oxygen saturation. Please enter an oxygen saturation between 70 and 100%.")
        else:
            # add to file, and update patients dictionary
            patient_file.write("\n{},{},{},{},{},{},{},{}".format(patientId, date, temp, hr, rr, sbp, dbp, spo2))  
            if patientId in patients:
                patients[patientId].append([date,temp,hr,rr,sbp,dbp,spo2])
            else:
                patients[patientId] = [[date,temp,hr,rr,sbp,dbp,spo2]]
    # print any value errors that may have been raised
    except ValueError as e:
        print(e)
    # if an unexpected error occurs (any exception) print following message
    except Exception as e:
        print("An unexpected error occurred while adding new data.")
    # close file that has been opened
    finally:
        patient_file.close()

@app.get("/patients/visits/{year}/{month}")
def findVisitsByDate(patients, year: int | None = None, month: int | None = None):
    """
    Find visits by year, month, or both.

    patients: A dictionary of patient IDs, where each patient has a list of visits.
    year: The year to filter by.
    month: The month to filter by.
    return: A list of tuples containing patient ID and visit that match the filter.
    """
    visits = []
    
    if len(patients) == 0:
        print("Patients dictionary is empty. No visits found.")
    # if no month was provided, only a year
    elif month == None and year != None:
        # first we check if the year provided is valid
        if year >= 1990 and len(str(year)) == 4:
            for patient in patients:
                for visit in patients[patient]:
                    if int(visit[0].split("-")[0]) == year:
                        visits.append((patient, visit))
    # if both the year and month were provided
    elif month != None and year != None:
        # check provided data is valid
        if year >= 1990 and month in range(1,13):
            for patient in patients:
                for visit in patients[patient]:
                    if (int(visit[0].split("-")[0]) == year and int(visit[0].split("-")[1]) == month):
                        visits.append((patient, visit))
    # if no month or year were provided, all patients visits will be returned
    else:
        for patient in patients:
            for visit in patients[patient]:
                visits.append((patient, visit))
    return visits

@app.get("/patients/follow_up")
def findPatientsWhoNeedFollowUp(patients):
    """
    Find patients who need follow-up visits based on abnormal vital signs.

    patients: A dictionary of patient IDs, where each patient has a list of visits.
    return: A list of patient IDs that need follow-up visits to to abnormal health stats.
    """
    followup_patients = []
    # a patient needs a followup if any of the following is true
    # heart rate > 100 or heart rate is < 60 or systolic is > 140 or diastolic is > 90 or blood oxygen saturation is < 90
    for patient in patients:
        for visit in patients[patient]:
            if (visit[2] > 100 or visit[2] < 60 or visit[4] > 140 or visit[5] > 90 or visit[6] < 90): 
                # if patient id is already in list do not duplicate
                if patient not in followup_patients:
                    followup_patients.append(patient)
    return followup_patients

@app.delete("patients/{patient_id}")
def deleteAllVisitsOfPatient(patients, patientId, filename):
    """
    Delete all visits of a particular patient.

    patients: The dictionary of patient IDs, where each patient has a list of visits, to delete data from.
    patientId: The ID of the patient to delete data for.
    filename: The name of the file to save the updated patient data.
    return: None
    """
    if patientId in patients:
        patients.pop(patientId)
        try:
            patient_file = open(filename, "w")
            for patient in patients:
                for visit in patients[patient]:
                    date = visit[0]
                    temp = visit[1]
                    hr = visit[2]
                    rr =  visit[3]
                    sbp = visit[4]
                    dbp =  visit[5]
                    spo2 = visit[6]
                    patient_file.write("{},{},{},{},{},{},{},{}\n".format(patient, date, temp, hr, rr, sbp, dbp, spo2))  
            print("Data for patient {} has been deleted.".format(patientId))
        # if file is not found, exit program
        except IOError : 
            print("The file '" + str(filename) + "' could not be found.")
            exit()
        # close file after reading it 
        finally:
            patient_file.close()
    else:
        print("No data found for patient with ID {}".format(patientId))



