import logging
from typing import List

import pandas as pd
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

from challenge.model import DelayModel

logging.basicConfig(level=logging.INFO)

app = FastAPI()

delay_model = DelayModel()

VALID_AIRLINES = {
        "American Airlines",
        "Air Canada",
        "Air France",
        "Aeromexico",
        "Aerolineas Argentinas",
        "Austral",
        "Avianca",
        "Alitalia",
        "British Airways",
        "Copa Air",
        "Delta Air",
        "Gol Trans",
        "Iberia",
        "K.L.M.",
        "Qantas Airways",
        "United Airlines",
        "Grupo LATAM",
        "Sky Airline",
        "Latin American Wings",
        "Plus Ultra Lineas Aereas",
        "JetSmart SPA",
        "Oceanair Linhas Aereas",
        "Lacsa"
    }

# ######################
#    Pydantic Models
# ######################

class FlightData(BaseModel):
    """
    Represents fields required by the DelayModel for making a prediction.
    Utilizes Pydantic built-in constraints and enum.
    """
    # OPERA must be a string
    OPERA: str
    # MES must be an integer
    MES: int
    # TIPOVUELO must a string
    TIPOVUELO: str


class FlightsBatch(BaseModel):
    """
    A container for a list of flights to predict.
    """
    flights: List[FlightData]

@app.get("/health", status_code=200)
async def get_health() -> dict:
    """
    Health check to verify if the api is up and running.
    """
    return {"status": "OK"}

# ######################
#    API Endpoints
# ######################

@app.post("/predict", status_code=200)
async def post_predict(batch: FlightsBatch) -> dict:
    """
    Accepts flight data, transforms it using the DelayModel,
    and returns the predictions (0 = On-time, 1 = Delayed).
    """

    for flight in batch.flights:
        if flight.MES < 1 or flight.MES > 12:
            raise HTTPException(status_code=400, detail="MES must be 1–12.")
        if flight.TIPOVUELO not in ["I", "N"]:
            raise HTTPException(status_code=400, detail="TIPOVUELO must be 'I' or 'N'.")
        if flight.OPERA not in VALID_AIRLINES:
            raise HTTPException(status_code=400, detail="Unknown airline.")

    try:
        data = [
            {
                "OPERA": flight.OPERA,
                "MES": flight.MES,
                "TIPOVUELO": flight.TIPOVUELO
            }
            for flight in batch.flights
        ]
        df = pd.DataFrame(data)

        X = delay_model.preprocess(df)

        predictions = delay_model.predict(X)

        return {"predict": predictions}

    except ValueError as val_err:
        logging.error("ValueError encountered in /predict: %s", str(val_err))
        raise HTTPException(status_code=400, detail=f"Error during prediction: {val_err}") from val_err

    except Exception as exc:
        logging.exception("Unexpected error in /predict.")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {exc}") from exc