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
        self.czas_godzin = 8
        self.maxkm = 200

        # Wczytanie zdarzeń z pliku JSON
        with open(events_file, "r", encoding="utf-8") as f:
            self.events = json.load(f)

        # Zdarzenia które już wystąpiły (żeby się nie powtarzały)
        self.occurred_events = set()

    def pokaz_czas_dnia(self):
        godzina = int(self.czas_godzin) % 24
        if 6 <= godzina < 18:
            print(f"Jest dzień, godzina: {godzina}:00 ☀️")
        else:
            print(f"Jest noc, godzina: {godzina}:00 🌙")

    def sprawdz_zdarzenia(self):
        # Sprawdzenie zdarzeń specjalnych na podstawie przebiegu
        for event in self.events:
            name = event.get("name")
            if name in self.occurred_events:
                continue  # nie powtarzamy zdarzenia

            trigger_km = event.get("trigger_km", 0)
            if trigger_km > 0 and self.przebieg >= trigger_km:
                # Wywołujemy zdarzenie
                print(f"\n💥 {event['description']}")
                # Aktualizacja paliwa
                if "fuel_loss" in event:
                    self.paliwo = max(0, self.paliwo - event["fuel_loss"])
                # Aktualizacja baku
                if "tank_upgrade" in event:
                    self.pojbak += event["tank_upgrade"]
                # Dodanie usterek
                if "damage" in event:
                    for dmg in event["damage"]:
                        self.usterki.append(dmg)
                        self.liczbausterek += 1
                self.occurred_events.add(name)
                return True
        return False

    def losowe_zdarzenia(self):
        # Zdarzenia losowe (trigger_km == 0)
        for event in self.events:
            if event.get("trigger_km") == 0 and random.random() < 0.2:
                if event["name"] not in self.occurred_events:
                    print(f"🚨 {event['description']}")
                    if "damage" in event:
                        for dmg in event["damage"]:
                            self.usterki.append(dmg)
                            self.liczbausterek += 1
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
        self.czas_godzin += km / 50
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

        dostepne_miejsce = self.pojbak - self.paliwo
        do_tankowania = min(litry, dostepne_miejsce)
        print("\nTankujesz furkę...")
        time.sleep(0.5)
        self.paliwo += do_tankowania
        self.czas_godzin += do_tankowania / 2.5
        print(f"Zatankowałeś {do_tankowania:.2f}L. Stan: {self.paliwo:.2f}/{self.pojbak:.2f}L\n")

    def napraw(self):
        if self.usterki:
            print(f"Naprawiam usterki")
            time.sleep(2)
            self.usterki = []
        else:
            print(f"Nie ma nic do naprawy")

    def statystyki(self):
        print(f"Producent:{self.name} Model: {self.model} Rok Produkcji: {self.year}")
        print(f"Przebieg: {self.przebieg:.2f}km")
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
            "czas_godzin": self.czas_godzin,
            "maksymalna_podroz": self.maxkm,
            "napad1_wydarzyl_sie": "napad1" in self.occurred_events,
            "napad2_wydarzyl_sie": "napad2" in self.occurred_events,
            "ulepszenie1_wydarzylo_sie": "ulepszenie1" in self.occurred_events,
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
        car.czas_godzin = data["czas_godzin"]
        car.maxkm = data["maksymalna_podroz"]
        car.occurred_events = set()
        if data.get("napad1_wydarzyl_sie"):
            car.occurred_events.add("napad1")
        if data.get("napad2_wydarzyl_sie"):
            car.occurred_events.add("napad2")
        if data.get("ulepszenie1_wydarzylo_sie"):
            car.occurred_events.add("ulepszenie1")
        return car