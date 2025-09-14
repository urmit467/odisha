from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
from typing import Optional
from datetime import datetime
from temperature import temperature_calculator
from rainfall import get_rainfall_forecast
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import report_utils  # We'll create this next
import os
import tempfile

app = FastAPI(title="Odisha Crop Yield Predictor")

# Load the training pipeline (preproc + model)
PIPE_PATH = "odisha_crop_pipeline.joblib"
try:
    pipeline = joblib.load(PIPE_PATH)
    # Check how many outputs the model has
    if hasattr(pipeline.named_steps['model'], 'estimators_'):
        n_outputs = len(pipeline.named_steps['model'].estimators_)
        print(f"Model loaded with {n_outputs} outputs")
    else:
        # For MultiOutputRegressor, we need to check the number of estimators
        n_outputs = len(pipeline.named_steps['model'].estimators_)
        print(f"Model loaded with {n_outputs} outputs")
except FileNotFoundError:
    print(f"Warning: Model file {PIPE_PATH} not found. Please train the model first.")
    pipeline = None
    n_outputs = 0

class PredictionRequest(BaseModel):
    district: str
    crop: str
    season: str
    sowing_date: str  # "YYYY-MM-DD"

class PredictionResponse(BaseModel):
    predicted_environmental_conditions: dict
    predicted_soil_conditions: dict
    predicted_fertilizer_recommendation: dict
    predicted_yield_kg_per_ha: float
    predicted_harvest_days: float

@app.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Please train the model first.")
    
    # Convert sowing_date to day of year and extract month/day for weather calculations
    try:
        sow_dt = pd.to_datetime(req.sowing_date)
        sowing_doy = int(sow_dt.dayofyear)
        month = sow_dt.month
        day = sow_dt.day
    except:
        raise HTTPException(status_code=400, detail="Invalid sowing_date format. Use YYYY-MM-DD.")
    
    # Calculate temperature and rainfall for the season
    try:
        # Calculate average temperature for the next 100 days
        avg_temp = temperature_calculator.get_avg_temperature(
            req.district, month, day, days=100
        )
        
        # Calculate total rainfall for the next 100 days
        total_rainfall = get_rainfall_forecast(
            req.district, req.sowing_date
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Weather data error: {str(e)}")
    
    # Build input data with only the provided features (no weather data)
    data = {
        "district": req.district,
        "crop": req.crop,
        "season": req.season,
        "sowing_doy": sowing_doy
    }
    
    X = pd.DataFrame([data])
    
    try:
        # Get predictions for all target features
        preds = pipeline.predict(X)
        
        # The model now predicts 12 outputs in this order:
        # 0: season_avg_humidity
        # 1: soil_pH
        # 2: soil_N_kg_ha
        # 3: soil_P_kg_ha
        # 4: soil_K_kg_ha
        # 5: organic_carbon_pct
        # 6: soil_moisture_pct
        # 7: yield_kg_per_ha
        # 8: harvest_days
        # 9: fertilizer_N_kg_ha
        # 10: fertilizer_P_kg_ha
        # 11: fertilizer_K_kg_ha
        
        # Use calculated weather data from external services
        environmental_conditions = {
            "season_total_rainfall_mm": round(float(total_rainfall), 1),
            "season_avg_temp_c": round(float(avg_temp), 1),
            "season_avg_humidity": round(float(preds[0, 0]), 1)  # First output from model
        }
        
        soil_conditions = {
            "soil_pH": round(float(preds[0, 1]), 1),
            "soil_N_kg_ha": round(float(preds[0, 2]), 1),
            "soil_P_kg_ha": round(float(preds[0, 3]), 1),
            "soil_K_kg_ha": round(float(preds[0, 4]), 1),
            "organic_carbon_pct": round(float(preds[0, 5]), 2),
            "soil_moisture_pct": round(float(preds[0, 6]), 1)
        }
        
        fertilizer_recommendation = {
            "N": round(float(preds[0, 9]), 1),
            "P": round(float(preds[0, 10]), 1),
            "K": round(float(preds[0, 11]), 1)
        }
        
        yield_kg_per_ha = round(float(preds[0, 7]), 2)
        harvest_days = round(float(preds[0, 8]), 1)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    return PredictionResponse(
        predicted_environmental_conditions=environmental_conditions,
        predicted_soil_conditions=soil_conditions,
        predicted_fertilizer_recommendation=fertilizer_recommendation,
        predicted_yield_kg_per_ha=yield_kg_per_ha,
        predicted_harvest_days=harvest_days
    )

@app.post("/download-report")
async def download_report(req: PredictionRequest):
    """Generate and download a PDF report for the prediction"""
    # Get the prediction data
    prediction_response = predict(req)
    
    # Generate PDF
    pdf_content = report_utils.generate_pdf_report(prediction_response, req)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_content)
        tmp_path = tmp.name
    
    # Return the file as a response
    return FileResponse(
        tmp_path,
        media_type="application/pdf",
        filename=f"crop_report_{req.district}_{req.crop}.pdf"
    )

@app.get("/")
def read_root():
    return {"message": "Odisha Crop Yield Prediction API"}

@app.get("/model-info")
def model_info():
    """Check what the model is configured to predict"""
    if pipeline is None:
        return {"error": "Model not loaded"}
    
    # The new model has 12 outputs
    info = {
        "outputs": n_outputs,
        "has_fertilizer_predictions": n_outputs >= 12  # 12 outputs total
    }
    
    return info

origins = ["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)