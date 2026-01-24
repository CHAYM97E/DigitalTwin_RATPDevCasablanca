import mysql.connector

def read_all():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="3Mama1baba@",
        database="tram_rATP"
    )
    cursor = conn.cursor()

    print("\n📍 LISTE DES ARRÊTS")
    cursor.execute("SELECT * FROM stops")
    for row in cursor.fetchall():
        print(row)

    print("\n⏱️ RETARDS DES TRAMS")
    cursor.execute("SELECT tram_id, delay_minutes FROM tram_operations LIMIT 10")
    for row in cursor.fetchall():
        print(row)

    print("\n🛠️ MAINTENANCE")
    cursor.execute("SELECT tram_id, component, temperature, vibration FROM maintenance LIMIT 10")
    for row in cursor.fetchall():
        print(row)

    cursor.close()
    conn.close()
