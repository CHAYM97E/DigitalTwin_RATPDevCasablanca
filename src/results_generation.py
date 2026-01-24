import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Créer le dossier results si non existant
os.makedirs("../results", exist_ok=True)

# ---- 1. Lecture des données ----
delay_data = pd.read_csv("../data/raw/tram_operation.csv")
maintenance_data = pd.read_csv("../data/raw/maintenance.csv")

# ---- 2. Statistiques des retards ----
delay_stats = delay_data["delay_minutes"].describe()
delay_stats.to_csv("../results/delay_statistics.csv")
print("✅ Delay statistics saved.")

# Histogramme des retards
plt.figure(figsize=(8,5))
sns.histplot(delay_data["delay_minutes"], bins=20, kde=True, color="skyblue")
plt.title("Distribution des retards des trams")
plt.xlabel("Minutes de retard")
plt.ylabel("Nombre de trajets")
plt.grid(True)
plt.savefig("../results/delay_histogram.png")
plt.close()
print("✅ Delay histogram saved.")

# ---- 3. Analyse des maintenances ----
# Nombre de défaillances par composant
failures_per_component = maintenance_data.groupby("component")["failure"].sum()
failures_per_component.to_csv("../results/failures_per_component.csv")

plt.figure(figsize=(8,5))
failures_per_component.plot(kind="bar", color="salmon")
plt.title("Défaillances par composant")
plt.xlabel("Composant")
plt.ylabel("Nombre de défaillances")
plt.grid(axis="y")
plt.savefig("../results/failures_per_component.png")
plt.close()
print("✅ Failures per component saved.")

# Corrélation maintenance
corr_matrix = maintenance_data[["temperature", "vibration", "days_since_last_maintenance", "failure"]].corr()
corr_matrix.to_csv("../results/maintenance_correlation.csv")

plt.figure(figsize=(6,5))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm")
plt.title("Corrélation maintenance")
plt.savefig("../results/maintenance_correlation.png")
plt.close()
print("✅ Maintenance correlation matrix saved.")

# ---- 4. Lien retard vs maintenance ----
# On suppose que tram_id est commun aux deux datasets
merged = pd.merge(delay_data, maintenance_data, on="tram_id", how="left")

# Corrélation retard ↔ maintenance
corr_delay_maint = merged[["delay_minutes", "temperature", "vibration", "days_since_last_maintenance", "failure"]].corr()
corr_delay_maint.to_csv("../results/delay_maintenance_correlation.csv")

plt.figure(figsize=(8,6))
sns.heatmap(corr_delay_maint, annot=True, cmap="viridis")
plt.title("Corrélation retards et maintenance")
plt.savefig("../results/delay_maintenance_correlation.png")
plt.close()
print("✅ Delay vs maintenance correlation saved.")

# ---- 5. Estimation économique ----
# On peut définir un coût moyen par minute de retard et par défaillance
cost_per_minute_delay = 50  # € par minute de retard
cost_per_failure = 200      # € par défaillance

total_delay_cost = delay_data["delay_minutes"].sum() * cost_per_minute_delay
total_failure_cost = maintenance_data["failure"].sum() * cost_per_failure

economic_summary = pd.DataFrame({
    "Type": ["Retard total (€)", "Coût défaillances (€)", "Coût total (€)"],
    "Montant": [total_delay_cost, total_failure_cost, total_delay_cost + total_failure_cost]
})

economic_summary.to_csv("../results/economic_summary.csv", index=False)
print("✅ Economic summary saved.")

# ---- 6. Graphique économique ----
plt.figure(figsize=(6,4))
sns.barplot(x="Type", y="Montant", data=economic_summary, palette="Set2")
plt.title("Résumé économique du tram")
plt.ylabel("Montant (€)")
plt.xticks(rotation=15)
plt.savefig("../results/economic_summary.png")
plt.close()
print("✅ Economic summary plot saved.")

print("🎉 All pro results generated successfully!")
