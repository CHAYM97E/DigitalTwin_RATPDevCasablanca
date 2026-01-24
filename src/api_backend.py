"""
API Backend REST complète pour le Digital Twin
Endpoints pour ML, analytics, et données temps réel
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
import os

app = Flask(__name__)
CORS(app)

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '3Mama1baba@',
    'database': 'tram_rATP'
}

MODELS_DIR = "../data/processed"
os.makedirs(MODELS_DIR, exist_ok=True)

# ============================================================================
# CLASSE DE GESTION DES MODÈLES ML
# ============================================================================

class MLModels:
    """Gestionnaire centralisé des modèles ML"""
    
    def __init__(self):
        self.delay_model = None
        self.maintenance_model = None
        self.delay_metrics = {}
        self.maintenance_metrics = {}
        
    def load_models(self):
        """Charge les modèles depuis le disque"""
        try:
            delay_path = f"{MODELS_DIR}/delay_model.pkl"
            maint_path = f"{MODELS_DIR}/maintenance_model.pkl"
            
            if os.path.exists(delay_path):
                with open(delay_path, 'rb') as f:
                    self.delay_model = pickle.load(f)
                print("✅ Modèle de retard chargé")
            
            if os.path.exists(maint_path):
                with open(maint_path, 'rb') as f:
                    self.maintenance_model = pickle.load(f)
                print("✅ Modèle de maintenance chargé")
                
        except Exception as e:
            print(f"⚠️  Erreur chargement modèles: {e}")
    
    def train_delay_model(self):
        """Entraîne le modèle de prédiction des retards"""
        conn = mysql.connector.connect(**DB_CONFIG)
        
        query = """
        SELECT passenger_load, weather, incident_flag, delay_minutes
        FROM tram_operations
        WHERE delay_minutes IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Encoder
        df['weather'] = df['weather'].map({'clear': 0, 'rain': 1, 'wind': 2})
        df = df.fillna(0)
        
        X = df[['passenger_load', 'weather', 'incident_flag']]
        y = df['delay_minutes']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.delay_model = RandomForestRegressor(
            n_estimators=100, 
            max_depth=10,
            random_state=42
        )
        self.delay_model.fit(X_train, y_train)
        
        # Métriques
        from sklearn.metrics import mean_absolute_error, r2_score
        y_pred = self.delay_model.predict(X_test)
        
        self.delay_metrics = {
            'mae': float(mean_absolute_error(y_test, y_pred)),
            'r2': float(r2_score(y_test, y_pred)),
            'rmse': float(np.sqrt(np.mean((y_test - y_pred) ** 2)))
        }
        
        # Sauvegarder
        with open(f"{MODELS_DIR}/delay_model.pkl", 'wb') as f:
            pickle.dump(self.delay_model, f)
        
        return self.delay_metrics
    
    def train_maintenance_model(self):
        """Entraîne le modèle de maintenance prédictive"""
        conn = mysql.connector.connect(**DB_CONFIG)
        
        query = """
        SELECT temperature, vibration, days_since_last_maintenance, failure
        FROM maintenance
        WHERE failure IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        X = df[['temperature', 'vibration', 'days_since_last_maintenance']]
        y = df['failure']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.maintenance_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        self.maintenance_model.fit(X_train, y_train)
        
        # Métriques
        from sklearn.metrics import accuracy_score, precision_score, recall_score
        y_pred = self.maintenance_model.predict(X_test)
        
        self.maintenance_metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, zero_division=0))
        }
        
        # Sauvegarder
        with open(f"{MODELS_DIR}/maintenance_model.pkl", 'wb') as f:
            pickle.dump(self.maintenance_model, f)
        
        return self.maintenance_metrics
    
    def predict_delay(self, passenger_load, weather, incident_flag):
        """Prédit le retard"""
        if self.delay_model is None:
            return None
        
        weather_map = {'clear': 0, 'rain': 1, 'wind': 2}
        weather_encoded = weather_map.get(weather, 0)
        
        X = np.array([[passenger_load, weather_encoded, incident_flag]])
        prediction = self.delay_model.predict(X)[0]
        
        return max(0, float(prediction))
    
    def predict_maintenance(self, temperature, vibration, days_since):
        """Prédit le risque de panne"""
        if self.maintenance_model is None:
            return None
        
        X = np.array([[temperature, vibration, days_since]])
        prediction = self.maintenance_model.predict(X)[0]
        proba = self.maintenance_model.predict_proba(X)[0]
        
        return {
            'will_fail': bool(prediction),
            'failure_probability': float(proba[1] * 100),
            'risk_level': 'high' if proba[1] > 0.7 else 'medium' if proba[1] > 0.4 else 'low'
        }

# Instance globale
ml_models = MLModels()

# ============================================================================
# ENDPOINTS API
# ============================================================================

@app.route('/api/status')
def api_status():
    """Statut du système"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM tram_operations")
        total_ops = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT tram_id) FROM tram_operations")
        total_trams = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'online',
            'database': 'connected',
            'total_operations': total_ops,
            'total_trams': total_trams,
            'models': {
                'delay': ml_models.delay_model is not None,
                'maintenance': ml_models.maintenance_model is not None
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/trams')
def get_all_trams():
    """Liste tous les tramways avec leurs statistiques"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
    SELECT 
        tram_id,
        COUNT(*) as total_trips,
        AVG(delay_minutes) as avg_delay,
        MAX(delay_minutes) as max_delay,
        AVG(passenger_load) as avg_passengers,
        MAX(timestamp) as last_seen
    FROM tram_operations
    GROUP BY tram_id
    ORDER BY tram_id
    """)
    
    trams = cursor.fetchall()
    
    # Ajouter les données de maintenance
    for tram in trams:
        cursor.execute("""
        SELECT component, temperature, vibration, failure
        FROM maintenance
        WHERE tram_id = %s
        """, (tram['tram_id'],))
        tram['maintenance'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'count': len(trams),
        'trams': trams
    })

@app.route('/api/operations')
def get_operations():
    """Récupère les opérations avec filtres"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # Paramètres
    tram_id = request.args.get('tram_id')
    limit = int(request.args.get('limit', 100))
    
    query = "SELECT * FROM tram_operations"
    params = []
    
    if tram_id:
        query += " WHERE tram_id = %s"
        params.append(tram_id)
    
    query += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    operations = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'count': len(operations),
        'operations': operations
    })

@app.route('/api/analytics')
def get_analytics():
    """Analytics complètes du réseau"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # Stats globales
    cursor.execute("""
    SELECT 
        COUNT(*) as total_operations,
        COUNT(DISTINCT tram_id) as active_trams,
        AVG(delay_minutes) as avg_delay,
        SUM(passenger_load) as total_passengers,
        SUM(incident_flag) as total_incidents
    FROM tram_operations
    """)
    global_stats = cursor.fetchone()
    
    # Par ligne
    cursor.execute("""
    SELECT 
        SUBSTRING(tram_id, 1, 2) as line,
        COUNT(*) as operations,
        AVG(delay_minutes) as avg_delay,
        AVG(passenger_load) as avg_passengers
    FROM tram_operations
    GROUP BY line
    """)
    line_stats = cursor.fetchall()
    
    # Par heure
    cursor.execute("""
    SELECT 
        HOUR(timestamp) as hour,
        COUNT(*) as operations,
        AVG(delay_minutes) as avg_delay,
        AVG(passenger_load) as avg_passengers
    FROM tram_operations
    GROUP BY hour
    ORDER BY hour
    """)
    hourly_stats = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'global': global_stats,
        'by_line': line_stats,
        'by_hour': hourly_stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/maintenance/alerts')
def maintenance_alerts():
    """Alertes de maintenance critiques"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
    SELECT *
    FROM maintenance
    WHERE temperature > 70 OR vibration > 5 OR failure = 1
    ORDER BY failure DESC, temperature DESC
    """)
    
    alerts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'alerts': alerts,
        'count': len(alerts),
        'critical': len([a for a in alerts if a['failure'] == 1])
    })

@app.route('/api/maintenance/predict', methods=['POST'])
def predict_component_failure():
    """
    Prédit la panne d'un composant avec le système industriel
    
    Body JSON:
    {
        "tram_id": "T1-001",
        "component": "motor",
        "temperature": 75,
        "vibration": 5.2,
        "days_since_maintenance": 45
    }
    """
    try:
        # Charger le système de maintenance prédictive
        import sys
        sys.path.append('../src')
        from predictive_maintenance_industrial import IndustrialPredictiveMaintenanceSystem
        
        system = IndustrialPredictiveMaintenanceSystem()
        
        # Charger les modèles
        import pickle
        component = request.json.get('component', 'motor')
        model_path = f"{MODELS_DIR}/xgb_model_{component}.pkl"
        
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                system.models[component] = pickle.load(f)
            with open(f"{MODELS_DIR}/scaler_{component}.pkl", 'rb') as f:
                system.scalers[component] = pickle.load(f)
            with open(f"{MODELS_DIR}/anomaly_{component}.pkl", 'rb') as f:
                system.anomaly_detectors[component] = pickle.load(f)
        else:
            return jsonify({'error': 'Model not trained. Train models first.'}), 400
        
        # Prédire
        prediction = system.predict_failure_probability(
            request.json.get('tram_id'),
            component,
            request.json
        )
        
        # Ajouter l'explainability
        explanation = system.explain_prediction(component, request.json)
        prediction['explanation'] = explanation
        
        return jsonify(prediction)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/maintenance/rul/<tram_id>/<component>')
def get_remaining_useful_life(tram_id, component):
    """Calcule le RUL (Remaining Useful Life) pour un composant"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
        SELECT *
        FROM maintenance
        WHERE tram_id = %s AND component = %s
        LIMIT 1
        """, (tram_id, component))
        
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not data:
            return jsonify({'error': 'Component not found'}), 404
        
        # Charger le système
        import sys
        sys.path.append('../src')
        from predictive_maintenance_industrial import IndustrialPredictiveMaintenanceSystem
        
        system = IndustrialPredictiveMaintenanceSystem()
        
        # Calculer RUL
        rul = system._calculate_rul(data, 0.5)  # Estimation moyenne
        
        return jsonify({
            'tram_id': tram_id,
            'component': component,
            'remaining_useful_life_days': rul,
            'recommended_maintenance_date': (datetime.now() + timedelta(days=rul)).isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/train', methods=['POST'])
def train_models():
    """Entraîne ou réentraîne les modèles ML"""
    try:
        results = {}
        
        # Entraîner le modèle de retard
        print("🧠 Entraînement du modèle de prédiction des retards...")
        delay_metrics = ml_models.train_delay_model()
        results['delay_model'] = {
            'status': 'success',
            'metrics': delay_metrics
        }
        
        # Entraîner le modèle de maintenance
        print("🔧 Entraînement du modèle de maintenance prédictive...")
        maintenance_metrics = ml_models.train_maintenance_model()
        results['maintenance_model'] = {
            'status': 'success',
            'metrics': maintenance_metrics
        }
        
        return jsonify({
            'status': 'success',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/ml/predict/delay', methods=['POST'])
def predict_delay():
    """Prédit le retard pour des conditions données"""
    data = request.json
    
    if ml_models.delay_model is None:
        return jsonify({
            'error': 'Model not trained. Call /api/ml/train first'
        }), 400
    
    prediction = ml_models.predict_delay(
        data.get('passenger_load', 150),
        data.get('weather', 'clear'),
        data.get('incident_flag', 0)
    )
    
    return jsonify({
        'predicted_delay': prediction,
        'metrics': ml_models.delay_metrics,
        'input': data
    })

@app.route('/api/ml/predict/maintenance', methods=['POST'])
def predict_maintenance():
    """Prédit le risque de panne"""
    data = request.json
    
    if ml_models.maintenance_model is None:
        return jsonify({
            'error': 'Model not trained. Call /api/ml/train first'
        }), 400
    
    prediction = ml_models.predict_maintenance(
        data.get('temperature', 65),
        data.get('vibration', 4),
        data.get('days_since_maintenance', 30)
    )
    
    return jsonify({
        'prediction': prediction,
        'metrics': ml_models.maintenance_metrics,
        'input': data
    })

@app.route('/api/stations')
def get_stations():
    """Liste des stations par ligne"""
    stations = {
        'T1': [
            'Sidi Moumen', 'Nassim', 'Mohammed Zefzaf', 'Centre de maintenance',
            'Hôpital Sidi Moumen', 'Attacharouk', 'Okba Ibnou Nafia', 'Forces Auxiliaires',
            'Hay Raja', 'Ibn Tachfine', 'Hay Mohammadi', 'Achouhada', 'Ali Yata',
            'Grande Ceinture', 'Anciens Abattoirs', 'Bahmad', 'Gare Casa-Voyageurs',
            'Place Al Yassir', 'La Résistance', 'Mohammed Diouri', 'Marché Central',
            'Place Nations-Unies', 'Place Mohammed V', 'Avenue Hassan II', 'Les Hôpitaux',
            'Faculté de Médecine', 'Abdelmoumen', 'Bachkou', 'Mekka', 'Gare Oasis',
            'Panoramique', 'Technopark', 'Zénith', 'Gare Casa-Sud', 'Facultés',
            'Al Laymoun', 'Lissasfa'
        ],
        'T2': [
            'Ain Diab Plage', 'Corniche', 'Boulevard Océan', 'Abdelmoumen',
            'Nations-Unies', 'Mdakra', 'Ali Yata', 'Derb Sultan',
            'Abdellah Ben Cherif', 'Moulay Rachid', 'Derb Mila',
            'Hay Hassani', 'Sidi Bernoussi'
        ],
        'T3': [
            'Gare Casa Port', 'Boulevard Mohammed VI', 'Place Victoire',
            'Mohammed Smiha', 'Derb Sultan', 'Moulay Rachid',
            'Driss El Harti', 'Hay El Wahda'
        ],
        'T4': [
            'Parc Ligue Arabe', 'Place Mohammed V', 'Derb Mila',
            'Moulay Rachid', 'Driss El Harti', 'Place Victoire',
            'Mohammed Erradien'
        ]
    }
    
    return jsonify(stations)

@app.route('/api/report/generate', methods=['POST'])
def generate_report():
    """Déclenche la génération d'un rapport PDF"""
    try:
        import report_generator
        
        date_str = request.args.get('date')
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else None
        
        report_path = report_generator.generate_daily_report(date)
        
        return jsonify({
            'status': 'success',
            'report_path': report_path,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# LANCEMENT DU SERVEUR
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🚊 API BACKEND - DIGITAL TWIN RATP DEV CASABLANCA")
    print("=" * 70)
    
    # Charger les modèles existants
    ml_models.load_models()
    
    print("\n✅ Serveur API démarré sur http://localhost:5001")
    print("\n📊 Endpoints disponibles:")
    print("   - GET  /api/status")
    print("   - GET  /api/trams")
    print("   - GET  /api/operations")
    print("   - GET  /api/analytics")
    print("   - GET  /api/maintenance/alerts")
    print("   - GET  /api/stations")
    print("   - POST /api/ml/train")
    print("   - POST /api/ml/predict/delay")
    print("   - POST /api/ml/predict/maintenance")
    print("   - POST /api/report/generate")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5001)