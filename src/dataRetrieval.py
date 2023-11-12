import requests
import time
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
import math

#Initializing Values: File Path for Data, Request URL to get info from Blynk
#Update URL to send info to Blynk, Data Values to store UV Value history for the past hour
#Event URLs to send events (notifications) to the app
file_path = "full_uv_harshness_dataset_exp.txt"
fileTwo_path = "adjusted_simulated_uv_skin_cancer_dataset.csv"
request_url = "https://blr1.blynk.cloud/external/api/get?token=ofAnR6pN0YG7rBbaqVRuAQuvxpcU2OtM&v4"
update_url = "https://blr1.blynk.cloud/external/api/update?token=ofAnR6pN0YG7rBbaqVRuAQuvxpcU2OtM&V6="
updateTwo_url = "https://blr1.blynk.cloud/external/api/update?token=ofAnR6pN0YG7rBbaqVRuAQuvxpcU2OtM&V5="
updateThree_url = "https://blr1.blynk.cloud/external/api/update?token=ofAnR6pN0YG7rBbaqVRuAQuvxpcU2OtM&V7="
updateFour_url = "https://blr1.blynk.cloud/external/api/update?token=ofAnR6pN0YG7rBbaqVRuAQuvxpcU2OtM&V8="
eventOne_url = "https://blr1.blynk.cloud/external/api/logEvent?token=ofAnR6pN0YG7rBbaqVRuAQuvxpcU2OtM&code=notif"
eventTwo_url = "https://blr1.blynk.cloud/external/api/logEvent?token=ofAnR6pN0YG7rBbaqVRuAQuvxpcU2OtM&code=notif2"
eventThree_url = "https://blr1.blynk.cloud/external/api/logEvent?token=ofAnR6pN0YG7rBbaqVRuAQuvxpcU2OtM&code=notif3"
dataValues = []
dataValuesTwo = []
SPF_BENCHMARK = 300

#Function to Standardize a List
def standardize_list(data):
    data_array = np.array(data)
    mean = np.mean(data_array)
    std_dev = np.std(data_array)
    standardized_data = (data_array - mean) / std_dev
    return standardized_data

#Gets SPF Recommended SPF Value from Data
def getSPF(data):
    SPF = sum(data)/SPF_BENCHMARK
    SPF = round(SPF / 5) * 5
    return SPF

#Sets Up Machine Learning for Cancer Data

#Reads the Data File
df = pd.read_csv(fileTwo_path)
    
#Splitting each line into X and Y components (CancerX is input, CancerY is output)
mean_sun_exposure_time = df['Average Sun Exposure Time'].mean()
mean_skin_cancer_incidence = df['Skin Cancer Incidence'].mean()
CancerX = df[['Average UV Index', 'Average Sun Exposure Time']].values.tolist()
CancerY = df['Skin Cancer Incidence'].values.tolist()
scaler_X = StandardScaler()
CancerX = scaler_X.fit_transform(CancerX)

#Calculates the average of the UV values and scales it to a range from 0 to 12
def transformHistoryRawDataToScaledCancerData(data):
    avg_uv = sum(data) / len(data)
    scaled_avg = (avg_uv / 180) * 12
    scaled_avg = min(scaled_avg, 12)
    newData = [scaled_avg, mean_sun_exposure_time]
    new_data_points_scaled = scaler_X.transform([newData])
    return new_data_points_scaled[0]

def getLikelihoodOfCancer(data):
    return (data-mean_skin_cancer_incidence)/mean_skin_cancer_incidence

#Trains the RandomForestRegressor Model
lr_model = LinearRegression(fit_intercept=True, n_jobs=None)
lr_model.fit(CancerX, CancerY)
print("Training One Completed")

#Sets Up Machine Learning for Harshness Index Data

#Reads the Data File
with open(file_path, 'r') as file:
    lines = file.readlines()

#Splitting each line into X and Y components (X is input, Y is output)
X = []
Y = []
for line in lines:
    uv_values_str, harshness_str = line.strip().split('], Harshness Index: ')
    uv_values = [float(val) for val in uv_values_str.strip('[').split(', ')]
    harshness_index = float(harshness_str)
    X.append(uv_values)
    Y.append(harshness_index)
    
#Gets the mean of the data and initializes each of the Data Values to the mean
means = []
for i in X:
    mean = np.mean(i)
    means.append(mean)
mean = np.mean(means)
for i in range(120):
    dataValues.append(mean)

#Standardizes the Y values and converts X and Y to numpy arrays
Y = standardize_list(Y)
X = np.array(X)
Y = np.array(Y)

#Trains the RandomForestRegressor Model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X, Y)
print("Training Two Completed")

#While Loop that updates every 30 seconds
#It gets the data from Blynk and adds the data to history of values (removing the oldest one)
#Uses the model on the new history of values, predicting a Y component
#Updates the Y component and sends it back to Blynk
count = 0
while True:
    response = requests.get(request_url)
    if response.status_code == 200:
        # Extracting data and adding to history
        data = response.json()
        print("DataPoint: ", data)
        if data > 200:
            data = 200
        dataValues.append(data)
        dataValues.pop(0)
        
        #Harshness Index Model Usage
        result = rf_model.predict([dataValues])[0]
        result = math.ceil(result*100)/100
        if result >= 2:
            resultTwo = 4
        elif result >= 1:
            resultTwo = 3
        elif result <= -1.5:
            resultTwo = 1
        else:
            resultTwo = 2
        requests.get(update_url + str(result))
        requests.get(updateTwo_url + str(resultTwo))
        print("Harshness Index Data Sent: ", result)
        
        #Cancer Model Usage
        transformedData = transformHistoryRawDataToScaledCancerData(dataValues)
        resultThree = lr_model.predict([transformedData])[0]
        resultThree = getLikelihoodOfCancer(resultThree)
        resultThree = math.ceil(resultThree*10000)/100
        requests.get(updateThree_url + str(resultThree))
        print("Cancer Percentage Data Sent: ", resultThree)
        
        #Get Recommended SPF
        recommendedSPF = getSPF(dataValues)
        requests.get(updateFour_url, recommendedSPF)
        print("Recommended SPF Data Sent: ", recommendedSPF)
        
        #Notifications Based on Harshness Index
        if count >= 360:
            if result >= 2:
                count = 0
                requests.get(eventTwo_url)
            elif result >= 1:
                count = 0
                requests.get(eventOne_url)
            elif result <= -1.5:
                count = 0
                requests.get(eventThree_url)
        count += 1
        time.sleep(30)
    else:
        print("Failed to retrieve data:", response.status_code)
