import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Manually defined data samples
data = [
    {"cpu": 10, "memory": 20, "network": 15, "allocated_server": "AWS"},
    {"cpu": 15, "memory": 25, "network": 20, "allocated_server": "GCP"},
    {"cpu": 12, "memory": 22, "network": 18, "allocated_server": "Azure"},
    {"cpu": 50, "memory": 60, "network": 70, "allocated_server": "Azure"},
    {"cpu": 5, "memory": 10, "network": 8, "allocated_server": "AWS"},
    {"cpu": 25, "memory": 35, "network": 30, "allocated_server": "GCP"},
    {"cpu": 80, "memory": 85, "network": 90, "allocated_server": "Azure"},
    {"cpu": 18, "memory": 20, "network": 15, "allocated_server": "AWS"},
    {"cpu": 22, "memory": 28, "network": 26, "allocated_server": "GCP"},
]

# Convert to DataFrame
df = pd.DataFrame(data)

# Define features and labels
FEATURES = ["cpu", "memory", "network"]  # Explicit feature names
X = df[FEATURES]
y = df["allocated_server"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Accuracy check (optional)
accuracy = model.score(X_test, y_test)
print(f" Model Accuracy: {accuracy:.2f}")

# Save model with metadata
model_metadata = {
    "model": model,
    "features": FEATURES  # Save feature names
}

joblib.dump(model_metadata, "load_balancer.pkl")
print(" Model saved as load_balancer.pkl")
