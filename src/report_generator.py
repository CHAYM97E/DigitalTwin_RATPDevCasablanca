"""
Module de génération de rapports PDF
Compatible avec votre structure de projet
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import mysql.connector
from datetime import datetime
import os

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '3Mama1baba@',
    'database': 'tram_rATP'
}

# Chemins adaptés à votre structure
REPORTS_DIR = "../reports/pdf"
FIGURES_DIR = "../reports/figures"

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)


def generate_daily_report(date=None):
    """Génère un rapport quotidien PDF professionnel"""
    
    if date is None:
        date = datetime.now()
    
    print(f"📊 Génération du rapport pour {date.strftime('%d/%m/%Y')}...")
    
    # Connexion DB
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # ========================================================================
    # COLLECTE DES DONNÉES
    # ========================================================================
    
    # Stats globales
    cursor.execute("""
    SELECT 
        COUNT(*) as total_operations,
        COUNT(DISTINCT tram_id) as active_trams,
        AVG(delay_minutes) as avg_delay,
        MAX(delay_minutes) as max_delay,
        SUM(passenger_load) as total_passengers,
        AVG(passenger_load) as avg_passengers,
        SUM(incident_flag) as total_incidents
    FROM tram_operations
    """)
    global_stats = cursor.fetchone()
    
    # Stats par ligne
    cursor.execute("""
    SELECT 
        SUBSTRING(tram_id, 1, 2) as line,
        COUNT(*) as operations,
        AVG(delay_minutes) as avg_delay,
        AVG(passenger_load) as avg_passengers
    FROM tram_operations
    GROUP BY line
    ORDER BY line
    """)
    line_stats = cursor.fetchall()
    
    # Stats horaires
    cursor.execute("""
    SELECT 
        HOUR(timestamp) as hour,
        AVG(delay_minutes) as avg_delay,
        AVG(passenger_load) as avg_passengers
    FROM tram_operations
    GROUP BY hour
    ORDER BY hour
    """)
    hourly_stats = cursor.fetchall()
    
    # Alertes maintenance
    cursor.execute("""
    SELECT 
        tram_id, component, temperature, vibration, failure
    FROM maintenance
    WHERE temperature > 70 OR vibration > 5 OR failure = 1
    LIMIT 10
    """)
    maintenance_alerts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # ========================================================================
    # GÉNÉRATION DES GRAPHIQUES
    # ========================================================================
    
    print("📈 Génération des graphiques...")
    
    # Graphique 1: Retards horaires
    if hourly_stats:
        df_hourly = pd.DataFrame(hourly_stats)
        plt.figure(figsize=(10, 5))
        plt.bar(df_hourly['hour'], df_hourly['avg_delay'], color='#FF6B35', alpha=0.7)
        plt.xlabel('Heure', fontsize=12)
        plt.ylabel('Retard moyen (min)', fontsize=12)
        plt.title('Distribution des retards par heure', fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        chart1_path = f"{FIGURES_DIR}/hourly_delays.png"
        plt.savefig(chart1_path, dpi=150, bbox_inches='tight')
        plt.close()
    
    # Graphique 2: Performance par ligne
    if line_stats:
        df_lines = pd.DataFrame(line_stats)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        ax1.bar(df_lines['line'], df_lines['avg_delay'], color='#EF4444')
        ax1.set_ylabel('Retard moyen (min)')
        ax1.set_title('Retards par ligne')
        ax1.grid(axis='y', alpha=0.3)
        
        ax2.bar(df_lines['line'], df_lines['avg_passengers'], color='#10B981')
        ax2.set_ylabel('Passagers moyens')
        ax2.set_title('Fréquentation par ligne')
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        chart2_path = f"{FIGURES_DIR}/line_performance.png"
        plt.savefig(chart2_path, dpi=150, bbox_inches='tight')
        plt.close()
    
    # ========================================================================
    # CRÉATION DU PDF
    # ========================================================================
    
    print("📄 Création du PDF...")
    
    filename = f"{REPORTS_DIR}/rapport_{date.strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#334155'),
        spaceAfter=12
    )
    
    # ===== PAGE DE GARDE =====
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("🚊 RAPPORT QUOTIDIEN", title_style))
    story.append(Paragraph("Digital Twin - RATP Dev Casablanca", styles['Heading2']))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Date: {date.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Paragraph(f"Généré: {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
    story.append(PageBreak())
    
    # ===== RÉSUMÉ EXÉCUTIF =====
    story.append(Paragraph("📊 RÉSUMÉ EXÉCUTIF", heading_style))
    
    on_time_rate = 100 - (global_stats['avg_delay'] / 5 * 100) if global_stats['avg_delay'] else 100
    
    summary_data = [
        ['Indicateur', 'Valeur', 'Statut'],
        ['Tramways actifs', str(global_stats['active_trams']), '✅'],
        ['Total opérations', str(global_stats['total_operations']), '✅'],
        ['Retard moyen', f"{global_stats['avg_delay']:.2f} min", 
         '✅' if global_stats['avg_delay'] < 3 else '⚠️'],
        ['Ponctualité', f"{on_time_rate:.1f}%", 
         '✅' if on_time_rate > 90 else '⚠️'],
        ['Passagers totaux', f"{global_stats['total_passengers']:,}", '✅'],
        ['Incidents', str(global_stats['total_incidents']), 
         '✅' if global_stats['total_incidents'] < 5 else '⚠️']
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ===== GRAPHIQUES =====
    if os.path.exists(chart1_path):
        story.append(Paragraph("📈 RETARDS HORAIRES", heading_style))
        story.append(Image(chart1_path, width=6*inch, height=3*inch))
        story.append(Spacer(1, 0.2*inch))
    
    if os.path.exists(chart2_path):
        story.append(Paragraph("🚃 PERFORMANCE PAR LIGNE", heading_style))
        story.append(Image(chart2_path, width=6*inch, height=3*inch))
        story.append(PageBreak())
    
    # ===== ALERTES MAINTENANCE =====
    story.append(Paragraph("🔧 ALERTES MAINTENANCE", heading_style))
    
    if maintenance_alerts:
        alert_data = [['Tram', 'Composant', 'Temp (°C)', 'Vibration', 'État']]
        for alert in maintenance_alerts:
            alert_data.append([
                alert['tram_id'],
                alert['component'],
                f"{alert['temperature']:.1f}",
                f"{alert['vibration']:.2f}",
                '🔴 Panne' if alert['failure'] else '🟡 Risque'
            ])
        
        alert_table = Table(alert_data)
        alert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(alert_table)
    else:
        story.append(Paragraph("✅ Aucune alerte critique", styles['Normal']))
    
    # ===== FOOTER =====
    story.append(PageBreak())
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        "Document généré automatiquement par le Digital Twin RATP Dev",
        ParagraphStyle('Footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Construire le PDF
    doc.build(story)
    
    print(f"✅ Rapport généré: {filename}")
    return filename


if __name__ == "__main__":
    print("=" * 70)
    print("📋 GÉNÉRATEUR DE RAPPORTS PDF")
    print("=" * 70)
    
    report_path = generate_daily_report()
    
    print("=" * 70)
    print(f"✅ Rapport disponible: {report_path}")
    print("=" * 70)