import yfinance as yf
import json
import pandas as pd  # Biblioteka do łatwego zapisu CSV
import os            # Do otwierania pliku w systemie
import platform      # Do sprawdzenia systemu operacyjnego
import numpy as np
from strategies.strategies import pobierz_sygnal_donchian
from strategies.pullBackStrategy import pobierz_sygnal_pullBack
from strategies.goldCross import pobierz_sygnal_goldCross
from strategies.bollingerBands import pobierz_sygnal_bollingerBandsSquezze
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
          f"{'ROR(30)':>{8}} | "
          f"{'RSI':>{7}} |"
          f"{'(RSI + Trend)':>{7}} |"
          f"{'Złoty Krzyż (SMA)':>{7}} |"
          f"{'Donchian':>{7}}")
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

                pullBackSignal = pobierz_sygnal_pullBack(rate_of_return, current_rsi)
                donchianSignal = pobierz_sygnal_donchian(symbol)
                goldCrossSignal = pobierz_sygnal_goldCross(dane,np)
                bollingerSignal = pobierz_sygnal_bollingerBandsSquezze(dane,np)

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
                    f"{rate_of_return*100:>7.2f}% | "
                    f"{current_rsi:>7.2f} | "
                    f"{pullBackSignal} | "
                    f"{goldCrossSignal} |"
                    f"{donchianSignal} |"
                    f"{bollingerSignal}"
                )
            else:
                print(f"{symbol:<10} | Brak danych")
        except Exception as e:
            print(f"{symbol:<7} | Błąd: {e}")

print("\n--- KONIEC ---")