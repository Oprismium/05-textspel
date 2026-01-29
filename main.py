import pygame
import sys
import json
import os
from collections import deque

# ======================================================
# CONFIGURATION
# ======================================================
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

FONT_SIZE = 18
MAX_LINES = 20
SAVE_FILE = "savegame.json"

BG_COLOR = (20, 20, 20)
TEXT_COLOR = (200, 200, 200)
INPUT_COLOR = (180, 180, 255)

ANIM_SPEED = 14  # animation speed for overlays

# ======================================================
# START MENU
# ======================================================

pygame.init()

# Screen
os.environ['SDL_VIDEO_CENTERED'] = '1'
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
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
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
    else:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Button helper
def draw_button(text, y, w=220, h=40):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    rect = pygame.Rect(SCREEN_WIDTH//2 - w//2, y, w, h)
    pygame.draw.rect(screen, GRAY if rect.collidepoint(mouse) else WHITE, rect)

    label = font.render(text, True, BLACK)
    screen.blit(label, label.get_rect(center=rect.center))

    if rect.collidepoint(mouse) and click[0]:
        pygame.time.delay(200)
        return True
    return False

def main_menu():
    global menu

if draw_button("New Game", 120):
    print("The campaign begins.")

if draw_button("Load Game", 170):
    print("Loading data...")

if draw_button("Options", 220):
    menu = "options"

if draw_button("Quit", 270):
    pygame.quit()
    sys.exit()

def options_menu():
    global menu
    title = font.render("Options", True, WHITE)
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 50)))

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

# ======================================================
# TEXT UTILITIES
# ======================================================
def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        test = current + word + " "
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current.strip())
            current = word + " "
    if current:
        lines.append(current.strip())
    return lines

# ======================================================
# FLOATING TEXT (for "+1" notifications)
# ======================================================
class FloatingText:
    def __init__(self, text, font, pos, color=TEXT_COLOR, duration=0.8):
        self.text = text
        self.font = font
        self.color = color
        self.start_x, self.start_y = pos
        self.y_offset = 0
        self.duration = duration
        self.time = 0
        self.alpha = 255

    def update(self, dt):
        self.time += dt
        progress = min(1, self.time / self.duration)
        self.y_offset = -30 * progress
        self.alpha = int(255 * (1 - progress))

    def draw(self, surface):
        txt = self.font.render(self.text, True, self.color)
        txt.set_alpha(self.alpha)
        surface.blit(txt, (self.start_x, self.start_y + self.y_offset))
        return self.time >= self.duration  # finished?

# ======================================================
# TERMINAL
# ======================================================
class Terminal:
    def __init__(self, font):
        self.font = font
        self.lines = deque(maxlen=MAX_LINES)

    def add_line(self, text):
        self.lines.append(text)

    def draw(self, surface):
        y = 10
        for line in self.lines:
            surface.blit(self.font.render(line, True, TEXT_COLOR), (10, y))
            y += FONT_SIZE + 2

# ======================================================
# BUTTON
# ======================================================
class Button:
    def __init__(self, text, font):
        self.text = text
        self.font = font
        self.rect = None

    def draw(self, surface, rect, selected=False):
        self.rect = rect
        color = (170, 170, 170) if selected else (110, 110, 110)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (220, 220, 220), rect, 2)
        txt = self.font.render(self.text, True, (10, 10, 10))
        surface.blit(txt, txt.get_rect(center=rect.center))

    def check_click(self, pos):
        if self.rect and self.rect.collidepoint(pos):
            return True
        return False

# ======================================================
# PAUSE MENU
# ======================================================
class PauseMenu:
    def __init__(self, font):
        self.font = font
        self.buttons = ["Resume", "Save", "Load", "Quit"]
        self.selected = 0
        self.anim = 0.0
        self.button_rects = []

    def reset(self):
        self.anim = 0.0

    def update(self, active, dt):
        target = 1.0 if active else 0.0
        self.anim += (target - self.anim) * dt * ANIM_SPEED

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.buttons)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.buttons)
            elif event.key == pygame.K_RETURN:
                return self.buttons[self.selected]
        return None

    def draw(self, surface):
        self.button_rects = []
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(int(180 * self.anim))
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        w, h = 300, 260
        x = SCREEN_WIDTH // 2 - w // 2
        y = (-h) + (SCREEN_HEIGHT // 2 - h // 2 + h) * self.anim

        panel = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (40, 40, 40), panel)
        pygame.draw.rect(surface, (200, 200, 200), panel, 2)

        for i, label in enumerate(self.buttons):
            r = pygame.Rect(x + 40, y + 40 + i * 50, w - 80, 40)
            Button(label, self.font).draw(surface, r, i == self.selected)
            self.button_rects.append(r)

# ======================================================
# TAB OVERLAY
# ======================================================
class TabOverlay:
    def __init__(self, font):
        self.font = font
        self.visible = False
        self.anim = 0.0
        self.scroll = 0
        self.width = 880
        self.height = 420
        self.x = 200
        self.y = 150

    def toggle(self):
        self.visible = not self.visible

    def update(self, active, dt):
        target = 1.0 if active else 0.0
        self.anim += (target - self.anim) * dt * ANIM_SPEED

    def handle_event(self, event, max_scroll):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.scroll - event.y, max_scroll))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll = max(0, self.scroll - 1)
            elif event.key == pygame.K_DOWN:
                self.scroll = min(max_scroll, self.scroll + 1)

    def draw(self, surface, game):
        if self.anim < 0.01:
            return 0

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(int(160 * self.anim))
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, (35, 35, 35), panel)
        pygame.draw.rect(surface, (200, 200, 200), panel, 2)

        # Inventory
        surface.blit(self.font.render("Inventory", True, TEXT_COLOR), (self.x + 20, self.y + 20))
        for i, item in enumerate(game.inventory):
            surface.blit(self.font.render(f"- {item}", True, TEXT_COLOR), (self.x + 20, self.y + 50 + i * 22))

        # Objectives
        surface.blit(self.font.render("Objectives", True, TEXT_COLOR), (self.x + 360, self.y + 20))

        y = self.y + 50
        visible = 7
        quests = game.quests[self.scroll:self.scroll + visible]
        max_scroll = max(0, len(game.quests) - visible)

        for q in quests:
            color = TEXT_COLOR if q["state"] != "Failed" else (130, 130, 130)
            lines = wrap_text(q["text"], self.font, 360)
            for line in lines:
                txt = self.font.render(line, True, color)
                surface.blit(txt, (self.x + 360, y))
                if q["state"] == "Completed":
                    pygame.draw.line(surface, color,
                                     (self.x + 360, y + FONT_SIZE // 2),
                                     (self.x + 360 + txt.get_width(), y + FONT_SIZE // 2), 2)
                y += 22
            y += 8

        return max_scroll

# ======================================================
# GAME
# ======================================================
class Game:
    def __init__(self, terminal, font):
        self.terminal = terminal
        self.font = font
        self.turn = 0
        self.location = "chamber"
        self.inventory = ["Torch", "Old Key"]
        self.quests = [
            {"text": "Placeholder mission 1.", "state": "Active"},
            {"text": "Placeholder mission 2.", "state": "Active"},
        ]

        self.menu_options = ["Look", "Wait"]
        self.menu_selected = 0

        # Items in the environment
        self.nearby_items = ["Herb", "Stone Key"]
        self.pickup_prompt = None  # {"item": str, "options": ["Yes","No"], "selected":0}

    def update(self):
        pass  # Placeholder if needed

    def draw_menu(self, surface):
        x = 10
        y = SCREEN_HEIGHT - 150
        self.menu_rects = []
        for i, option in enumerate(self.menu_options):
            rect = pygame.Rect(x, y + i*40, 200, 35)
            color = (170, 170, 170) if i == self.menu_selected else (110, 110, 110)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (220, 220, 220), rect, 2)
            txt = self.font.render(option, True, (10, 10, 10))
            surface.blit(txt, txt.get_rect(center=rect.center))
            self.menu_rects.append(rect)

    def handle_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                self.activate_menu(self.menu_selected)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for i, rect in enumerate(self.menu_rects):
                if rect.collidepoint(event.pos):
                    self.activate_menu(i)

    def activate_menu(self, index):
        action = self.menu_options[index]
        if self.pickup_prompt:
            return  # Ignore main menu if pickup active

        if action == "Look":
            self.terminal.add_line("You look around.")
            if self.nearby_items:
                item = self.nearby_items.pop(0)
                self.pickup_prompt = {"item": item, "options":["Yes","No"], "selected":0}
        elif action == "Wait":
            self.terminal.add_line("You wait.")

    def draw_pickup_prompt(self, surface):
        if not self.pickup_prompt:
            return
        prompt = self.pickup_prompt
        w, h = 400, 120
        x = SCREEN_WIDTH//2 - w//2
        y = SCREEN_HEIGHT//2 - h//2
        panel = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (50,50,50), panel)
        pygame.draw.rect(surface, (200,200,200), panel, 2)

        text = f"Pick up '{prompt['item']}'?"
        surface.blit(self.font.render(text, True, TEXT_COLOR), (x+20, y+20))

        # Options
        for i, opt in enumerate(prompt["options"]):
            rect = pygame.Rect(x+50 + i*120, y+60, 80, 35)
            color = (170,170,170) if i==prompt["selected"] else (110,110,110)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (220,220,220), rect, 2)
            surface.blit(self.font.render(opt, True, (10,10,10)), rect.center)
            prompt[f"rect_{i}"] = rect

    def handle_pickup_event(self, event, floating_texts):
        if not self.pickup_prompt:
            return
        prompt = self.pickup_prompt
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                prompt["selected"] = (prompt["selected"] -1) % len(prompt["options"])
            elif event.key == pygame.K_RIGHT:
                prompt["selected"] = (prompt["selected"] +1) % len(prompt["options"])
            elif event.key == pygame.K_RETURN:
                self.resolve_pickup(prompt["selected"], floating_texts)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for i, opt in enumerate(prompt["options"]):
                if prompt[f"rect_{i}"].collidepoint(event.pos):
                    self.resolve_pickup(i, floating_texts)

    def resolve_pickup(self, selected, floating_texts):
        prompt = self.pickup_prompt
        if prompt["options"][selected] == "Yes":
            self.inventory.append(prompt["item"])
            floating_texts.append(FloatingText(f"{prompt['item']} +1", self.font, (10, SCREEN_HEIGHT-50)))
            self.terminal.add_line(f"You picked up {prompt['item']}.")
        else:
            self.terminal.add_line(f"You leave {prompt['item']} behind.")
        self.pickup_prompt = None

# ======================================================
# MAIN LOOP
# ======================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Undercooked Two - This smell like poo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", FONT_SIZE)

    terminal = Terminal(font)
    game = Game(terminal, font)
    pause_menu = PauseMenu(font)
    tab_overlay = TabOverlay(font)
    floating_texts = []

    paused = False
    running = True

    while running:
        dt = clock.tick(FPS)/1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ESC pause
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                paused = not paused
                if paused:
                    pause_menu.reset()

            # TAB overlay
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                tab_overlay.toggle()

            if paused:
                action = pause_menu.handle_event(event)
                if action == "Resume":
                    paused = False
                elif action == "Save":
                    with open(SAVE_FILE,"w") as f:
                        json.dump({
                            "inventory": game.inventory,
                            "quests": game.quests
                        }, f, indent=2)
                    terminal.add_line("[Game state saved.]")
                elif action == "Load":
                    if os.path.exists(SAVE_FILE):
                        with open(SAVE_FILE,"r") as f:
                            data = json.load(f)
                            game.inventory = data.get("inventory", [])
                            game.quests = data.get("quests", [])
                    else:
                        terminal.add_line("[No save file found.]")
                elif action == "Quit":
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, rect in enumerate(pause_menu.button_rects):
                        if rect.collidepoint(event.pos):
                            action = pause_menu.buttons[i]
                            if action == "Resume": paused=False
                            elif action == "Quit": pygame.quit(); sys.exit()

            elif game.pickup_prompt:
                game.handle_pickup_event(event, floating_texts)
            else:
                game.handle_menu_event(event)

        # draw
        screen.fill(BG_COLOR)
        terminal.draw(screen)
        game.draw_menu(screen)
        game.draw_pickup_prompt(screen)
        tab_overlay.update(tab_overlay.visible, dt)
        tab_overlay.draw(screen, game)
        pause_menu.update(paused, dt)
        if paused: pause_menu.draw(screen)

        # floating texts
        for ft in floating_texts[:]:
            ft.update(dt)
            if ft.draw(screen):
                floating_texts.remove(ft)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
