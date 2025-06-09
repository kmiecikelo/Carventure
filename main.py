import os
from core.car import Car

SAVE_FILE = "savegame.json"

def show_logo():
    logo = r"""
 _____                            _                  
/  __ \                          | |                 
| /  \/ __ _ _ ____   _____ _ __ | |_ _   _ _ __ ___ 
| |    / _` | '__\ \ / / _ \ '_ \| __| | | | '__/ _ \
| \__/\ (_| | |   \ V /  __/ | | | |_| |_| | | |  __/
 \____/\__,_|_|    \_/ \___|_| |_|\__|\__,_|_|  \___|
    """
    print(logo)

def try_load_game():
    if os.path.exists(SAVE_FILE):
        print("🔍 Wykryto zapis gry.")
        choice = input("Czy chcesz wczytać zapis? (t/n): ").strip().lower()
        if choice == "t":
            try:
                return Car.load()
            except Exception as e:
                print(f"Błąd wczytywania zapisu: {e}")
    return None

def main():
    show_logo()
    pojazd = try_load_game()
    if not pojazd:
        pojazd = Car("Toyota", "Corolla", 2002, 500, 45, 50)

    while True:
        print("\n--- MENU ---")
        print("[1] Statystyki")
        print("[2] Jazda")
        print("[3] Zapisz grę")
        print("[4] Wczytaj zapis")
        print("[0] Wyjście")

        wybor = input("Wybierz opcję: ").strip().lower()

        if wybor in ["1", "statystyki", "status", "stat"]:
            pojazd.statystyki()
        elif wybor in ["2", "jazda", "jedz", "jedź"]:
            try:
                km = int(input("🚗 Ile km chcesz przejechać? "))
                pojazd.jedz(km)
            except ValueError:
                print("❌ Podaj poprawną liczbę kilometrów.")
        elif wybor in ["3", "zapisz"]:
            pojazd.save()
            print("💾 Gra została zapisana.")
        elif wybor in ["4", "wczytaj"]:
            try:
                pojazd = Car.load()
                print("✅ Gra została wczytana.")
            except Exception as e:
                print(f"❌ Błąd podczas wczytywania: {e}")
        elif wybor in ["0", "wyjście", "exit", "koniec"]:
            print("👋 Zamykanie programu...")
            break
        else:
            print("❌ Nieprawidłowy wybór, spróbuj ponownie.")

if __name__ == "__main__":
    main()
