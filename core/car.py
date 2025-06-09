import os
import sys
import time
import json
import random
from core.save import save_game, load_game


class Car:
    def __init__(self, name, model, year, przebieg, paliwo, pojbak, events_file="utils/events.json",
                 items_file="utils/items.json"):
        self.name = name
        self.model = model
        self.year = year
        self.przebieg = przebieg
        self.paliwo = paliwo
        self.pojbak = pojbak
        self.debuffs = []
        self.buffs = []
        self.event_cooldowns = {}
        self.liczbausterek = 0
        self.czas_dni = 1
        self.czas_godzin = 6
        self.base_maxkm = 200
        self.base_fuel_consumption = 0.1
        self.ostatni_postoj = 0
        self.odstep_postoj = random.randint(50, 70)
        self.kasa = 50
        self.pakiety_naprawcze = 1
        self.inventory = []

        # Ładowanie zdarzeń
        path = resource_path(events_file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.events = data.get("events", [])

        # Ładowanie przedmiotów
        self.load_items(items_file)

        self.occurred_events = set()

    def load_items(self, items_file):
        path = resource_path(items_file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.available_items = data.get("items", [])

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
        multiplier = 1.0
        for debuff in self.debuffs:
            if debuff["type"] == "max_range":
                multiplier *= debuff["value"]
        for buff in self.buffs:
            if buff["type"] == "max_range":
                multiplier *= buff["value"]
        return self.base_maxkm * multiplier

    def get_current_fuel_consumption(self):
        multiplier = 1.0
        for debuff in self.debuffs:
            if debuff["type"] == "fuel_consumption":
                multiplier *= debuff["value"]
        for buff in self.buffs:
            if buff["type"] == "fuel_consumption":
                multiplier *= buff["value"]
        return self.base_fuel_consumption * multiplier

    def update_buffs(self, distance):
        for buff in self.buffs[:]:
            if "duration" in buff:
                buff["duration"] -= distance
                if buff["duration"] <= 0:
                    self.buffs.remove(buff)
                    print(f"Efekt '{buff['description']}' wygasł.")

    def sprawdz_zdarzenia(self):
        for event in self.events:
            name = event.get("name")
            if not event.get("repeatable", False) and name in self.occurred_events:
                continue

            if event.get("repeatable", False):
                last_occurred = self.event_cooldowns.get(name, 0)
                if self.przebieg - last_occurred < 100:
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
                else:
                    self.event_cooldowns[name] = self.przebieg
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
        if not lokacja.options and not lokacja.shop_items:
            print("Nie masz nic do zrobienia w tym miejscu.\n")
            return

        while True:
            print("Co chcesz zrobić?")

            for i, opcja in enumerate(lokacja.options, 1):
                print(f"{i}. {opcja.capitalize()}")

            if lokacja.shop_items:
                for i, item in enumerate(lokacja.shop_items, len(lokacja.options) + 1):
                    print(f"{i}. Kup {item['name']} ({item['price']} zł)")

            if self.inventory:
                print(f"{len(lokacja.options) + len(lokacja.shop_items) + 1}. Użyj przedmiotu z ekwipunku")

            print("0. Opuść lokację\n")

            wybor = input("Wybierz opcję: ").strip()

            if wybor == "0":
                print("Opuściłeś lokację.\n")
                break

            elif wybor.isdigit():
                wybor = int(wybor)

                if 1 <= wybor <= len(lokacja.options):
                    akcja = lokacja.options[wybor - 1]
                    if akcja == "tankowanie":
                        try:
                            litry = float(input("Ile litrów zatankować? "))
                            self.tankuj(litry)
                        except ValueError:
                            print("Nieprawidłowa wartość.")
                    elif akcja == "naprawa":
                        self.napraw()
                    elif akcja == "handel":
                        print("💰 Handlarz oferuje swoje towary.")

                elif len(lokacja.options) < wybor <= len(lokacja.options) + len(lokacja.shop_items):
                    item = lokacja.shop_items[wybor - len(lokacja.options) - 1]
                    self.buy_item(item["id"])

                elif wybor == len(lokacja.options) + len(lokacja.shop_items) + 1 and self.inventory:
                    self.show_inventory()
                    item_choice = input("Wybierz numer przedmiotu do użycia (0 - anuluj): ").strip()
                    if item_choice.isdigit():
                        item_num = int(item_choice)
                        if 1 <= item_num <= len(self.inventory):
                            self.use_item(self.inventory[item_num - 1]["id"])

                else:
                    print("Nieprawidłowy wybór.")
            else:
                print("Nieprawidłowy wybór.")

    def jedz(self, km):
        current_maxkm = self.get_current_maxkm()
        current_consumption = self.get_current_fuel_consumption()
        zuzycie = km * current_consumption
        fluktuacja = random.gauss(1.0, 0.1)  # średnia 1.0, odchylenie 0.1
        zarobek = (km / 5) * fluktuacja
        self.kasa += zarobek

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
        self.update_buffs(km)

        print(f"Przejechałeś {km:.2f}km i zużyłeś {zuzycie:.2f}L (spalanie: {current_consumption * 100:.1f}L/100km)")
        print(f"Po drodze znalazłeś: {zarobek:.2f}zł")
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

    def buy_item(self, item_id):
        for item in self.available_items:
            if item["id"] == item_id:
                if self.kasa >= item["price"]:
                    self.kasa -= item["price"]
                    self.inventory.append(item)
                    print(f"Kupiłeś {item['name']} za {item['price']} zł. Pozostało {self.kasa} zł.")
                    return True
                else:
                    print("Nie masz wystarczająco pieniędzy!")
                    return False
        print("Nie ma takiego przedmiotu w sklepie!")
        return False

    def use_item(self, item_id):
        for item in self.inventory:
            if item["id"] == item_id:
                effect = item["effect"]
                if effect["action"] == "repair_all":
                    self.debuffs = []
                    print("Użyto zestawu naprawczego. Wszystkie usterki naprawione!")
                elif effect["action"] == "add_fuel":
                    fuel_to_add = min(effect["amount"], self.pojbak - self.paliwo)
                    self.paliwo += fuel_to_add
                    print(f"Dodano {fuel_to_add}L paliwa. Aktualny stan: {self.paliwo:.1f}/{self.pojbak}L")
                elif effect["action"] == "reduce_breakdown_chance":
                    self.buffs.append({
                        "type": "breakdown_chance",
                        "value": effect["value"],
                        "duration": effect["duration"],
                        "description": "Zmniejszona szansa na awarię"
                    })
                    print("Zainstalowano część zamienną. Szansa na awarię zmniejszona!")
                elif effect["action"] == "reduce_consumption":
                    self.buffs.append({
                        "type": "fuel_consumption",
                        "value": effect["value"],
                        "duration": effect["duration"],
                        "description": "Zmniejszone spalanie dzięki paliwu premium"
                    })
                    print("Zatankowano paliwo premium. Spalanie zmniejszone!")

                self.inventory.remove(item)
                return True

        print("Nie masz takiego przedmiotu w ekwipunku!")
        return False

    def show_inventory(self):
        if not self.inventory:
            print("Twój ekwipunek jest pusty.")
            return

        print("\nTwój ekwipunek:")
        for i, item in enumerate(self.inventory, 1):
            print(f"{i}. {item['name']} - {item['description']}")

    def statystyki(self):
        print(f"\n📊 {self.name} {self.model} ({self.year})")
        print(f"🔧 Przebieg: {self.przebieg} km")
        print(f"⛽ Paliwo: {self.paliwo:.1f} / {self.pojbak} L")
        print(f"🚀 Zasięg: {self.get_current_maxkm()} km")
        print(f"🔥 Spalanie: {self.get_current_fuel_consumption() * 100:.1f}L/100km")
        print(f"🧰 Pakiety naprawcze: {self.pakiety_naprawcze}")
        print(f"💰 Kasa: {self.kasa:.2f} zł")
        print(f"🎒 Przedmioty: {len(self.inventory)}")
        print(f"🛠️ Usterki: {self.liczbausterek}")
        print(f"\n🌤️ Aktualna godzina: ", end="")
        self.pokaz_czas_dnia()
        print()
        if self.buffs:
            print("\nAktywne bonusy:")
            for buff in self.buffs:
                print(f"- {buff['description']}" +
                      (f" (pozostało {buff['duration']}km)" if "duration" in buff else ""))

        if self.debuffs:
            print("\nAktualne problemy:")
            for debuff in self.debuffs:
                print(f"- {debuff['description']}")

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
            "event_cooldowns": self.event_cooldowns,
            "liczbausterek": self.liczbausterek,
            "czas_dni": self.czas_dni,
            "czas_godzin": self.czas_godzin,
            "base_maxkm": self.base_maxkm,
            "base_fuel_consumption": self.base_fuel_consumption,
            "occurred_events": list(self.occurred_events),
            "ostatni_postoj": self.ostatni_postoj,
            "kasa": self.kasa,
            "pakiety_naprawcze": self.pakiety_naprawcze,
            "inventory": self.inventory
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
        car.event_cooldowns = data.get("event_cooldowns", {})
        car.liczbausterek = data["liczbausterek"]
        car.czas_dni = data["czas_dni"]
        car.czas_godzin = data["czas_godzin"]
        car.base_maxkm = data["base_maxkm"]
        car.base_fuel_consumption = data.get("base_fuel_consumption", 0.1)
        car.occurred_events = set(data.get("occurred_events", []))
        car.ostatni_postoj = data["ostatni_postoj"]
        car.kasa = data["kasa"]
        car.pakiety_naprawcze = data["pakiety_naprawcze"]
        car.inventory = data.get("inventory", [])
        return car


class Lokacja:
    def __init__(self, name, type_, description, options, bonus=None, shop_items=None):
        self.name = name
        self.type = type_
        self.description = description
        self.options = options
        self.bonus = bonus or {}
        self.shop_items = shop_items or []

    def pokaz(self):
        print(f"\n🌍 {self.name} ({self.type})")
        print(self.description)

        if self.shop_items:
            print("\nW sklepie dostępne są:")
            for i, item in enumerate(self.shop_items, 1):
                print(f"{i}. {item['name']} - {item['description']} (Cena: {item['price']} zł)")

        if self.options:
            print(f"\nDostępne opcje: {', '.join(self.options)}")
        else:
            print("Nie ma tu nic ciekawego...")
        print()


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def wygeneruj_lokacje():
    path = resource_path("utils/locations.json")
    with open(path, "r", encoding="utf-8") as f:
        dane_lokacji = json.load(f)

    losowa_lokacja = random.choice(dane_lokacji)

    shop_items = []
    if random.random() < 0.7:
        path_items = resource_path("utils/items.json")
        with open(path_items, "r", encoding="utf-8") as f:
            items_data = json.load(f)
            all_items = items_data.get("items", [])
            shop_items = random.sample(all_items, min(random.randint(1, 3), len(all_items)))

    return Lokacja(
        name=losowa_lokacja["name"],
        type_=losowa_lokacja["type"],
        description=losowa_lokacja["description"],
        options=losowa_lokacja.get("options", []),
        bonus=losowa_lokacja.get("bonus", {}),
        shop_items=shop_items
    )