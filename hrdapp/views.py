from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
from .services import get_all_rows
from collections import OrderedDict

from django.contrib import messages
from .forms import CreateUserForm, FileUploadForm

import xgboost
import shap
import pandas as pd
from sklearn.model_selection import train_test_split
from catboost import Pool
from joblib import load
import numpy as np
import time
import os, shutil
from django.conf import settings

import re
from pdfminer.high_level import extract_pages, extract_text

username = "Unknown"

# Create your views here.
def Main(request):
    form = CreateUserForm()
    if request.method == 'POST':
        if 'login' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password1')
            print(username)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('Process')

        if 'register' in request.POST:
            form = CreateUserForm(request.POST)
            if form.is_valid():
                print("Registration Successful!")
                messages.success(request, "Registration Successful")
                form.save()

    context = { 'form':form }
    return render(request, 'registration/login.html', context)

def Logout(request):
    logout(request)
    folder = 'media'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    return redirect('Login')

def extract_data(text, search, type="d", index=0):
    strings = text.split('\n')
    pattern = ""
    for string in strings:
        if re.search(r'\b{}\b'.format(search), string):
            pattern = string
    ext_number = re.compile(r'\d+')
    if type == "s":
        ext_number = re.compile(r'\s?(M|Male|F|Female)')
    if type == "f":
        ext_number = re.compile(r'\d+\.\d+')
    match = ext_number.findall(pattern)[index]
    if match:
        return match
    else:
        return 0

result_h = False
result_s = False
result_d = False
age = 0
sex = 0
def Process(request):
    data = get_all_rows("Test sheet")
    years = list()
    country_data = OrderedDict()

    # pdf report form
    fileform = FileUploadForm()
    
    for rows in data:
        years.append(rows['Year'])
        
        if rows['Entity'] in country_data:
            country_data[rows['Entity']].append(rows['Deaths'])
        else:
            country_data[rows['Entity']] = list()
        
    years = list(set(years))

    if not request.user.is_authenticated:
        return redirect('Login')
    
    (age, sex, cp, fbs, trestbps, thalach, chol, restecg, exang, oldpeak, slope, ca, thal) = (0,0,0,0,0,0,0,0,0,0,0,0,0)
    (heartDisease, married, work, residence, avgglucose, bmi, smoke) = (0,0,0,0,0,0,0)
    (chol_question, chol_check, phy_check, fruits, veggy, drinker, health_rate, mental_check, phy_act_check, walking, bp) = (0,0,0,0,0,0,0,0,0,0,0)
    valid = False
    file_extracted = False
    result_type = ""

    result_h = False
    result_s = False
    result_d = False

    #####################################################
    #####################################################
    ## Shap Analysis Part // Samarth Halyal
    #####################################################
    feat_imp_xgboost = []
    feat_imp_xgboost_names = []
    feat_imp_xgboost_colors_database = ['rgb(66, 189, 111)', 'rgb(54, 162, 235)', 'rgb(255, 205, 86)', 'rgb(255, 99, 132)', 'rgb(154, 66, 189)', 'rgb(87, 66, 189)', 'rgb(66, 187, 189)', 'rgb(224, 108, 170)', 'rgb(209, 98, 234)']
    feat_imp_xgboost_colors = []

    hrp_dataset = pd.read_csv('./saved_models/hypertension_data.csv')
    normalized_dataset = (hrp_dataset-hrp_dataset.min())/(hrp_dataset.max()-hrp_dataset.min())
    normalized_dataset.dropna()
    y = normalized_dataset.pop('target')
    X = normalized_dataset

    _, X_test, _, _ = train_test_split(X, y, test_size=0.3)
    X_test = np.array(X_test)

    model = load('./saved_models/model.joblib')

    explainer = shap.Explainer(model)
    shap_values = explainer.shap_values(X_test)
    temp = [0.0 for i in range(len(shap_values[0]))]
    for row in shap_values:
        temp += row
        tot_sum = 0
    for i in temp:
        tot_sum += abs(i)
    rem_val = 0
    k = 0
    for ii, i in enumerate(temp):
        if i != 0.0:
            ab_val = abs(i)
            perc_value = (float(ab_val)/float(tot_sum)) * 100.0
            rem_val += int(perc_value)
            feat_imp_xgboost.append(int(perc_value))
            feat_imp_xgboost_names.append(normalized_dataset.columns[ii])
            feat_imp_xgboost_colors.append(feat_imp_xgboost_colors_database[k])
            k += 1
    feat_imp_xgboost_colors.append(feat_imp_xgboost_colors_database[k])
    k = 0
    feat_imp_xgboost.append(100-rem_val)
    feat_imp_xgboost_names.append("Others")
    #####################################################
    #####################################################
    #####################################################

    feat_imp_catboost = []
    feat_imp_catboost_names = []
    feat_imp_catboost_colors_database = ['rgb(66, 189, 111)', 'rgb(54, 162, 235)', 'rgb(255, 205, 86)', 'rgb(255, 99, 132)', 'rgb(154, 66, 189)', 'rgb(87, 66, 189)', 'rgb(66, 187, 189)', 'rgb(224, 108, 170)', 'rgb(209, 98, 234)']
    feat_imp_catboost_colors = []

    model = load('./saved_models/c_model_h.joblib')

    explainer = shap.Explainer(model)
    shap_values = explainer.shap_values(X_test)
    temp = [0.0 for i in range(len(shap_values[0]))]
    for row in shap_values:
        temp += row
        tot_sum = 0
    for i in temp:
        tot_sum += abs(i)
    rem_val = 0
    k = 0
    for ii, i in enumerate(temp):
        if i != 0.0:
            ab_val = abs(i)
            perc_value = (float(ab_val)/float(tot_sum)) * 100.0
            rem_val += int(perc_value)
            feat_imp_catboost.append(int(perc_value))
            feat_imp_catboost_names.append(normalized_dataset.columns[ii])
            feat_imp_catboost_colors.append(feat_imp_catboost_colors_database[k])
            k += 1
    feat_imp_catboost_colors.append(feat_imp_catboost_colors_database[k])
    k = 0
    feat_imp_catboost.append(100-rem_val)
    feat_imp_catboost_names.append("Others")
    #####################################################
    #####################################################
    #####################################################

    print(request.POST)
    if request.method == 'POST':
        if "upload" in request.POST:
            # try:
            uploaded_file = request.FILES['file']
            fs = FileSystemStorage()
            save_url = 'media/' + uploaded_file.name 
            filename = fs.save(save_url, uploaded_file)
            filename = filename[6:]
            uploaded_file_url = os.path.join(settings.MEDIA_DIR, filename)
            text = extract_text(uploaded_file_url)
            
            sex = extract_data(text, "Gender", "s")
            age = extract_data(text, "Age")
            cp = extract_data(text, "Cerebral Palsy")
            fbs = extract_data(text, "Blood Sugar")
            trestbps = extract_data(text, "Trest BPS")
            restecg = extract_data(text, "Rest-ECG")
            thalach = extract_data(text, "Heart Rate")
            chol = extract_data(text, "Cholesterol")
            exang = extract_data(text, "Angina")
            oldpeak = extract_data(text, "Old Peak", "f")
            slope = extract_data(text, "Slope of ST")
            ca = extract_data(text, "Calcium Level")
            thal = extract_data(text, "Thal")

            heartDisease = extract_data(text, "Heart-Related")
            married = extract_data(text, "Married")
            work = extract_data(text, "Work Type")
            residence = extract_data(text, "Residency")
            avgglucose = extract_data(text, "average glucose level", "f")
            bmi = extract_data(text, "Body Mass", "f")
            smoke = extract_data(text, "Smoking")

            chol_question = extract_data(text, "High cholesterol")
            chol_check = extract_data(text, "cholesterol check")
            phy_check = extract_data(text, "physical")
            fruits = extract_data(text, "fruits")
            veggy = extract_data(text, "vegetables")
            drinker = extract_data(text, "heavy drinker")
            health_rate = extract_data(text, "rate yourself in terms of health")
            mental_check = extract_data(text, "mental health")
            phy_act_check = extract_data(text, "Physical")
            walking = extract_data(text, "walking")
            bp = extract_data(text, "high blood pressure")

            file_extracted = True
            print([age, sex, float(heartDisease), float(married), float(work), float(residence), float(avgglucose), float(bmi), float(smoke)])
                # print([chol_question, chol_check, phy_check, fruits, veggy, drinker, health_rate, mental_check, phy_act_check, walking, bp])
            # except:
            #     print("Error occured while extracting pdf!")
            #     file_extracted = False

        if "hypertensionBtn" in request.POST:
            # try:
            age = float(request.POST['Age']) / 87.0
            sex = request.POST['Sex']
            if 'm' in sex.lower():
                sex = 1
            else:
                sex = 0
            cp = float(request.POST['cp']) / 3.0
            fbs = float(request.POST['fbs']) / 1.0
            trestbps = float(request.POST['trestbps']) / 106.0
            restecg = float(request.POST['restecg']) / 2.0
            thalach = float(request.POST['thalach']) / 131.0
            chol = float(request.POST['chol']) / 438.0
            exang = float(request.POST['exang']) / 1.0
            oldpeak = float(request.POST['oldpeak']) / 6.2
            slope = float(request.POST['slope']) / 2.0
            ca = float(request.POST['ca']) / 3.0
            thal = float(request.POST['thal']) / 3.0

            print(float(age), float(sex), float(cp), float(fbs), float(trestbps), 
                float(restecg), float(exang), float(oldpeak), float(slope), float(ca), float(thal))
            inp_data = np.array([[float(age), float(sex), float(cp), float(trestbps), float(chol), 
                                float(fbs), float(restecg), float(thalach), float(exang), 
                                float(oldpeak), float(slope), float(ca), float(thal)]])
            
            selected_model = request.POST['selected_model']
            model = load('./saved_models/model.joblib')
            
            if selected_model == 'xgboost':
                inp_data = xgboost.DMatrix(inp_data)
                model = load('./saved_models/model.joblib')
            elif selected_model == 'kmeans':
                model = load('./saved_models/k_model_h.joblib') 
            elif selected_model == 'catboost':
                inp_data = Pool(inp_data)
                model = load('./saved_models/c_model_h.joblib') 
            elif selected_model == 'random':
                model = load('./saved_models/k_model_h.joblib') 

            
            result_h = model.predict(inp_data)
            print("Hypertension ###### ", result_h)
            result_h = bool(round(result_h[0]))
            valid = True
            # except:
            #     print("Error occured while hypertension predicting!")
            #     valid = False
            result_type = "Hypertension"

        if "strokeBtn" in request.POST:
            try:
                age = float(request.POST['Age']) / 112.0
                sex = request.POST['Sex']
                if 'm' in sex.lower():
                    sex = 1
                else:
                    sex = 0
                heartDisease = float(request.POST['heartdisease'])
                married = float(request.POST['married'])
                work = float(request.POST['worktype']) / 4.0
                residence = float(request.POST['residencytype'])
                avgglucose = float(request.POST['glucose']) / 216.62
                bmi = float(request.POST['bmi']) / 80.50
                smoke = float(request.POST['smoking'])
                result_h = 0.0 if request.POST['hypertension_pred'] == 'False' else 1.0

                print(float(sex), float(age), float(result_h), float(heartDisease), float(married), float(work), float(residence), float(avgglucose), float(bmi), float(smoke))
                selected_model = request.POST['selected_model']
                model = load('./saved_models/model_s.joblib')
                
                inp_data = np.array([[float(sex), float(age), float(result_h), float(heartDisease), float(married), float(work), float(residence), float(avgglucose), float(bmi), float(smoke)]])
                if selected_model == 'xgboost':
                    inp_data = xgboost.DMatrix(inp_data)
                    model = load('./saved_models/model_s.joblib')
                elif selected_model == 'kmeans':
                    model = load('./saved_models/k_model_s.joblib') 
                elif selected_model == 'catboost':
                    inp_data = Pool(inp_data)
                    model = load('./saved_models/c_model_s.joblib') 
                elif selected_model == 'random':
                    model = load('./saved_models/k_model_h.joblib') 
                
                result_s = model.predict(inp_data)

                valid = True
            except:
                print("Error occured while stroke predicting!")
                valid = False

            result_type = "Stroke"

        if "diabetesBtn" in request.POST:
            try:
                age = float(request.POST['Age']) / 12.0
                sex = request.POST['Sex']
                if 'm' in sex.lower():
                    sex = 1
                else:
                    sex = 0
                chol_question = float(request.POST['highchol'])
                chol_check = float(request.POST['cholcheck'])
                bmi = float(request.POST['Bmi']) / 86.0
                smoke = float(request.POST['smoke'])
                heartDisease = float(request.POST['heartdisease'])
                phy_check = float(request.POST['physactivity'])
                fruits = float(request.POST['fruits'])
                veggy = float(request.POST['veggies'])
                drinker = float(request.POST['alcohol'])
                health_rate = float(request.POST['genhealth']) / 4.0
                mental_check = float(request.POST['menhealth']) / 30.0
                phy_act_check = float(request.POST['phyhealth']) / 30.0
                walking = float(request.POST['diffwalk'])
                result_s = 0.0 if request.POST['stroke_pred'] == 'False' else 1.0
                bp = float(request.POST['highBp'])

                print(float(age), float(sex), float(chol_question), float(chol_check), float(phy_check), float(fruits), float(veggy), 
                      float(drinker), float(health_rate), float(mental_check), float(phy_act_check), float(walking), float(bp))
                selected_model = request.POST['selected_model']
                model = load('./saved_models/model_d.joblib')
                
                inp_data = np.array([[float(age), float(sex), float(chol_question), float(chol_check), float(bmi), float(smoke), float(heartDisease), float(phy_check), float(fruits), 
                                      float(veggy), float(drinker), float(health_rate), float(mental_check), float(phy_act_check), float(walking), float(result_s), float(bp)]])
                if selected_model == 'xgboost':
                    inp_data = xgboost.DMatrix(inp_data)
                    model = load('./saved_models/model_d.joblib')
                elif selected_model == 'kmeans':
                    model = load('./saved_models/k_model_d.joblib')
                elif selected_model == 'catboost':
                    inp_data = Pool(inp_data)
                    model = load('./saved_models/c_model_d.joblib') 
                elif selected_model == 'random':
                    model = load('./saved_models/k_model_h.joblib') 
                
                result_s = model.predict(inp_data)

                valid = True
            except:
                print("Error occured while diabetes predicting!")
                valid = False
            result_type = "Diabetes"

    context = { 'username': username,
                'feature_important_xgboost': feat_imp_xgboost,
                'feature_important_xgboost_names': feat_imp_xgboost_names,
                'feature_important_xgboost_colors': feat_imp_xgboost_colors,
                'feature_important_catboost': feat_imp_catboost,
                'feature_important_catboost_names': feat_imp_catboost_names,
                'feature_important_catboost_colors': feat_imp_catboost_colors,
                'extracted_from_file': file_extracted,
                'extracted_data': [age, sex, cp, fbs, trestbps, thalach, chol, restecg, exang, oldpeak, slope, ca, thal, heartDisease, married, work, residence, avgglucose, bmi, smoke, chol_question, chol_check, phy_check, fruits, veggy, drinker, health_rate, mental_check, phy_act_check, walking, bp],
                'report_form': fileform,
                'type': result_type,
                'result_hypertension': result_h,
                'result_stroke': result_s,
                'result_diabetes': result_d, 
                'result_valid' : valid,
                'x_labels': years,
                'label1': "\'African Region\'",
                'label2': "\'Australia\'",
                'label3': "\'China\'",
                'label4': "\'Egypt\'",
                'label5': "\'England\'",
                'label6': "\'France\'",
                'label7': "\'India\'",
                'label8': "\'Ukraine\'",
                'label9': "\'United States\'",
                'data1': country_data["African Region (WHO)"],
                'data2': country_data["Australia"],
                'data3': country_data["China"],
                'data4': country_data["Egypt"],
                'data5': country_data["England"],
                'data6': country_data["France"],
                'data7': country_data["India"],
                'data8': country_data["Ukraine"],
                'data9': country_data["United States"],
              }
    
    return render(request, 'index.html', context)