#!/usr/bin/env python3
"""
Depot T+S — tägliche Kursabfrage via yfinance
Läuft als GitHub Actions Job, speichert kurse.json ins Repository
"""
import json
import datetime
import yfinance as yf

# Positionen mit Yahoo Finance Tickern
# Format: (name, yahoo_ticker, waehrung, stk, fixed_wert)
POSITIONEN = [
    # DB WM
    ("DWS Laufzeit 2027",   "DWS3JR.DE",  "EUR", 685,  None),
    ("DWS Infra. Europa",   "DWSE01.DE",  "EUR", 960,  None),
    # DiBa 536
    ("JPMorgan Global REI", "JREG.L",     "GBp", 387,  None),  # GBp = pence -> /100 -> GBP -> EUR
    ("UBS MSCI World SRI",  "WSRI.SW",    "CHF", 279,  None),
    ("GLS Mikrofinanz",     None,          "EUR", 152,  None),  # kein Ticker verfuegbar
    # DiBa 607
    ("Xtrackers XEON 607",  "XEON.DE",    "EUR", 134,  None),
    # DiBa 629
    ("iShares MSCI World",  "IWDA.AS",    "EUR", 230,  None),
    ("Xtrackers XEON 629",  "XEON.DE",    "EUR", 348,  None),
    # Cash (feste Werte)
    ("Cash Konto 972",      None,          "EUR", None, 7381),
    ("Cash Konto 766",      None,          "EUR", None, 9973),
    # Aktie
    ("Capgemini SE",        "CAP.PA",     "EUR", 295,  None),
    # Vorsorge (feste Werte — keine Boersenkurse)
    ("Riester Thomas",      None,          "EUR", None, 54550),
    ("Riester Stephanie",   None,          "EUR", None, 12828),
]

# EUR Wechselkurse via Yahoo
def get_rate(pair):
    try:
        t = yf.Ticker(pair)
        h = t.history(period="2d")
        if not h.empty:
            return float(h["Close"].iloc[-1])
    except:
        pass
    return None

def get_kurs(ticker, waehrung):
    if not ticker:
        return None, None
    try:
        t = yf.Ticker(ticker)
        h = t.history(period="5d")
        if h.empty:
            return None, None
        kurs = float(h["Close"].iloc[-1])
        datum = str(h.index[-1].date())

        # Umrechnung in EUR
        if waehrung == "GBp":  # Pence -> GBP -> EUR
            gbp_eur = get_rate("GBPEUR=X") or 1.17
            kurs = (kurs / 100) * gbp_eur
        elif waehrung == "CHF":
            chf_eur = get_rate("CHFEUR=X") or 1.05
            kurs = kurs * chf_eur
        elif waehrung == "USD":
            usd_eur = get_rate("USDEUR=X") or 0.92
            kurs = kurs * usd_eur

        return round(kurs, 4), datum
    except Exception as e:
        print(f"Fehler {ticker}: {e}")
        return None, None

def main():
    heute = datetime.date.today().isoformat()
    ergebnis = {
        "stand": heute,
        "generiert": datetime.datetime.now().isoformat(),
        "positionen": []
    }

    gesamt = 0
    for name, ticker, waehrung, stk, fw in POSITIONEN:
        if fw:
            # Fester Wert (Cash, Riester)
            eintrag = {
                "name": name,
                "kurs": None,
                "kurs_datum": None,
                "stk": stk,
                "wert": fw,
                "quelle": "manuell",
                "fehler": None
            }
            gesamt += fw
        else:
            kurs, datum = get_kurs(ticker, waehrung)
            if kurs and stk:
                wert = round(stk * kurs)
                fehler = None
            else:
                wert = None
                fehler = f"Kein Kurs verfuegbar fuer {ticker}"

            eintrag = {
                "name": name,
                "ticker": ticker,
                "kurs_eur": kurs,
                "kurs_datum": datum,
                "waehrung_original": waehrung,
                "stk": stk,
                "wert": wert,
                "quelle": "yahoo_finance",
                "fehler": fehler
            }
            if wert:
                gesamt += wert

        ergebnis["positionen"].append(eintrag)
        status = f"{round(eintrag.get('wert') or 0):>10,} EUR" if eintrag.get('wert') else "  KEIN KURS"
        print(f"{name:<25} {status}")

    ergebnis["gesamt"] = gesamt
    print(f"\nGesamt: {gesamt:,} EUR")

    with open("kurse.json", "w", encoding="utf-8") as f:
        json.dump(ergebnis, f, ensure_ascii=False, indent=2)
    print(f"\nGespeichert: kurse.json")

if __name__ == "__main__":
    main()
