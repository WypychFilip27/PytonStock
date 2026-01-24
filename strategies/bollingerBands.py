import pandas as pd
import numpy as np
import yfinance as yf 

pd.options.mode.chained_assignment = None 

def pobierz_sygnal_bollingerBandsSquezze(df, np):
    # --- OBLICZENIA WSKAŹNIKÓW ---

    # Parametry
    okres = 20
    mnoznik_bb = 2.0
    mnoznik_kc = 1.5

    # 1. Średnia krocząca (SMA) - baza dla obu wskaźników
    df['SMA'] = df['Close'].rolling(window=okres).mean()

    # 2. Wstęgi Bollingera (BB)
    # Odchylenie standardowe
    df['std_dev'] = df['Close'].rolling(window=okres).std()
    df['BB_Upper'] = df['SMA'] + (df['std_dev'] * mnoznik_bb)
    df['BB_Lower'] = df['SMA'] - (df['std_dev'] * mnoznik_bb)

    # 3. Kanały Keltnera (KC)
    # Najpierw obliczamy True Range (TR)
    df['tr0'] = abs(df['High'] - df['Low'])
    df['tr1'] = abs(df['High'] - df['Close'].shift(1))
    df['tr2'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)

    # ATR (Średnia z TR)
    df['ATR'] = df['TR'].rolling(window=okres).mean()

    df['KC_Upper'] = df['SMA'] + (df['ATR'] * mnoznik_kc)
    df['KC_Lower'] = df['SMA'] - (df['ATR'] * mnoznik_kc)


    # --- LOGIKA STRATEGII (SQUEEZE) ---

    # Warunek 1: SQUEEZE (Ścisk)
    # BB wchodzą do środka KC -> Zmienność jest ekstremalnie niska
    df['Squeeze_ON'] = (df['BB_Upper'] < df['KC_Upper']) & (df['BB_Lower'] > df['KC_Lower'])

    # Warunek 2: WYBICIE (Momentum)
    # Cena zamyka się powyżej górnej wstęgi BB (dla Longa)
    # Można też dodać warunek, że 'Squeeze_ON' był prawdą np. wczoraj (shift(1))
    cond_buy = (df['Close'] > df['BB_Upper']) & (df['Squeeze_ON'].shift(1) == True)
    cond_sell = (df['Close'] < df['BB_Lower']) & (df['Squeeze_ON'].shift(1) == True)

    # --- GENEROWANIE SYGNAŁÓW (np.select) ---

    # --- POBIERAMY TYLKO OSTATNIE WARTOŚCI (DZIŚ i WCZORAJ) ---
    
    # Stan z dzisiaj (ostatni wiersz: -1)
    cena_dzis = df['Close'].iloc[-1].item() # .item() zamienia na zwykłą liczbę
    bb_upper_dzis = df['BB_Upper'].iloc[-1].item()
    bb_lower_dzis = df['BB_Lower'].iloc[-1].item()
    squeeze_dzis = df['Squeeze_ON'].iloc[-1]

    # Stan z wczoraj (przedostatni wiersz: -2)
    squeeze_wczoraj = df['Squeeze_ON'].iloc[-2]

    # --- LOGIKA DECYZYJNA ---
    
    # Scenariusz 1: Wybicie w GÓRĘ (Wczoraj był ścisk, dziś cena przebiła górną bandę)
    if squeeze_wczoraj and (cena_dzis > bb_upper_dzis):
        return "KUPUJ"

    # Scenariusz 2: Wybicie w DÓŁ
    elif squeeze_wczoraj and (cena_dzis < bb_lower_dzis):
        return "SPRZEDAWAJ"

    # Scenariusz 3: Trwa ładowanie energii (Squeeze ON)
    elif squeeze_dzis:
        return "SQUEEZE TRWA (Czekaj)"

    # Scenariusz 4: Nic się nie dzieje
    else:
        return "Brak sygnału"