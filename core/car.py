import time
import json
import random

from core.save import save_game, load_game


class Car:
    def __init__(self, name, model, year, przebieg, paliwo, pojbak, events_file="utils/events.json"):
        self.name = name
        self.model = model
        self.year = year
        self.przebieg = przebieg
        self.paliwo = paliwo
        self.pojbak = pojbak
        self.usterki = []
        self.liczbausterek = 0
        self.czas_dni = 1
        self.czas_godzin = 6
        self.maxkm = 200
        self.ostatni_postoj = 0
        self.odstep_postoj = random.randint(50, 70)

        with open(events_file, "r", encoding="utf-8") as f:
            self.events = json.load(f)

        self.occurred_events = set()

    def pokaz_czas_dnia(self):
        godzina = int(self.czas_godzin) % 24
        dzien = self.czas_dni
        emoji = "☀️" if 6 <= godzina < 18 else "🌙"
        print(f"Dzień {dzien}, godzina: {godzina}:00 {emoji}")

    def dodaj_czas(self, godziny):
        self.czas_godzin += godziny
        if self.czas_godzin >= 24:
            self.czas_dni += int(self.czas_godzin // 24)
            self.czas_godzin %= 24

    def sprawdz_zdarzenia(self):
        for event in self.events:
            name = event.get("name")
            if not event.get("repeatable", False) and name in self.occurred_events:
                continue

            if (self.przebieg >= event.get("trigger_km", 0) and
                    self.czas_dni >= event.get("trigger_day", 0)):

                print(f"\n💥 {event['description']}")
                self.paliwo = max(0, self.paliwo - event.get("fuel_loss", 0))
                self.pojbak += event.get("tank_upgrade", 0)
                self.maxkm += event.get("maxkm_upgrade", 0)

                for dmg in event.get("damage", []):
                    self.usterki.append(dmg)
                    self.liczbausterek += 1

                if not event.get("repeatable", False):
                    self.occurred_events.add(name)
                return True
        return False

    def losowe_zdarzenia(self):
        for event in self.events:
            if event.get("trigger_km") == 0:
                if random.random() < event.get("chance", 0.2):
                    if not event.get("repeatable", False) and event["name"] in self.occurred_events:
                        continue
                    print(f"🚨 {event['description']}")
                    for dmg in event.get("damage", []):
                        self.usterki.append(dmg)
                        self.liczbausterek += 1
                    if not event.get("repeatable", False):
                        self.occurred_events.add(event["name"])

    def interakcja_z_lokacja(self, lokacja):
        if not lokacja.options:
            print("Nie masz nic do zrobienia w tym miejscu.\n")
            return

        while True:
            print("Co chcesz zrobić?")
            for i, opcja in enumerate(lokacja.options, 1):
                print(f"{i}. {opcja.capitalize()}")
            print("0. Opuść lokację\n")

            wybor = input("Wybierz opcję: ").strip()
            if wybor == "0":
                print("Opuściłeś lokację.\n")
                break
            elif wybor.isdigit() and 1 <= int(wybor) <= len(lokacja.options):
                akcja = lokacja.options[int(wybor) - 1]
                if akcja == "tankowanie":
                    try:
                        litry = float(input("Ile litrów zatankować? "))
                        self.tankuj(litry)
                    except ValueError:
                        print("Nieprawidłowa wartość.")
                elif akcja == "naprawa":
                    self.napraw()
                elif akcja == "handel":
                    print("💰 Spotkałeś handlarza, ale nic ciekawego nie miał.")
                    self.dodaj_czas(1)
                else:
                    print("Nieznana akcja.")
            else:
                print("Nieprawidłowy wybór.")

    def jedz(self, km):
        zuzycie = km * 0.1
        if self.usterki:
            print("Zanim pojedziesz musisz naprawić swoją furkę!\n")
            print(f"Usterki: {self.usterki}")
            return

        if km > self.maxkm:
            print(f"Nie możesz jechać dalej niż {self.maxkm} km na raz!")
            return

        if self.paliwo < zuzycie:
            print("Dalej nie pojedziesz, masz za mało paliwa")
            print(f"Paliwo: {self.paliwo:.2f}L/{self.pojbak:.2f}L\n")
            return

        self.paliwo -= zuzycie
        self.przebieg += km
        self.dodaj_czas(km / 50)

        print(f"Przejechałeś {km:.2f}km i zużyłeś {zuzycie:.2f}L")
        print(f"Aktualny przebieg: {self.przebieg:.2f}km")
        print(f"Paliwo: {self.paliwo:.2f}L/{self.pojbak:.2f}L")
        time.sleep(0.5)

        if not self.sprawdz_zdarzenia():
            self.losowe_zdarzenia()
        if self.przebieg - self.ostatni_postoj >= self.odstep_postoj:
            lokacja = wygeneruj_lokacje()
            lokacja.pokaz()
            self.interakcja_z_lokacja(lokacja)
            self.ostatni_postoj = self.przebieg
            self.odstep_postoj = random.randint(50, 70)


    def tankuj(self, litry):
        if self.paliwo >= self.pojbak:
            print("Nie możesz więcej zatankować")
            return
        if litry <= 0:
            print("Podano nieprawidłową ilość paliwa.")
            return

        do_tankowania = min(litry, self.pojbak - self.paliwo)

        print("\nTankujesz furkę...")
        time.sleep(0.5)

        self.paliwo += do_tankowania
        self.dodaj_czas(do_tankowania / 2.5)

        print(f"Zatankowałeś {do_tankowania:.2f}L. Stan: {self.paliwo:.2f}/{self.pojbak:.2f}L\n")

    def napraw(self):
        if self.usterki:
            print("Naprawiam usterki...")
            time.sleep(2)
            self.usterki = []
            print("Wszystkie usterki zostały naprawione.\n")
        else:
            print("Nie ma nic do naprawy.\n")

    def statystyki(self):
        print(f"Producent: {self.name}, Model: {self.model}, Rok: {self.year}")
        print(f"Przebieg: {self.przebieg:.2f}km")
        print(f"Maksymalna podróż: {self.maxkm:.2f}km")
        print(f"Paliwo: {self.paliwo:.2f}L/{self.pojbak:.2f}L")
        print(f"Usterki od początku podróży: {self.liczbausterek}")
        print(f"Aktualne usterki: {self.usterki if self.usterki else 'Brak'}")
        print(f"Aktualna godzina: ", end="")
        self.pokaz_czas_dnia()
        print()

    def to_dict(self):
        return {
            "name": self.name,
            "model": self.model,
            "year": self.year,
            "przebieg": self.przebieg,
            "paliwo": self.paliwo,
            "pojbak": self.pojbak,
            "usterki": self.usterki,
            "liczbausterek": self.liczbausterek,
            "czas_dni": self.czas_dni,
            "czas_godzin": self.czas_godzin,
            "maksymalna_podroz": self.maxkm,
            "occurred_events": list(self.occurred_events),
            "ostatni_postoj": self.ostatni_postoj,
        }

    def save(self, filename="savegame.json"):
        save_game(self.to_dict(), filename)

    @classmethod
    def load(cls, filename="savegame.json"):
        data = load_game(filename)
        car = cls(
            data["name"],
            data["model"],
            data["year"],
            data["przebieg"],
            data["paliwo"],
            data["pojbak"],
        )
        car.usterki = data["usterki"]
        car.liczbausterek = data["liczbausterek"]
        car.czas_dni = data["czas_dni"]
        car.czas_godzin = data["czas_godzin"]
        car.maxkm = data["maksymalna_podroz"]
        car.occurred_events = set(data.get("occurred_events", []))
        car.ostatni_postoj = data["ostatni_postoj"]
        return car

class Lokacja:
    def __init__(self, name, type_, description, options, bonus=None):
        self.name = name
        self.type = type_
        self.description = description
        self.options = options
        self.bonus = bonus or {}

    def pokaz(self):
        print(f"\n🗺️ {self.name} ({self.type})")
        print(self.description)
        if self.options:
            print(f"Dostępne opcje: {', '.join(self.options)}\n")
        else:
            print("Nie ma tu nic ciekawego...\n")

def wygeneruj_lokacje():
    with open("utils/locations.json", "r", encoding="utf-8") as f:
        dane_lokacji = json.load(f)
    dane = random.choice(dane_lokacji)
    return Lokacja(
        name=dane["name"],
        type_=dane["type"],
        description=dane["description"],
        options=dane["options"],
        bonus=dane.get("bonus", {})
    )