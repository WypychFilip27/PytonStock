# Plik: strategia.py
import yfinance as yf
import pandas as pd

pd.options.mode.chained_assignment = None 

def pobierz_sygnal_donchian(symbol, interwal='1d', okno=20):
    try:
        ticker = yf.Ticker(symbol)
        # Pobieramy trochę więcej danych niż 'okno'
        df = ticker.history(period='3mo', interval=interwal)
        
        if len(df) < okno + 1:
            return "BŁĄD: Za mało danych"

        # 1. Obliczanie kanałów (Góra/Dół)
        # Ważne: Przesuwamy o 1 (shift), żeby porównywać dzisiejszą cenę 
        # do szczytów z WCZORAJ i dni poprzednich (nie wliczając dzisiaj).
        df['Upper'] = df['High'].shift(1).rolling(window=okno).max()
        df['Lower'] = df['Low'].shift(1).rolling(window=okno).min()

        # 2. Pobieramy ostatnią świecę (DZIŚ)
        ostatnia = df.iloc[-1]
        cena_teraz = ostatnia['Close']
        gorna_banda = ostatnia['Upper']
        dolna_banda = ostatnia['Lower']

        # 3. Logika (Wybicia)
        
        if cena_teraz > gorna_banda:
            return "KUPUJ (Wybicie górą)"
            
        elif cena_teraz < dolna_banda:
            return "SPRZEDAJ (Wybicie dołem)"
            
        else:
            # Cena jest pomiędzy bandami
            return "CZEKAJ (W kanale)"

    except Exception as e:
        return f"BŁĄD: {str(e)}"