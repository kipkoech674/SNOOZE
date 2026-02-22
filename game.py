import os
import random
import threading
import pygame

# Optional Windows-only beep fallback for sound effects
try:
    import winsound  # type: ignore
except ImportError:
    winsound = None


# ---------------------------
# Configuration
# ---------------------------
WINDOW_SIZE = 600
GRID_COUNT = 20
CELL_SIZE = WINDOW_SIZE // GRID_COUNT

INITIAL_FPS = 10
MAX_FPS = 18

HIGH_SCORE_FILE = "high_score.txt"

# Colors
BG_COLOR = (18, 18, 18)
GRID_COLOR = (32, 32, 32)
SNAKE_HEAD_COLOR = (0, 200, 0)
SNAKE_BODY_COLOR = (0, 155, 0)
FOOD_COLOR = (220, 40, 40)
TEXT_COLOR = (240, 240, 240)
ACCENT_COLOR = (255, 200, 70)


class SoundManager:
    """Plays simple sound effects (non-blocking) if available."""

    def __init__(self):
        self.enabled = winsound is not None

    @staticmethod
    def _beep(freq: int, duration: int):
        try:
            winsound.Beep(freq, duration)
        except Exception:
            pass

    def play_eat(self):
        if self.enabled:
            threading.Thread(target=self._beep, args=(900, 70), daemon=True).start()

    def play_game_over(self):
        if self.enabled:

            def sequence():
                self._beep(500, 120)
                self._beep(350, 180)

            threading.Thread(target=sequence, daemon=True).start()


class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake Game")
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        self.clock = pygame.time.Clock()

        self.font_small = pygame.font.SysFont("consolas", 24)
        self.font_large = pygame.font.SysFont("consolas", 48, bold=True)

        self.sound = SoundManager()
        self.high_score = self.load_high_score()

        self.state = "START"  # START, PLAYING, GAME_OVER
        self.running = True

        self.reset_game()

    def load_high_score(self) -> int:
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as f:
                    return int(f.read().strip() or 0)
            except (ValueError, OSError):
                return 0
        return 0

    def save_high_score(self):
        try:
            with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as f:
                f.write(str(self.high_score))
        except OSError:
            pass

    def reset_game(self):
        center = GRID_COUNT // 2
        self.snake = [(center, center), (center - 1, center), (center - 2, center)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = self.spawn_food()
        self.score = 0
        self.fps = INITIAL_FPS

    def spawn_food(self):
        # Pick a random empty cell not occupied by the snake.
        empty_cells = [
            (x, y)
            for x in range(GRID_COUNT)
            for y in range(GRID_COUNT)
            if (x, y) not in self.snake
        ]
        return random.choice(empty_cells) if empty_cells else None

    @staticmethod
    def is_opposite(d1, d2):
        return d1[0] == -d2[0] and d1[1] == -d2[1]

    def handle_key_playing(self, key):
        key_to_dir = {
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
        }
        if key in key_to_dir:
            candidate = key_to_dir[key]
            if not self.is_opposite(candidate, self.direction):
                self.next_direction = candidate

    def update(self):
        self.direction = self.next_direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        # Wall collision
        if not (0 <= new_head[0] < GRID_COUNT and 0 <= new_head[1] < GRID_COUNT):
            self.to_game_over()
            return

        eating = new_head == self.food

        # Self collision
        # If not eating, tail moves away this frame, so ignore current tail cell in collision check.
        body_to_check = self.snake if eating else self.snake[:-1]
        if new_head in body_to_check:
            self.to_game_over()
            return

        # Move snake
        self.snake.insert(0, new_head)

        if eating:
            self.score += 1
            self.food = self.spawn_food()
            self.sound.play_eat()
            self.fps = min(MAX_FPS, INITIAL_FPS + self.score // 3)
        else:
            self.snake.pop()

    def to_game_over(self):
        self.state = "GAME_OVER"
        self.sound.play_game_over()
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def draw_grid(self):
        for x in range(0, WINDOW_SIZE, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, WINDOW_SIZE))
        for y in range(0, WINDOW_SIZE, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WINDOW_SIZE, y))

    def draw_snake(self):
        for i, (x, y) in enumerate(self.snake):
            color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_BODY_COLOR
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BG_COLOR, rect, 1)

    def draw_food(self):
        if self.food is None:
            return
        x, y = self.food
        rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.screen, FOOD_COLOR, rect)
        pygame.draw.rect(self.screen, BG_COLOR, rect, 1)

    def draw_score(self):
        score_text = f"Score: {self.score}   High Score: {self.high_score}   Speed: {self.fps} FPS"
        surface = self.font_small.render(score_text, True, TEXT_COLOR)
        self.screen.blit(surface, (10, 10))

    def draw_start_screen(self):
        title = self.font_large.render("SNAKE", True, ACCENT_COLOR)
        line1 = self.font_small.render("Arrow Keys to Move", True, TEXT_COLOR)
        line2 = self.font_small.render("Press SPACE to Start", True, TEXT_COLOR)
        line3 = self.font_small.render("Press ESC to Quit", True, TEXT_COLOR)

        self.screen.blit(title, title.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 - 80)))
        self.screen.blit(line1, line1.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2)))
        self.screen.blit(line2, line2.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 40)))
        self.screen.blit(line3, line3.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 80)))

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        text1 = self.font_large.render("GAME OVER", True, (255, 90, 90))
        text2 = self.font_small.render(f"Score: {self.score}", True, TEXT_COLOR)
        text3 = self.font_small.render(f"High Score: {self.high_score}", True, TEXT_COLOR)
        text4 = self.font_small.render("Press R to Restart", True, ACCENT_COLOR)
        text5 = self.font_small.render("Press Q or ESC to Quit", True, TEXT_COLOR)

        self.screen.blit(text1, text1.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 - 70)))
        self.screen.blit(text2, text2.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 - 15)))
        self.screen.blit(text3, text3.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 20)))
        self.screen.blit(text4, text4.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 65)))
        self.screen.blit(text5, text5.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 100)))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if self.state == "START":
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.reset_game()
                        self.state = "PLAYING"

                elif self.state == "PLAYING":
                    self.handle_key_playing(event.key)

                elif self.state == "GAME_OVER":
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = "PLAYING"
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        self.running = False

    def render(self):
        self.screen.fill(BG_COLOR)
        self.draw_grid()

        if self.state in ("PLAYING", "GAME_OVER"):
            self.draw_food()
            self.draw_snake()
            self.draw_score()

        if self.state == "START":
            self.draw_start_screen()
        elif self.state == "GAME_OVER":
            self.draw_game_over()

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()

            if self.state == "PLAYING":
                self.update()
                self.clock.tick(self.fps)
            else:
                self.clock.tick(30)

            self.render()

        pygame.quit()


if __name__ == "__main__":
    SnakeGame().run()
