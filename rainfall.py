import pandas as pd
from datetime import datetime, timedelta

def load_and_prepare_data(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath)
        # Fix month format (full month names, e.g. January)
        df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'], format='%Y-%B')
        # Standardize district names
        df['District'] = df['District'].str.title()
        return df
    except FileNotFoundError:
        print(f"ERROR: File '{filepath}' not found.")
        return pd.DataFrame()

rainfall_df = load_and_prepare_data("rainfall.csv")

def get_rainfall_forecast(district: str, start_date_str: str):
    """
    Calculates total rainfall for 100 days starting from given date
    (approximates daily values from monthly averages).
    """
    if rainfall_df.empty:
        raise ValueError("Rainfall data file not found.")

    district_name = district.strip().title()

    try:
        start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    # Filter for district
    district_data = rainfall_df[rainfall_df['District'] == district_name]
    if district_data.empty:
        available = sorted(rainfall_df['District'].unique())
        raise ValueError(f"District '{district_name}' not found. Available: {available}")

    # Normalize to reference year
    ref_year = 2000
    district_data = district_data.copy()
    district_data['RefDate'] = pd.to_datetime(district_data['Date'].dt.strftime(f"{ref_year}-%m-%d"))

    # Expand monthly rainfall to daily
    district_data['DaysInMonth'] = district_data['RefDate'].dt.days_in_month
    daily_rows = []
    for _, row in district_data.iterrows():
        for d in range(1, row['DaysInMonth'] + 1):
            daily_rows.append({
                "District": row['District'],
                "Date": datetime(ref_year, row['RefDate'].month, d),
                "Rainfall_mm": row['Rainfall_mm'] / row['DaysInMonth']
            })
    daily_data = pd.DataFrame(daily_rows)

    # Build reference start & end
    ref_start = datetime(ref_year, start_date_obj.month, start_date_obj.day)
    ref_end = ref_start + timedelta(days=100)

    if ref_end.year > ref_year:  # wrap-around
        mask = (daily_data['Date'] >= ref_start) | (daily_data['Date'] < ref_end.replace(year=ref_year))
    else:
        mask = (daily_data['Date'] >= ref_start) & (daily_data['Date'] < ref_end)

    period_data = daily_data.loc[mask]

    if period_data.empty:
        raise ValueError("No rainfall data available for this date range.")

    return period_data['Rainfall_mm'].sum()
