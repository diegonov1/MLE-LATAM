import logging
from enum import Enum
from typing import List

import pandas as pd
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

from .model import DelayModel

logging.basicConfig(level=logging.INFO)

app = FastAPI()

delay_model = DelayModel()

# ######################
#    Pydantic Models
# ######################

class FlightType(str, Enum):
    """
    Enum check for the type of flight.
    """
    I = "I"  # International
    N = "N"  # National


class FlightData(BaseModel):
    """
    Represents fields required by the DelayModel for making a prediction.
    Utilizes Pydantic built-in constraints and enum.
    """
    # OPERA must be a string
    OPERA: str
    # MES must be an integer
    MES: int
    # TIPOVUELO must be either 'I' or 'N'
    TIPOVUELO: FlightType


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
    try:
        data = [
            {
                "OPERA": flight.OPERA,
                "MES": flight.MES,
                "TIPOVUELO": flight.TIPOVUELO.value
            }
            for flight in batch.flights
        ]
        df = pd.DataFrame(data)

        X = delay_model.preprocess(df)

        predictions = delay_model.predict(X)

        return {"predictions": predictions}

    except ValueError as val_err:
        logging.error("ValueError encountered in /predict: %s", str(val_err))
        raise HTTPException(status_code=400, detail=f"Error during prediction: {val_err}") from val_err

    except Exception as exc:
        logging.exception("Unexpected error in /predict.")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {exc}") from exc