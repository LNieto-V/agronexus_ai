import datetime
import io
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fpdf import FPDF
from typing import List, Dict, Any, Optional

def sanitize_text(text: str) -> str:
    """Elimina emojis y caracteres no soportados."""
    if not text: return ""
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text

class AgriReport(FPDF):
    def header(self):
        # Fondo decorativo
        self.set_fill_color(245, 250, 245)
        self.rect(0, 0, 210, 45, 'F')
        
        # Logo
        self.set_fill_color(45, 211, 111) 
        self.ellipse(10, 10, 14, 14, 'F')
        
        self.set_xy(28, 12)
        self.set_font("helvetica", "B", 18)
        self.set_text_color(30, 41, 59)
        self.cell(40, 10, "AgroNexus", ln=False)
        self.set_text_color(45, 211, 111)
        self.cell(20, 10, "AI", ln=True)
        
        self.set_xy(28, 20)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(100, 5, "Intelligence for Precision Agriculture", ln=True)
        
        self.set_xy(140, 15)
        self.set_font("helvetica", "B", 9)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(30, 41, 59)
        self.cell(60, 8, "TECHNICAL HEALTH REPORT", ln=True, align="C", fill=True)
        self.ln(25)

    def chapter_title(self, title):
        self.set_font("helvetica", "B", 11)
        self.set_text_color(30, 41, 59)
        self.set_fill_color(241, 245, 249)
        self.cell(0, 8, f"  {title}", ln=True, fill=True)
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Generado por AgroNexus AI Kernel | Página {self.page_no()}", align="C")

def create_trend_chart(history_raw: List[Dict[str, Any]]) -> Optional[io.BytesIO]:
    if not history_raw: return None
    try:
        data = history_raw[-24:] # Últimas 24 muestras
        temps = [d.get('temperature', 0) for d in data]
        hums = [d.get('humidity', 0) for d in data]
        
        plt.figure(figsize=(9, 3.5), facecolor='#ffffff')
        plt.plot(temps, label='Temp (°C)', color='#ef4444', linewidth=1.5, marker='.')
        plt.plot(hums, label='Hum (%)', color='#3b82f6', linewidth=1.5)
        
        plt.title('Tendencia de Parámetros Críticos', fontsize=10, fontweight='bold')
        plt.legend(loc='lower right', frameon=False, fontsize=8)
        plt.grid(True, linestyle=':', alpha=0.4)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf
    except:
        return None

def generate_health_report(
    latest_data: Dict[str, Any], 
    aggregated_data: Dict[str, Any], 
    history_raw: List[Dict[str, Any]],
    ai_analysis: Optional[str] = None, 
    zone_name: str = "Principal",
    focus: str = "General"
) -> bytes:
    pdf = AgriReport()
    pdf.add_page()
    
    # 1. Info Reporte
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 8, f"Zona: {zone_name}", ln=True)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 4, f"Enfoque: {focus.upper()}", ln=True)
    pdf.cell(0, 4, f"Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(6)
    
    # 2. Resumen Técnico (KPIs)
    pdf.chapter_title("Resumen Técnico (KPIs)")
    metrics = aggregated_data.get("metrics", {})
    
    # Tabla simple de métricas agregadas
    pdf.set_font("helvetica", "B", 8)
    pdf.set_fill_color(248, 250, 252)
    pdf.cell(45, 7, " Métrica", 1, 0, 'L', True)
    pdf.cell(30, 7, " Promedio", 1, 0, 'C', True)
    pdf.cell(30, 7, " Rango (Min/Max)", 1, 0, 'C', True)
    pdf.cell(30, 7, " Tendencia", 1, 1, 'C', True)
    
    pdf.set_font("helvetica", "", 8)
    for m_name, vals in metrics.items():
        label = m_name.replace('_', ' ').title()
        pdf.cell(45, 6, f" {label}", 1)
        pdf.cell(30, 6, f"{vals['avg']}", 1, 0, 'C')
        pdf.cell(30, 6, f"{vals['min']} / {vals['max']}", 1, 0, 'C')
        
        trend = vals['trend']
        if trend == "ASCENDENTE": pdf.set_text_color(220, 38, 38)
        elif trend == "DESCENDENTE": pdf.set_text_color(37, 99, 235)
        else: pdf.set_text_color(30, 41, 59)
        
        pdf.cell(30, 6, trend, 1, 1, 'C')
        pdf.set_text_color(30, 41, 59)

    pdf.ln(8)
    
    # 3. Gráfico
    chart = create_trend_chart(history_raw)
    if chart:
        pdf.chapter_title("Visualización de Tendencias (24h)")
        pdf.image(chart, x=20, w=170)
        pdf.ln(6)

    # 4. Diagnóstico IA
    pdf.chapter_title(f"Diagnóstico de AgrosNexus IA ({focus})")
    if ai_analysis:
        pdf.set_font("helvetica", "", 10)
        clean_text = sanitize_text(ai_analysis).replace("**", "").replace("#", "")
        pdf.multi_cell(0, 5.5, clean_text)
    else:
        pdf.set_font("helvetica", "I", 10)
        pdf.set_text_color(150, 50, 50)
        pdf.multi_cell(0, 6, "El diagnóstico detallado de la IA no pudo generarse en este momento debido a límites de cuota diaria. Los datos técnicos mostrados arriba son precisos y representan el estado real de sus sensores.")
    
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(220, 38, 38)
    pdf.cell(0, 5, "AVISO DE SEGURIDAD:", ln=True)
    pdf.set_font("helvetica", "I", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(0, 4, "Los análisis de IA son recomendaciones basadas en datos y no sustituyen el criterio de un experto en campo. Verifique fisicamente el cultivo antes de aplicar cambios críticos en fertirriego o control climático.")

    return pdf.output()
