from django.shortcuts import render
from django.http import HttpResponse

from joblib import load
import numpy as np

model = load('./saved_models/model.joblib')

# Create your views here.
def Login(request):
    return render(request, 'registration/login.html')

def Process(request):
    (age, sex, cp, fbs, trestbps, thalach, chol, restecg, exang, oldpeak, slope, ca, thal, pred) = (0,0,0,0,0,0,0,0,0,0,0,0,0,0)
    result = False
    if request.method == 'POST':
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
        pred = model.predict(inp_data)[0]
        result = True

    return render(request, 'index.html', { 'result_valid' : result, 'predict': pred })


def Main(request):
    username = request.POST['username']
    password = request.POST['pass']
    
    return render(request, 'index.html')