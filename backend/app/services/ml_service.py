from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        try:
            # Initialize sentiment analysis
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            # Initialize text classification for complaint categories
            # Using zero-shot classification as a fallback
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            
            self.categories = [
                "water supply",
                "garbage collection",
                "street lights",
                "roads",
                "drainage",
                "health services",
                "other"
            ]
            
            logger.info("ML models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            self.sentiment_analyzer = None
            self.classifier = None
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment of text
        Returns: (label, score) where score is -1 to 1
        """
        if not self.sentiment_analyzer:
            return "neutral", 0.0
        
        try:
            result = self.sentiment_analyzer(text[:512])[0]
            label = result['label'].lower()
            score = result['score']
            
            # Convert to -1 to 1 scale
            if label == 'negative':
                sentiment_score = -score
            else:
                sentiment_score = score
            
            return label, sentiment_score
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return "neutral", 0.0
    
    def classify_complaint(self, text: str) -> Tuple[str, float]:
        """
        Classify complaint into category
        Returns: (category, confidence)
        """
        if not self.classifier:
            return "other", 0.5
        
        try:
            result = self.classifier(text[:512], self.categories)
            category = result['labels'][0]
            confidence = result['scores'][0]
            
            # Map to enum value
            category_map = {
                "water supply": "water_supply",
                "garbage collection": "garbage_collection",
                "street lights": "street_lights",
                "roads": "roads",
                "drainage": "drainage",
                "health services": "health_services",
                "other": "other"
            }
            
            return category_map.get(category, "other"), confidence
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return "other", 0.5
    
    def determine_priority(self, sentiment_score: float, text: str) -> str:
        """
        Determine priority based on sentiment and keywords
        """
        urgent_keywords = ['urgent', 'emergency', 'critical', 'danger', 'immediate', 'severe']
        high_keywords = ['important', 'serious', 'major', 'significant']
        
        text_lower = text.lower()
        
        # Check for urgent keywords
        if any(keyword in text_lower for keyword in urgent_keywords):
            return "critical"
        
        # Negative sentiment + high keywords
        if sentiment_score < -0.5 and any(keyword in text_lower for keyword in high_keywords):
            return "high"
        
        # Very negative sentiment
        if sentiment_score < -0.7:
            return "high"
        
        # Moderately negative
        if sentiment_score < -0.3:
            return "medium"
        
        return "low"

# Global instance
ml_service = MLService()
