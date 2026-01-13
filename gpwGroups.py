import pandas as pd
import json
import requests
from io import StringIO

linki = {
    "WIG20": "https://strefainwestorow.pl/notowania/spolki-wig20", 
    "mWIG40": "https://strefainwestorow.pl/notowania/spolki-mwig40",
    "sWIG80": "https://strefainwestorow.pl/notowania/spolki-swig80"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

mozliwe_nazwy_kolumn = ["Symbol", "Skrót", "Ticker", "Kod", "Nazwa", "Walor"]

# <--- ZMIANA 1: Zamiast listy [], tworzymy słownik {} do trzymania grup
spolki_grupowane = {}

print("--- ROZPOCZYNAM POBIERANIE Z PODZIAŁEM NA GRUPY ---")

for nazwa_indeksu, url in linki.items():
    print(f"\nAnalizuję: {nazwa_indeksu}... ({url})")
    spolki_grupowane[nazwa_indeksu] = [] # Tworzymy pustą listę dla danej grupy
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            try:
                # Uwaga: Wikipedia i StrefaInwestorow mogą mieć różne kodowanie lub strukturę
                tabele = pd.read_html(StringIO(response.text))
            except ValueError:
                print("  -> Nie znaleziono żadnej tabeli.")
                continue

            znaleziono = False
            for i, tabela in enumerate(tabele):
                dostepne_kolumny = list(tabela.columns)
                pasujace = set(dostepne_kolumny).intersection(mozliwe_nazwy_kolumn)
                
                if pasujace:
                    nazwa_kolumny = list(pasujace)[0]
                    print(f"  -> Tabela nr {i}: Znaleziono kolumnę '{nazwa_kolumny}'!")
                    
                    ticker_list = tabela[nazwa_kolumny].tolist()
                    clean_list = []
                    
                    for t in ticker_list:
                        t = str(t).strip()
                        # Proste czyszczenie
                        if len(t) > 0 and len(t) < 15: 
                            # Dodajemy .WA tylko jeśli go nie ma (zabezpieczenie)
                            if not t.endswith(".WA"):
                                t = f"{t}.WA"
                            clean_list.append(t)
                            
                    # <--- ZMIANA 2: Przypisujemy wyniki do konkretnego klucza w słowniku
                    # Używamy set(), żeby od razu usunąć duplikaty w obrębie jednej grupy
                    spolki_grupowane[nazwa_indeksu] = sorted(list(set(clean_list)))
                    
                    print(f"     Pobrano {len(spolki_grupowane[nazwa_indeksu])} wpisów do grupy {nazwa_indeksu}.")
                    znaleziono = True
                    break 
            
            if not znaleziono:
                print(f"  -> OSTRZEŻENIE: Nie rozpoznano kolumn dla {nazwa_indeksu}.")

        else:
            print(f"  -> Błąd HTTP: {response.status_code}")

    except Exception as e:
        print(f"  -> Błąd przy {nazwa_indeksu}: {e}")

# <--- ZMIANA 3: Sprawdzenie czy cokolwiek pobraliśmy (sumujemy długości list)
laczna_ilosc = sum(len(v) for v in spolki_grupowane.values())

if laczna_ilosc > 0:
    print(f"\nSUKCES: Łącznie masz {laczna_ilosc} symboli w podziale na grupy.")
    
    # Tworzymy ostateczną strukturę JSON
    dane_wyjsciowe = {
        "okres": "1d",
        "grupy": spolki_grupowane  # Tu wrzucamy nasz słownik z podziałem
    }
    
    with open('configGPW.json', 'w') as f:
        json.dump(dane_wyjsciowe, f, indent=4)
        print("Zapisano plik 'configGPW.json'.")
else:
    print("\nPORAŻKA: Nic nie pobrano.")