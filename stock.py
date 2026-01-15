import yfinance as yf
import json
import pandas as pd  # Biblioteka do łatwego zapisu CSV
import os            # Do otwierania pliku w systemie
import platform      # Do sprawdzenia systemu operacyjnego

# 1. Wczytujemy konfigurację
try:
    with open('config.json', 'r') as plik:
        konfiguracja = json.load(plik)
    symbole = konfiguracja['symbole']
    okres = konfiguracja.get('okres', '1d')
    print(f"Wczytano {len(symbole)} spółek.")
except FileNotFoundError:
    print("Błąd: Nie znaleziono pliku config.json!")
    symbole = []

# 2. Pobieranie danych i zapis do listy
wyniki = []
if symbole:
    print(f"--- POBIERANIE DANYCH ({okres}) ---")
    print(f"{'SYMBOL':<{10}} | {'CENA':>{12}} | {'WOLUMEN':>{12}}")
    for symbol in symbole:
        try:
            ticker = yf.Ticker(symbol)
            dane = ticker.history(period=okres)
            
            if not dane.empty:
                cena = dane['Close'].iloc[-1]
                waluta = ticker.info.get('currency', '?')
                wolumen = dane['Volume'].iloc[-1]
                wyniki.append({
                    "Symbol": symbol,
                    "Cena": round(cena, 2),
                    "Waluta": waluta,
                    "Wolumen" : wolumen,
                    "Data": dane.index[-1].strftime('%Y-%m-%d')
                })
                print(f"{symbol:<10} | {cena:>8.2f} {waluta:<3} | {wolumen:>12}")
            else:
                print(f"{symbol:<10} | Brak danych")
        except Exception as e:
            print(f"{symbol:<10} | Błąd: {e}")

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