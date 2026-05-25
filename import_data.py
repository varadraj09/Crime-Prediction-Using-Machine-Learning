import os
import django
import pandas as pd

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'crimeprediction.settings'
)

django.setup()

from users.models import CrimeReport

csv_files = [

    'media/chicago_crime_2014.csv',

    'media/chicago_crime_2015.csv',

    'media/chicago_crime_2016.csv'
]

for file in csv_files:

    print(f'Importing {file}...')

    df = pd.read_csv(file)

    df = df.dropna()

    for _, row in df.iterrows():

        try:

            CrimeReport.objects.create(

                PrimaryType=str(row['PrimaryType']),

                LocationDescription=str(
                    row['LocationDescription']
                ),

                District=int(row['District']),

                Ward=int(row['Ward']),

                CommunityArea=int(row['CommunityArea']),

                FBICode=str(row['FBICode']),

                Latitude=float(row['Latitude']),

                Longitude=float(row['Longitude'])
            )

        except Exception as e:

            print("Skipped:", e)

print("Crime data imported successfully")