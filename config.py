"""
Configuration Manager - Lädt Einstellungen aus .env Datei
"""
import os
from dotenv import load_dotenv

# .env Datei laden
load_dotenv()


class Config:
    """Konfigurationsklasse für die WAI Backend Anwendung"""
    
    # Server Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Data Source
    DATA_URL = os.getenv(
        "DATA_URL",
        "https://raw.githubusercontent.com/Whale-Activity-Analysis/wai-collector/refs/heads/main/data/daily_metrics.json"
    )
    
    # WAI Calculation Parameters
    SMA_WINDOW = int(os.getenv("SMA_WINDOW", 30))
    WAI_MIN = int(os.getenv("WAI_MIN", 0))
    WAI_MAX = int(os.getenv("WAI_MAX", 100))
    
    # Robust Baseline Feature Flag
    # Optionen: "sma" (Standard), "ewma" (Exponentially Weighted), "median" (Rolling Median)
    USE_ROBUST_BASELINE = os.getenv("USE_ROBUST_BASELINE", "sma").lower()
    EWMA_SPAN = int(os.getenv("EWMA_SPAN", 30))  # Span für EWMA (äquivalent zu SMA_WINDOW)


# Singleton-Instanz
config = Config()
