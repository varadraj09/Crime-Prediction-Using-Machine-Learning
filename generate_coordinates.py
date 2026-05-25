import pandas as pd
from geopy.geocoders import Nominatim
import time

df = pd.read_csv(
    'dataset/crime_dataset_india.csv'
)

geolocator = Nominatim(
    user_agent="crime_app"
)

# unique cities only
unique_cities = df['City'].dropna().unique()

city_coordinates = {}

for city in unique_cities:

    try:

        location = geolocator.geocode(
            city + ", India"
        )

        if location:

            city_coordinates[city] = [

                location.latitude,

                location.longitude

            ]

        else:

            city_coordinates[city] = [

                None,

                None

            ]

    except:

        city_coordinates[city] = [

            None,

            None

        ]

    print("Done:", city)

    time.sleep(1)


df['Latitude'] = df['City'].map(

    lambda x: city_coordinates.get(
        x,
        [None,None]
    )[0]
)

df['Longitude'] = df['City'].map(

    lambda x: city_coordinates.get(
        x,
        [None,None]
    )[1]
)

df.to_csv(

'dataset/crime_dataset_india.csv',

index=False

)

print(
"Coordinates Added Successfully"
)