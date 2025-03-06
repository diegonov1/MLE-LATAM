import pickle
import logging
import numpy as np
import pandas as pd

from typing import Tuple, Union, List
from datetime import datetime
from sklearn.linear_model import LogisticRegression

# Configuring logging for the model as INFO
logging.basicConfig(level=logging.INFO)

class DelayModel:
    """
    A model based on Logistic Regression to predict delays in flights.

    Attributes:
        _FEATURES: Features used to train the model.
        _THRESHOLD: Threshold to classify delays (in minutes).
        _MODEL_FILE: File to save the model.
    """

    _TOP_FEATURES = [
        "OPERA_Latin American Wings",
        "MES_7",
        "MES_10",
        "OPERA_Grupo LATAM",
        "MES_12",
        "TIPOVUELO_I",
        "MES_4",
        "MES_11",
        "OPERA_Sky Airline",
        "OPERA_Copa Air",
    ]
    _MODEL_FILE = 'model.pkl'
    _THRESHOLD_IN_MINUTES = 15

    def __init__(self) -> None:
        """
        Constructor for the model.
        """
        self._model = None # Predictions are blocked until the model is trained
        self._is_trained = False
        self._model = self.__load_model()

    def __load_model(self) -> Union[LogisticRegression, None]:
        """
        Load the model from the file. If available.

        Returns:
            Union[LogisticRegression, None]: Loaded model or None if the file does not exist.
        """

        try:
            with open(self._MODEL_FILE, 'rb') as file:
                model = pickle.load(file)
                logging.info("Model loaded successfully.")
                self._is_trained = True
                return model
            
        except FileNotFoundError:
            logging.warning("Model file does is not found. Please train the model first.")
            return None
        
        except Exception as e:
            logging.error(f"Error loading the model: {e}")
            return None
        
    def __save_model(self) -> None:
        """
        Save the model to a pickle file.
        """
        if self._model is None:
            logging.error("The model has not been trained yet, therefore it cannot be saved.")
            return
        
        try:
            with open(self._MODEL_FILE, 'wb') as file:
                pickle.dump(self._model, file)
                logging.info("Model saved successfully.")

        except Exception as e:
            logging.error(f"Error saving the model: {e}")

    def _get_min_diff(self, row: pd.Series) -> float:
        """
        Calculate the difference in minutes between the scheduled (Fecha-I) and actual departure time (Fecha-O).

        Args:
            row (pd.Series): Row containing the scheduled and actual departure times as strings timestamps.

        Returns:
            float: The time difference in minutes.
        """
        try:
            fecha_o = datetime.strptime(row['Fecha-O'], '%Y-%m-%d %H:%M:%S')
            fecha_i = datetime.strptime(row['Fecha-I'], '%Y-%m-%d %H:%M:%S')
            diff = (fecha_o - fecha_i).total_seconds() / 60
            return diff
        
        except Exception as e:
            logging.error(f"Error calculating the difference: {e}")
            return np.nan

    def preprocess(self, data: pd.DataFrame, target_column: str = None) -> Union[Tuple[pd.DataFrame, pd.DataFrame], pd.DataFrame]:
        """
        Prepare raw data for training or predict.

        Args:
            data (pd.DataFrame): raw data.
            target_column (str, optional): if set, the target is returned.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: features and target.
            or
            pd.DataFrame: features.
        """
        # One-hot encoding for the categorical variables
        df_encoded = pd.concat([
            pd.get_dummies(data["OPERA"], prefix="OPERA"),
            pd.get_dummies(data["TIPOVUELO"], prefix="TIPOVUELO"),
            pd.get_dummies(data["MES"], prefix="MES")
        ], axis=1)
    
        # Ensure we only keep the top features
        df_encoded = df_encoded.reindex(columns=self._FEATURES, fill_value=0)

        # If target column is provided, return features and target
        if target_column:
            if target_column == "delay" and "delay" not in data.columns:
                data["min_diff"] = data.apply(self._get_min_diff, axis=1)
                data["delay"] = np.where(
                    data["min_diff"] > self._THRESHOLD_IN_MINUTES, 1, 0
                )
            target = pd.DataFrame(data[target_column].astype(int), columns=[target_column])
            return df_encoded, target

        return df_encoded

    def fit(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        """
        Fit model with preprocessed data.

        Args:
            features (pd.DataFrame): preprocessed data.
            target (pd.DataFrame): target.
        """
        # Class imbalance handling
        n_y0 = (target == 0).sum().sum()
        n_y1 = (target == 1).sum().sum()

        if n_y1 == 0:
            logging.error("No positive samples in target, training aborted.")
            return None
        
        scale = n_y0 / n_y1

        # Train the logistic regression model
        self._model = LogisticRegression(class_weight={0: 1, 1: scale}, random_state=42)
        target_series = target.iloc[:, 0]
        self._model.fit(features, target_series)

        # Flag model as trained
        self._is_trained = True  
        logging.info("Model training complete.")
        self.__save_model()

    def predict(self, features: pd.DataFrame) -> List[int]:
        """
        Predict delays for new flights.

        Args:
            features (pd.DataFrame): preprocessed data.
        
        Returns:
            (List[int]): predicted targets.
        """
        if not self._is_trained or self._model is None:
            raise ValueError(
                "Model has not been trained yet."
                "Call '.fit(features, target)' before making predictions."
            )

        predictions = self._model.predict(features)
        return predictions.tolist()