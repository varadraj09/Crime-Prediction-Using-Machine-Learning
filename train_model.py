import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import pickle

# Load dataset
df = pd.read_csv('dataset/crime_dataset_india.csv')

# Select required columns
df = df[['City', 'Crime Description', 'Victim Age', 'Victim Gender']]

# Remove null values
df.dropna(inplace=True)

# Encode text columns
city_encoder = LabelEncoder()
crime_encoder = LabelEncoder()
gender_encoder = LabelEncoder()

df['City'] = city_encoder.fit_transform(df['City'])
df['Crime Description'] = crime_encoder.fit_transform(df['Crime Description'])
df['Victim Gender'] = gender_encoder.fit_transform(df['Victim Gender'])

# Features
X = df[['City', 'Victim Age', 'Victim Gender']]

# Target
y = df['Crime Description']

# Train model
model = RandomForestClassifier()

model.fit(X, y)

# Save model
pickle.dump(model, open('crime_model.pkl', 'wb'))

# Save encoders
pickle.dump(city_encoder, open('city_encoder.pkl', 'wb'))
pickle.dump(crime_encoder, open('crime_encoder.pkl', 'wb'))
pickle.dump(gender_encoder, open('gender_encoder.pkl', 'wb'))

print("Indian Crime Model Trained Successfully")