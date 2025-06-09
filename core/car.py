import os
import sys
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
        self.debuffs = []  # Lista aktywnych debuffów
        self.buffs = []
        self.liczbausterek = 0
        self.czas_dni = 1
        self.czas_godzin = 6
        self.base_maxkm = 200  # Bazowy maksymalny zasięg
        self.base_fuel_consumption = 0.1  # Bazowe spalanie (L/km)
        self.ostatni_postoj = 0
        self.odstep_postoj = random.randint(50, 70)
        self.kasa = 500  # zł
        self.pakiety_naprawcze = 1

        path = resource_path(events_file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.events = data.get("events", [])

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

    def get_current_maxkm(self):
        """Oblicza aktualny maksymalny zasięg uwzględniając debuffy i buffy"""
        multiplier = 1.0
        for debuff in self.debuffs:
            if debuff["type"] == "max_range":
                multiplier *= debuff["value"]
        for buff in self.buffs:
            if buff["type"] == "max_range":
                multiplier *= buff["value"]
        return self.base_maxkm * multiplier

    def get_current_fuel_consumption(self):
        """Oblicza aktualne spalanie uwzględniając debuffy i buffy"""
        multiplier = 1.0
        for debuff in self.debuffs:
            if debuff["type"] == "fuel_consumption":
                multiplier *= debuff["value"]
        for buff in self.buffs:
            if buff["type"] == "fuel_consumption":
                multiplier *= buff["value"]
        return self.base_fuel_consumption * multiplier

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
                self.base_maxkm += event.get("maxkm_upgrade", 0)

                for debuff in event.get("debuffs", []):
                    self.debuffs.append(debuff)
                    self.liczbausterek += 1
                for buff in event.get("buffs", []):
                    self.buffs.append(buff)

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
                    for debuff in event.get("debuffs", []):
                        self.debuffs.append(debuff)
                        self.liczbausterek += 1
                    for buff in event.get("buffs", []):
                        self.buffs.append(buff)
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
        current_maxkm = self.get_current_maxkm()
        current_consumption = self.get_current_fuel_consumption()
        zuzycie = km * current_consumption

        if self.debuffs:
            print("\n⚠️ Uwaga! Samochód ma następujące problemy:")
            for debuff in self.debuffs:
                print(f"- {debuff['description']}")
            print()

        if km > current_maxkm:
            print(f"Nie możesz jechać dalej niż {current_maxkm:.2f} km na raz!")
            return

        if self.paliwo < zuzycie:
            print("Dalej nie pojedziesz, masz za mało paliwa")
            print(f"Paliwo: {self.paliwo:.2f}L/{self.pojbak:.2f}L\n")
            return

        self.paliwo -= zuzycie
        self.przebieg += km
        self.dodaj_czas(km / 50)

        print(f"Przejechałeś {km:.2f}km i zużyłeś {zuzycie:.2f}L (spalanie: {current_consumption * 100:.1f}L/100km)")
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
        if self.debuffs:
            print("Naprawiam problemy...")
            time.sleep(2)
            self.debuffs = []
            print("Wszystkie problemy zostały naprawione.\n")
        else:
            print("Nie ma nic do naprawy.\n")

    def use_repair_kit(self):
        if self.pakiety_naprawcze <= 0:
            print("Brak pakietów naprawczych!")
            return False
        if not self.debuffs:
            print("Pojazd jest już w pełni sprawny.")
            return False
        if self.debuffs:
            self.pakiety_naprawcze -= 1
            self.debuffs = []
            print(f"Użyto pakietu naprawczego. Naprawiono samochód. Pozostało {self.pakiety_naprawcze} pakietów.")
            return True

    def statystyki(self):
        print(f"\n📊 {self.name} {self.model} ({self.year})")
        print(f"🔧 Przebieg: {self.przebieg} km")
        print(f"⛽ Paliwo: {self.paliwo:.1f} / {self.pojbak} L")
        print(f"🚀 Zasięg: {self.get_current_maxkm()} km")
        print(f"🔥 Spalanie: {self.get_current_fuel_consumption() * 100:.1f}L/100km")
        print(f"🧰 Pakiety naprawcze: {self.pakiety_naprawcze}")
        print(f"💰 Kasa: {self.kasa} zł")
        print(f"🛠️ Usterki: {self.liczbausterek}")
        print(f"🌤️ Dzień {self.czas_dni}, godzina {self.czas_godzin}:00")
        if self.buffs:
            print("Aktywne bonusy:")
            for buff in self.buffs:
                print(f"- {buff['description']}")
        else:
            print("Aktywne bonusy: Brak")

        if self.debuffs:
            print("Aktualne problemy:")
            for debuff in self.debuffs:
                print(f"- {debuff['description']}")
        else:
            print("Aktualne problemy: Brak")

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
            "debuffs": self.debuffs,
            "buffs": self.buffs,
            "liczbausterek": self.liczbausterek,
            "czas_dni": self.czas_dni,
            "czas_godzin": self.czas_godzin,
            "base_maxkm": self.base_maxkm,
            "base_fuel_consumption": self.base_fuel_consumption,
            "occurred_events": list(self.occurred_events),
            "ostatni_postoj": self.ostatni_postoj,
            "kasa": self.kasa,
            "pakiety_naprawcze": self.pakiety_naprawcze,
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
        car.debuffs = data["debuffs"]
        car.buffs = data["buffs"]
        car.liczbausterek = data["liczbausterek"]
        car.czas_dni = data["czas_dni"]
        car.czas_godzin = data["czas_godzin"]
        car.base_maxkm = data["base_maxkm"]
        car.base_fuel_consumption = data.get("base_fuel_consumption", 0.1)
        car.occurred_events = set(data.get("occurred_events", []))
        car.ostatni_postoj = data["ostatni_postoj"]
        car.kasa = data["kasa"]
        car.pakiety_naprawcze = data["pakiety_naprawcze"]
        return car


class Lokacja:
    def __init__(self, name, type_, description, options, bonus=None):
        self.name = name
        self.type = type_
        self.description = description
        self.options = options
        self.bonus = bonus or {}

    def pokaz(self):
        print(f"\n🌍 {self.name} ({self.type})")
        print(self.description)
        if self.options:
            print(f"Dostępne opcje: {', '.join(self.options)}\n")
        else:
            print("Nie ma tu nic ciekawego...\n")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # używane przez PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def wygeneruj_lokacje():
    path = resource_path("utils/locations.json")
    with open(path, "r", encoding="utf-8") as f:
        dane_lokacji = json.load(f)

    losowa_lokacja = random.choice(dane_lokacji)
    return Lokacja(
        name=losowa_lokacja["name"],
        type_=losowa_lokacja["type"],
        description=losowa_lokacja["description"],
        options=losowa_lokacja.get("options", []),
        bonus=losowa_lokacja.get("bonus", {})
    )