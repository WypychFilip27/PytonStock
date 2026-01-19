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
          f"{'WOLUMEN':>{12}} | "
          f"{'PRZYROST DZIENNY':>{10}} | "
          f"{'STOPA ZWROTU 1m':>{16}} | "
          f"{'STOPA ZWROTU 3m':>{16}} | "
          f"{'STOPA ZWROTU 6m':>{16}} |"
          f"{'RSI':>{7}} |")
    for symbol in symbole:
        try:
            ticker = yf.Ticker(symbol)
            dane = ticker.history(period='9mo')
            
            if not dane.empty:
                cena = dane['Close'].iloc[-1]
                waluta = ticker.info.get('currency', '?')
                wolumen = dane['Volume'].iloc[-1]
                # 1. Przyrost Dzienny (Cena dzisiaj vs wczoraj)
                day_rate_of_return = dane['Close'].pct_change().iloc[-1]
                # 2. Przyrost Miesięczny (Cena dzisiaj vs cena 21 dni sesyjnych temu)
                # Giełda działa średnio 21 dni w miesiącu
                rate_of_return = dane['Close'].pct_change(periods=21).iloc[-1]
                three_months_rate_of_return = dane['Close'].pct_change(periods=63).iloc[-1]
                six_months_rate_of_return = dane['Close'].pct_change(periods=128).iloc[-1]
                # obliczanie RSI
                delta = dane['Close'].diff()
                up = delta.clip(lower =0)
                down = -1 * delta.clip(upper =0)
                roll_up = up.ewm(com=13, adjust=False).mean()
                roll_down = down.ewm(com=13, adjust=False).mean()
                rs = roll_up / roll_down
                rsi = 100 - (100 /(1 +rs))
                current_rsi = rsi.iloc[-1]
                wyniki.append({
                    "Symbol": symbol,
                    "Cena": round(cena, 2),
                    "Waluta": waluta,
                    "Wolumen" : wolumen,
                    "Zwrot dzienny" : day_rate_of_return,
                    "Stopa zwrotu 1m" : rate_of_return,
                    "Stopa zwrotu 3m" : three_months_rate_of_return,
                    "Stopa zwrotu 6m" : six_months_rate_of_return,
                    "RSI" : current_rsi,
                    "Data": dane.index[-1].strftime('%Y-%m-%d')
                })
                print(
                    f"{symbol:<10} | "
                    f"{cena:>8.2f} {waluta:<3} | "
                    f"{wolumen:>12} | "
                    f"{day_rate_of_return*100:>15.2f}% | "
                    f"{rate_of_return*100:>15.2f}% | "
                    f"{three_months_rate_of_return*100:>15.2f}% | "
                    f"{six_months_rate_of_return*100:>15.2f}% | "
                    f"{current_rsi:>6.2f}"
                )
            else:
                print(f"{symbol:<10} | Brak danych")
        except Exception as e:
            print(f"{symbol:<7.2f} | Błąd: {e}")

# 3. Zapis do CSV i otwarcie pliku
if wyniki:
    nazwa_pliku = "notowania_gieldowe.csv"
    df = pd.DataFrame(wyniki)
    
    # Zapisujemy do CSV (używamy średnika jako separatora, lepiej działa w polskim Excelu)
    df.to_csv(nazwa_pliku, index=False, sep=';', encoding='utf-8-sig')
    print(f"\nZapisano dane do: {nazwa_pliku}")

    # 4. Automatyczne otwarcie pliku zależnie od systemu
    try:
        if platform.system() == "Windows":
            os.startfile(nazwa_pliku)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open {nazwa_pliku}")
        else:  # Linux
            os.system(f"xdg-open {nazwa_pliku}")
    except Exception as e:
        print(f"Nie udało się otworzyć pliku automatycznie: {e}")
else:
    print("Nie pobrano żadnych danych do zapisu.")

print("\n--- KONIEC ---")