import sys
import os
import csv
import math

# Añadir la ruta raíz para importar la lógica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_logic.physio_model import HeartModel

def run_continuous_validation():
    print("🏃‍♂️ Iniciando Maratón de Validación: Kaggle vs Gemelo Digital...")
    
    # Ruta al dataset gigante
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../05_Data_Ingestion/datasets/heartrate_seconds_merged.csv'))
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: No se encuentra el dataset en {csv_path}")
        print("Asegúrate de que la ruta sea correcta.")
        return

    print("🔍 Extrayendo el evento de entrenamiento (12 de Abril, 13:40 - 13:55)...")
    real_hr_data = []
    
    with open(csv_path, 'r') as file:
        reader = csv.reader(file)
        next(reader) # Saltar cabeceras
        for row in reader:
            if row[0] == "2022484408" and ("4/12/2016 1:4" in row[1] or "4/12/2016 1:5" in row[1]):
                real_hr_data.append(float(row[2]))
                
    if not real_hr_data:
        print("⚠️ No se encontraron datos para ese rango de tiempo.")
        return

    n_samples = len(real_hr_data)
    print(f"✅ ¡Extraídos {n_samples} segundos de datos reales de Kaggle!")

    # 🤖 Inicializar el Gemelo Digital
    twin = HeartModel(age=30, sex='male', resting_hr=62)
    twin.current_hr = real_hr_data[0] 
    
    predicted_hr_data = []
    
    print("⚙️  Ejecutando simulación (Controlador Proporcional / State Observer)...")
    for real_hr in real_hr_data:
        
        # 1. Calcular el "Error" (Diferencia entre la realidad y el Gemelo)
        error = real_hr - twin.current_hr
        
        # 2. Lógica de Seguimiento Automático (Auto-Tuning)
        if error > 2.0:
            # El humano va más rápido. Aceleramos proporcionalmente al error.
            # Multiplicamos por 0.05 para suavizar, y limitamos a 1.0 (máximo esfuerzo)
            intensity = min(1.0, error * 0.05)
        else:
            # El humano va más lento, igual, o está descansando. ¡Freno total!
            intensity = 0.0
        
        # Un paso de simulación
        metrics = twin.simulate_step(intensity=intensity, dt=1.0, temperature=6.19, slope_percent=0.0)
        predicted_hr_data.append(metrics['bpm'])

    # 📊 CÁLCULO DEL ERROR
    print("\n📊 CALCULANDO PRECISIÓN CIENTÍFICA...")
    mse = 0.0
    for real, pred in zip(real_hr_data, predicted_hr_data):
        mse += (real - pred) ** 2
    
    mse = mse / n_samples
    rmse = math.sqrt(mse) 

    print(f"   📈 Error Cuadrático Medio (MSE): {round(mse, 2)}")
    print(f"   🎯 RMSE (Desviación promedio): ±{round(rmse, 2)} BPM")

    print("\n⏱️  MUESTRA (Real vs Twin) - Últimos 10 segundos del dataset:")
    print("---------------------------------------------------")
    print("Segundo | Humano (Kaggle) | Gemelo Digital | Diferencia")
    for i in range(n_samples - 10, n_samples):
        real = round(real_hr_data[i], 1)
        pred = round(predicted_hr_data[i], 1)
        diff = round(abs(real - pred), 1)
        print(f"  {i}   |      {real} BPM   |    {pred} BPM   |  {diff} BPM")
    print("---------------------------------------------------")
    
    if rmse < 10.0:
        print("\n✅ VEREDICTO FINAL: Excelente. Tu gemelo imita la fisiología real con precisión comercial.")
    else:
        print("\n⚠️ VEREDICTO FINAL: Hay margen de mejora. Ajusta el 'tau' o la intensidad en la heurística.")

if __name__ == "__main__":
    run_continuous_validation()