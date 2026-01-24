import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# Load data
data = pd.read_csv("data/raw/tram_operation.csv")

# Encode weather
data["weather"] = data["weather"].map({
    "clear": 0,
    "wind": 1,
    "rain": 2
})

# Features & target
X = data[["speed_kmh", "passenger_load", "weather"]]
y = data["delay_min"]

# Train / test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Prediction
y_pred = model.predict(X_test)

# Evaluation
mae = mean_absolute_error(y_test, y_pred)

print(f"📊 Mean Absolute Error: {mae:.2f} minutes")

# Save result
with open("results/metrics.txt", "w") as f:
    f.write(f"Delay prediction MAE: {mae:.2f} minutes\n")

print("✅ Delay prediction model trained successfully.")
#“The digital twin integrates an AI model capable of predicting operational delays using real-time variables such as passenger load, speed, and weather. This enables proactive traffic regulation.”