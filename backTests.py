import yfinance as yf
import json
import pandas as pd  # Biblioteka do łatwego zapisu CSV
import os            # Do otwierania pliku w systemie
import platform      # Do sprawdzenia systemu operacyjnego
import numpy as np
# 1. Wczytujemy konfigurację
try:
    with open('config.json', 'r') as plik:
        konfiguracja = json.load(plik)
    symbole = konfiguracja['symbole']
    okres = konfiguracja.get('okres', '6mo')
    print(f"Wczytano {len(symbole)} spółek.")
except FileNotFoundError:
    print("Błąd: Nie znaleziono pliku config.json!")
    symbole = []

# 2. Pobieranie danych i zapis do listy
wyniki = []
if symbole:
    print(f"--- POBIERANIE DANYCH ({okres}) ---")
    print(f"{'SYMBOL':<{10}} | "
          f"{'CENA':>{12}} | "
          f"{'ROR(30)':>{12}} | "
          f"{'RSI':>{7}} |"
          f"{'Trend Pullback (RSI + Trend)':>{7}} |"
          f"{'Złoty Krzyż (SMA)':>{7}}")
    for symbol in symbole:
        try:
            ticker = yf.Ticker(symbol)
            dane = ticker.history(period='2y')
            
            if not dane.empty:
                cena = dane['Close'].iloc[-1]
                waluta = ticker.info.get('currency', '?')
                wolumen = dane['Volume'].iloc[-1]
                # 1. Przyrost Dzienny (Cena dzisiaj vs wczoraj)
                day_rate_of_return = dane['Close'].pct_change().iloc[-1]
                # 2. Przyrost Miesięczny (Cena dzisiaj vs cena 21 dni sesyjnych temu)
                # Giełda działa średnio 21 dni w miesiącu
                rate_of_return = dane['Close'].pct_change(periods=21).iloc[-1] 
                # obliczanie RSI
                delta = dane['Close'].diff()
                up = delta.clip(lower =0)
                down = -1 * delta.clip(upper =0)
                roll_up = up.ewm(com=13, adjust=False).mean()
                roll_down = down.ewm(com=13, adjust=False).mean()
                rs = roll_up / roll_down
                rsi = 100 - (100 /(1 +rs))
                current_rsi = rsi.iloc[-1]

                if rate_of_return > 0 and current_rsi < 30:
                    backtest1 = "KUPUJ"

                elif current_rsi > 70:
                    backtest1 = "SPRZEDAJ"

                elif rate_of_return < 0:
                    backtest1 = "ZAMKNIJ POZYCJĘ"

                else:
                    backtest1 = "CZEKAJ (Brak sygnału)"

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
                wyniki = ['KUPUJ (Sygnał)', 'SPRZEDAJ (Sygnał)', 'TRZYMAJ']

                # Domyślnie (jeśli żaden warunek nie pasuje) wpisz "POZA RYNKIEM" (trend spadkowy, brak akcji)
                dane['Strategia'] = np.select(warunki, wyniki, default='POZA RYNKIEM')
                wyniki.append({
                    "Symbol": symbol,
                    "Cena": round(cena, 2),
                    "Waluta": waluta,
                    "Wolumen" : wolumen, 
                    "Data": dane.index[-1].strftime('%Y-%m-%d')
                })
                print(
                    f"{symbol:<10} | "
                    f"{cena:>8.2f} {waluta:<3} | "
                    f"{rate_of_return*100:>15.2f}% | "
                    f"{current_rsi:>6.2f} | "
                    f"{backtest1} | "
                    f"{dane['Strategia'].iloc[-1]}"
                )
            else:
                print(f"{symbol:<10} | Brak danych")
        except Exception as e:
            print(f"{symbol:<7} | Błąd: {e}")

print("\n--- KONIEC ---")