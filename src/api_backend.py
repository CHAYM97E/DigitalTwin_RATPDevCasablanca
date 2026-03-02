"""
Flask REST API for Predictive Maintenance Integration
Connects ML engine with Digital Twin frontend
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime
import sys
import os
import numpy as np




# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  # Enable CORS for frontend integration


@app.route("/", methods=["GET"])
def frontend():
    return render_template("index.html")


from Predictive_maintenance import (
    CasablancaFleetMonitor,
    PredictiveMaintenanceEngine,
    ComponentType,
    prediction_to_dict
)


# Initialize monitoring system
fleet_monitor = CasablancaFleetMonitor()
engine = PredictiveMaintenanceEngine()


@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'RATP Dev Casablanca Predictive Maintenance API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/fleet/summary', methods=['GET'])
def get_fleet_summary():
    """
    Get fleet-wide health summary
    Returns aggregated metrics for all vehicles
    """
    try:
        summary = fleet_monitor.get_fleet_health_summary()
        
        # Convert predictions to serializable format
        serialized_predictions = {
            'critical': [prediction_to_dict(p) for p in summary['predictions']['critical']],
            'warning': [prediction_to_dict(p) for p in summary['predictions']['warning']],
            'normal': [prediction_to_dict(p) for p in summary['predictions']['normal'][:10]]  # Limit normal
        }
        
        return jsonify({
            'success': True,
            'data': {
                'total_vehicles': summary['total_vehicles'],
                'critical_count': summary['critical_count'],
                'warning_count': summary['warning_count'],
                'normal_count': summary['normal_count'],
                'fleet_health_score': round(summary['fleet_health_score'], 1),
                'predictions': serialized_predictions,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/vehicle/<vehicle_id>/prediction', methods=['GET'])
def get_vehicle_prediction(vehicle_id):
    """
    Get real-time prediction for specific vehicle
    Example: /api/vehicle/T1-001/prediction
    """
    try:
        # Extract line from vehicle_id
        line = vehicle_id.split('-')[0]
        
        # Simulate sensor reading for this vehicle
        reading = engine.simulate_sensor_data(
            vehicle_id=vehicle_id,
            line=line,
            station_idx=0,
            is_faulty=False  # Will be random in real system
        )
        
        # Get prediction
        prediction = engine.predict(reading, ComponentType.AIR_PRODUCTION_UNIT)
        
        return jsonify({
            'success': True,
            'data': prediction_to_dict(prediction)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/vehicle/<vehicle_id>/sensors', methods=['GET'])
def get_vehicle_sensors(vehicle_id):
    """
    Get current sensor readings for a vehicle
    """
    try:
        line = vehicle_id.split('-')[0]
        
        reading = engine.simulate_sensor_data(
            vehicle_id=vehicle_id,
            line=line,
            station_idx=0
        )
        
        return jsonify({
            'success': True,
            'data': {
                'vehicle_id': reading.vehicle_id,
                'timestamp': reading.timestamp.isoformat(),
                'sensors': {
                    'air_pressure_tp2': round(reading.tp2_pressure, 2),
                    'air_pressure_tp3': round(reading.tp3_pressure, 2),
                    'compressor_temperature': round(reading.h1_temperature, 1),
                    'motor_current': round(reading.motor_current, 1),
                    'oil_temperature': round(reading.oil_temperature, 1),
                    'differential_pressure': round(reading.dv_pressure, 2),
                    'reservoir_pressure': round(reading.reservoirs_pressure, 2),
                    'speed': round(reading.speed, 1),
                    'compressor_status': reading.comp_status,
                    'dryer_status': reading.dryer_status,
                    'governor_status': reading.mpg_status
                },
                'location': {
                    'latitude': round(reading.latitude, 6),
                    'longitude': round(reading.longitude, 6)
                },
                'environment': {
                    'ambient_temperature': round(reading.ambient_temperature, 1),
                    'humidity': round(reading.humidity, 1)
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/alerts', methods=['GET'])
def get_active_alerts():
    """
    Get all active maintenance alerts
    """
    try:
        summary = fleet_monitor.get_fleet_health_summary()
        
        # Combine critical and warning
        alerts = []
        
        for pred in summary['predictions']['critical']:
            alerts.append({
                **prediction_to_dict(pred),
                'alert_level': 'CRITICAL',
                'priority': 1
            })
        
        for pred in summary['predictions']['warning']:
            alerts.append({
                **prediction_to_dict(pred),
                'alert_level': 'WARNING',
                'priority': 2
            })
        
        # Sort by priority and failure probability
        alerts.sort(key=lambda x: (x['priority'], -x['failure_probability']))
        
        return jsonify({
            'success': True,
            'data': {
                'total_alerts': len(alerts),
                'critical_alerts': len(summary['predictions']['critical']),
                'warning_alerts': len(summary['predictions']['warning']),
                'alerts': alerts,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/line/<line_id>/health', methods=['GET'])
def get_line_health(line_id):
    """
    Get health summary for specific line (T1, T2, T3, T4)
    """
    try:
        summary = fleet_monitor.get_fleet_health_summary()
        
        # Filter predictions for this line
        line_predictions = {
            'critical': [p for p in summary['predictions']['critical'] if p.vehicle_id.startswith(line_id)],
            'warning': [p for p in summary['predictions']['warning'] if p.vehicle_id.startswith(line_id)],
            'normal': [p for p in summary['predictions']['normal'] if p.vehicle_id.startswith(line_id)]
        }
        
        total = sum(len(v) for v in line_predictions.values())
        
        return jsonify({
            'success': True,
            'data': {
                'line_id': line_id,
                'total_vehicles': total,
                'critical_count': len(line_predictions['critical']),
                'warning_count': len(line_predictions['warning']),
                'normal_count': len(line_predictions['normal']),
                'line_health_score': (len(line_predictions['normal']) / total * 100) if total > 0 else 0,
                'predictions': {
                    'critical': [prediction_to_dict(p) for p in line_predictions['critical']],
                    'warning': [prediction_to_dict(p) for p in line_predictions['warning']],
                    'normal': [prediction_to_dict(p) for p in line_predictions['normal'][:5]]
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/maintenance/schedule', methods=['POST'])
def schedule_maintenance():
    """
    Schedule maintenance based on predictions
    Expects: {"vehicle_id": "T1-001", "maintenance_type": "PREVENTIVE", "scheduled_time": "2026-01-29T10:00:00"}
    """
    try:
        data = request.json
        
        # In real system, this would update database and notify maintenance team
        return jsonify({
            'success': True,
            'data': {
                'vehicle_id': data.get('vehicle_id'),
                'maintenance_type': data.get('maintenance_type'),
                'scheduled_time': data.get('scheduled_time'),
                'status': 'SCHEDULED',
                'confirmation_id': f"MAINT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/statistics/daily', methods=['GET'])
def get_daily_statistics():
    """
    Get daily statistics for dashboard charts
    """
    # Generate historical data for charts
    hours = list(range(24))
    
    # Simulate daily health trend
    health_scores = [92 - (i * 0.5) + np.random.uniform(-2, 2) for i in range(24)]
    
    # Simulate failure predictions per hour
    failure_predictions = [int(32 * (1 + 0.3 * np.sin(i/4)) + np.random.uniform(-3, 3)) for i in range(24)]
    
    # Simulate alerts per hour
    alerts_per_hour = [int(5 * (1 + 0.5 * np.sin(i/3)) + np.random.uniform(-1, 1)) for i in range(24)]
    
    return jsonify({
        'success': True,
        'data': {
            'hours': [f"{h:02d}:00" for h in hours],
            'fleet_health_scores': [round(s, 1) for s in health_scores],
            'failure_predictions': failure_predictions,
            'alerts_generated': alerts_per_hour,
            'maintenance_scheduled': [int(a * 0.3) for a in alerts_per_hour]
        }
    })


@app.route('/api/components/health', methods=['GET'])
def get_components_health():
    """
    Get health status for all component types
    """
    components_status = []
    
    for component in ComponentType:
        # Simulate component health
        health = np.random.uniform(75, 98)
        
        components_status.append({
            'component': component.value,
            'health_score': round(health, 1),
            'status': 'GOOD' if health > 85 else 'DEGRADED',
            'vehicles_affected': int((100 - health) * 2) if health < 85 else 0,
            'next_maintenance': datetime.now().isoformat()
        })
    
    return jsonify({
        'success': True,
        'data': components_status
    })


if __name__ == '__main__':
    print("\n🚋 RATP Dev Casablanca - Predictive Maintenance API")
    print("=" * 60)
    print("Starting API server on http://localhost:5001")
    print("\nAvailable endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/fleet/summary")
    print("  GET  /api/vehicle/<vehicle_id>/prediction")
    print("  GET  /api/vehicle/<vehicle_id>/sensors")
    print("  GET  /api/alerts")
    print("  GET  /api/line/<line_id>/health")
    print("  POST /api/maintenance/schedule")
    print("  GET  /api/statistics/daily")
    print("  GET  /api/components/health")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)