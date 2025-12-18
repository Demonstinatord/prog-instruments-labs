import random
from enum import Enum
from typing import Tuple, List, Optional, Union

import numpy as np
import pygame
import tcod


class Direction(Enum):
    """Перечисление возможных направлений движения персонажей."""
    DOWN = -90
    RIGHT = 0
    UP = 90
    LEFT = 180
    NONE = 360


class ScoreType(Enum):
    """Перечисление типов очков с соответствующими значениями."""
    COOKIE = 10
    POWERUP = 50
    GHOST = 400


class GhostBehaviour(Enum):
    """Перечисление режимов поведения привидений."""
    CHASE = 1
    SCATTER = 2


def translate_screen_to_maze(in_coords: Tuple[int, int], in_size: int = 32) -> Tuple[int, int]:
    """
    Преобразует координаты экрана в координаты лабиринта.

    Args:
        in_coords: Координаты на экране в пикселях (x, y)
        in_size: Размер одной клетки лабиринта в пикселях. По умолчанию 32.

    Returns:
        Координаты в системе лабиринта (номер столбца, номер строки)
    """
    return int(in_coords[0] / in_size), int(in_coords[1] / in_size)


def translate_maze_to_screen(in_coords: Tuple[int, int], in_size: int = 32) -> Tuple[int, int]:
    """
    Преобразует координаты лабиринта в координаты экрана.

    Args:
        in_coords: Координаты в лабиринте (номер столбца, номер строки)
        in_size: Размер одной клетки лабиринта в пикселях. По умолчанию 32.

    Returns:
        Координаты на экране в пикселях (x, y)
    """
    return in_coords[0] * in_size, in_coords[1] * in_size


class GameObject:
    """
    Базовый класс для всех игровых объектов.

    Предоставляет общую функциональность для отрисовки и управления
    положением объектов на игровом поле.
    """

    def __init__(self, in_surface: 'GameRenderer', x: int, y: int,
                 in_size: int, in_color: Tuple[int, int, int] = (255, 0, 0),
                 is_circle: bool = False):
        """
        Инициализирует игровой объект.

        Args:
            in_surface: Объект рендерера игры
            x: Координата X объекта на экране в пикселях
            y: Координата Y объекта на экране в пикселях
            in_size: Размер объекта в пикселях
            in_color: Цвет объекта в формате RGB. По умолчанию красный (255, 0, 0)
            is_circle: Флаг, указывающий круглую форму объекта.
                      По умолчанию False (прямоугольник)
        """
        self._size = in_size
        self._renderer: GameRenderer = in_surface
        self._surface = in_surface._screen
        self.y = y
        self.x = x
        self._color = in_color
        self._circle = is_circle
        self._shape = pygame.Rect(self.x, self.y, in_size, in_size)

    def draw(self) -> None:
        """Отрисовывает объект на экране."""
        if self._circle:
            pygame.draw.circle(self._surface,
                               self._color,
                               (self.x, self.y),
                               self._size)
        else:
            rect_object = pygame.Rect(self.x, self.y, self._size, self._size)
            pygame.draw.rect(self._surface,
                             self._color,
                             rect_object,
                             border_radius=1)

    def tick(self) -> None:
        """Обновляет состояние объекта. Базовый метод, переопределяется в наследниках."""
        pass

    def get_shape(self) -> pygame.Rect:
        """
        Возвращает прямоугольник, описывающий границы объекта.

        Returns:
            Прямоугольник с координатами и размерами объекта
        """
        return pygame.Rect(self.x, self.y, self._size, self._size)

    def set_position(self, in_x: int, in_y: int) -> None:
        """
        Устанавливает новую позицию объекта.

        Args:
            in_x: Новая координата X в пикселях
            in_y: Новая координата Y в пикселях
        """
        self.x = in_x
        self.y = in_y

    def get_position(self) -> Tuple[int, int]:
        """
        Возвращает текущую позицию объекта.
        Returns:
            Текущие координаты объекта (x, y)
        """
        return (self.x, self.y)


class Wall(GameObject):
    """Класс, представляющий стену в лабиринте."""

    def __init__(self, in_surface: 'GameRenderer', x: int, y: int,
                 in_size: int, in_color: Tuple[int, int, int] = (0, 0, 255)):
        """
        Инициализирует стену.
        Args:
            in_surface: Объект рендерера игры
            x: Координата X стены в клетках лабиринта
            y: Координата Y стены в клетках лабиринта
            in_size: Размер стены в пикселях
            in_color: Цвет стены в формате RGB. По умолчанию синий (0, 0, 255)
        """
        super().__init__(in_surface, x * in_size, y * in_size, in_size, in_color)


class GameRenderer:
    """
    Основной класс для управления игровым процессом и отрисовки.
    Отвечает за отрисовку всех игровых объектов, обработку событий,
    управление состоянием игры и подсчет очков.
    """

    def __init__(self, in_width: int, in_height: int):
        """
        Инициализирует игровой рендерер.
        Args:
            in_width: Ширина игрового окна в пикселях
            in_height: Высота игрового окна в пикселях
        """
        pygame.init()
        self._width = in_width
        self._height = in_height
        self._screen = pygame.display.set_mode((in_width, in_height))
        pygame.display.set_caption('Pacman')
        self._clock = pygame.time.Clock()
        self._done = False
        self._won = False
        self._game_objects: List[GameObject] = []
        self._walls: List[Wall] = []
        self._cookies: List['Cookie'] = []
        self._powerups: List['Powerup'] = []
        self._ghosts: List['Ghost'] = []
        self._hero: Optional['Hero'] = None
        self._lives = 3
        self._score = 0
        self._score_cookie_pickup = 10
        self._score_ghost_eaten = 400
        self._score_powerup_pickup = 50
        self._kokoro_active = False  # powerup, special ability
        self._current_mode = GhostBehaviour.SCATTER
        self._mode_switch_event = pygame.USEREVENT + 1  # custom event
        self._kokoro_end_event = pygame.USEREVENT + 2
        self._pakupaku_event = pygame.USEREVENT + 3
        self._modes = [
            (7, 20),
            (7, 20),
            (5, 20),
            (5, 999999)  # 'infinite' chase seconds
        ]
        self._current_phase = 0

    def tick(self, in_fps: int) -> None:
        """
        Основной игровой цикл.
        Args:
            in_fps: Количество кадров в секунду
        """
        black = (0, 0, 0)

        self.handle_mode_switch()
        pygame.time.set_timer(self._pakupaku_event, 200)  # open close mouth
        while not self._done:
            for game_object in self._game_objects:
                game_object.tick()
                game_object.draw()

            self.display_text(f"[Score: {self._score}]  [Lives: {self._lives}]")

            if self._hero is None:
                self.display_text("YOU DIED",
                        (self._width / 2 - 256, self._height / 2 - 256),
                            100
                                  )
            if self.get_won():
                self.display_text("YOU WON",
                                  (self._width / 2 - 256, self._height / 2 - 256),
                                  100
                                  )
            pygame.display.flip()
            self._clock.tick(in_fps)
            self._screen.fill(black)
            self._handle_events()

        print("Game over")

    def handle_mode_switch(self) -> None:
        """
        Обрабатывает смену режима поведения привидений.

        Переключает между режимами CHASE и SCATTER согласно фазам игры.
        """
        current_phase_timings = self._modes[self._current_phase]
        print(f"Current phase: {str(self._current_phase)}, current_phase_timings: {str(current_phase_timings)}")
        scatter_timing = current_phase_timings[0]
        chase_timing = current_phase_timings[1]

        if self._current_mode == GhostBehaviour.CHASE:
            self._current_phase += 1
            self.set_current_mode(GhostBehaviour.SCATTER)
        else:
            self.set_current_mode(GhostBehaviour.CHASE)

        used_timing = scatter_timing if self._current_mode == GhostBehaviour.SCATTER else chase_timing
        pygame.time.set_timer(self._mode_switch_event, used_timing * 1000)

    def start_kokoro_timeout(self) -> None:
        """Запускает таймер окончания действия пауэр-апа (15 секунд)."""
        pygame.time.set_timer(self._kokoro_end_event, 15000)  # 15s

    def add_game_object(self, obj: GameObject) -> None:
        """
        Добавляет игровой объект в список для отрисовки и обновления.

        Args:
            obj: Объект для добавления
        """
        self._game_objects.append(obj)

    def add_cookie(self, obj: 'Cookie') -> None:
        """
        Добавляет печенье в игру.

        Args:
            obj: Объект печенья
        """
        self._game_objects.append(obj)
        self._cookies.append(obj)

    def add_ghost(self, obj: 'Ghost') -> None:
        """
        Добавляет привидение в игру.

        Args:
            obj: Объект привидения
        """
        self._game_objects.append(obj)
        self._ghosts.append(obj)

    def add_powerup(self, obj: 'Powerup') -> None:
        """
        Добавляет пауэр-ап в игру.

        Args:
            obj: Объект пауэр-апа
        """
        self._game_objects.append(obj)
        self._powerups.append(obj)

    def activate_kokoro(self) -> None:
        """Активирует пауэр-ап: включает специальный режим и меняет поведение привидений."""
        self._kokoro_active = True
        self.set_current_mode(GhostBehaviour.SCATTER)
        self.start_kokoro_timeout()

    def set_won(self) -> None:
        """Устанавливает флаг победы в игре."""
        self._won = True

    def get_won(self) -> bool:
        """
        Проверяет, выиграна ли игра.

        Returns:
            True если игра выиграна, иначе False
        """
        return self._won

    def add_score(self, in_score: ScoreType) -> None:
        """
        Добавляет очки к общему счету.

        Args:
            in_score: Тип очков для добавления
        """
        self._score += in_score.value

    def get_hero_position(self) -> Tuple[int, int]:
        """
        Возвращает позицию главного героя.
        Returns:
            Координаты героя (x, y) или (0, 0) если герой отсутствует
        """
        return self._hero.get_position() if self._hero is not None else (0, 0)

    def set_current_mode(self, in_mode: GhostBehaviour) -> None:
        """
        Устанавливает текущий режим поведения привидений.
        Args:
            in_mode: Режим поведения (CHASE или SCATTER)
        """
        self._current_mode = in_mode

    def get_current_mode(self) -> GhostBehaviour:
        """
        Возвращает текущий режим поведения привидений.
        Returns:
            Текущий режим поведения
        """
        return self._current_mode

    def end_game(self) -> None:
        """Завершает игру, удаляя героя из списка объектов."""
        if self._hero in self._game_objects:
            self._game_objects.remove(self._hero)
        self._hero = None

    def kill_pacman(self) -> None:
        """Обрабатывает смерть Пакмана: уменьшает жизни и сбрасывает позицию."""
        self._lives -= 1
        self._hero.set_position(32, 32)
        self._hero.set_direction(Direction.NONE)
        if self._lives == 0:
            self.end_game()

    def display_text(self, text: str, in_position: Tuple[float, float] = (32, 0),
                         in_size: int = 30) -> None:
        """
        Отображает текст на экране.
        Args:
            text: Текст для отображения
            in_position: Позиция текста на экране. По умолчанию (32, 0)
            in_size: Размер шрифта. По умолчанию 30
        """

        font = pygame.font.SysFont('Arial', in_size)
        text_surface = font.render(text, False, (255, 255, 255))
        self._screen.blit(text_surface, in_position)

    def is_kokoro_active(self) -> bool:
        """
        Проверяет, активен ли пауэр-ап.
        Returns:
            True если пауэр-ап активен, иначе False
        """
        return self._kokoro_active

    def add_wall(self, obj: Wall) -> None:
        """
        Добавляет стену в игру.

        Args:
            obj: Объект стены
        """
        self.add_game_object(obj)
        self._walls.append(obj)

    def get_walls(self) -> List[Wall]:
        """
        Возвращает список всех стен.

        Returns:
            Список объектов стен
        """
        return self._walls

    def get_cookies(self) -> List['Cookie']:
        """
        Возвращает список всех печений.
        Returns:
            Список объектов печений
        """
        return self._cookies

    def get_ghosts(self) -> List['Ghost']:
        """
        Возвращает список всех привидений.
        Returns:
            Список объектов привидений
        """
        return self._ghosts

    def get_powerups(self) -> List['Powerup']:
        """
        Возвращает список всех пауэр-апов.
        Returns:
            Список объектов пауэр-апов
        """
        return self._powerups

    def get_game_objects(self) -> List[GameObject]:
        """
        Возвращает список всех игровых объектов.
        Returns:
            Список всех игровых объектов
        """
        return self._game_objects

    def add_hero(self, in_hero: 'Hero') -> None:
        """
        Добавляет героя в игру.
        Args:
            in_hero: Объект героя
        """
        self.add_game_object(in_hero)
        self._hero = in_hero

    def _handle_events(self) -> None:
        """Обрабатывает все события pygame (клавиатура, таймеры, закрытие окна)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._done = True

            if event.type == self._mode_switch_event:
                self.handle_mode_switch()

            if event.type == self._kokoro_end_event:
                self._kokoro_active = False

            if event.type == self._pakupaku_event:
                if self._hero is None:
                    break
                self._hero.mouth_open = not self._hero.mouth_open

        pressed = pygame.key.get_pressed()
        if self._hero is None:
            return
        if pressed[pygame.K_UP]:
            self._hero.set_direction(Direction.UP)
        elif pressed[pygame.K_LEFT]:
            self._hero.set_direction(Direction.LEFT)
        elif pressed[pygame.K_DOWN]:
            self._hero.set_direction(Direction.DOWN)
        elif pressed[pygame.K_RIGHT]:
            self._hero.set_direction(Direction.RIGHT)


class MovableObject(GameObject):
    """
    Базовый класс для подвижных объектов.
    Расширяет GameObject, добавляя функциональность движения
    и обработки столкновений.
    """

    def __init__(self, in_surface: 'GameRenderer', x: int, y: int,
                 in_size: int, in_color: Tuple[int, int, int] = (255, 0, 0),
                 is_circle: bool = False):
        """
        Инициализирует подвижный объект.
        Args:
            in_surface: Объект рендерера игры
            x: Начальная координата X
            y: Начальная координата Y
            in_size: Размер объекта
            in_color: Цвет объекта. По умолчанию красный
            is_circle: Флаг круглой формы. По умолчанию False
        """
        super().__init__(in_surface, x, y, in_size, in_color, is_circle)
        self.current_direction = Direction.NONE
        self.direction_buffer = Direction.NONE
        self.last_working_direction = Direction.NONE
        self.location_queue: List[Tuple[int, int]] = []
        self.next_target: Optional[Tuple[int, int]] = None
        self.image = pygame.image.load('images/ghost.png')

    def get_next_location(self) -> Optional[Tuple[int, int]]:
        """
        Возвращает следующую точку из очереди пути.
        Returns:
            Следующая точка (x, y) или None если очередь пуста
        """
        return None if len(self.location_queue) == 0 else self.location_queue.pop(0)

    def set_direction(self, in_direction: Direction) -> None:
        """
        Устанавливает направление движения объекта.
        Args:
            in_direction: Направление для установки
        """
        self.current_direction = in_direction
        self.direction_buffer = in_direction

    def collides_with_wall(self, in_position: Tuple[int, int]) -> bool:
        """
        Проверяет столкновение с любой стеной в заданной позиции.

        Args:
            in_position: Позиция для проверки (x, y)

        Returns:
            True если есть столкновение, иначе False
        """
        collision_rect = pygame.Rect(in_position[0], in_position[1], self._size, self._size)
        collides = False
        walls = self._renderer.get_walls()
        for wall in walls:
            collides = collision_rect.colliderect(wall.get_shape())
            if collides:
                break
        return collides

    def check_collision_in_direction(self, in_direction: Direction) -> Tuple[bool, Tuple[int, int]]:
        """
        Проверяет столкновение в заданном направлении.
        Args:
            in_direction: Направление для проверки
        Returns:
            (has_collision, desired_position) где:
                has_collision: True если есть столкновение
                desired_position: Желаемая позиция после движения
        """
        desired_position = (0, 0)
        if in_direction == Direction.NONE:
            return False, desired_position
        if in_direction == Direction.UP:
            desired_position = (self.x, self.y - 1)
        elif in_direction == Direction.DOWN:
            desired_position = (self.x, self.y + 1)
        elif in_direction == Direction.LEFT:
            desired_position = (self.x - 1, self.y)
        elif in_direction == Direction.RIGHT:
            desired_position = (self.x + 1, self.y)

        return self.collides_with_wall(desired_position), desired_position

    def automatic_move(self, in_direction: Direction) -> None:
        """
        Автоматически перемещает объект в заданном направлении.
        Args:
            in_direction: Направление движения
        """
        pass

    def tick(self) -> None:
        """Обновляет состояние подвижного объекта."""
        self.reached_target()
        self.automatic_move(self.current_direction)

    def reached_target(self) -> None:
        """Обрабатывает достижение целевой точки."""
        pass

    def draw(self) -> None:
        """Отрисовывает объект с использованием спрайта."""
        self.image = pygame.transform.scale(self.image, (32, 32))
        self._surface.blit(self.image, self.get_shape())


class Hero(MovableObject):
    """Класс главного героя (Пакмана)."""

    def __init__(self, in_surface: 'GameRenderer', x: int, y: int, in_size: int):
        """
        Инициализирует героя.

        Args:
            in_surface: Объект рендерера игры
            x: Начальная координата X
            y: Начальная координата Y
            in_size: Размер героя
        """
        super().__init__(in_surface, x, y, in_size, (255, 255, 0), False)
        self.last_non_colliding_position: Tuple[int, int] = (0, 0)
        self.open = pygame.image.load("images/paku.png")
        self.closed = pygame.image.load("images/man.png")
        self.image = self.open
        self.mouth_open = True

    def tick(self) -> None:
        """Обновляет состояние героя: телепортацию, движение, сбор предметов."""
        # TELEPORT
        if self.x < 0:
            self.x = self._renderer._width

        if self.x > self._renderer._width:
            self.x = 0

        self.last_non_colliding_position = self.get_position()

        if self.check_collision_in_direction(self.direction_buffer)[0]:
            self.automatic_move(self.current_direction)
        else:
            self.automatic_move(self.direction_buffer)
            self.current_direction = self.direction_buffer

        if self.collides_with_wall((self.x, self.y)):
            self.set_position(self.last_non_colliding_position[0],
                              self.last_non_colliding_position[1])

        self.handle_cookie_pickup()
        self.handle_ghosts()

    def automatic_move(self, in_direction: Direction) -> None:
        """
        Автоматическое движение героя с проверкой столкновений.

        Args:
            in_direction: Направление движения
        display_"""

        collision_result = self.check_collision_in_direction(in_direction)

        desired_position_collides = collision_result[0]
        if not desired_position_collides:
            self.last_working_direction = self.current_direction
            desired_position = collision_result[1]
            self.set_position(desired_position[0], desired_position[1])
        else:
            self.current_direction = self.last_working_direction

    def handle_cookie_pickup(self) -> None:
        """Обрабатывает сбор печений и пауэр-апов."""
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        cookies = self._renderer.get_cookies()
        powerups = self._renderer.get_powerups()
        game_objects = self._renderer.get_game_objects()
        cookie_to_remove: Optional['Cookie'] = None

        for cookie in cookies:
            collides = collision_rect.colliderect(cookie.get_shape())
            if collides and cookie in game_objects:
                game_objects.remove(cookie)
                self._renderer.add_score(ScoreType.COOKIE)
                cookie_to_remove = cookie

        if cookie_to_remove is not None:
            cookies.remove(cookie_to_remove)

        if len(self._renderer.get_cookies()) == 0:
            self._renderer.set_won()

        for powerup in powerups:
            collides = collision_rect.colliderect(powerup.get_shape())
            if collides and powerup in game_objects:
                if not self._renderer.is_kokoro_active():
                    game_objects.remove(powerup)
                    self._renderer.add_score(ScoreType.POWERUP)
                    self._renderer.activate_kokoro()

    def handle_ghosts(self) -> None:
        """Обрабатывает столкновения с привидениями."""
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        ghosts = self._renderer.get_ghosts()
        game_objects = self._renderer.get_game_objects()

        for ghost in ghosts:
            collides = collision_rect.colliderect(ghost.get_shape())
            if collides and ghost in game_objects:
                if self._renderer.is_kokoro_active():
                    game_objects.remove(ghost)
                    self._renderer.add_score(ScoreType.GHOST)
                else:
                    if not self._renderer.get_won():
                        self._renderer.kill_pacman()

    def draw(self) -> None:
        """Отрисовывает героя с анимацией рта и поворотом в направлении движения."""
        self.image = self.open if self.mouth_open else self.closed
        self.image = pygame.transform.rotate(self.image, self.current_direction.value)
        super(Hero, self).draw()


class Ghost(MovableObject):
    """Класс привидения."""

    def __init__(self, in_surface: 'GameRenderer', x: int, y: int, in_size: int,
                 in_game_controller: 'PacmanGameController',
                 sprite_path: str = "images/ghost_fright.png"):
        """
        Инициализирует привидение.

        Args:
            in_surface: Объект рендерера игры
            x: Начальная координата X
            y: Начальная координата Y
            in_size: Размер привидения
            in_game_controller: Контроллер игры
            sprite_path: Путь к спрайту привидения. По умолчанию "images/ghost_fright.png"
        """
        super().__init__(in_surface, x, y, in_size)
        self.game_controller = in_game_controller
        self.sprite_normal = pygame.image.load(sprite_path)
        self.sprite_fright = pygame.image.load("images/ghost_fright.png")

    def reached_target(self) -> None:
        """Обрабатывает достижение целевой точки и вычисляет следующее направление."""
        if (self.x, self.y) == self.next_target:
            self.next_target = self.get_next_location()
        self.current_direction = self.calculate_direction_to_next_target()

    def set_new_path(self, in_path: List[Tuple[int, int]]) -> None:
        """
        Устанавливает новый путь для привидения.

        Args:
            in_path: Список точек пути [(x1, y1), (x2, y2), ...]
        """
        for item in in_path:
            self.location_queue.append(item)
        self.next_target = self.get_next_location()

    def calculate_direction_to_next_target(self) -> Direction:
        """
        Вычисляет направление к следующей целевой точке.
        Returns:
            Направление движения или NONE если требуется новый путь
        """
        if self.next_target is None:
            mode = self._renderer.get_current_mode()
            if (mode == GhostBehaviour.CHASE and
                    not self._renderer.is_kokoro_active()):
                self.request_path_to_player(self)
            else:
                self.game_controller.request_new_random_path(self)
            return Direction.NONE

        diff_x = self.next_target[0] - self.x
        diff_y = self.next_target[1] - self.y

        if diff_x == 0:
            return Direction.DOWN if diff_y > 0 else Direction.UP
        if diff_y == 0:
            return Direction.LEFT if diff_x < 0 else Direction.RIGHT

        mode = self._renderer.get_current_mode()
        if (mode == GhostBehaviour.CHASE and
                not self._renderer.is_kokoro_active()):
            self.request_path_to_player(self)
        else:
            self.game_controller.request_new_random_path(self)
        return Direction.NONE

    def request_path_to_player(self, in_ghost: 'Ghost') -> None:
        """
        Запрашивает путь к игроку для данного привидения.

        Args:
            in_ghost: Привидение, для которого запрашивается путь
        """

        player_position = translate_screen_to_maze(in_ghost._renderer.get_hero_position())
        current_maze_coord = translate_screen_to_maze(in_ghost.get_position())
        path = self.game_controller.p.get_path(
            current_maze_coord[1],
            current_maze_coord[0],
            player_position[1],
            player_position[0]
        )

        new_path = [translate_maze_to_screen(item) for item in path]
        in_ghost.set_new_path(new_path)

    def automatic_move(self, in_direction: Direction) -> None:
        """
        Перемещает привидение в заданном направлении.
        Args:
            in_direction: Направление движения
        """
        if in_direction == Direction.UP:
            self.set_position(self.x, self.y - 1)
        elif in_direction == Direction.DOWN:
            self.set_position(self.x, self.y + 1)
        elif in_direction == Direction.LEFT:
            self.set_position(self.x - 1, self.y)
        elif in_direction == Direction.RIGHT:
            self.set_position(self.x + 1, self.y)

    def draw(self) -> None:
        """Отрисовывает привидение с учетом текущего состояния (обычное или испуганное)."""
        self.image = self.sprite_fright if self._renderer.is_kokoro_active() else self.sprite_normal
        super(Ghost, self).draw()


class Cookie(GameObject):
    """Класс печенья."""

    def __init__(self, in_surface: 'GameRenderer', x: int, y: int):
        """
        Инициализирует печенье.

        Args:
            in_surface: Объект рендерера игры
            x: Координата X
            y: Координата Y
        """
        super().__init__(in_surface, x, y, 4, (255, 255, 0), True)


class Powerup(GameObject):
    """Класс пауэр-апа (специальное умение)."""
    
    def __init__(self, in_surface: 'GameRenderer', x: int, y: int):
        """
        Инициализирует пауэр-ап.
        Args:
            in_surface: Объект рендерера игры
            x: Координата X
            y: Координата Y
        """
        super().__init__(in_surface, x, y, 8, (255, 255, 255), True)


class Pathfinder:
    """Класс для поиска пути в лабиринте."""

    def __init__(self, in_arr: List[List[int]]):
        """
        Инициализирует поисковик пути.
        Args:
            in_arr: Двумерный массив лабиринта (0 - стена, 1 - проход)
        """
        cost = np.array(in_arr, dtype=np.bool_).tolist()
        self.pf = tcod.path.AStar(cost=cost, diagonal=0)

    def get_path(self, from_x: int, from_y: int, to_x: int, to_y: int) -> List[Tuple[int, int]]:
        """
        Находит путь от начальной точки к конечной.
        Args:
            from_x: Начальная координата X
            from_y: Начальная координата Y
            to_x: Конечная координата X
            to_y: Конечная координата Y

        Returns:
            Список точек пути [(y1, x1), (y2, x2), ...]
        """
        res = self.pf.get_path(from_x, from_y, to_x, to_y)
        return [(sub[1], sub[0]) for sub in res]


class PacmanGameController:
    """Контроллер игры, управляющий состоянием лабиринта и AI привидений."""

    def __init__(self):
        """Инициализирует контроллер игры с предопределенным лабиринтом."""
        self.ascii_maze: List[str] = [
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "XP           XX            X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X XXXXOXXXXX XX XXXXXOXXXX X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X                          X",
            "X XXXX XX XXXXXXXX XX XXXX X",
            "X XXXX XX XXXXXXXX XX XXXX X",
            "X      XX    XX    XX      X",
            "XXXXXX XXXXX XX XXXXX XXXXXX",
            "XXXXXX XXXXX XX XXXXX XXXXXX",
            "XXXXXX XX     G    XX XXXXXX",
            "XXXXXX XX XXX  XXX XX XXXXXX",
            "XXXXXX XX X      X XX XXXXXX",
            "   G      X      X          ",
            "XXXXXX XX X      X XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "XXXXXX XX    G     XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "XXXXXX XX XXXXXXXX XX XXXXXX",
            "X            XX            X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X XXXX XXXXX XX XXXXX XXXX X",
            "X   XX       G        XX   X",
            "XXX XX XX XXXXXXXX XX XX XXX",
            "XXX XX XX XXXXXXXX XX XX XXX",
            "X      XX    XX    XX      X",
            "X XXXXXXXXXX XX XXXXXXXXXX X",
            "X XXXXXXXXXX XX XXXXXXXXXX X",
            "X   O                 O    X",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]

        self.numpy_maze: List[List[int]] = []
        self.cookie_spaces: List[Tuple[int, int]] = []
        self.powerup_spaces: List[Tuple[int, int]] = []
        self.reachable_spaces: List[Tuple[int, int]] = []
        self.ghost_spawns: List[Tuple[int, int]] = []
        self.ghost_colors: List[str] = [
            "images/ghost.png",
            "images/ghost_pink.png",
            "images/ghost_orange.png",
            "images/ghost_blue.png"
        ]
        self.size: Tuple[int, int] = (0, 0)
        self.convert_maze_to_numpy()
        self.p = Pathfinder(self.numpy_maze)

    def request_new_random_path(self, in_ghost: Ghost) -> None:
        """
        Запрашивает случайный путь для привидения.
        Args:
            in_ghost: Привидение, для которого нужен путь
        """
        random_space = random.choice(self.reachable_spaces)
        current_maze_coord = translate_screen_to_maze(in_ghost.get_position())

        path = self.p.get_path(current_maze_coord[1],
                               current_maze_coord[0],
                               random_space[1],
                               random_space[0]
                               )
        test_path = [translate_maze_to_screen(item) for item in path]
        in_ghost.set_new_path(test_path)

    def convert_maze_to_numpy(self) -> None:
        """Преобразует ASCII представление лабиринта в numpy массив."""
        for x, row in enumerate(self.ascii_maze):
            self.size = (len(row), x + 1)
            binary_row: List[int] = []
            for y, column in enumerate(row):
                if column == "G":
                    self.ghost_spawns.append((y, x))

                if column == "X":
                    binary_row.append(0)
                else:
                    binary_row.append(1)
                    self.cookie_spaces.append((y, x))
                    self.reachable_spaces.append((y, x))
                    if column == "O":
                        self.powerup_spaces.append((y, x))

            self.numpy_maze.append(binary_row)


if __name__ == "__main__":
    """
    Основная точка входа в игру.
    Инициализирует игру, создает объекты и запускает игровой цикл.
    """
    unified_size = 32
    pacman_game = PacmanGameController()
    size = pacman_game.size
    game_renderer = GameRenderer(size[0] * unified_size, size[1] * unified_size)

    for y, row in enumerate(pacman_game.numpy_maze):
        for x, column in enumerate(row):
            if column == 0:
                game_renderer.add_wall(Wall(game_renderer, x, y, unified_size))

    for cookie_space in pacman_game.cookie_spaces:
        translated = translate_maze_to_screen(cookie_space)
        cookie = Cookie(game_renderer,
                        translated[0] + unified_size / 2,
                        translated[1] + unified_size / 2
                        )
        game_renderer.add_cookie(cookie)

    for powerup_space in pacman_game.powerup_spaces:
        translated = translate_maze_to_screen(powerup_space)
        powerup = Powerup(game_renderer,
                          translated[0] + unified_size / 2,
                          translated[1] + unified_size / 2
                          )
        game_renderer.add_powerup(powerup)

    for i, ghost_spawn in enumerate(pacman_game.ghost_spawns):
        translated = translate_maze_to_screen(ghost_spawn)
        ghost = Ghost(game_renderer, translated[0], translated[1], unified_size, pacman_game,
                      pacman_game.ghost_colors[i % 4])
        game_renderer.add_ghost(ghost)

    pacman = Hero(game_renderer, unified_size, unified_size, unified_size)
    game_renderer.add_hero(pacman)
    game_renderer.set_current_mode(GhostBehaviour.CHASE)
    game_renderer.tick(120)










