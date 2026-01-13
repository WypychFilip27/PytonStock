import pandas as pd
import json
import requests
from io import StringIO

# Dodałem Bossa.pl do listy linków
linki = {
    "WIG20 (Wikipedia)": "https://pl.wikipedia.org/wiki/WIG20",
    "Bossa WIG20": "https://strefainwestorow.pl/notowania/spolki-wig20",
    "WIG40": "https://strefainwestorow.pl/notowania/spolki-mwig40",
    "WIG80": "https://strefainwestorow.pl/notowania/spolki-swig80"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# Dodałem "Nazwa" i "Walor" do poszukiwanych kolumn
mozliwe_nazwy_kolumn = ["Symbol", "Skrót", "Ticker", "Kod", "Nazwa", "Walor"]

wszystkie_spolki = []

print("--- ROZPOCZYNAM POBIERANIE (Tryb Hybrydowy: Wiki + Bossa) ---")

for indeks, url in linki.items():
    print(f"\nAnalizuję: {indeks}...")
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Pandas szuka wszystkich tabel w kodzie HTML
            try:
                tabele = pd.read_html(StringIO(response.text))
            except ValueError:
                print("  -> Nie znaleziono żadnej tabeli na stronie (może być ładowana przez JS).")
                continue

            znaleziono = False
            for i, tabela in enumerate(tabele):
                dostepne_kolumny = list(tabela.columns)
                
                # Szukamy części wspólnej między naszymi nazwami a kolumnami tabeli
                pasujace = set(dostepne_kolumny).intersection(mozliwe_nazwy_kolumn)
                
                if pasujace:
                    nazwa_kolumny = list(pasujace)[0]
                    print(f"  -> Tabela nr {i}: Znaleziono kolumnę '{nazwa_kolumny}'!")
                    
                    # Pobieramy dane
                    ticker_list = tabela[nazwa_kolumny].tolist()
                    
                    # Filtrowanie i czyszczenie
                    clean_list = []
                    for t in ticker_list:
                        t = str(t).strip()
                        # Bossa czasem daje pełne nazwy spółek w kolumnie Nazwa (np. "PKOBP" zamiast "PKO")
                        # To może być problem dla Yahoo, ale pobieramy co dają.
                        if len(t) > 0 and len(t) < 15: 
                            clean_list.append(f"{t}.WA")
                            
                    wszystkie_spolki.extend(clean_list)
                    print(f"     Pobrano {len(clean_list)} wpisów.")
                    znaleziono = True
                    break 
            
            if not znaleziono:
                print(f"  -> OSTRZEŻENIE: Strona pobrana, ale nie rozpoznano kolumn. Dostępne: {tabele[0].columns.tolist() if tabele else 'Brak'}")

        else:
            print(f"  -> Błąd HTTP: {response.status_code}")

    except Exception as e:
        print(f"  -> Błąd przy {indeks}: {e}")

# Czyszczenie duplikatów
wszystkie_spolki = list(set(wszystkie_spolki))
wszystkie_spolki.sort()

if wszystkie_spolki:
    print(f"\nSUKCES: Łącznie masz {len(wszystkie_spolki)} symboli.")
    # Zapis
    with open('configGPW.json', 'w') as f:
        json.dump({"okres": "1d", "symbole": wszystkie_spolki}, f, indent=4)
else:
    print("\nPORAŻKA: Nic nie pobrano.")