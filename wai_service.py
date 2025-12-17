"""
WAI Service - Berechnet den Whale Activity Index
"""
import httpx
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from config import config


class WAIService:
    """Service zur Berechnung des Whale Activity Index"""
    
    DATA_URL = config.DATA_URL
    SMA_WINDOW = config.SMA_WINDOW
    WAI_MIN = config.WAI_MIN
    WAI_MAX = config.WAI_MAX
    
    def __init__(self):
        self.cached_data: Optional[pd.DataFrame] = None
        self.last_fetch: Optional[datetime] = None
    
    async def fetch_daily_metrics(self) -> pd.DataFrame:
        """Lädt die täglichen Metriken von der API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.DATA_URL, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        
        # JSON in DataFrame konvertieren
        df = pd.DataFrame(data['daily_metrics'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return df
    
    def calculate_sma(self, series: pd.Series, window: int) -> pd.Series:
        """Berechnet den Simple Moving Average"""
        return series.rolling(window=window, min_periods=1).mean()
    
    def calculate_wai(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Berechnet den WAI nach der Formel:
        
        1. Normalisierung:
           T̂_d = T_d / SMA_30(T)
           V̂_d = V_d / SMA_30(V)
        
        2. WAI-Formel:
           WAI_d = 0.5 · T̂_d + 0.5 · V̂_d
        """
        # Kopie erstellen
        result = df.copy()
        
        # SMA für Transaction Count und Volume berechnen
        result['sma_transaction_count'] = self.calculate_sma(
            result['whale_tx_count'], 
            self.SMA_WINDOW
        )
        result['sma_total_volume'] = self.calculate_sma(
            result['whale_tx_volume_btc'], 
            self.SMA_WINDOW
        )
        
        # Normalisierung
        result['normalized_transaction_count'] = (
            result['whale_tx_count'] / result['sma_transaction_count']
        )
        result['normalized_volume'] = (
            result['whale_tx_volume_btc'] / result['sma_total_volume']
        )
        
        # WAI berechnen (50/50 Gewichtung)
        result['wai'] = (
            0.5 * result['normalized_transaction_count'] + 
            0.5 * result['normalized_volume']
        )
        
        # Auf 0-100 skalieren
        result['wai'] = result['wai'] * 100
        result['wai'] = result['wai'].clip(lower=self.WAI_MIN, upper=self.WAI_MAX)
        
        # NaN-Werte behandeln (für erste Tage ohne vollständigen SMA)
        result['wai'] = result['wai'].fillna(0)
        
        return result
    
    async def get_wai_data(self, 
                          start_date: Optional[str] = None, 
                          end_date: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Dict]:
        """
        Gibt WAI-Daten für einen bestimmten Zeitraum zurück
        
        Args:
            start_date: Startdatum (YYYY-MM-DD)
            end_date: Enddatum (YYYY-MM-DD)
            limit: Maximale Anzahl der Ergebnisse (neueste zuerst)
        
        Returns:
            Liste mit WAI-Berechnungen
        """
        # Daten laden
        df = await self.fetch_daily_metrics()
        
        # WAI berechnen
        df_with_wai = self.calculate_wai(df)
        
        # Filtern nach Datumsbereich
        if start_date:
            start = pd.to_datetime(start_date)
            df_with_wai = df_with_wai[df_with_wai['date'] >= start]
        
        if end_date:
            end = pd.to_datetime(end_date)
            df_with_wai = df_with_wai[df_with_wai['date'] <= end]
        
        # Sortieren (neueste zuerst)
        df_with_wai = df_with_wai.sort_values('date', ascending=False)
        
        # Limit anwenden
        if limit:
            df_with_wai = df_with_wai.head(limit)
        
        # In Dictionary-Format konvertieren
        result = []
        for _, row in df_with_wai.iterrows():
            result.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'wai_index': int(round(float(row['wai']))),
                'normalized_transaction_count': round(float(row['normalized_transaction_count']), 4),
                'normalized_volume': round(float(row['normalized_volume']), 4),
                'whale_tx_count': int(row['whale_tx_count']),
                'whale_tx_volume_btc': round(float(row['whale_tx_volume_btc']), 2),
                'sma_transaction_count': round(float(row['sma_transaction_count']), 2),
                'sma_volume': round(float(row['sma_total_volume']), 2)
            })
        
        return result
    
    async def get_latest_wai(self) -> Dict:
        """Gibt den aktuellsten WAI-Wert zurück"""
        data = await self.get_wai_data(limit=1)
        return data[0] if data else {}
    
    async def get_wai_statistics(self, 
                                start_date: Optional[str] = None, 
                                end_date: Optional[str] = None) -> Dict:
        """Berechnet Statistiken über einen optionalen Zeitraum"""
        df = await self.fetch_daily_metrics()
        df_with_wai = self.calculate_wai(df)
        
        # Filtern nach Datumsbereich
        if start_date:
            start = pd.to_datetime(start_date)
            df_with_wai = df_with_wai[df_with_wai['date'] >= start]
        
        if end_date:
            end = pd.to_datetime(end_date)
            df_with_wai = df_with_wai[df_with_wai['date'] <= end]
        
        return {
            'total_days': len(df_with_wai),
            'date_range': {
                'start': df_with_wai['date'].min().strftime('%Y-%m-%d'),
                'end': df_with_wai['date'].max().strftime('%Y-%m-%d')
            },
            'wai_stats': {
                'mean': round(float(df_with_wai['wai'].mean()), 4),
                'median': round(float(df_with_wai['wai'].median()), 4),
                'min': round(float(df_with_wai['wai'].min()), 4),
                'max': round(float(df_with_wai['wai'].max()), 4),
                'std': round(float(df_with_wai['wai'].std()), 4)
            },
            'latest_wai': round(float(df_with_wai.iloc[-1]['wai']), 4),
            'latest_date': df_with_wai.iloc[-1]['date'].strftime('%Y-%m-%d')
        }
