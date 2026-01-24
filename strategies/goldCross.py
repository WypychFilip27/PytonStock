# Plik: strategia.py
import yfinance as yf
import pandas as pd

pd.options.mode.chained_assignment = None 

def pobierz_sygnal_goldCross(dane, np):
        # 1. Oblicz średnie (jeśli jeszcze ich nie masz)
        dane['SMA50'] = dane['Close'].rolling(window=50).mean()
        dane['SMA200'] = dane['Close'].rolling(window=200).mean()

        # 2. Określ czy jesteśmy w trendzie wzrostowym (1) czy spadkowym (0)
        dane['Trend_Wzrostowy'] = np.where(dane['SMA50'] > dane['SMA200'], 1, 0)

        # 3. Wykryj MOMENT zmiany (1 = przecięcie w górę, -1 = przecięcie w dół)
        dane['Zmiana'] = dane['Trend_Wzrostowy'].diff() 
        # 4. Logika tekstowa (Kolejność warunków jest ważna!)
        warunki = [
            (dane['Zmiana'] == 1),              # Sytuacja A: Właśnie przecięło w górę -> KUPUJ
            (dane['Zmiana'] == -1),             # Sytuacja B: Właśnie przecięło w dół -> SPRZEDAJ
            (dane['Trend_Wzrostowy'] == 1)      # Sytuacja C: Brak zmiany, ale trend jest wzrostowy -> TRZYMAJ
        ]

        # Co wpisać dla poszczególnych sytuacji
        wyniki = ['KUPUJ', 'SPRZEDAJ', 'TRZYMAJ']

        # Domyślnie (jeśli żaden warunek nie pasuje) wpisz "POZA RYNKIEM" (trend spadkowy, brak akcji)
        return np.select(warunki, wyniki, default='POZA RYNKIEM')[-1]