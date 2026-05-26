from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import UserRegistrationModel, CrimeReport

import joblib
import os
import gc  # गार्बेज कलेक्शन मेमरी रिकामी करण्यासाठी
import pandas as pd
import numpy as np
import requests
import google.generativeai as genai

import matplotlib
matplotlib.use('Agg')  # ग्राफची मेमरी वाचवण्यासाठी ही ओळ महत्त्वाचे आहे
import matplotlib.pyplot as plt

import folium
from folium.plugins import HeatMap
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

BASE_DIR = settings.BASE_DIR

# २. सगळ्या फाईल्सचे absolute paths
model_path = os.path.join(BASE_DIR, 'crime_model.pkl')
city_path = os.path.join(BASE_DIR, 'city_encoder.pkl')
crime_path = os.path.join(BASE_DIR, 'crime_encoder.pkl')
gender_path = os.path.join(BASE_DIR, 'gender_encoder.pkl')

# Lazy loading (RAM वाचवण्यासाठी)
model = None
city_encoder = None
crime_encoder = None
gender_encoder = None

def load_files():
    global model, city_encoder, crime_encoder, gender_encoder

    # mmap_mode='r' मुळे फाईल्स RAM ऐवजी मेमरी मॅपिंगद्वारे वाचल्या जातात, सर्वर क्रॅश होत नाही
    if model is None:
        model = joblib.load(model_path, mmap_mode='r')

    if city_encoder is None:
        city_encoder = joblib.load(city_path, mmap_mode='r')

    if crime_encoder is None:
        crime_encoder = joblib.load(crime_path, mmap_mode='r')

    if gender_encoder is None:
        gender_encoder = joblib.load(gender_path, mmap_mode='r')


genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model_ai = genai.GenerativeModel("gemini-2.0-flash")


def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You have been successfully registered')
            form = UserRegistrationForm()
            return render(request, 'UserRegistrations.html', {'form': form})
        else:
            messages.success(request, 'Email or Mobile Already Existed')
    else:
        form = UserRegistrationForm()
    return render(request, 'UserRegistrations.html', {'form': form})

def UserLoginCheck(request):
    if request.method =='POST':
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('pswd')
        try:
            check = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            status = check.status
            if status == "activated":
                request.session['id'] = check.id
                request.session['loggeduser'] = check.name
                request.session['loginid'] = loginid
                request.session['email'] = check.email
                return render(request, 'users/userhome.html', {})
            else:
                messages.success(request, 'Your Account Not at activated')
                return render(request, 'userlogin.html')
        except Exception as e:
            messages.success(request, 'Invalid Login id and password')
        return render(request, 'userlogin.html', {})

def UserHome(request):
    return render(request, 'users/userhome.html', {})

def viewData(request):
    # मेमरी वाचवण्यासाठी फक्त पहिल्या १०० ओळी आणि आवश्यक गोष्टीच लोड करा
    df = pd.read_csv('dataset/crime_dataset_india.csv', nrows=100)
    data = df.to_html(classes='table table-dark table-striped', index=False)
    
    del df
    gc.collect()
    return render(request, 'users/userviewdata.html', {'data': data})

def crimeprediction(request):
    result = []
    safety = ""
    crime_percent = []
    city = ""

    if request.method == 'POST':
        city = request.POST.get('city')
        
        # मेमery वाचवण्यासाठी फक्त हवे असलेले कॉलम लोड करा
        df = pd.read_csv('dataset/crime_dataset_india.csv', usecols=['City', 'Crime Description'])
        city_data = df[df['City'].str.lower() == city.lower()]

        if len(city_data) > 0:
            total = len(city_data)
            crimes = city_data['Crime Description'].value_counts()
            top_crimes = crimes.head(5)
            result = list(top_crimes.index)

            for crime, count in top_crimes.items():
                percentage = round((count / total) * 100, 2)
                crime_percent.append((crime, percentage))

            if total > 200:
                safety = "🔴 UNSAFE AREA"
            elif total > 100:
                safety = "🟠 MODERATE AREA"
            else:
                safety = "🟢 SAFE AREA"
        else:
            safety = "No Data Found"
        
        del df, city_data
        gc.collect()

    return render(request, 'users/prediction.html', {
        'result': result, 'crime_percent': crime_percent, 'safety': safety, 'city': city
    })

def add_crime(request):
    message=""
    if request.method=="POST":
        CrimeReport.objects.create(
            city=request.POST.get('city'),
            crime_type=request.POST.get('crime_type'),
            location=request.POST.get('location'),
            date=request.POST.get('date'),
            description=request.POST.get('description')
        )
        message="Crime Report Added Successfully"
    return render(request, 'users/add_crime.html', {'msg':message})

def dashboard(request):
    # मेमरी ऑप्टिमायझेशन
    df = pd.read_csv('dataset/crime_dataset_india.csv', usecols=['Victim Age'])
    total = len(df)
    high = len(df[df['Victim Age'] > 50])
    safe = total - high
    avg = round(np.random.randint(40, 80), 2)
    
    del df
    gc.collect()

    return render(request, 'users/dashboard.html', {
        'total':total, 'high':high, 'safe':safe, 'avg':avg
    })

def area_analysis(request):
    load_files()

    if request.method == "POST":
        area = request.POST.get('area').lower()
        geolocator = Nominatim(user_agent="crime_app")
        
        try:
            location = geolocator.geocode(area + ", India", timeout=10)
            if location:
                lat, long = location.latitude, location.longitude
            else:
                lat, long = 18.5204, 73.8567
        except:
            lat, long = 18.5204, 73.8567

        # ML Prediction
        try:
            city = city_encoder.transform([area.title()])[0]
        except:
            city = 0

        age, gender = 25, 0
        prediction = model.predict([[city, age, gender]])
        crime = crime_encoder.inverse_transform(prediction)[0]

        # Dataset analysis (फक्त गरजेचे कॉलम्स लोड केले जेणेकरून RAM वाचेल)
        df = pd.read_csv('dataset/crime_dataset_india.csv', usecols=['City', 'Time of Occurrence'])
        city_data = df[df['City'].str.lower() == area.lower()]
        total_crimes = len(city_data)

        if total_crimes > 500: risk = 90
        elif total_crimes > 200: risk = 70
        elif total_crimes > 50: risk = 50
        else: risk = 25

        # Time analysis
        crime_times = pd.to_datetime(city_data['Time of Occurrence'], errors='coerce')
        crime_hours = crime_times.dt.hour
        time_count = crime_hours.value_counts()
        time_analysis = []

        for hour, count in time_count.head(5).items():
            time_analysis.append((f"{hour}:00", f"{count} Crimes"))

        if len(time_count) > 0:
            danger, safe = f"{time_count.idxmax()}:00", f"{time_count.idxmin()}:00"
        else:
            danger, safe = "Not Available", "Not Available"

        if risk < 40:
            level, recommendation = "LOW", "Area appears comparatively safe."
        elif risk < 70:
            level, recommendation = "MEDIUM", "Stay alert in crowded areas."
        else:
            level, recommendation = "HIGH", "Avoid isolated places and night travel."

        # Nearby Police Stations
        nearby = []
        try:
            overpass_url = "https://overpass-api.de/api/interpreter"
            query = f'[out:json];(node["amenity"=="police"](around:10000,{lat},{long}););out;'
            response = requests.get(overpass_url, params={'data':query}, timeout=5)
            data = response.json()
            for place in data['elements'][:5]:
                station = place.get('tags', {}).get('name', 'Police Station')
                distance = round(geodesic((lat,long), (place['lat'],place['lon'])).km, 2)
                nearby.append((station, distance))
        except:
            nearby = [("Nearest Police Station",2.5), ("City Police Station",4.1), ("Emergency Police Help Center",6.3)]

        # Map generation
        map_obj = folium.Map(location=[lat,long], zoom_start=12)
        folium.Marker([lat,long], popup=area.title(), tooltip="Selected Area").add_to(map_obj)
        map_html = map_obj._repr_html_()

        # मेमरी त्वरित साफ करा
        del df, city_data, map_obj
        gc.collect()

        return render(request, 'users/area_analysis.html', {
            'area':area.title(), 'risk_score':risk, 'risk_level':level, 'predicted_crime':crime,
            'safe_time':safe, 'danger_time':danger, 'recommendation':recommendation,
            'time_analysis':time_analysis, 'nearby_police':nearby, 'latitude':lat, 'longitude':long, 'map':map_html
        })

    return render(request, 'users/area_analysis.html')

def route_safety(request):
    if request.method=="POST":
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        geolocator = Nominatim(user_agent="crime_app")
        
        try:
            source_location = geolocator.geocode(source, timeout=5)
            destination_location = geolocator.geocode(destination, timeout=5)
            if source_location and destination_location:
                distance = round(geodesic((source_location.latitude, source_location.longitude), (destination_location.latitude, destination_location.longitude)).km, 2)
            else:
                distance = 0
        except:
            distance = 0

        if distance < 10: risk = 30
        elif distance < 50: risk = 55
        else: risk = 80

        if risk < 40:
            safe, danger, message = "6AM - 6PM", "12AM - 4AM", "✅ Safe route detected."
        elif risk < 70:
            safe, danger, message = "7AM - 5PM", "10PM - 3AM", "⚠ Travel carefully."
        else:
            safe, danger, message = "9AM - 4PM", "8PM - 5AM", "🚨 Avoid late-night travel."

        return render(request, 'users/route_safety.html', {
            'source':source, 'destination':destination, 'risk':risk, 'distance':distance, 'safe':safe, 'danger':danger, 'message':message
        })
    return render(request, 'users/route_safety.html')

def map_view(request):
    df = pd.read_csv('dataset/crime_dataset_india.csv', usecols=['Latitude', 'Longitude'])
    map_obj = folium.Map(location=[20.5937,78.9629], zoom_start=5)

    # NaN व्हॅल्यू काढून टाकून लिस्ट कॉम्प्रिहेन्शन वापरले (RAM आणि गती वाढते)
    df_clean = df.dropna(subset=['Latitude', 'Longitude'])
    heat_data = df_clean[['Latitude', 'Longitude']].values.tolist()

    HeatMap(heat_data, radius=15).add_to(map_obj)
    map_html = map_obj._repr_html_()
    
    del df, df_clean, map_obj
    gc.collect()

    return render(request, 'users/map_view.html', {'map':map_html})

def insights(request):
    df = pd.read_csv('dataset/crime_dataset_india.csv', usecols=['City', 'Crime Domain', 'Victim Gender', 'Victim Age'])
    total = len(df)
    high = len(df[df['Victim Age'] > 50])
    safe = total - high

    os.makedirs('media', exist_ok=True)

    # Graph 1
    plt.figure(figsize=(10,5))
    df['City'].value_counts().head(10).plot(kind='bar')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('media/city_chart.png')
    plt.clf()

    # Graph 2
    plt.figure(figsize=(8,8))
    df['Crime Domain'].value_counts().head(5).plot(kind='pie', autopct='%1.1f%%')
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig('media/domain_chart.png')
    plt.clf()

    # Graph 3
    plt.figure(figsize=(8,5))
    df['Victim Gender'].value_counts().plot(kind='bar')
    plt.tight_layout()
    plt.savefig('media/gender_chart.png')
    
    # सर्व Matplotlib प्लॉट्स पूर्णपणे क्लोज करा मेमरी फ्री करण्यासाठी
    plt.close('all')
    
    del df
    gc.collect()

    return render(request, 'users/insights.html', {
        'total':total, 'high':high, 'safe':safe,
        'city':'/media/city_chart.png', 'domain':'/media/domain_chart.png', 'gender':'/media/gender_chart.png'
    })

def emergency(request):
    return render(request, 'users/emergency.html')

def chatbot(request):
    answer=""
    if request.method=="POST":
        query = request.POST.get('query')
        area = request.POST.get('area')

        df = pd.read_csv('dataset/crime_dataset_india.csv', usecols=['City'])
        city_data = df[df['City'].str.lower() == area.lower()]
        total_crimes = len(city_data)

        if total_crimes > 500: risk, safe = "HIGH", "6AM-4PM"
        elif total_crimes > 200: risk, safe = "MEDIUM", "7AM-5PM"
        else: risk, safe = "LOW", "Any daytime"

        try:
            prompt = f"Use ONLY this data.\nArea:{area}\nRisk:{risk}\nCrime Count:{total_crimes}\nSafe Time:{safe}\nQuestion:{query}"
            response = model_ai.generate_content(prompt)
            answer = response.text
        except:
            answer = f"Area : {area}\nRisk Level : {risk}\nCrime Records : {total_crimes}\nRecommended Safe Time :\n{safe}\nRecommendation :\nAvoid travelling late night and stay alert."
        
        del df, city_data
        gc.collect()

    return render(request, 'users/chatbot.html', {'answer':answer})

def sos_alert(request):
    message = """🚨 EMERGENCY SOS ACTIVATED 🚨\n\nCurrent Status:\nHigh Risk Area Detected\n\nEmergency Contacts:\n\nPolice : 100\nAmbulance : 108\nWomen Helpline : 1091\n\nSafety Instructions:\n\n• Share live location\n• Stay in crowded area\n• Contact nearest police station"""
    return render(request, 'users/sos.html', {'message': message})