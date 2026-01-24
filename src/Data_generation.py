"""
Générateur de données RÉALISTES pour maintenance prédictive
Simule des capteurs industriels avec patterns de dégradation réels
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

RAW_PATH = "../data/raw"
os.makedirs(RAW_PATH, exist_ok=True)

# ============================================================================
# PARAMÈTRES PHYSIQUES RÉALISTES (basés sur standards industriels)
# ============================================================================

COMPONENT_SPECS = {
    'motor': {
        'temp_nominal': 65,
        'temp_max': 95,
        'vibration_nominal': 3.5,
        'vibration_max': 8.0,
        'mtbf': 8000,  # Mean Time Between Failures (heures)
        'degradation_rate': 0.0001
    },
    'brake': {
        'temp_nominal': 70,
        'temp_max': 110,
        'vibration_nominal': 4.0,
        'vibration_max': 9.0,
        'mtbf': 6000,
        'degradation_rate': 0.00015
    },
    'door': {
        'temp_nominal': 45,
        'temp_max': 60,
        'vibration_nominal': 2.5,
        'vibration_max': 6.0,
        'mtbf': 10000,
        'degradation_rate': 0.00008
    },
    'pantograph': {
        'temp_nominal': 55,
        'temp_max': 85,
        'vibration_nominal': 3.0,
        'vibration_max': 7.5,
        'mtbf': 7000,
        'degradation_rate': 0.00012
    },
    'hvac': {
        'temp_nominal': 50,
        'temp_max': 75,
        'vibration_nominal': 2.0,
        'vibration_max': 5.0,
        'mtbf': 12000,
        'degradation_rate': 0.00006
    },
    'suspension': {
        'temp_nominal': 40,
        'temp_max': 65,
        'vibration_nominal': 3.5,
        'vibration_max': 8.5,
        'mtbf': 9000,
        'degradation_rate': 0.0001
    }
}

# ============================================================================
# GÉNÉRATEUR DE DONNÉES AVEC PHYSIQUE RÉALISTE
# ============================================================================

def generate_realistic_sensor_data(component_type, days_since_maintenance, 
                                   weather='clear', load=150, incident=False):
    """
    Génère des données de capteurs réalistes avec patterns de dégradation
    
    Paramètres:
        component_type: Type de composant
        days_since_maintenance: Jours depuis dernière maintenance
        weather: Conditions météo
        load: Charge (passagers)
        incident: Incident récent
    
    Returns:
        dict avec température, vibration, health_score
    """
    
    specs = COMPONENT_SPECS[component_type]
    
    # === TEMPÉRATURE ===
    # Base nominale + drift temporel + facteurs externes
    temp_base = specs['temp_nominal']
    temp_drift = days_since_maintenance * specs['degradation_rate'] * 30
    
    # Facteurs environnementaux
    weather_factor = {'clear': 0, 'rain': -2, 'wind': 1}[weather]
    load_factor = (load - 150) / 50 * 3  # +3°C par 50 passagers supplémentaires
    incident_factor = 15 if incident else 0
    
    # Bruit gaussien (variation naturelle)
    noise = np.random.normal(0, 2)
    
    temperature = temp_base + temp_drift + weather_factor + load_factor + incident_factor + noise
    temperature = np.clip(temperature, temp_base - 5, specs['temp_max'])
    
    # === VIBRATION ===
    vib_base = specs['vibration_nominal']
    vib_drift = days_since_maintenance * specs['degradation_rate'] * 20
    
    # Vibration augmente avec usure et température excessive
    temp_effect = max(0, (temperature - temp_base) / 10 * 0.5)
    load_effect = (load - 150) / 100 * 0.3
    incident_effect = 2.5 if incident else 0
    
    noise_vib = np.random.normal(0, 0.3)
    
    vibration = vib_base + vib_drift + temp_effect + load_effect + incident_effect + noise_vib
    vibration = np.clip(vibration, vib_base - 0.5, specs['vibration_max'])
    
    # === SCORE DE SANTÉ (0-100) ===
    temp_health = max(0, 100 - (temperature - temp_base) / (specs['temp_max'] - temp_base) * 100)
    vib_health = max(0, 100 - (vibration - vib_base) / (specs['vibration_max'] - vib_base) * 100)
    age_health = max(0, 100 - days_since_maintenance / 180 * 100)
    
    health_score = (temp_health * 0.35 + vib_health * 0.35 + age_health * 0.30)
    
    # === PROBABILITÉ DE PANNE ===
    # Modèle de Weibull simplifié (standard industriel)
    failure_base = (days_since_maintenance / specs['mtbf'] * 100) ** 1.5
    temp_risk = max(0, (temperature - temp_base) / 10) * 5
    vib_risk = max(0, (vibration - vib_base) / 2) * 8
    
    failure_probability = np.clip(failure_base + temp_risk + vib_risk, 0, 100)
    
    # Panne réelle si probabilité > seuil aléatoire
    failure = failure_probability > np.random.uniform(85, 95)
    
    return {
        'temperature': round(temperature, 2),
        'vibration': round(vibration, 2),
        'health_score': round(health_score, 1),
        'failure_probability': round(failure_probability, 1),
        'failure': int(failure)
    }


def generate_enhanced_maintenance_data():
    """Génère un dataset de maintenance avec patterns réalistes"""
    
    print("🔧 Génération de données de maintenance réalistes...")
    
    trams = [f"T{line}-{str(i).zfill(3)}" for line in [1,2,3,4] for i in range(1, 11)]
    components = list(COMPONENT_SPECS.keys())
    weather_conditions = ['clear', 'rain', 'wind']
    
    records = []
    
    for tram_id in trams:
        for component in components:
            # Nombre de relevés par tramway (historique)
            n_readings = np.random.randint(20, 40)
            
            # Date de dernière maintenance (variable)
            last_maintenance = datetime.now() - timedelta(days=np.random.randint(1, 180))
            
            for reading_idx in range(n_readings):
                # Timestamp progressif
                timestamp = last_maintenance + timedelta(hours=reading_idx * 6)
                days_since = (datetime.now() - last_maintenance).days
                
                # Conditions opérationnelles variables
                hour = timestamp.hour
                is_peak = (7 <= hour <= 9) or (17 <= hour <= 19)
                
                passenger_load = np.random.randint(200, 280) if is_peak else np.random.randint(50, 150)
                weather = np.random.choice(weather_conditions, p=[0.7, 0.2, 0.1])
                incident = np.random.random() < 0.03  # 3% d'incidents
                
                # Générer les données de capteurs
                sensor_data = generate_realistic_sensor_data(
                    component, 
                    days_since, 
                    weather, 
                    passenger_load,
                    incident
                )
                
                # Enregistrement complet
                record = {
                    'tram_id': tram_id,
                    'component': component,
                    'timestamp': timestamp,
                    'days_since_last_maintenance': days_since,
                    'temperature': sensor_data['temperature'],
                    'vibration': sensor_data['vibration'],
                    'health_score': sensor_data['health_score'],
                    'passenger_load': passenger_load,
                    'weather': weather,
                    'incident_flag': int(incident),
                    'failure_probability': sensor_data['failure_probability'],
                    'failure': sensor_data['failure']
                }
                
                records.append(record)
    
    # Créer DataFrame
    df = pd.DataFrame(records)
    
    # Sauvegarder
    csv_path = f"{RAW_PATH}/maintenance_realistic.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"✅ {len(df)} enregistrements générés")
    print(f"📊 Distribution des pannes: {df['failure'].sum()} pannes ({df['failure'].mean()*100:.1f}%)")
    print(f"💾 Sauvegardé: {csv_path}")
    
    return df


def generate_time_series_data():
    """Génère des séries temporelles pour LSTM"""
    
    print("\n📈 Génération de séries temporelles pour LSTM...")
    
    trams = [f"T1-{str(i).zfill(3)}" for i in range(1, 6)]
    component = 'motor'
    
    all_series = []
    
    for tram_id in trams:
        # Série de 180 jours (6 mois)
        start_date = datetime.now() - timedelta(days=180)
        
        # État initial
        last_maintenance_days = 0
        
        for day in range(180):
            timestamp = start_date + timedelta(days=day)
            
            # Données horaires (24 points par jour)
            for hour in range(0, 24, 3):  # Tous les 3 heures
                current_time = timestamp + timedelta(hours=hour)
                last_maintenance_days = day
                
                # Conditions
                is_peak = (7 <= hour <= 9) or (17 <= hour <= 19)
                load = np.random.randint(200, 280) if is_peak else np.random.randint(50, 150)
                weather = np.random.choice(['clear', 'rain'], p=[0.8, 0.2])
                
                # Générer capteurs
                data = generate_realistic_sensor_data(
                    component, last_maintenance_days, weather, load, False
                )
                
                record = {
                    'tram_id': tram_id,
                    'component': component,
                    'timestamp': current_time,
                    'hour': hour,
                    'day_of_week': current_time.weekday(),
                    'days_since_maintenance': last_maintenance_days,
                    'temperature': data['temperature'],
                    'vibration': data['vibration'],
                    'health_score': data['health_score'],
                    'passenger_load': load,
                    'weather': weather,
                    'failure': data['failure']
                }
                
                all_series.append(record)
    
    df = pd.DataFrame(all_series)
    
    # Sauvegarder
    csv_path = f"{RAW_PATH}/timeseries_lstm.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"✅ {len(df)} points temporels générés")
    print(f"💾 Sauvegardé: {csv_path}")
    
    return df


# ============================================================================
# SCRIPT PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🏭 GÉNÉRATEUR DE DONNÉES INDUSTRIELLES RÉALISTES")
    print("=" * 70)
    
    # Générer maintenance
    df_maint = generate_enhanced_maintenance_data()
    
    # Générer séries temporelles
    df_ts = generate_time_series_data()
    
    print("\n" + "=" * 70)
    print("✅ GÉNÉRATION TERMINÉE")
    print("=" * 70)
    print(f"\n📁 Fichiers créés dans: {RAW_PATH}/")
    print("   - maintenance_realistic.csv")
    print("   - timeseries_lstm.csv")