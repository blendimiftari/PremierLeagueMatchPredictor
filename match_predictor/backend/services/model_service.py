import os
import logging
from typing import Dict, List
import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class ModelService:
    """Service for making match predictions using the trained LightGBM model."""
    
    def __init__(self, model_path: str = None):
        """Initialize the model service."""
        if model_path is None:
            model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'model', 'premier-league_match_predictor.pkl')
            scaler_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'model', 'feature_scaler.pkl')
        else:
            scaler_path = os.path.join(os.path.dirname(model_path), 'feature_scaler.pkl')
        
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = self._load_model()
        self.scaler = self._load_scaler()
        logger.info(f"Model and scaler loaded successfully from {model_path}")

    def _load_model(self):
        """Load the trained LightGBM model using joblib."""
        try:
            model = joblib.load(self.model_path)
            return model
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def _load_scaler(self):
        """Load the feature scaler using joblib."""
        try:
            scaler = joblib.load(self.scaler_path)
            return scaler
        except Exception as e:
            logger.error(f"Error loading scaler: {str(e)}")
            raise

    def prepare_features(self, features: Dict) -> List[float]:
        """Prepare features for prediction in the correct order."""
        feature_order = [
            'Away_Elo',
            'Home_Elo',
            'H2H_Draws_Last_5',
            'Draw_Tendency_Home',
            'Draw_Tendency_Away',
            'Avg_Home_GD_Last_5',
            'Avg_Away_GD_Last_5',
            'Elo_Difference'
        ]
        
        # Get Elo values first
        home_elo = features.get('Home_Elo', 1500)
        away_elo = features.get('Away_Elo', 1500)
        
        # Calculate raw Elo difference first to maintain consistency with training data
        elo_difference = home_elo - away_elo
        
        # Create feature array with default values if any are missing
        feature_values = [
            away_elo,
            home_elo,
            features.get('H2H_Draws_Last_5', 0),
            features.get('Draw_Tendency_Home', 0.2),
            features.get('Draw_Tendency_Away', 0.2),
            features.get('Avg_Home_GD_Last_5', 0),
            features.get('Avg_Away_GD_Last_5', 0),
            elo_difference  # Use raw Elo difference instead of placeholder
        ]
        
        # Log raw feature values before scaling
        logger.info("Raw features before scaling:")
        for name, value in zip(feature_order, feature_values):
            logger.info(f"{name}: {value}")
        
        # Create DataFrame and scale all features consistently with training
        feature_df = pd.DataFrame([feature_values], columns=feature_order)
        scaled_features = self.scaler.transform(feature_df)
        
        # Clip all features to a reasonable range to prevent extreme values
        for i in range(len(feature_order)):
            scaled_features[0, i] = np.clip(scaled_features[0, i], -3, 3)
        
        # Log final scaled features
        logger.info("Final scaled features:")
        for name, value in zip(feature_order, scaled_features[0]):
            logger.info(f"{name}: {value}")
        
        return scaled_features[0].tolist()

    def predict(self, features: List[float]) -> Dict[str, float]:
     
        try:
          
            X = np.array(features).reshape(1, -1)
            
    
            probabilities = self.model.predict_proba(X)[0]
            
            # Log prediction probabilities
            logger.info("Model predictions:")
            logger.info(f"Home Win: {probabilities[0]:.3f}")
            logger.info(f"Draw: {probabilities[1]:.3f}")
            logger.info(f"Away Win: {probabilities[2]:.3f}")
            
        
            return {
                'home_win': float(probabilities[0]),
                'draw': float(probabilities[1]),
                'away_win': float(probabilities[2])
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
           
            return {
                'home_win': 0.4,
                'draw': 0.3,
                'away_win': 0.3
            } 