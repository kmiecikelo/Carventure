from core.car import Car

def main():
    pojazd = Car("Toyota", "Corolla", 2002, 500, 45, 50)

    # Pętla programu - nie zmieniam, możesz ją zostawić tak samo
    while True:
        print("\n--- MENU ---")
        print("statystyki – pokaż statystyki")
        print("jazda / jedź – jedź")
        print("tankuj – zatankuj")
        print("napraw – napraw samochód")
        print("wyjście / koniec / exit – zakończ program")

        wybor = input("Wybierz opcję: ").strip().lower()

        if wybor in ["statystyki", "status", "stat"]:
            pojazd.statystyki()
        elif wybor in ["jazda", "jedz", "jedź"]:
            km = int(input("Ile km chcesz przejechać? "))
            pojazd.jedz(km)
        elif wybor in ["tankuj", "paliwo", "zatankuj"]:
            litry = float(input("Ile litrów chcesz zatankować? "))
            pojazd.tankuj(litry)
        elif wybor in ["napraw", "mechanik"]:
            pojazd.napraw()
        elif wybor in ["wyjście", "exit", "koniec"]:
            print("Zamykanie programu...")
            break
        else:
            print("Nieprawidłowy wybór, spróbuj ponownie.")

if __name__ == "__main__":
    main()
