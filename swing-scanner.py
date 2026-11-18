
import json
import pandas as pd
import yfinance as yf


def safe_get(df: pd.DataFrame, keys: list[str], col_idx: int = 0) -> float | None:
    """Bezpiecznie pobiera wartość ze sprawozdania finansowego po liście możliwych nazw wiersza."""
    if df is None or df.empty or df.shape[1] <= col_idx:
        return None
    for key in keys:
        if key in df.index:
            val = df.loc[key].iloc[col_idx]
            if pd.notna(val):
                return float(val)
    return None


def oblicz_piotroski(bs: pd.DataFrame, inc: pd.DataFrame, cf: pd.DataFrame) -> int | None:
    """Oblicza Piotroski F-Score (0-9) na podstawie ostatnich 2 lat obrotowych."""
    if any(df is None or df.empty or df.shape[1] < 2 for df in (bs, inc, cf)):
        return None

    # Dane za bieżący rok (0) i poprzedni rok (1)
    ni_0 = safe_get(inc, ["Net Income", "Net Income Common Stockholders"], 0)
    ni_1 = safe_get(inc, ["Net Income", "Net Income Common Stockholders"], 1)

    ta_0 = safe_get(bs, ["Total Assets"], 0)
    ta_1 = safe_get(bs, ["Total Assets"], 1)

    cfo_0 = safe_get(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], 0)

    ltd_0 = safe_get(bs, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"], 0) or 0.0
    ltd_1 = safe_get(bs, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"], 1) or 0.0

    ca_0 = safe_get(bs, ["Current Assets"], 0)
    ca_1 = safe_get(bs, ["Current Assets"], 1)
    cl_0 = safe_get(bs, ["Current Liabilities"], 0)
    cl_1 = safe_get(bs, ["Current Liabilities"], 1)

    shares_0 = safe_get(bs, ["Ordinary Shares Number", "Share Issued"], 0)
    shares_1 = safe_get(bs, ["Ordinary Shares Number", "Share Issued"], 1)

    gp_0 = safe_get(inc, ["Gross Profit"], 0)
    gp_1 = safe_get(inc, ["Gross Profit"], 1)
    rev_0 = safe_get(inc, ["Total Revenue", "Operating Revenue"], 0)
    rev_1 = safe_get(inc, ["Total Revenue", "Operating Revenue"], 1)

    # Sprawdzenie minimalnego zestawu danych
    if None in (ni_0, ni_1, ta_0, ta_1, cfo_0, ca_0, ca_1, cl_0, cl_1, gp_0, gp_1, rev_0, rev_1):
        return None
    if any(x == 0 for x in (ta_0, ta_1, cl_0, cl_1, rev_0, rev_1)):
        return None

    score = 0
    # 1. Rentowność (4 pkt)
    roa_0 = ni_0 / ta_0
    roa_1 = ni_1 / ta_1
    if roa_0 > 0:
        score += 1
    if cfo_0 > 0:
        score += 1
    if roa_0 > roa_1:
        score += 1
    if cfo_0 > ni_0:  # Jakość zysków (akruale)
        score += 1

    # 2. Dźwignia, płynność i źródła finansowania (3 pkt)
    if (ltd_0 / ta_0) <= (ltd_1 / ta_1):
        score += 1
    if (ca_0 / cl_0) > (ca_1 / cl_1):
        score += 1
    if shares_0 is not None and shares_1 is not None and shares_0 <= shares_1:
        score += 1

    # 3. Efektywność operacyjna (2 pkt)
    if (gp_0 / rev_0) > (gp_1 / rev_1):
        score += 1
    if (rev_0 / ta_0) > (rev_1 / ta_1):
        score += 1

    return score


def oblicz_altman_z(bs: pd.DataFrame, inc: pd.DataFrame, market_cap: float | None) -> float | None:
    """Oblicza klasyczny Altman Z-Score dla spółek giełdowych."""
    if bs is None or bs.empty or inc is None or inc.empty or not market_cap:
        return None

    ta = safe_get(bs, ["Total Assets"], 0)
    ca = safe_get(bs, ["Current Assets"], 0)
    cl = safe_get(bs, ["Current Liabilities"], 0)
    re = safe_get(bs, ["Retained Earnings"], 0)
    ebit = safe_get(inc, ["EBIT", "Operating Income"], 0)
    tl = safe_get(bs, ["Total Liabilities Net Minority Interest", "Total Liabilities"], 0)
    rev = safe_get(inc, ["Total Revenue", "Operating Revenue"], 0)

    if None in (ta, ca, cl, re, ebit, tl, rev) or ta == 0 or tl == 0:
        return None

    working_capital = ca - cl
    x1 = working_capital / ta
    x2 = re / ta
    x3 = ebit / ta
    x4 = market_cap / tl
    x5 = rev / ta

    z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
    return round(z_score, 2)


def oblicz_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    roll_up = up.ewm(com=period - 1, adjust=False).mean()
    roll_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))


# === GŁÓWNA PĘTLA SKANERA ===
try:
    with open("config.json", "r", encoding="utf-8") as plik:
        symbole = json.load(plik).get("symbole", [])
except FileNotFoundError:
    print("Błąd: Nie znaleziono pliku config.json!")
    symbole = []

if symbole:
    print(
        f"{'SYMBOL':<10} | {'KURS':>12} | {'RSI(wcz->dziś)':>16} | "
        f"{'PIOTROSKI':>9} | {'ALTMAN Z':>9} | {'SYGNAŁ SWING'}"
    )
    print("-" * 85)

    for symbol in symbole:
        try:
            ticker = yf.Ticker(symbol)
            dane = ticker.history(period="6mo")

            if dane.empty or len(dane) < 20:
                print(f"{symbol:<10} | Brak wystarczających danych cenowych")
                continue

            # 1. Aktualny kurs i waluta
            kurs = dane["Close"].iloc[-1]
            waluta = ticker.fast_info.get("currency", "?")
            market_cap = ticker.fast_info.get("marketCap")

            # 2. RSI (wczoraj vs dziś)
            rsi_seria = oblicz_rsi(dane["Close"])
            rsi_wczoraj = rsi_seria.iloc[-2]
            rsi_dzis = rsi_seria.iloc[-1]

            # 3. Fundamenty (Piotroski & Altman)
            bs = ticker.balance_sheet
            inc = ticker.financials
            cf = ticker.cashflow

            f_score = oblicz_piotroski(bs, inc, cf)
            z_score = oblicz_altman_z(bs, inc, market_cap)

            # 4. Logika sygnału Swing:
            # RSI przebiło 30 od dołu (wczoraj < 30, dziś >= 30) + zdrowe fundamenty (F >= 6, Z > 1.8)
            odbicie_rsi = (rsi_wczoraj < 30.0) and (rsi_dzis >= 30.0)
            zdrowy_piotroski = (f_score is not None) and (f_score >= 6)
            bezpieczny_altman = (z_score is not None) and (z_score > 1.8)

            if odbicie_rsi and zdrowy_piotroski and bezpieczny_altman:
                sygnal = "KUPUJ (Silne fundamenty + RSI 30)"
            elif odbicie_rsi:
                sygnal = "OBSERWUJ (Odbicie RSI 30, słabsze/brak fund.)"
            else:
                sygnal = "-"

            f_str = f"{f_score}/9" if f_score is not None else "Brak"
            z_str = f"{z_score:.2f}" if z_score is not None else "Brak"
            rsi_str = f"{rsi_wczoraj:>5.1f} -> {rsi_dzis:>5.1f}"

            print(
                f"{symbol:<10} | {kurs:>8.2f} {waluta:<3} | {rsi_str:>16} | "
                f"{f_str:>9} | {z_str:>9} | {sygnal}"
            )

        except Exception as e:
            print(f"{symbol:<10} | Błąd: {e}")