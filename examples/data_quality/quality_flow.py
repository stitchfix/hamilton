"""
This code is a supplement to the example used in examples/numpy/ that could be used to check the incoming raw data for that analysis.
"""
from hamilton.function_modifiers import check_output
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def pollutant_names() -> dict:
    return {
            "Datetime": "date_time",
            "PM10": "particles",
            "PM2.5": "fine_particles",
            "NO2": "nitrogen_dioxide",
            "NH3": "ammonia",
            "SO2": "sulfur_dioxide",
            "CO": "carbon_monoxide",
            "O3": "ozone",
            "NOx": "nitrogen_oxides",
            "NO": "nitric_oxide",
            "Benzene": "benzene",
            "Toluene": "toluene",
            "Xylene": "xylene"
        }

def pollutant_data(pollutant_names: dict, input_file_name: str = 'air-quality-data.csv') -> pd.DataFrame:
    """Returns the raw pollutant data."""
    return pd.read_csv("air-quality-data.csv").rename(columns=pollutant_names)

@check_output(
    importance="warn",
    datatype=np.datetime64,
    range=(datetime.today() - timedelta(days=4*365), datetime.today())
)
def date_time(pollutant_data: pd.DataFrame) -> pd.Series:
    """Time of measurement"""
    return pd.to_datetime(pollutant_data["date_time"])

@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,None)
)
def particles(pollutant_data: pd.DataFrame) -> pd.Series:
    """Particles that are 10 micrometers or less in width, able to travel deep into respiratory system"""
    return pollutant_data["particles"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def fine_particles(pollutant_data: pd.DataFrame) -> pd.Series:
    """Fine particles that are 2.5 microns or less in width, able to travel deep into respiratory system"""
    return pollutant_data["fine_particles"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def nitrogen_dioxide(pollutant_data: pd.DataFrame) -> pd.Series:
    """NO2 - found in the air from burning fuel, irritates the respiratory system"""
    return pollutant_data["nitrogen_dioxide"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def ammonia(pollutant_data: pd.DataFrame) -> pd.Series:
    """NH3 - dangerous to wildlife and helps in formation of fine particulate matter"""
    return pollutant_data["ammonia"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def sulfur_dioxide(pollutant_data: pd.DataFrame) -> pd.Series:
    """SO2 - created by burning fossil fuels, irritates the respiratory system and can damage foliage growth"""
    return pollutant_data["sulfur_dioxide"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def carbon_monoxide(pollutant_data: pd.DataFrame) -> pd.Series:
    """CO - deadly in high concentrations"""
    return pollutant_data["carbon_monoxide"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def ozone(pollutant_data: pd.DataFrame) -> pd.Series:
    """O3"""
    return pollutant_data["ozone"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def nitrogen_oxides(pollutant_data: pd.DataFrame) -> pd.Series:
    """NOx"""
    return pollutant_data["nitrogen_oxides"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def nitric_oxide(pollutant_data: pd.DataFrame) -> pd.Series:
    """NO - not hazardous at ambient levels, at high levels causes respiratory issues, vomiting, nausea"""
    return pollutant_data["nitric_oxide"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def benzene(pollutant_data: pd.DataFrame) -> pd.Series:
    """Benzene (C6H6) - a carcinogen found in gasoline, dyes, rubber, pesticides, etc."""
    return pollutant_data["benzene"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def toluene(pollutant_data: pd.DataFrame) -> pd.Series:
    """
    Toluene is a common ingredient in degreasers. It's a colorless liquid with a sweet smell and taste.
    It evaporates quickly. Toluene is found naturally in crude oil, and is used in oil refining
    and the manufacturing of paints, lacquers, explosives (TNT) and glues
https://www.dhs.wisconsin.gov/chemical/toluene.htm#:~:text=Toluene%20is%20a%20common%20ingredient,explosives%20(TNT)%20and%20glues.
    """
    return pollutant_data["toluene"]


@check_output(
    importance="warn",
    datatype=np.float64,
    range=(0,1000)
)
def xylene(pollutant_data: pd.DataFrame) -> pd.Series:
    """
    Xylene (C8H10) is a colorless, flammable liquid with a sweet odor.
    Exposure to xylene can irritate the eyes, nose, skin, and throat.
    Xylene can also cause headaches, dizziness, confusion, loss of muscle coordination, and in high doses, death.
https://www.cdc.gov/niosh/topics/xylene/default.html#:~:text=Xylene%20(C8H10,and%20in%20high%20doses%2C%20death.
    """
    return pollutant_data["xylene"]


@check_output(
    importance="fail",
    range=(-1,1)
)
def correlation_matrix(pollutant_data: pd.DataFrame) -> pd.DataFrame:
        return pollutant_data.corr().replace({1: 0}) # just to remove 1.0 self-corr we don't need to check
    
    
    
@check_output(
    importance="warn",
    range=(-0.9, 0.9)
)
def correlation_matrix2(pollutant_data: pd.DataFrame) -> pd.DataFrame:
        return pollutant_data.corr().replace({1: 0}) # just to remove 1.0 self-corr we don't need to check