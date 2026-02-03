import pygame
import sys
import json
import os
from collections import deque

# ======================================================
# CONFIGURATION
# ======================================================
FPS = 60
FONT_SIZE = 18
SAVE_FILE = "savegame.json"
TYPE_SPEED = 40  # characters per second

BG_COLOR = (20, 20, 20)
TEXT_COLOR = (200, 200, 200)
WHITE = (240, 240, 240)
BLACK = (20, 20, 20)
GRAY = (120, 120, 120)
DARK = (40, 40, 40)

RESOLUTIONS = [(1280, 720), (1600, 900), (1920, 1080)]
DEFAULT_RES = (1920, 1080)
VIRTUAL_RES = (1920, 1080)

ANIM_SPEED = 10

# ======================================================
# INITIALISATION
# ======================================================
pygame.init()
os.environ["SDL_VIDEO_CENTERED"] = "1"

display_info = pygame.display.Info()
DESKTOP_RES = (display_info.current_w, display_info.current_h)

fullscreen = True
current_res_index = RESOLUTIONS.index(DEFAULT_RES)

screen = pygame.display.set_mode(DESKTOP_RES, pygame.NOFRAME)
pygame.display.set_caption("Undercooked Two")
clock = pygame.time.Clock()

ui_surface = pygame.Surface(VIRTUAL_RES)

font_ui = pygame.font.SysFont("timesnewroman", 32)
font_term = pygame.font.SysFont("consolas", FONT_SIZE)

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
mode = "main_menu"  # global to allow transition callback to change it

# ======================================================
# DISPLAY CONTROL
# ======================================================
def apply_display_mode():
    global screen, SCREEN_WIDTH, SCREEN_HEIGHT
    if fullscreen:
        screen = pygame.display.set_mode(DESKTOP_RES, pygame.NOFRAME)
    else:
        screen = pygame.display.set_mode(RESOLUTIONS[current_res_index])
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

def toggle_fullscreen():
    global fullscreen
    fullscreen = not fullscreen
    apply_display_mode()

def cycle_resolution():
    global current_res_index
    if fullscreen:
        return
    current_res_index = (current_res_index + 1) % len(RESOLUTIONS)
    apply_display_mode()

# ======================================================
# HELPERS
# ======================================================

class MenuButtons:
    def __init__(self, labels, start_pos, size=(300, 50), gap=20):
        self.labels = labels
        self.selected = 0
        self.rects = []
        self.start_x, self.start_y = start_pos
        self.w, self.h = size
        self.gap = gap
        self.rebuild()

    def rebuild(self):
        self.rects = []
        y = self.start_y
        for lbl in self.labels:
            r = pygame.Rect(self.start_x, y, self.w, self.h)
            self.rects.append((lbl, r))
            y += self.h + self.gap

    def handle_keyboard(self, event):
        if event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % len(self.labels)
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % len(self.labels)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return self.labels[self.selected]
        return None

    def handle_mouse(self, event):
        for lbl, r in self.rects:
            if button_clicked(r, event):
                return lbl
        return None

    def draw(self):
        mouse = screen_to_virtual(pygame.mouse.get_pos())
        for i, (lbl, r) in enumerate(self.rects):
            hovered = r.collidepoint(mouse)
            draw_button(ui_surface, lbl, r, selected=(i == self.selected or hovered))


def screen_to_virtual(pos):
    sx, sy = pos
    return int(sx * VIRTUAL_RES[0] / SCREEN_WIDTH), int(sy * VIRTUAL_RES[1] / SCREEN_HEIGHT)

def smooth(current, target, speed, dt):
    return current + (target - current) * speed * dt

def draw_button(surface, text, rect, selected=False):
    pygame.draw.rect(surface, GRAY if selected else WHITE, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    label = font_ui.render(text, True, BLACK)
    surface.blit(label, label.get_rect(center=rect.center))

def draw_health_bar(state):
    x, y = 40, 1040
    width, height = 300, 28

    # Background
    pygame.draw.rect(ui_surface, DARK, (x, y, width, height))
    pygame.draw.rect(ui_surface, WHITE, (x, y, width, height), 2)

    # Health fill
    hp_ratio = state.hp / state.max_hp
    fill_width = int((width - 4) * hp_ratio)
    pygame.draw.rect(
        ui_surface,
        (160, 40, 40),
        (x + 2, y + 2, fill_width, height - 4)
    )

    # Text
    label = font_term.render(f"HP {state.hp}/{state.max_hp}", True, WHITE)
    ui_surface.blit(label, (x + width + 15, y + 4))


def button_clicked(rect, event):
    if not rect or event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False
    return rect.collidepoint(screen_to_virtual(event.pos))

# ======================================================
# TRANSITION SYSTEM
# ======================================================
class Transition:
    def __init__(self):
        self.alpha = 0
        self.active = False
        self.direction = 1
        self.callback = None

    def start(self, callback=None):
        self.alpha = 0
        self.direction = 1
        self.active = True
        self.callback = callback

    def update(self, dt):
        if not self.active:
            return
        self.alpha += self.direction * 600 * dt
        if self.alpha >= 255:
            self.alpha = 255
            if self.callback:
                self.callback()
                self.callback = None
            self.direction = -1
        elif self.alpha <= 0:
            self.alpha = 0
            self.active = False

    def draw(self):
        if not self.active:
            return
        fade = pygame.Surface(VIRTUAL_RES)
        fade.fill((0, 0, 0))
        fade.set_alpha(int(self.alpha))
        ui_surface.blit(fade, (0, 0))

# ======================================================
# TERMINAL
# ======================================================
class Terminal:
    def __init__(self):
        self.lines = deque(maxlen=40)  # finished lines
        self.queue = deque()            # messages waiting to be typed
        self.current = ""               # current message being typed
        self.typed = ""                 # typed portion of current message
        self.timer = 0

    def add(self, text):
        self.queue.append(text)

    def update(self, dt):
        if not self.current and self.queue:
            self.current = self.queue.popleft()
            self.typed = ""
            self.timer = 0

        if self.current:
            self.timer += dt
            chars_to_type = int(self.timer * TYPE_SPEED)
            if chars_to_type > 0:
                self.timer -= chars_to_type / TYPE_SPEED
                for _ in range(chars_to_type):
                    if self.current:
                        self.typed += self.current[0]
                        self.current = self.current[1:]
                    else:
                        break
                # When finished typing this line, move it to finished lines
                if not self.current:
                    self.lines.append(self.typed)
                    self.typed = ""

    def draw(self):
        y = 10
        # draw finished lines
        for line in self.lines:
            ui_surface.blit(font_term.render(line, True, TEXT_COLOR), (10, y))
            y += FONT_SIZE + 2
        # draw current line being typed
        if self.current or self.typed:
            ui_surface.blit(font_term.render(self.typed, True, TEXT_COLOR), (10, y))


# ======================================================
# GAME STATE
# ======================================================
class GameState:
    def __init__(self):
        self.max_hp = 100
        self.hp = self.max_hp
        self.inventory = ["Torch"]
        self.quests = [{"text": "Placeholder objective.", "state": "Active"}]

    def damage(self, amount):
        self.hp = max(0, self.hp - amount)
        return self.hp == 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def save(self):
        with open(SAVE_FILE, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    def load(self):
        if not os.path.exists(SAVE_FILE):
            return False
        with open(SAVE_FILE) as f:
            self.__dict__.update(json.load(f))
        # Safety clamp after load
        self.hp = max(0, min(self.hp, self.max_hp))
        return True


# ======================================================
# INVENTORY PANEL
# ======================================================
class InventoryPanel:
    def __init__(self, state):
        self.state = state
        self.visible = False

    def toggle(self):
        self.visible = not self.visible

    def draw(self):
        if not self.visible:
            return
        panel = pygame.Rect(300, 120, 600, 600)
        pygame.draw.rect(ui_surface, DARK, panel)
        pygame.draw.rect(ui_surface, WHITE, panel, 2)

        y = panel.y + 20
        ui_surface.blit(font_ui.render("Inventory", True, WHITE), (panel.x + 20, y))
        y += 40
        for item in self.state.inventory:
            ui_surface.blit(font_term.render(f"- {item}", True, TEXT_COLOR), (panel.x + 30, y))
            y += 22
        y += 30
        ui_surface.blit(font_ui.render("Objective", True, WHITE), (panel.x + 20, y))
        y += 40
        for q in self.state.quests:
            ui_surface.blit(font_term.render(q["text"], True, TEXT_COLOR), (panel.x + 30, y))

# ======================================================
# ACTION BUTTONS
# ======================================================
class ActionButtons:
    def __init__(self, terminal):
        self.labels = ["Search", "Move", "Wait", "Fight"]
        self.selected = 0
        self.rects = []
        self.terminal = terminal
        self.last_action = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.selected = (self.selected - 1) % len(self.labels)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.selected = (self.selected + 1) % len(self.labels)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.last_action = self.labels[self.selected]
                self.terminal.add(f"> {self.last_action}")


        for lbl, r in self.rects:
            if button_clicked(r, event):
                self.last_action = lbl
                self.terminal.add(f"> {lbl}")


    def draw(self):
        self.rects = []
        x, y = 40, VIRTUAL_RES[1] - 260
        for i, lbl in enumerate(self.labels):
            r = pygame.Rect(x, y, 200, 45)
            draw_button(ui_surface, lbl, r, i == self.selected)
            self.rects.append((lbl, r))
            y += 55

# ======================================================
# MENUS
# ======================================================
class MainMenu:
    def __init__(self):
        self.options = ["New Game", "Load Game", "Editor", "Options", "Quit"]
        self.selected = 0
        self.rects = []

    def draw(self):
        self.rects = []
        for i, opt in enumerate(self.options):
            r = pygame.Rect(VIRTUAL_RES[0]//2 - 150, 260 + i*70, 300, 50)
            draw_button(ui_surface, opt, r, i == self.selected)
            self.rects.append((opt, r))

class OptionsMenu:
    def __init__(self):
        self.rects = {}

    def draw(self):
        title = font_ui.render("Options", True, WHITE)
        ui_surface.blit(title, title.get_rect(center=(VIRTUAL_RES[0]//2, 120)))

        fs_text = f"Borderless Fullscreen: {'ON' if fullscreen else 'OFF'}"
        res_text = f"Resolution: {RESOLUTIONS[current_res_index][0]}x{RESOLUTIONS[current_res_index][1]}"

        self.rects["fs"] = pygame.Rect(VIRTUAL_RES[0]//2 - 200, 240, 400, 50)
        self.rects["res"] = pygame.Rect(VIRTUAL_RES[0]//2 - 200, 310, 400, 50)
        self.rects["back"] = pygame.Rect(VIRTUAL_RES[0]//2 - 200, 400, 400, 50)

        draw_button(ui_surface, fs_text, self.rects["fs"])
        draw_button(ui_surface, res_text, self.rects["res"])
        draw_button(ui_surface, "Back", self.rects["back"])

class PauseMenu:
    def __init__(self):
        self.active = False
        self.anim = 0
        self.buttons = MenuButtons(
            ["Resume", "Save Game", "Quit to Menu"],
            (VIRTUAL_RES[0]//2 - 150, VIRTUAL_RES[1]//2 - 80),
            size=(300, 45),
            gap=20
        )
        self.rects = []

    def update(self, dt):
        target = 1 if self.active else 0
        self.anim = smooth(self.anim, target, ANIM_SPEED, dt)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            return self.buttons.handle_keyboard(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self.buttons.handle_mouse(event)
        return None

    def draw(self):
        if self.anim < 0.01:
            return

        overlay = pygame.Surface(VIRTUAL_RES)
        overlay.set_alpha(int(180 * self.anim))
        overlay.fill((0, 0, 0))
        ui_surface.blit(overlay, (0, 0))

        self.buttons.draw()



class Editor:
    def __init__(self):
        self.active = True
        self.buttons = {}
        self.labels = ["Quit to Menu", "New Story", "Save Story", "Load Story"]
        self.selected = 0  # for keyboard navigation
        self._build_buttons()

    def _build_buttons(self):
        x, y = 20, 20
        w, h = 220, 40
        gap = 10

        self.buttons = {}
        for text in self.labels:
            self.buttons[text] = pygame.Rect(x, y, w, h)
            y += h + gap

    def handle_event(self, event, terminal, set_mode_fn):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.selected = (self.selected - 1) % len(self.labels)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.selected = (self.selected + 1) % len(self.labels)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.activate_button(self.labels[self.selected], terminal, set_mode_fn)

        if event.type == pygame.MOUSEBUTTONDOWN:
            for text, rect in self.buttons.items():
                if button_clicked(rect, event):
                    self.activate_button(text, terminal, set_mode_fn)

    def activate_button(self, label, terminal, set_mode_fn):
        if label == "Quit to Menu":
            set_mode_fn("main_menu")
        else:
            terminal.add(f">> {label} placeholder.")

    def draw_workspace(self):
        if not self.active:
            return

        # Draw buttons, highlight if selected or hovered
        mouse_pos = pygame.mouse.get_pos()
        for i, text in enumerate(self.labels):
            rect = self.buttons[text]
            virtual_mouse = screen_to_virtual(mouse_pos)
            hovered = rect.collidepoint(virtual_mouse)
            draw_button(ui_surface, text, rect, selected=(i == self.selected or hovered))

        # Draw workspace title
        title = font_ui.render("Narrative Editor", True, WHITE)
        ui_surface.blit(title, (300, 120))

        hint = font_term.render(
            "Story workspace active. Creation systems pending.",
            True,
            TEXT_COLOR
        )
        ui_surface.blit(hint, (300, 180))


class GameOverMenu:
    def __init__(self):
        self.options = ["Load Game", "Quit to Menu"]
        self.selected = 0
        self.rects = []

    def draw(self):
        self.rects = []
        y = VIRTUAL_RES[1] // 2 + 80  # mid-low screen
        for i, opt in enumerate(self.options):
            r = pygame.Rect(VIRTUAL_RES[0]//2 - 150, y + i*70, 300, 50)
            draw_button(ui_surface, opt, r, i == self.selected)
            self.rects.append((opt, r))


def handle_game_over_choice(choice, state, terminal, transition):
    global mode
    if choice == "Load Game":
        if state.load():
            terminal.lines.clear()
            terminal.queue.clear()
            terminal.add(">> Restoration complete.")
            mode = "game"
        else:
            terminal.add(">> No save found.")
    elif choice == "Quit to Menu":
        transition.start(lambda: set_mode("main_menu"))


# ======================================================
# MAIN LOOP
# ======================================================
def main():
    global mode
    editor = Editor()
    terminal = Terminal()
    state = GameState()
    inventory = InventoryPanel(state)
    actions = ActionButtons(terminal)
    transition = Transition()
    pause_menu = PauseMenu()
    main_menu = MainMenu()
    options_menu = OptionsMenu()
    game_over_menu = GameOverMenu()


    terminal.add("Awaiting...")

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        ui_surface.fill(BG_COLOR)

        terminal.update(dt)
        transition.update(dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if transition.active:
                continue

            # --- MAIN MENU ---
            if mode == "main_menu":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        main_menu.selected = (main_menu.selected - 1) % 4
                    elif event.key == pygame.K_DOWN:
                        main_menu.selected = (main_menu.selected + 1) % 4
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        choice = main_menu.options[main_menu.selected]
                        if choice == "New Game" and mode != "game":
                            def start_new_game():
                                nonlocal state, inventory, terminal
                                state = GameState()
                                inventory.state = state
                                terminal.lines.clear()
                                terminal.queue.clear()
                                terminal.add(">> New operational instance initialised.")
                                set_mode("game")

                            transition.start(start_new_game)
                        elif choice == "Load Game":
                            if state.load():
                                # Refresh terminal and inventory to match loaded state
                                inventory.state = state
                                terminal.add("Save loaded.")
                                transition.start(lambda: set_mode("game"))
                            else:
                                terminal.add("No save found.")
                        elif choice == "Options" and mode != "options":
                            transition.start(lambda: set_mode("options"))
                        elif choice == "Quit":
                            running = False

                for text, r in main_menu.rects:
                    if button_clicked(r, event):
                        if text == "New Game" and mode != "game":
                            def start_new_game():
                                nonlocal state, inventory, terminal
                                state = GameState()
                                inventory.state = state
                                terminal.lines.clear()
                                terminal.queue.clear()
                                terminal.add(">> New operational instance initialised.")
                                set_mode("game")

                            transition.start(start_new_game)
                        elif text == "Load Game":
                            if state.load():
                                inventory.state = state
                                terminal.add("Save loaded.")
                                transition.start(lambda: set_mode("game"))
                            else:
                                terminal.add("No save found.")
                        elif text == "Editor" and mode != "editor":
                            transition.start(lambda: set_mode("editor"))
                        elif text == "Options" and mode != "options":
                            transition.start(lambda: set_mode("options"))
                        elif text == "Quit":
                            running = False

            elif mode == "editor":
                editor.handle_event(event, terminal, set_mode)



            # --- OPTIONS MENU ---
            elif mode == "options":
                if button_clicked(options_menu.rects.get("fs"), event):
                    toggle_fullscreen()
                elif button_clicked(options_menu.rects.get("res"), event):
                    cycle_resolution()
                elif button_clicked(options_menu.rects.get("back"), event):
                    if mode != "main_menu":
                        transition.start(lambda: set_mode("main_menu"))

            # --- GAME MODE ---
            elif mode == "game":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        inventory.toggle()
                    elif event.key == pygame.K_ESCAPE:
                        pause_menu.active = not pause_menu.active

                if pause_menu.active:
                    choice = pause_menu.handle_event(event)
                    if choice:
                        handle_pause_choice(choice, state, terminal, transition)
                elif not inventory.visible:
                    actions.handle_event(event)


                if actions.last_action == "Fight":
                    actions.last_action = None  # consume action
                    if state.damage(0):
                        terminal.add(">> SYSTEM FAILURE: Vital signs terminated.")
                        terminal.add("Load last saved game?")
                        mode = "game_over"




                # Gameplay input ONLY when not pause_menu.active
                elif not inventory.visible:
                    actions.handle_event(event)

            # --- GAME OVER ---
            elif mode == "game_over":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_w, pygame.K_UP):
                        game_over_menu.selected = (game_over_menu.selected - 1) % len(game_over_menu.options)
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        game_over_menu.selected = (game_over_menu.selected + 1) % len(game_over_menu.options)
    
                        handle_game_over_choice(choice, state, terminal, transition)

                for text, r in game_over_menu.rects:
                    if button_clicked(r, event):
                        handle_game_over_choice(text, state, terminal, transition)

        # ======================================================


        # DRAW
        if mode == "main_menu":
            main_menu.draw()
        elif mode == "options":
            options_menu.draw()
        elif mode == "game":
            draw_health_bar(state)
            terminal.draw()
            actions.draw()
            inventory.draw()
            pause_menu.update(dt)
            pause_menu.draw()
        elif mode == "editor":
            editor.draw_workspace()
        elif mode == "game_over":
            terminal.draw()
            game_over_menu.draw()


        transition.draw()

        scaled = pygame.transform.smoothscale(ui_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

def handle_pause_choice(choice, state, terminal, transition):
    global mode
    if choice == "Resume":
        # handled by pause_menu.active toggle
        pass
    elif choice == "Save Game":
        state.save()
        terminal.add("[Game saved]")
    elif choice == "Quit to Menu":
        transition.start(lambda: set_mode("main_menu"))




def set_mode(m):
    global mode
    mode = m




if __name__ == "__main__":
    main()

