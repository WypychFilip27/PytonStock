# Plik: strategia.py
import yfinance as yf
import pandas as pd

pd.options.mode.chained_assignment = None 

def pobierz_sygnal_pullBack(rate_of_return, current_rsi):
      if rate_of_return > 0 and current_rsi < 30:
                    return "KUPUJ"

      elif current_rsi > 70:
        return "SPRZEDAJ"

      elif rate_of_return < 0:
        return "ZAMKNIJ"

      else:
        return "CZEKAJ"