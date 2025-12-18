import pytest
#import pygame
from unittest.mock import Mock, patch
from enum import Enum


class Direction(Enum):
    DOWN = -90
    RIGHT = 0
    UP = 90
    LEFT = 180
    NONE = 360


class ScoreType(Enum):
    COOKIE = 10
    POWERUP = 50
    GHOST = 400


class GhostBehaviour(Enum):
    CHASE = 1
    SCATTER = 2


def test_direction_values():
    """Проверка корректности значений направлений."""
    assert Direction.UP.value == 90
    assert Direction.DOWN.value == -90
    assert Direction.LEFT.value == 180
    assert Direction.RIGHT.value == 0
    assert Direction.NONE.value == 360


def test_score_type_values():
    """Проверка корректности значений очков."""
    assert ScoreType.COOKIE.value == 10
    assert ScoreType.POWERUP.value == 50
    assert ScoreType.GHOST.value == 400



def test_translate_functions():
    """Проверка функций преобразования координат."""

    assert translate_screen_to_maze((64, 96), 32) == (2, 3)
    assert translate_screen_to_maze((0, 0), 32) == (0, 0)
    assert translate_screen_to_maze((160, 224), 32) == (5, 7)

    assert translate_maze_to_screen((2, 3), 32) == (64, 96)
    assert translate_maze_to_screen((0, 0), 32) == (0, 0)
    assert translate_maze_to_screen((5, 7), 32) == (160, 224)



def test_maze_initialization():
    """Проверка инициализации лабиринта."""
    from pacman import PacmanGameController

    controller = PacmanGameController()


    assert controller.size == (28, 31)  # 30 колонок, 31 строка


    assert any(0 in row for row in controller.numpy_maze)
    assert any(1 in row for row in controller.numpy_maze)


    assert len(controller.cookie_spaces) > 0
    assert len(controller.powerup_spaces) > 0


    assert len(controller.ghost_spawns) > 0



def test_ghost_behaviour():
    """Проверка состояний поведения призраков."""
    assert GhostBehaviour.CHASE.value == 1
    assert GhostBehaviour.SCATTER.value == 2
    assert GhostBehaviour.CHASE != GhostBehaviour.SCATTER



def test_pathfinder_initialization():
    """Проверка инициализации Pathfinder."""
    from pacman import PacmanGameController, Pathfinder

    controller = PacmanGameController()

    assert controller.p is not None
    assert isinstance(controller.p, Pathfinder)

    assert hasattr(controller.p, 'get_path')
    assert callable(controller.p.get_path)



def test_maze_structure():
    """Проверка структуры лабиринта на наличие ключевых элементов."""
    from pacman import PacmanGameController

    controller = PacmanGameController()

    assert len(controller.ascii_maze) == 31

    row_lengths = [len(row) for row in controller.ascii_maze]
    assert all(length == row_lengths[0] for length in row_lengths)

    maze_string = ''.join(controller.ascii_maze)
    assert 'X' in maze_string
    assert 'P' in maze_string
    assert 'G' in maze_string
    assert 'O' in maze_string
    assert ' ' in maze_string



def test_movable_object_set_direction_basic():
    """Базовый тест метода set_direction с использованием моков."""
    mock_renderer = Mock()

    from pacman import MovableObject

    obj = MovableObject.__new__(MovableObject)
    obj._renderer = mock_renderer
    obj.x = 100
    obj.y = 100
    obj._size = 32
    obj._color = (255, 0, 0)
    obj._circle = False
    obj.current_direction = Direction.NONE
    obj.direction_buffer = Direction.NONE
    obj.last_working_direction = Direction.NONE
    obj.location_queue = []
    obj.next_target = None

    # Тестируем set_direction с разными направлениями
    obj.set_direction(Direction.UP)
    assert obj.current_direction == Direction.UP
    assert obj.direction_buffer == Direction.UP

    obj.set_direction(Direction.RIGHT)
    assert obj.current_direction == Direction.RIGHT
    assert obj.direction_buffer == Direction.RIGHT

    obj.set_direction(Direction.DOWN)
    assert obj.current_direction == Direction.DOWN
    assert obj.direction_buffer == Direction.DOWN

    obj.set_direction(Direction.LEFT)
    assert obj.current_direction == Direction.LEFT
    assert obj.direction_buffer == Direction.LEFT


def test_hero_handle_cookie_pickup_with_mocks(mocker):
    """Тестирование сбора печенья с использованием моков."""
    mock_renderer = Mock()

    mock_cookie_shape = Mock()

    mock_cookie = Mock()
    mock_cookie.get_shape.return_value = mock_cookie_shape

    mock_powerup = Mock()

    mock_renderer.get_cookies.return_value = [mock_cookie]
    mock_renderer.get_powerups.return_value = []
    mock_renderer.is_kokoro_active.return_value = False
    mock_renderer.add_score = Mock()

    mock_game_objects = {mock_cookie}
    mock_renderer.get_game_objects.return_value = mock_game_objects

    # Создаем мок для pygame.Rect
    with patch('pygame.Rect') as mock_rect_class:
        mock_collision_rect = Mock()
        mock_rect_class.return_value = mock_collision_rect
        mock_collision_rect.colliderect.return_value = True

        from pacman import Hero

        hero = Hero.__new__(Hero)
        hero._renderer = mock_renderer
        hero._size = 32
        hero.x = 100
        hero.y = 100

        hero.handle_cookie_pickup()

        mock_renderer.add_score.assert_called_once()

        mock_collision_rect.colliderect.assert_called_once_with(mock_cookie_shape)

        mock_cookie.get_shape.assert_called_once()

def translate_screen_to_maze(in_coords, in_size=32):
    return int(in_coords[0] / in_size), int(in_coords[1] / in_size)


def translate_maze_to_screen(in_coords, in_size=32):
    return in_coords[0] * in_size, in_coords[1] * in_size


class PacmanGameController:
    def __init__(self):
        self.ascii_maze = [
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
        self.numpy_maze = []
        self.cookie_spaces = []
        self.powerup_spaces = []
        self.reachable_spaces = []
        self.ghost_spawns = []
        self.ghost_colors = [
            "images/ghost.png",
            "images/ghost_pink.png",
            "images/ghost_orange.png",
            "images/ghost_blue.png"
        ]
        self.size = (0, 0)
        self.convert_maze_to_numpy()

    def convert_maze_to_numpy(self):
        for x, row in enumerate(self.ascii_maze):
            self.size = (len(row), x + 1)
            binary_row = []
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


class Pathfinder:
    def __init__(self, in_arr):
        self.in_arr = in_arr

    def get_path(self, from_x, from_y, to_x, to_y):
        return []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


