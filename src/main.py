import sys, os
sys.path.append(os.path.dirname(__file__))

import Data_generation
import fill_mysql
import read_data

print("🚊 Digital Twin Tramway RATP Dev - Casablanca")

print("\n1️⃣ Génération des données...")
Data_generation.generate()

print("\n2️⃣ Remplissage de la base MySQL...")
fill_mysql.fill_database()

print("\n3️⃣ Lecture des données...")
read_data.read_all()

