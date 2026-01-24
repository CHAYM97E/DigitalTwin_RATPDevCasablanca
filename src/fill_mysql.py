import mysql.connector
import pandas as pd
import os

RAW_PATH = "data/raw"

def fill_database():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="3Mama1baba@", 
        database="tram_rATP"
    )
    cursor = conn.cursor()

    # 🧨 Supprimer tables
    cursor.execute("DROP TABLE IF EXISTS tram_operations")
    cursor.execute("DROP TABLE IF EXISTS maintenance")
    cursor.execute("DROP TABLE IF EXISTS routes")
    cursor.execute("DROP TABLE IF EXISTS stops")

    # ✅ Création tables
    cursor.execute("""
    CREATE TABLE stops (
        stop_id INT PRIMARY KEY AUTO_INCREMENT,
        stop_name VARCHAR(100),
        zone VARCHAR(50)
    )""")

    cursor.execute("""
    CREATE TABLE routes (
        route_id INT PRIMARY KEY AUTO_INCREMENT,
        line_name VARCHAR(10),
        start_stop_id INT,
        end_stop_id INT,
        num_stops INT,
        FOREIGN KEY (start_stop_id) REFERENCES stops(stop_id),
        FOREIGN KEY (end_stop_id) REFERENCES stops(stop_id)
    )""")

    cursor.execute("""
    CREATE TABLE tram_operations (
        operation_id INT PRIMARY KEY AUTO_INCREMENT,
        tram_id VARCHAR(10),
        station_id VARCHAR(100),
        timestamp DATETIME,
        passenger_load INT,
        weather VARCHAR(10),
        incident_flag BOOLEAN,
        delay_minutes FLOAT
    )""")

    cursor.execute("""
    CREATE TABLE maintenance (
        maintenance_id INT PRIMARY KEY AUTO_INCREMENT,
        tram_id VARCHAR(10),
        component VARCHAR(50),
        days_since_last_maintenance INT,
        temperature FLOAT,
        vibration FLOAT,
        failure BOOLEAN
    )""")

    conn.commit()
    print("✅ Tables created")

    # -------------------------
    # INSERT DATA
    # -------------------------
    stops_df = pd.read_csv(os.path.join(RAW_PATH,"stops.csv"))
    tram_df = pd.read_csv(os.path.join(RAW_PATH,"tram_operation.csv"))
    maint_df = pd.read_csv(os.path.join(RAW_PATH,"maintenance.csv"))

    for _, row in stops_df.iterrows():
        cursor.execute("INSERT INTO stops (stop_name, zone) VALUES (%s,%s)", (row.stop_name,row.zone))

    # route factice
    cursor.execute("INSERT INTO routes (line_name,start_stop_id,end_stop_id,num_stops) VALUES (%s,%s,%s,%s)",
                   ("T1",1,len(stops_df),len(stops_df)))

    for _, row in tram_df.iterrows():
        cursor.execute("""
        INSERT INTO tram_operations (tram_id,station_id,timestamp,passenger_load,weather,incident_flag,delay_minutes)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (row.tram_id,row.station_id,row.timestamp,row.passenger_load,row.weather,row.incident_flag,row.delay_minutes))

    for _, row in maint_df.iterrows():
        cursor.execute("""
        INSERT INTO maintenance (tram_id,component,days_since_last_maintenance,temperature,vibration,failure)
        VALUES (%s,%s,%s,%s,%s,%s)
        """, (row.tram_id,row.component,row.days_since_last_maintenance,row.temperature,row.vibration,row.failure))

    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 MySQL filled with professional data")
