import json

def save_game(obj, filename="savegame.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4)
    print(f"Stan gry zapisany do {filename}")

def load_game(filename="savegame.json"):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Stan gry wczytany z {filename}")
    return data
