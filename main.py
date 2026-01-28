import pygame
import sys
import json
import os
from collections import deque

# ======================================================
# CONFIGURATION
# ======================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

FONT_SIZE = 18
MAX_LINES = 20
SAVE_FILE = "savegame.json"

BG_COLOR = (20, 20, 20)
TEXT_COLOR = (200, 200, 200)
INPUT_COLOR = (180, 180, 255)

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
# TERMINAL
# ======================================================
class Terminal:
    def __init__(self, font):
        self.font = font
        self.lines = deque(maxlen=MAX_LINES)
        self.input_text = ""

    def add_line(self, text):
        self.lines.append(text)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                cmd = self.input_text.strip()
                self.input_text = ""
                return cmd
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.unicode.isprintable():
                self.input_text += event.unicode
        return None

    def draw(self, surface):
        y = 10
        for line in self.lines:
            surface.blit(self.font.render(line, True, TEXT_COLOR), (10, y))
            y += FONT_SIZE + 2
        surface.blit(
            self.font.render("> " + self.input_text, True, INPUT_COLOR),
            (10, SCREEN_HEIGHT - FONT_SIZE - 10)
        )

# ======================================================
# GAME LOGIC
# ======================================================
class Game:
    def __init__(self, terminal):
        self.terminal = terminal
        self.turn = 0
        self.location = "chamber"

        self.inventory = ["Torch", "Old Key"]

        self.quests = [
            {"text": "Gather ingredients for the alchemical rite.", "state": "Active"},
            {"text": "Locate the sealed archivum door hidden in the stone.", "state": "Active"},
            {"text": "Ensure the torch does not extinguish.", "state": "Failed"},
            {"text": "Survive the chamber.", "state": "Completed"},
        ]

        terminal.add_line("You awaken within a silent stone chamber.")
        terminal.add_line("TAB: Inventory & Objectives | ESC: Command Menu")

    def process_command(self, command):
        self.turn += 1
        self.terminal.add_line(f"> {command}")

        if command == "look":
            self.terminal.add_line("Cold stone. Lingering purpose.")
            for q in self.quests:
                if q["state"] == "Active":
                    q["state"] = "Completed"
                    self.terminal.add_line("An objective has been completed.")
                    break
        elif command == "wait":
            self.terminal.add_line("Time passes.")
        else:
            self.terminal.add_line("Nothing happens.")

    def serialize(self):
        return {
            "turn": self.turn,
            "location": self.location,
            "inventory": self.inventory,
            "quests": self.quests,
            "terminal": list(self.terminal.lines),
        }

    def deserialize(self, data):
        self.turn = data["turn"]
        self.location = data["location"]
        self.inventory = data["inventory"]
        self.quests = data["quests"]
        self.terminal.lines.clear()
        for line in data["terminal"]:
            self.terminal.lines.append(line)
        self.terminal.add_line("[Game state restored.]")

# ======================================================
# BUTTON
# ======================================================
class Button:
    def __init__(self, text, font):
        self.text = text
        self.font = font

    def draw(self, surface, rect, selected):
        color = (170, 170, 170) if selected else (110, 110, 110)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (220, 220, 220), rect, 2)
        txt = self.font.render(self.text, True, (10, 10, 10))
        surface.blit(txt, txt.get_rect(center=rect.center))

# ======================================================
# PAUSE MENU
# ======================================================
class PauseMenu:
    def __init__(self, font):
        self.font = font
        self.buttons = ["Resume", "Save", "Load", "Quit"]
        self.selected = 0
        self.anim = 0.0

    def reset(self):
        self.anim = 0.0

    def update(self, active, dt):
        target = 1.0 if active else 0.0
        self.anim += (target - self.anim) * dt * 14

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
        self.anim += (target - self.anim) * dt * 14

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
                    pygame.draw.line(
                        surface, color,
                        (self.x + 360, y + FONT_SIZE // 2),
                        (self.x + 360 + txt.get_width(), y + FONT_SIZE // 2),
                        2
                    )
                y += 22
            y += 8

        return max_scroll

# ======================================================
# MAIN LOOP
# ======================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Undercooked Two")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", FONT_SIZE)

    terminal = Terminal(font)
    game = Game(terminal)
    pause_menu = PauseMenu(font)
    tab_overlay = TabOverlay(font)

    paused = False
    running = True

    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                    if paused:
                        pause_menu.reset()

                elif event.key == pygame.K_TAB and not paused:
                    tab_overlay.toggle()

            if paused:
                action = pause_menu.handle_event(event)
                if action == "Resume":
                    paused = False
                elif action == "Save":
                    with open(SAVE_FILE, "w") as f:
                        json.dump(game.serialize(), f, indent=2)
                    terminal.add_line("[Game state saved.]")
                elif action == "Load":
                    if os.path.exists(SAVE_FILE):
                        with open(SAVE_FILE, "r") as f:
                            game.deserialize(json.load(f))
                    else:
                        terminal.add_line("[No save file found.]")
                elif action == "Quit":
                    pygame.quit()
                    sys.exit()

            elif tab_overlay.visible:
                max_scroll = tab_overlay.draw(screen, game)
                tab_overlay.handle_event(event, max_scroll)

            else:
                cmd = terminal.handle_event(event)
                if cmd:
                    game.process_command(cmd)

        screen.fill(BG_COLOR)
        terminal.draw(screen)

        pause_menu.update(paused, dt)
        tab_overlay.update(tab_overlay.visible, dt)

        if tab_overlay.visible:
            tab_overlay.draw(screen, game)
        if paused:
            pause_menu.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
