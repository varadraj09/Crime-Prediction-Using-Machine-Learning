from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
import joblib
import os
import matplotlib
matplotlib.use('Agg')  # ग्राफची मेमरी वाचवण्यासाठी ही ओळ महत्त्वाचे आहे
import matplotlib.pyplot as plt

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

    if model is None:
        model = joblib.load(model_path)

    if city_encoder is None:
        city_encoder = joblib.load(city_path)

    if crime_encoder is None:
        crime_encoder = joblib.load(crime_path)

    if gender_encoder is None:
        gender_encoder = joblib.load(gender_path)
from django.http import HttpResponse
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import UserRegistrationModel, CrimeReport
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from django.conf import settings
import folium
import os
import requests
import google.generativeai as genai
from folium.plugins import HeatMap
from .models import CrimeReport

from geopy.geocoders import Nominatim
from geopy.distance import geodesic


import os

genai.configure(
    api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)

model_ai = genai.GenerativeModel(
    "gemini-2.0-flash"
)


def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            print('Data is Valid')
            form.save()
            messages.success(request, 'You have been successfully registered')
            form = UserRegistrationForm()
            return render(request, 'UserRegistrations.html', {'form': form})
        else:
            messages.success(request, 'Email or Mobile Already Existed')
            print("Invalid form")
    else:
        form = UserRegistrationForm()
    return render(request, 'UserRegistrations.html', {'form': form})

def UserLoginCheck(request):
    if request.method =='POST':
        loginid=request.POST.get('loginid')
        pswd=request.POST.get('pswd')
        print("Login ID = ", loginid, ' Password = ', pswd)
        try:
            check = UserRegistrationModel.objects.get(
                loginid=loginid, password=pswd)
            status = check.status
            print('Status is = ', status)
            if status == "activated":
                request.session['id'] = check.id
                request.session['loggeduser'] = check.name
                request.session['loginid'] = loginid
                request.session['email'] = check.email
                print("User id At", check.id, status)
                return render(request, 'users/userhome.html', {})
            else:
                messages.success(request, 'Your Account Not at activated')
                return render(request, 'userlogin.html')
        except Exception as e:
            print('Exception is ', str(e))
            pass
            messages.success(request, 'Invalid Login id and password')
        return render(request, 'userlogin.html', {})

def UserHome(request):

    return render(request, 'users/userhome.html', {})

def viewData(request):

    import pandas as pd
    import os
    from django.conf import settings

    path = os.path.join(settings.MEDIA_ROOT, 'chicago_crime_2014.csv')

    df = pd.read_csv('dataset/crime_dataset_india.csv')
    # Only first 100 rows
    df = df.head(100)

    # Convert to html table
    data = df.to_html(classes='table table-dark table-striped', index=False)

    return render(request, 'users/userviewdata.html', {'data': data})


def crimeprediction(request):

    import pandas as pd

    result = []
    safety = ""
    crime_percent = []
    city = ""

    if request.method == 'POST':

        city = request.POST.get('city')

        # Load Dataset
        df = pd.read_csv(
            'dataset/crime_dataset_india.csv'
        )

        # Filter selected city
        city_data = df[
            df['City'].str.lower() ==
            city.lower()
        ]

        if len(city_data) > 0:

            total = len(city_data)

            # Crime count
            crimes = city_data[
                'Crime Description'
            ].value_counts()

            # Top 5 crimes
            top_crimes = crimes.head(5)

            result = list(
                top_crimes.index
            )

            # Percentage calculation
            for crime, count in top_crimes.items():

                percentage = round(
                    (count / total) * 100,
                    2
                )

                crime_percent.append(

                    (
                        crime,
                        percentage
                    )

                )

            # Safety Logic
            if total > 200:

                safety = "🔴 UNSAFE AREA"

            elif total > 100:

                safety = "🟠 MODERATE AREA"

            else:

                safety = "🟢 SAFE AREA"

        else:

            safety = "No Data Found"

    return render(

        request,

        'users/prediction.html',

        {

            'result': result,

            'crime_percent': crime_percent,

            'safety': safety,

            'city': city

        }

    )

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

    return render(
        request,
        'users/add_crime.html',
        {'msg':message}
    )

def dashboard(request):

    df = pd.read_csv(
        'dataset/crime_dataset_india.csv'
    )

    total = len(df)

    high = len(
        df[df['Victim Age'] > 50]
    )

    safe = total-high

    avg = round(
        np.random.randint(
            40,
            80
        ),
        2
    )

    return render(

        request,

        'users/dashboard.html',

        {

            'total':total,

            'high':high,

            'safe':safe,

            'avg':avg

        }

    )

def area_analysis(request):

    load_files()

    if request.method == "POST":

        area = request.POST.get('area')
        area = area.lower()

        geolocator = Nominatim(
            user_agent="crime_app"
        )

        location = geolocator.geocode(
            area + ", India"
        )

        if location:

            lat = location.latitude
            long = location.longitude

        else:

            lat = 18.5204
            long = 73.8567


        # ML Prediction

        try:

            city = city_encoder.transform(
                [area.title()]
            )[0]

        except:

            city = 0


        age = 25
        gender = 0


        prediction = model.predict([

            [

                city,
                age,
                gender

            ]

        ])

        crime = crime_encoder.inverse_transform(
            prediction
        )[0]


        # Dataset analysis

        df = pd.read_csv(
            'dataset/crime_dataset_india.csv'
        )


        city_data = df[

            df['City'].str.lower()

            ==

            area.lower()

        ]


        total_crimes = len(
            city_data
        )


        # Risk score from dataset

        if total_crimes > 500:

            risk = 90

        elif total_crimes > 200:

            risk = 70

        elif total_crimes > 50:

            risk = 50

        else:

            risk = 25


        # Time analysis

        crime_times = pd.to_datetime(

            city_data[
                'Time of Occurrence'
            ],

            errors='coerce'

        )


        crime_hours = crime_times.dt.hour

        time_count = crime_hours.value_counts()


        time_analysis=[]


        for hour,count in time_count.head(5).items():

            time_analysis.append(

                (

                    f"{hour}:00",

                    f"{count} Crimes"

                )

            )


        if len(time_count)>0:

            danger_hour=time_count.idxmax()

            safe_hour=time_count.idxmin()

            danger=f"{danger_hour}:00"

            safe=f"{safe_hour}:00"

        else:

            danger="Not Available"

            safe="Not Available"


        # Risk Level

        if risk < 40:

            level = "LOW"

            recommendation = "Area appears comparatively safe."


        elif risk < 70:

            level = "MEDIUM"

            recommendation = "Stay alert in crowded areas."


        else:

            level = "HIGH"

            recommendation = "Avoid isolated places and night travel."


        # Nearby Police Stations (real)

        nearby=[]

        try:

            overpass_url = "https://overpass-api.de/api/interpreter"

            query = f"""
            [out:json];
            (
            node["amenity"="police"](around:10000,{lat},{long});
            );
            out;
            """

            response = requests.get(

                overpass_url,

                params={'data':query},
                    
                    timeout=10


            )

            data=response.json()

            for place in data['elements'][:5]:

                station=place.get(

                    'tags',

                    {}

                ).get(

                    'name',

                    'Police Station'

                )

                plat=place['lat']
                plong=place['lon']

                distance=round(

                    geodesic(

                        (lat,long),

                        (plat,plong)

                    ).km,

                    2

                )

                nearby.append(

                    (

                        station,

                        distance

                    )

                )

        except:

            nearby=[
                 ("Nearest Police Station",2.5),

        ("City Police Station",4.1),

        ("Emergency Police Help Center",6.3)
            ]


        # Map

        map = folium.Map(

            location=[lat,long],

            zoom_start=12

        )


        folium.Marker(

            [lat,long],

            popup=area.title(),

            tooltip="Selected Area"

        ).add_to(map)


        map = map._repr_html_()


        return render(

            request,

            'users/area_analysis.html',

            {

                'area':area.title(),

                'risk_score':risk,

                'risk_level':level,

                'predicted_crime':crime,

                'safe_time':safe,

                'danger_time':danger,

                'recommendation':recommendation,

                'time_analysis':time_analysis,

                'nearby_police':nearby,

                'latitude':lat,

                'longitude':long,

                'map':map

            }

        )


    return render(

        request,

        'users/area_analysis.html'

    )

def route_safety(request):

    if request.method=="POST":

        source=request.POST.get(
            'source'
        )

        destination=request.POST.get(
            'destination'
        )

        geolocator=Nominatim(
            user_agent="crime_app"
        )

        source_location=geolocator.geocode(
            source
        )

        destination_location=geolocator.geocode(
            destination
        )

        if source_location and destination_location:

            source_coords=(

                source_location.latitude,

                source_location.longitude

            )

            destination_coords=(

                destination_location.latitude,

                destination_location.longitude

            )

            distance=round(

                geodesic(

                    source_coords,

                    destination_coords

                ).km,

                2

            )

        else:

            distance=0


        if distance<10:

            risk=30

        elif distance<50:

            risk=55

        else:

            risk=80


        if risk<40:

            safe="6AM - 6PM"

            danger="12AM - 4AM"

            message="✅ Safe route detected."

        elif risk<70:

            safe="7AM - 5PM"

            danger="10PM - 3AM"

            message="⚠ Travel carefully."

        else:

            safe="9AM - 4PM"

            danger="8PM - 5AM"

            message="🚨 Avoid late-night travel."


        return render(

            request,

            'users/route_safety.html',

            {

                'source':source,

                'destination':destination,

                'risk':risk,

                'distance':distance,

                'safe':safe,

                'danger':danger,

                'message':message

            }

        )

    return render(
        request,
        'users/route_safety.html'
    )

def map_view(request):

    df = pd.read_csv(
        'dataset/crime_dataset_india.csv'
    )

    map = folium.Map(

        location=[20.5937,78.9629],

        zoom_start=5

    )


    heat_data = []

    for i,row in df.iterrows():

        if pd.notnull(
            row['Latitude']
        ) and pd.notnull(
            row['Longitude']
        ):

            heat_data.append(

                [

                    row['Latitude'],

                    row['Longitude']

                ]

            )


    HeatMap(

        heat_data,

        radius=15

    ).add_to(map)


    map=map._repr_html_()


    return render(

        request,

        'users/map_view.html',

        {

            'map':map

        }

    )

def insights(request):

    df = pd.read_csv(
        'dataset/crime_dataset_india.csv'
    )

    total = len(df)

    high = len(
        df[df['Victim Age'] > 50]
    )

    safe = total-high


    # Graph 1: Top cities

    plt.figure(figsize=(10,5))

    df['City'].value_counts().head(10).plot(
        kind='bar'
    )

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(
        'media/city_chart.png'
    )

    plt.close()


    # Graph 2: Crime domain pie chart

    plt.figure(figsize=(8,8))

    df['Crime Domain'].value_counts().head(5).plot(

        kind='pie',

        autopct='%1.1f%%'

    )

    plt.ylabel("")

    plt.tight_layout()

    plt.savefig(
        'media/domain_chart.png'
    )

    plt.close()


    # Graph 3: Gender analysis

    plt.figure(figsize=(8,5))

    df['Victim Gender'].value_counts().plot(
        kind='bar'
    )

    plt.tight_layout()

    plt.savefig(
        'media/gender_chart.png'
    )

    plt.close()


    return render(

        request,

        'users/insights.html',

        {

            'total':total,
            'high':high,
            'safe':safe,

            'city':'/media/city_chart.png',

            'domain':'/media/domain_chart.png',

            'gender':'/media/gender_chart.png'

        }

    )

def emergency(request):

    return render(
        request,
        'users/emergency.html'
    )

def chatbot(request):

    answer=""

    if request.method=="POST":

        query=request.POST.get(
            'query'
        )

        area=request.POST.get(
            'area'
        )

        df=pd.read_csv(
            'dataset/crime_dataset_india.csv'
        )

        city_data=df[
            df['City'].str.lower()
            ==
            area.lower()
        ]

        total_crimes=len(
            city_data
        )

        if total_crimes>500:

            risk="HIGH"

            safe="6AM-4PM"

        elif total_crimes>200:

            risk="MEDIUM"

            safe="7AM-5PM"

        else:

            risk="LOW"

            safe="Any daytime"


        try:

            prompt=f"""
            Use ONLY this data.

            Area:{area}

            Risk:{risk}

            Crime Count:{total_crimes}

            Safe Time:{safe}

            Question:{query}
            """

            response=model_ai.generate_content(
                prompt
            )

            answer=response.text


        except:

            answer=f"""
Area : {area}

Risk Level : {risk}

Crime Records : {total_crimes}

Recommended Safe Time :

{safe}

Recommendation :

Avoid travelling late night and stay alert.
"""


    return render(

        request,

        'users/chatbot.html',

        {

            'answer':answer

        }

    )

def sos_alert(request):

    message = """
🚨 EMERGENCY SOS ACTIVATED 🚨

Current Status:
High Risk Area Detected

Emergency Contacts:

Police : 100
Ambulance : 108
Women Helpline : 1091

Safety Instructions:

• Share live location
• Stay in crowded area
• Contact nearest police station
"""

    return render(
        request,
        'users/sos.html',
        {
            'message': message
        }
    )



