import yfinance as yf
import json # Biblioteka do obsługi plików konfiguracyjnych

# 1. Wczytujemy konfigurację z pliku
try:
    with open('config.json', 'r') as plik:
        konfiguracja = json.load(plik)
        
    symbole = konfiguracja['symbole']
    okres = konfiguracja.get('okres', '1d') # Domyślnie 1d, jeśli brak w pliku

    print(f"Wczytano {len(symbole)} spółek z pliku config.json")

except FileNotFoundError:
    print("Błąd: Nie znaleziono pliku config.json!")
    symbole = [] # Pusta lista, żeby program się nie wywalił dalej

# 2. Pętla po spółkach (reszta bez większych zmian)
if symbole:
    print(f"--- POBIERANIE DANYCH (Okres: {okres}) ---")
    
    for symbol in symbole:
        try:
            ticker = yf.Ticker(symbol)
            # Używamy okresu z pliku config
            dane = ticker.history(period=okres)
            
            if not dane.empty:
                cena = dane['Close'].iloc[-1]
                # Dodajemy symbol waluty dla czytelności
                waluta = ticker.info.get('currency', '?')
                print(f"{symbol:<10} | {cena:>8.2f} {waluta}")
            else:
                print(f"{symbol:<10} | Brak danych")
        except Exception as e:
            print(f"{symbol:<10} | Błąd: {e}")
else:
    print("Brak symboli do sprawdzenia.")

print("\n--- KONIEC ---")