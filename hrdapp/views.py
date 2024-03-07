from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .services import get_all_rows
from collections import OrderedDict

from django.contrib import messages
from .forms import CreateUserForm, FileUploadForm

from joblib import load
import numpy as np

import os
from django.conf import settings

import re
from pdfminer.high_level import extract_pages, extract_text

model = load('./saved_models/model.joblib')
username = "Unknown"

# Create your views here.
def Main(request):
    form = CreateUserForm()
    if request.method == 'POST':
        if request.POST.get('login') != None:
            username = request.POST.get('username')
            password = request.POST.get('password1')
            print(username)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('Process')

        if request.POST.get('register') != None:
            form = CreateUserForm(request.POST)
            if form.is_valid():
                print("Registration Successful!")
                messages.success(request, "Registration Successful")
                form.save()

    context = { 'form':form }
    return render(request, 'registration/login.html', context)

def Logout(request):
    logout(request)
    return redirect('Login')

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
    
    (age, sex, cp, fbs, trestbps, thalach, chol, restecg, exang, oldpeak, slope, ca, thal, pred) = (0,0,0,0,0,0,0,0,0,0,0,0,0,0)
    result_h = False
    result_s = False
    result_d = False
    valid = False

    if request.method == 'POST':
        if request.FILES['file']:
            uploaded_file = request.FILES['file']
            uploaded_file_url = os.path.join(settings.MEDIA_DIR, uploaded_file.name)
            text = extract_text(uploaded_file_url)
            print(text)

        if request.POST.get("hypertensionBtn"):
            try:
                age = float(request.POST['Age']) / 98.0
                sex = request.POST['Sex']
                if 'm' in sex.lower():
                    sex = 1
                else:
                    sex = 0
                cp = float(request.POST['cp']) / 3.0
                fbs = float(request.POST['fbs']) / 1.0
                trestbps = float(request.POST['trestbps']) / 200.0
                restecg = float(request.POST['restecg']) / 2.0
                thalach = float(request.POST['thalach']) / 202.0
                chol = float(request.POST['chol']) / 564.0
                exang = float(request.POST['exang']) / 1.0
                oldpeak = float(request.POST['oldpeak']) / 6.2
                slope = float(request.POST['slope']) / 2.0
                ca = float(request.POST['ca']) / 4.0
                thal = float(request.POST['thal']) / 3.0

                # print(float(age), float(sex), float(cp), float(fbs), float(trestbps), 
                #      float(restecg), float(exang), float(oldpeak), float(slope), float(ca), float(thal))
                inp_data = np.array([[float(age), float(sex), float(cp), float(trestbps), float(chol), 
                                    float(fbs), float(restecg), float(thalach), float(exang), 
                                    float(oldpeak), float(slope), float(ca), float(thal)]])
                result_h = model.predict(inp_data)[0]
                valid = True
            except:
                valid = False

        if request.POST.get("strokeBtn"):
            try:
                valid = True
            except:
                valid = False

        if request.POST.get("diabetesBtn"):
            try:
                valid = True
            except:
                valid = False

    context = { 'username': username,
                'report_form': fileform,
                'result_hypertension': result_h,
                'result_hypertension': result_s,
                'result_hypertension': result_d, 
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