#!/usr/bin/env python3
"""
Monitor Cinema City: wysyła powiadomienie push (ntfy.sh), gdy w repertuarze
na wybrany dzień pojawi się film z podanym słowem w tytule.

Uruchomienie:  python3 diuna_watch.py
Wymaga tylko Pythona 3 (bez dodatkowych bibliotek).
"""
import json
import random
import time
import urllib.error
import urllib.request

# ---------------- KONFIGURACJA ----------------
# ID kina: patrz instrukcja (DevTools -> Network -> "film-events").
# Możesz podać kilka kin naraz.
CINEMAS = {
    "Moje kino": "1064",
}
DATE = "2026-12-18"                 # dzień regularnych seansów
KEYWORDS = ("diuna", "dune")        # słowa szukane w tytule (małe litery)
NTFY_TOPIC = "moraay-dune"  # unikalna nazwa kanału
INTERVAL = 60                       # sekundy między sprawdzeniami
# Jeśli URL z DevTools wygląda inaczej, wklej tutaj jego wzorzec
# z {cid} i {date} w miejscu ID kina i daty.
URL = ("https://www.cinema-city.pl/pl/data-api-service/v1/quickbook/10103/film-events/in-cinema/{cid}/at-date/{date}?attr=&lang=pl_PL")
# -----------------------------------------------

HEADERS = {"User-Agent": "Mozilla/5.0 (osobisty monitor repertuaru)"}


def notify(title, message, urgent=True):
    # Nagłówki HTTP bez polskich znaków, treść może je mieć.
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "urgent" if urgent else "default",
            "Click": "https://www.cinema-city.pl/",
        },
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print("Nie udało się wysłać powiadomienia:", e)


def fetch(cid):
    req = urllib.request.Request(URL.format(cid=cid, date=DATE), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def find_matches(data):
    """Zwraca tytuły pasujące do KEYWORDS, które mają seans w danym dniu."""
    body = data.get("body", data) if isinstance(data, dict) else {}
    films = body.get("films", []) or []
    events = body.get("events", []) or []
    with_events = {e.get("filmId") for e in events}
    found = []
    for f in films:
        name = str(f.get("name", ""))
        if any(k in name.lower() for k in KEYWORDS) and f.get("id") in with_events:
            found.append(name)
    return found


def main():
    if "WPISZ_ID_KINA" in CINEMAS.values():
        raise SystemExit("Najpierw wpisz ID kina w CINEMAS (patrz instrukcja).")
    notify("Monitor Cinema City dziala",
           f"Sprawdzam {DATE}, co {INTERVAL}s.", urgent=False)
    print("Start. Ctrl+C, żeby zakończyć.")
    while True:
        for cinema, cid in CINEMAS.items():
            try:
                matches = find_matches(fetch(cid))
            except (urllib.error.URLError, ValueError, OSError) as e:
                print(f"[{time.strftime('%H:%M:%S')}] {cinema}: błąd {e}")
                continue
            print(f"[{time.strftime('%H:%M:%S')}] {cinema}: "
                  f"{'ZNALEZIONO ' + ', '.join(matches) if matches else 'jeszcze nic'}")
            if matches:
                notify("BILETY RUSZYLY!",
                       f"{cinema}: {', '.join(matches)} na {DATE}. Wchodź!")
                return
        time.sleep(INTERVAL + random.uniform(0, 10))


if __name__ == "__main__":
    main()
