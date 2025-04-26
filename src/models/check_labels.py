import joblib

# Path to your label encoder file
label_encoder_path = "label_encoder.pkl"

# Load the encoder
label_encoder = joblib.load(label_encoder_path)

# Print classes
print("📚 Labels in the encoder:")
for idx, label in enumerate(label_encoder.classes_):
    print(f"{idx}: {label}")
