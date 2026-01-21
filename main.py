def start_menu():
    print("=== SKOLMATS-SIMULATORN 3000 ===")
    name = input("Välj ditt namn: ")
    print(f"Välkommen {name}! Dags att möta skolmaten...\n")
    return name


def lunch_event(points, health, inventory):
    print("\nLunchmatsalen:")
    print("1. Ät maten som den är")
    print("2. Lägg till mystisk ingrediens")

    choice = input("Vad gör du? ")

    if choice == "1":
        print("Den smakar... misstänkt.")
        health -= 1
    elif choice == "2":
        ingredient = "Okänt kött"
        print(f"Du lägger till {ingredient}. Realismen ökar!")
        inventory.append(ingredient)
        points += 10
        health -= 1
    else:
        print("Du tvekar och tappar aptiten.")

    return points, health


def kitchen_event(points, inventory):
    print("\nSkolköket:")
    print("1. Häll i rengöringsmedel")
    print("2. Håll dig borta")

    choice = input("Val: ")

    if choice == "1":
        print("Extremt realistiskt. Läraren tittar bort.")
        inventory.append("Rengöringsmedel")
        points += 20
    else:
        print("Tråkigt men säkert.")

    return points


def show_status(points, health, inventory):
    print("\n--- STATUS ---")
    print("Poäng:", points)
    print("Hälsa:", health)
    print("Ingredienser:", inventory)


def game_over(points):
    print("\nSpelet är slut!")
    print(f"Du fick {points} realism-poäng.")
    if points >= 30:
        print("Skolmaten är nu 100% realistisk.")
    else:
        print("Maten kunde varit värre...")


# Huvudprogram
player_name = start_menu()
points = 0
health = 3
inventory = []

while health > 0:
    points, health = lunch_event(points, health, inventory)
    points = kitchen_event(points, inventory)
    show_status(points, health, inventory)

    cont = input("\nFortsätta spela? (j/n): ")
    if cont.lower() != "j":
        break

game_over(points)
