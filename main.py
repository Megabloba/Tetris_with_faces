import pygame
import random

pygame.init()
# константы
FIGURE_FALLEN_EVENT = pygame.USEREVENT + 1
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
CELL_SIZE = 40
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
FPS = 60
BLACK = (0, 0, 0)
# Картинки блоков
faces = ['creepy', 'sad', 'angry', 'crying', 'dead', 'happy', 'O', 'ok', 'oops', 'sad', 'uwu']
blockImages = [f"images/{i}.png" for i in faces]  # Пример: block1.png, block2.png, ..., block10.png
# Список цветов
colors = [
    (255, 0, 0),
    (0, 255, 0),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (128, 0, 128),
    (255, 165, 0),
    (0, 128, 0),
    (128, 128, 128),
    (255, 183, 206)
]

# фигуры
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 0, 0], [1, 1, 1]],  # L
    [[0, 0, 1], [1, 1, 1]],  # J
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]],  # Z
]


class BlockSprite(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y):
        super().__init__()
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (CELL_SIZE, CELL_SIZE))
        self.rect = self.image.get_rect(topleft=(x, y))


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [[(0, 0)] * width for _ in range(height)]  # (номер_картинки, цвет)
        self.left = 300
        self.top = 100
        self.cell_size = CELL_SIZE
        self.current_shape = None
        self.current_position = (0, 0)
        self.current_shape_color = None  # Цвет для падающей фигуры
        self.current_shape_images = []  # Список картинок для блоков падающей фигуры
        self.blockImages = blockImages  # Список путей к изображениям
        self.colors = colors
        self.all_sprites = pygame.sprite.Group()
        self.last_fall_time = pygame.time.get_ticks()
        self.fall_delay = 500
        self.score = 0
        self.multiplier = 1.0
        self.font = pygame.font.Font(None, 36)
        self.render_current = True
        self.last_score_update = pygame.time.get_ticks()
        self.last_multiplier_update = pygame.time.get_ticks()

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def spawn_shape(self):
        shape = random.choice(SHAPES)
        self.current_shape = shape
        self.current_position = (self.width // 2 - len(shape[0]) // 2, 0)
        self.current_shape_color = random.choice(self.colors)
        self.current_shape_images = []
        num_blocks = sum(cell for row in shape for cell in row)
        # Уникальные картинки в пределах блока
        selected_images = random.sample(self.blockImages, num_blocks)
        image_index = 0
        for row in shape:
            for cell in row:
                if cell:
                    self.current_shape_images.append(selected_images[image_index])
                    image_index += 1

    def can_move(self, dx, dy):
        for y, row in enumerate(self.current_shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.current_position[0] + x + dx
                    new_y = self.current_position[1] + y + dy
                    if (new_x < 0 or new_x >= self.width or
                            new_y >= self.height or
                            (new_y >= 0 and self.board[new_y][new_x] != (0, 0))):
                        return False
        return True

    def move_shape(self, dx, dy):
        """Перемещает фигуру на (dx, dy)."""
        if self.can_move(dx, dy):
            self.current_position = (self.current_position[0] + dx, self.current_position[1] + dy)
            return True
        return False

    def rotate_shape(self):
        """Поворачивает фигуру."""
        if not self.current_shape:
            return
        rotated_shape = list(zip(*self.current_shape[::-1]))
        if self.can_rotate(rotated_shape):
            self.current_shape = rotated_shape

    def can_rotate(self, rotated_shape):
        """Проверяет, можно ли повернуть фигуру."""
        for y, row in enumerate(rotated_shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.current_position[0] + x
                    new_y = self.current_position[1] + y
                    if (new_x < 0 or new_x >= self.width or
                            new_y >= self.height or
                            (new_y >= 0 and self.board[new_y][new_x] != (0, 0))):
                        return False
        return True

    def fix_shape(self):
        """Фиксирует текущую фигуру на поле."""
        image_index = 0
        for y, row in enumerate(self.current_shape):
            for x, cell in enumerate(row):
                if cell:
                    image_path = self.current_shape_images[image_index]
                    image_index_in_list = self.blockImages.index(image_path)
                    color_index = self.colors.index(self.current_shape_color)
                    self.board[self.current_position[1] + y][self.current_position[0] + x] = (
                        image_index_in_list + 1, color_index)
                    image_index += 1
        self.current_shape = None
        self.current_shape_color = None
        self.current_shape_images = []
        self.check_lines()
        pygame.event.post(pygame.event.Event(FIGURE_FALLEN_EVENT))

    def check_lines(self):
        """Удаляет заполненные строки."""
        lines_to_remove = []
        for y, row in enumerate(self.board):
            if all(cell != (0, 0) for cell in row):
                lines_to_remove.append(y)
        for y in lines_to_remove:
            del self.board[y]
            self.board.insert(0, [(0, 0)] * self.width)
            self.score = int(self.score + 1000 * len(lines_to_remove) * self.multiplier)
            self.multiplier += 0.2

    def recolor_image(self, image, color):
        """Перекрашивает изображение в заданный цвет."""
        colored_image = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        colored_image.fill(color)
        colored_image.blit(image, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return colored_image

    def render(self, screen):
        self.all_sprites.empty()

        # Грыницы стакана
        border_color = (100, 100, 100)
        border_width = 2
        pygame.draw.rect(screen, border_color,
                         (self.left - border_width, self.top - border_width,
                          self.width * self.cell_size + 2 * border_width,
                          self.height * self.cell_size + 2 * border_width),
                         border_width)

        # Разлиновка
        grid_color = (50, 50, 50)
        for row in range(self.height + 1):
            pygame.draw.line(screen, grid_color,
                             (self.left, self.top + row * self.cell_size),
                             (self.left + self.width * self.cell_size, self.top + row * self.cell_size))
        for column in range(self.width + 1):
            pygame.draw.line(screen, grid_color,
                             (self.left + column * self.cell_size, self.top),
                             (self.left + column * self.cell_size, self.top + self.height * self.cell_size))
        # отрисовка уже упавших блоков
        for row in range(self.height):
            for column in range(self.width):
                if self.board[row][column] != (0, 0):
                    image_index, color_index = self.board[row][column]
                    block = BlockSprite(self.blockImages[image_index - 1],
                                        column * self.cell_size + self.left,
                                        row * self.cell_size + self.top)
                    colored_image = self.recolor_image(block.image, self.colors[color_index])
                    block.image = colored_image
                    self.all_sprites.add(block)

        # Отрисовка текущей фигуры
        if self.current_shape and self.render_current != False:
            image_index = 0
            for y, row in enumerate(self.current_shape):
                for x, cell in enumerate(row):
                    if cell:
                        block = BlockSprite(self.current_shape_images[image_index],
                                            (self.current_position[0] + x) * self.cell_size + self.left,
                                            (self.current_position[1] + y) * self.cell_size + self.top)
                        colored_image = self.recolor_image(block.image, self.current_shape_color)
                        block.image = colored_image
                        self.all_sprites.add(block)
                        image_index += 1

        self.all_sprites.draw(screen)

    def render_score(self, screen):
        if int(self.multiplier) == 1:
            mult_color = (255, 255, 255)
        elif int(self.multiplier) <= 3:
            mult_color = (255, 165, 0)
        else:
            mult_color = (255, 0, 0)
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))  # Белый цвет текста
        screen.blit(score_text, (self.left, 20))  # Позиция счета
        mult_text = self.font.render(f"x {self.multiplier}", True, mult_color)  # Белый цвет текста
        screen.blit(mult_text, (self.left + 150, 20))  # Позиция счета


def main():
    global FPS
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Тетрис")
    clock = pygame.time.Clock()
    board = Board(BOARD_WIDTH, BOARD_HEIGHT)
    board.set_view(300, 100, CELL_SIZE)
    board.spawn_shape()
    running = True
    fast_fall = False
    game_over = False

    while running:
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    board.move_shape(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    board.move_shape(1, 0)
                elif event.key == pygame.K_DOWN:
                    fast_fall = True
                elif event.key == pygame.K_UP:
                    board.rotate_shape()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    fast_fall = False
            elif event.type == FIGURE_FALLEN_EVENT:
                if any(cell != (0, 0) for cell in board.board[0]):
                    print("Игра окончена!")
                    game_over = True
        if not game_over:
            fall_delay = 50 if fast_fall else 500
            if current_time - board.last_fall_time > fall_delay:
                if not board.move_shape(0, 1):
                    board.fix_shape()
                    board.spawn_shape()
                board.last_fall_time = current_time

            if current_time - board.last_score_update >= 1000 and board.score != 0:
                board.score -= 10
                board.last_score_update = current_time
        else:
            for i in range(BOARD_HEIGHT):
                for i1 in range(BOARD_WIDTH):
                    image_index = random.randint(0, len(board.blockImages) - 1)
                    color_index = random.randint(0, len(board.colors) - 1)
                    board.board[i][i1] = (image_index, color_index)

        # Отрисовка
        screen.fill(BLACK)
        board.render(screen)
        board.render_score(screen)

        # "Game Over"
        if game_over:
            board.render_current = False
            font = pygame.font.Font(None, 200)  # Шрифт для текста "Game Over"
            text = font.render("Game Over", True, (255, 0, 0))  # Красный цвет текста
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))  # Центр экрана
            screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()