import pygame
import sys

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Undercooked Two - This smell like poo")

# Colors
WHITE = (240, 240, 240)
BLACK = (20, 20, 20)
GRAY = (100, 100, 100)

# Font
font = pygame.font.SysFont("timesnewroman", 32)

# Button helper
def draw_button(text, x, y, w, h):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, GRAY if rect.collidepoint(mouse) else WHITE, rect)

    label = font.render(text, True, BLACK)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

    if rect.collidepoint(mouse) and click[0]:
        pygame.time.delay(200)
        return True
    return False

# Main loop
running = True
while running:
    screen.fill(BLACK)

    title = font.render("Undercooked Two - This smell like poo", True, WHITE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))

    if draw_button("Start Game", 120, 100, 160, 40):
        print("The campaign begins.")

    if draw_button("Options", 120, 150, 160, 40):
        print("Options invoked.")

    if draw_button("Quit", 120, 200, 160, 40):
        pygame.quit()
        sys.exit()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.flip()
