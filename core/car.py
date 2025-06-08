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

        # Wczytanie zdarzeń z pliku JSON
        with open(events_file, "r", encoding="utf-8") as f:
            self.events = json.load(f)

        self.occurred_events = set()

    def pokaz_czas_dnia(self):
        godzina = int(self.czas_godzin) % 24
        dzien = self.czas_dni
        if 6 <= godzina < 18:
            print(f"Dzień {dzien}, godzina: {godzina}:00 ☀️")
        else:
            print(f"Dzień {dzien}, godzina: {godzina}:00 🌙")

    def dodaj_czas(self, godziny):
        self.czas_godzin += godziny
        if self.czas_godzin >= 24:
            dodatkowe_dni = int(self.czas_godzin // 24)
            self.czas_dni += dodatkowe_dni
            self.czas_godzin = self.czas_godzin % 24

    def sprawdz_zdarzenia(self):
        for event in self.events:
            name = event.get("name")
            if not event.get("repeatable", False) and name in self.occurred_events:
                continue

            trigger_km = event.get("trigger_km", 0)
            trigger_day = event.get("trigger_day", 0)
            if (self.przebieg >= trigger_km) and (self.czas_dni >= trigger_day):
                print(f"\n💥 {event['description']}")
                if "fuel_loss" in event:
                    self.paliwo = max(0, self.paliwo - event["fuel_loss"])
                if "tank_upgrade" in event:
                    self.pojbak += event["tank_upgrade"]
                if "maxkm_upgrade" in event:
                    self.maxkm += event["maxkm_upgrade"]
                if "damage" in event:
                    for dmg in event["damage"]:
                        self.usterki.append(dmg)
                        self.liczbausterek += 1
                if not event.get("repeatable", False):
                    self.occurred_events.add(name)
                return True
        return False

    def losowe_zdarzenia(self):
        for event in self.events:
            if event.get("trigger_km") == 0:
                szansa = event.get("chance", 0.2)
                if random.random() < szansa:
                    if not event.get("repeatable", False) and event["name"] in self.occurred_events:
                        continue
                    print(f"🚨 {event['description']}")
                    if "damage" in event:
                        for dmg in event["damage"]:
                            self.usterki.append(dmg)
                            self.liczbausterek += 1
                    if not event.get("repeatable", False):
                        self.occurred_events.add(event["name"])

    def jedz(self, km):
        zuzycie = km * 0.1
        if self.usterki:
            print(f"Zanim pojedziesz musisz naprawić swoją furkę!\n")
            print(f"Usterka: {self.usterki}")
            return

        if km > self.maxkm:
            print(f"Nie możesz jechać dalej niż {self.maxkm} km na raz!")
            return

        if self.paliwo < zuzycie:
            print(f"Dalej nie pojedziesz, masz za mało paliwa")
            print(f"Paliwo: : {self.paliwo:.2f}L/{self.pojbak:.2f}L\n")
            return

        self.paliwo -= zuzycie
        self.przebieg += km
        self.dodaj_czas(km / 50)
        print(f"Przejechałeś {km:.2f}km i zużyłeś {zuzycie:.2f}L")
        print(f"Aktualny przebieg {self.przebieg:.2f}km")
        print(f"Paliwo: {self.paliwo:.2f}L/{self.pojbak:.2f}L")
        time.sleep(0.5)

        wydarzenie = self.sprawdz_zdarzenia()
        if not wydarzenie:
            self.losowe_zdarzenia()

    def tankuj(self, litry):
        if self.paliwo >= self.pojbak:
            print(f"Nie możesz więcej zatankować")
            return
        if litry <= 0:
            print("Podano nieprawidłową ilość paliwa.")
            return

        dostepne_miejsce = self.pojbak - self.paliwo
        do_tankowania = min(litry, dostepne_miejsce)
        print("\nTankujesz furkę...")
        time.sleep(0.5)
        self.paliwo += do_tankowania
        self.dodaj_czas(do_tankowania / 2.5)
        print(f"Zatankowałeś {do_tankowania:.2f}L. Stan: {self.paliwo:.2f}/{self.pojbak:.2f}L\n")

    def napraw(self):
        if self.usterki:
            print(f"Naprawiam usterki...")
            time.sleep(2)
            self.usterki = []
            print("Wszystkie usterki zostały naprawione.\n")
        else:
            print(f"Nie ma nic do naprawy.\n")

    def statystyki(self):
        print(f"Producent:{self.name} Model: {self.model} Rok Produkcji: {self.year}")
        print(f"Przebieg: {self.przebieg:.2f}km")
        print(f"Maksymalna podróż: {self.maxkm:.2f}km")
        print(f"Paliwo: {self.paliwo:.2f}L/{self.pojbak:.2f}")
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
        return car