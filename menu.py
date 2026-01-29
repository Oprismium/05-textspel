import pygame
import sys

pygame.init()

# Screen
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Undercooked Two - This smell like poo")

# Colors
WHITE = (240, 240, 240)
BLACK = (20, 20, 20)
GRAY = (120, 120, 120)

# Font
font = pygame.font.SysFont("timesnewroman", 32)

# Menu state
menu = "main"
fullscreen = False


def toggle_fullscreen():
    global screen, fullscreen
    fullscreen = not fullscreen

    if fullscreen:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))


# Button helper
def draw_button(text, y, w=220, h=40):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    rect = pygame.Rect(WIDTH//2 - w//2, y, w, h)
    pygame.draw.rect(screen, GRAY if rect.collidepoint(mouse) else WHITE, rect)

    label = font.render(text, True, BLACK)
    screen.blit(label, label.get_rect(center=rect.center))

    if rect.collidepoint(mouse) and click[0]:
        pygame.time.delay(200)
        return True
    return False

terminal = None
SAVE_FILE = "savegame.json"
action = None
os = __import__('os') #jag när jag vill interagera med filerna
game = None
import json
def main_menu():
    global menu

    title = font.render("Undercooked Two - This smell like poo", True, WHITE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

    if draw_button("New Game", 120):
        print("The campaign begins.")

    if draw_button("Load Game", 170):
        print("Loading data...")
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                game.inventory = data.get('inventory', [])
                game.quests = data.get('quests', [])
        else:
            terminal.add_line("[No save file found.]")

    if draw_button("Options", 220):
        menu = "options"

    if draw_button("Quit", 270):
        pygame.quit()
        sys.exit()


def options_menu():
    global menu

    title = font.render("Options", True, WHITE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

    fs_text = "Fullscreen: ON" if fullscreen else "Fullscreen: OFF"
    if draw_button(fs_text, 150):
        toggle_fullscreen()

    if draw_button("Back", 260):
        menu = "main"


# Main loop
running = True
while running:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if menu == "main":
        main_menu()
    elif menu == "options":
        options_menu()

    pygame.display.flip()
