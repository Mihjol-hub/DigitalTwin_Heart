import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, r2_score
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

def train_anesthesia_model():
    print("🧠 Starting the Artificial Intelligence Laboratory...")
    
    # 1. Load the data
    data_path = os.path.join(os.path.dirname(__file__), 'training_data.csv')
    if not os.path.exists(data_path):
        print("❌ Error: Training data not found")
        return
        
    df = pd.read_csv(data_path)
    
    # Create a "Depth Score" from 0 to 100 based on the Propofol
    # ~4.0 is the maximum dose in this patient
    max_propofol = df['Propofol_Level'].max()
    df['Depth_Score'] = (df['Propofol_Level'] / max_propofol) * 100.0
    
    print(f"📊 Data loaded: {len(df)} samples.")
    
    # 2. Define Features and Target
    X = df[['BPM', 'RMSSD']].values
    y = df['Depth_Score'].values
    
    # Separate into Training (80%) and Test (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Normalize the data (super important for Neural Networks)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 3. Build and Train the Neural Network
    print("⚙️ Training Neural Network (Multi-Layer Perceptron)...")
    # Two hidden layers of 16 and 8 neurons
    model = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # 4. Evaluate the AI
    y_pred = model.predict(X_test_scaled)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print("\n✅ Training completed")
    print(f"🎯 Model precision (R2 Score): {r2:.2f} (1.0 is perfect)")
    print(f"📉 Mean Squared Error: {mse:.2f}")
    
    # 5. Export the AI to ONNX (The universal standard for carrying to Rust)
    print("\n📦 Packing the AI into a universal format (ONNX)...")
    
    # Specify that the input is 2 floating point numbers (BPM and RMSSD)
    initial_type = [('float_input', FloatTensorType([None, 2]))]
    
    # Note: In a strict production environment we would also export the 'scaler', 
    # but for the base architecture we export the model pure.
    onnx_model = convert_sklearn(model, initial_types=initial_type)
    
    onnx_path = os.path.join(os.path.dirname(__file__), 'anesthesia_model.onnx')
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())
        
    print(f"🚀 Model exported successfully to {onnx_path}")
    print("Este archivo .onnx es el 'cerebro' que inyectaremos en Rust.")

if __name__ == "__main__":
    train_anesthesia_model()