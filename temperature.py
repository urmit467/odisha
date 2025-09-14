# temperature.py
import pandas as pd
from datetime import datetime, timedelta

class TemperatureCalculator:
    def __init__(self, csv_file: str):
        try:
            self.df = pd.read_csv(csv_file)
            if self.df.empty:
                raise ValueError("CSV file is empty")

            # Melt wide format to long format
            self.df_long = self.df.melt(
                id_vars=["District"],
                var_name="MonthYear",
                value_name="Temperature"
            )

            # Convert MonthYear like "Jan-2023" to datetime (pick day=1)
            self.df_long["Date"] = pd.to_datetime(self.df_long["MonthYear"], format="%b-%Y", errors="coerce")
            self.df_long = self.df_long.dropna(subset=["Date"])

        except Exception as e:
            raise RuntimeError(f"Error loading data: {e}")

    def get_avg_temperature(self, district: str, month: int, day: int, days: int = 75) -> float:
        if self.df_long.empty:
            raise ValueError("Temperature data file not found or empty.")

        # Filter by district
        district_df = self.df_long[self.df_long["District"].str.lower() == district.lower()]
        if district_df.empty:
            raise ValueError(f"District '{district}' not found in dataset.")

        # Reference year for consistent month/year matching
        start_date = datetime(2023, month, day)
        date_range = [(start_date + timedelta(days=i)).strftime("%b-%Y") for i in range(days)]

        # Filter rows matching months in date_range
        filtered = district_df[district_df["MonthYear"].isin(date_range)]
        if filtered.empty:
            raise ValueError("No temperature data found for the given date range.")

        return filtered["Temperature"].mean()

# Create a global instance for easy access
temperature_calculator = TemperatureCalculator("temperature.csv")  # Update with your actual file path