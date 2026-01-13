import json
import yfinance as yf
import pandas as pd
import datetime

# --- KONFIGURACJA ---
PLIK_CONFIG = 'configGPW.json'
OKRES_DANYCH = "6mo"  # Pobieramy 6 miesięcy danych, żeby wyliczyć średnie
INTERWAL = "1d"

def wczytaj_konfiguracje():
    try:
        with open(PLIK_CONFIG, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Błąd: Nie znaleziono pliku configGPW.json. Uruchom najpierw poprzedni skrypt!")
        exit()

def oblicz_wskazniki(df_ticker):
    """
    Funkcja oblicza wskaźniki dla pojedynczej spółki.
    Zwraca słownik z wynikami lub None, jeśli brak danych.
    """
    if df_ticker.empty or len(df_ticker) < 50:
        return None

    # Obliczenia
    aktualna_cena = df_ticker['Close'].iloc[-1]
    wczorajsza_cena = df_ticker['Close'].iloc[-2]
    zmiana_procentowa = ((aktualna_cena - wczorajsza_cena) / wczorajsza_cena) * 100
    
    # Średnia krocząca z 50 sesji (SMA50)
    sma50 = df_ticker['Close'].rolling(window=50).mean().iloc[-1]
    
    # Prosty sygnał: Czy cena jest nad średnią?
    trend = "WZROSTOWY 🐂" if aktualna_cena > sma50 else "SPADKOWY 🐻"
    
    return {
        "Cena": round(aktualna_cena, 2),
        "Zmiana %": round(zmiana_procentowa, 2),
        "SMA50": round(sma50, 2),
        "Trend": trend
    }

# --- GŁÓWNA PĘTLA PROGRAMU ---
config = wczytaj_konfiguracje()
wszystkie_wyniki = []

print(f"--- ROZPOCZYNAM ANALIZĘ RYNKU [{datetime.date.today()}] ---")

# Iterujemy po grupach z pliku JSON (WIG20, mWIG40 itd.)
for nazwa_indeksu, lista_spolek in config['grupy'].items():
    print(f"\n>>> Pobieram dane dla grupy: {nazwa_indeksu} ({len(lista_spolek)} spółek)...")
    
    if not lista_spolek:
        continue

    # 1. Pobieranie masowe (znacznie szybsze niż pętla po jednej spółce)
    # group_by='ticker' sprawia, że dane są ładnie pogrupowane spółkami
    try:
        data = yf.download(lista_spolek, period=OKRES_DANYCH, interval=INTERWAL, group_by='ticker', progress=True)
    except Exception as e:
        print(f"Błąd pobierania: {e}")
        continue

    print(f"    Analizuję wskaźniki...")

    # 2. Przetwarzanie każdej spółki z pobranej paczki
    for symbol in lista_spolek:
        try:
            # Wyciągamy DataFrame dla konkretnej spółki
            # Jeśli pobrano tylko jedną spółkę, struktura yfinance jest inna, stąd 'if'
            if len(lista_spolek) == 1:
                df_spolka = data
            else:
                df_spolka = data[symbol]

            # Sprawdzamy czy mamy dane (czasem spółka jest zdelistowana)
            # Dropna usuwa puste wiersze (np. dni wolne)
            df_spolka = df_spolka.dropna(how='all')
            
            wynik = oblicz_wskazniki(df_spolka)
            
            if wynik:
                # Dodajemy nazwę i indeks do wyniku
                wynik['Symbol'] = symbol
                wynik['Indeks'] = nazwa_indeksu
                wszystkie_wyniki.append(wynik)
                
        except KeyError:
            # Czasem yfinance nie pobierze danych dla konkretnego tickera
            pass

# --- PREZENTACJA WYNIKÓW ---

if wszystkie_wyniki:
    # Tworzymy DataFrame z wyników, żeby łatwo to wyświetlić/posortować
    raport = pd.DataFrame(wszystkie_wyniki)
    
    # Ustawiamy kolejność kolumn
    raport = raport[['Indeks', 'Symbol', 'Cena', 'Zmiana %', 'Trend', 'SMA50']]
    
    # --- PRZYKŁAD 1: Pokaż 5 najlepszych spółek dzisiaj ---
    top_wzrosty = raport.sort_values(by='Zmiana %', ascending=False).head(5)
    print("\n\n🏆 TOP 5 WZROSTÓW DZISIAJ:")
    print(top_wzrosty.to_string(index=False))

    # --- PRZYKŁAD 2: Pokaż spółki w silnym trendzie wzrostowym (Cena > SMA50) ---
    silne_byki = raport[raport['Trend'] == "WZROSTOWY 🐂"]
    print(f"\n\n📈 Ilość spółek w trendzie wzrostowym (nad SMA50): {len(silne_byki)} z {len(raport)}")
    
    # --- ZAPIS DO EXCELA / CSV ---
    nazwa_pliku = f"Raport_GPW_{datetime.date.today()}.csv"
    raport.to_csv(nazwa_pliku, index=False, encoding='utf-8-sig', sep=';')
    print(f"\nPełny raport zapisano w pliku: {nazwa_pliku}")

else:
    print("Brak danych do analizy.")