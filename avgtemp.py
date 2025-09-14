import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from datetime import datetime, timedelta

# --- Data Loading ---
def load_and_prepare_data(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath)
        # Build actual datetime from Year+Month (assume data is monthly or daily avg temp)
        df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'], format='%Y-%b')
        return df
    except FileNotFoundError:
        print(f"ERROR: File '{filepath}' not found.")
        return pd.DataFrame()

# Load dataset
# Expected CSV columns: Year, Month, District, Temp_C
temperature_df = load_and_prepare_data("temperature.csv")

# Initialize FastAPI
app = FastAPI(title="Odisha Temperature Forecast API (Month-Day Based)")

@app.get("/")
def home():
    return {"message": "Welcome to the Odisha Temperature API. Use /forecast-temp to get average temperature."}

@app.get("/forecast-temp")
def get_forecast_temp(
    district: str = Query(..., description="District name (e.g., 'Cuttack')"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format (year is ignored)")
):
    """
    Calculate avg temperature = (sum of temperatures for 100 days starting from given MM-DD) / 100
    """
    if temperature_df.empty:
        raise HTTPException(status_code=500, detail="Temperature data file not found.")

    district_name = district.strip().title()

    try:
        # Only use month and day
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Filter dataset for given district
    district_data = temperature_df[temperature_df['District'].str.lower() == district_name.lower()]
    if district_data.empty:
        available_districts = sorted(temperature_df['District'].unique())
        raise HTTPException(
            status_code=404,
            detail={"error": f"District '{district_name}' not found.", "available_districts": available_districts}
        )

    # Normalize all dataset dates to a reference year (2000) for day-month comparison
    ref_year = 2000
    district_data = district_data.copy()
    district_data['RefDate'] = pd.to_datetime(
        district_data['Date'].dt.strftime(f"{ref_year}-%m-%d")
    )

    # Build reference window
    ref_start = datetime(ref_year, start_date_obj.month, start_date_obj.day)
    ref_end = ref_start + timedelta(days=100)

    # Handle year wrap-around
    if ref_end.year > ref_year:
        mask = (district_data['RefDate'] >= ref_start) | (district_data['RefDate'] < ref_end.replace(year=ref_year))
    else:
        mask = (district_data['RefDate'] >= ref_start) & (district_data['RefDate'] < ref_end)

    period_data = district_data.loc[mask]

    if period_data.empty:
        raise HTTPException(status_code=404, detail="No temperature data available for this date range.")

    # --- Calculation ---
    total_temp = period_data['Temp_C'].sum()
    avg_temp = total_temp / 100  # always divide by 100 days

    return {
        "district": district_name,
        "start_date_mmdd": start_date_obj.strftime("%m-%d"),
        "period_days": 100,
        "total_temp_c": round(total_temp, 2),
        "average_temp_c_per_day": round(avg_temp, 2)
    }
