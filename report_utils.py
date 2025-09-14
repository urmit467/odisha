from fpdf import FPDF
from datetime import datetime

def generate_pdf_report(prediction_response, prediction_request):
    pdf = FPDF()
    pdf.add_page()
    
    # Set title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Crop Yield Prediction Report", 0, 1, "C")
    pdf.ln(10)
    
    # Add request details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Input Parameters:", 0, 1)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"District: {prediction_request.district}", 0, 1)
    pdf.cell(0, 10, f"Crop: {prediction_request.crop}", 0, 1)
    pdf.cell(0, 10, f"Season: {prediction_request.season}", 0, 1)
    pdf.cell(0, 10, f"Sowing Date: {prediction_request.sowing_date}", 0, 1)
    pdf.ln(10)
    
    # Add environmental conditions
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Environmental Conditions:", 0, 1)
    pdf.set_font("Arial", "", 12)
    env = prediction_response.predicted_environmental_conditions
    pdf.cell(0, 10, f"Total Rainfall: {env['season_total_rainfall_mm']} mm", 0, 1)
    pdf.cell(0, 10, f"Average Temperature: {env['season_avg_temp_c']} °C", 0, 1)
    pdf.cell(0, 10, f"Average Humidity: {env['season_avg_humidity']}%", 0, 1)
    pdf.ln(10)
    
    # Add soil conditions
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Soil Conditions:", 0, 1)
    pdf.set_font("Arial", "", 12)
    soil = prediction_response.predicted_soil_conditions
    pdf.cell(0, 10, f"pH: {soil['soil_pH']}", 0, 1)
    pdf.cell(0, 10, f"Nitrogen: {soil['soil_N_kg_ha']} kg/ha", 0, 1)
    pdf.cell(0, 10, f"Phosphorus: {soil['soil_P_kg_ha']} kg/ha", 0, 1)
    pdf.cell(0, 10, f"Potassium: {soil['soil_K_kg_ha']} kg/ha", 0, 1)
    pdf.cell(0, 10, f"Organic Carbon: {soil['organic_carbon_pct']}%", 0, 1)
    pdf.cell(0, 10, f"Moisture: {soil['soil_moisture_pct']}%", 0, 1)
    pdf.ln(10)
    
    # Add fertilizer recommendation
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Fertilizer Recommendation:", 0, 1)
    pdf.set_font("Arial", "", 12)
    fert = prediction_response.predicted_fertilizer_recommendation
    pdf.cell(0, 10, f"Nitrogen (N): {fert['N']} kg/ha", 0, 1)
    pdf.cell(0, 10, f"Phosphorus (P): {fert['P']} kg/ha", 0, 1)
    pdf.cell(0, 10, f"Potassium (K): {fert['K']} kg/ha", 0, 1)
    pdf.ln(10)
    
    # Add yield prediction
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Yield Prediction:", 0, 1)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Expected Yield: {prediction_response.predicted_yield_kg_per_ha} kg/ha", 0, 1)
    pdf.cell(0, 10, f"Harvest Days: {prediction_response.predicted_harvest_days} days", 0, 1)
    pdf.ln(10)
    
    # Add footer with date
    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 0, "C")
    
    return pdf.output(dest="S").encode("latin1")