import math
import random
import threading
import os

import protocol
from protocol import Consts
from client_client import Client

import pygame
from colors import generate_random_color

# CONSTANTS
FPS = 60
SERVER_UPDATE_POSITION_FPS = 10

ASPECT_RATIO = 16 / 9
SCREEN_HEIGHT = 900
SCREEN_WIDTH = int(SCREEN_HEIGHT * ASPECT_RATIO)

PALLET_MASS = 10
PALLET_SPAWN_PER_SECOND = 15
SPAWN_PALLET_EXTRA_RANGE = 30

FONT_SIZE = 25

# COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PINK = (255, 0, 255)
BACKGROUND_COLOR = WHITE


def mass_to_radius(mass):
    """Circle area to radius, using the reverse of the circle area formula:
    (radius ** 2) * pi
    """
    return (mass / math.pi) ** 0.5


class Pallet:
    """Pallet. player's food."""

    def __init__(self, position):
        """INITIALIZER"""
        self.position = position
        self.color = generate_random_color()
        self.mass = PALLET_MASS

    def draw(self, camera):
        """Draw the pallet"""
        x, y = camera.coords_from_game_to_camera(self.position)
        pygame.draw.circle(camera.screen, self.color, (x, y),
                           camera.mass_to_camera_size(
                               mass_to_radius(self.mass))
                           )


class Player:
    """Represents a player in game"""

    def __init__(self, object_id, name, mass, position):
        """INITIALIZER"""
        self.position = position
        self.name = name
        self.color = generate_random_color()
        self.mass = mass
        self.id = object_id

        self.players_eaten_id = []

        self.name_surface, self.name_surface_rect = create_text(self.name, FONT_SIZE, WHITE)
        self.name_surface_outline, self.name_surface_outline_rect = create_text(self.name, FONT_SIZE + 1, BLACK)

    def eat(self, mass):
        """eat mass"""
        self.mass += mass

    def draw_name(self, camera):
        """draw self.name on the screen"""
        self.name_surface_rect.center = camera.coords_from_game_to_camera(self.position)
        self.name_surface_outline_rect.center = self.name_surface_rect.center
        self.name_surface_outline_rect.x -= 1
        self.name_surface_outline_rect.y -= 1

        camera.screen.blit(self.name_surface_outline, self.name_surface_outline_rect)
        camera.screen.blit(self.name_surface, self.name_surface_rect)

    def draw(self, camera):
        """Draw client on the screen"""
        x, y = camera.coords_from_game_to_camera(self.position)
        size = camera.mass_to_camera_size(
            mass_to_radius(self.mass)
        )
        pygame.draw.circle(camera.screen, self.color, (x, y), size)
        self.draw_name(camera)

    def __repr__(self):
        """Used for debugging: representation of the client"""
        return f"<Player {self.name} {self.position}>"


class Game:
    """Represents the game"""

    def __init__(self, width, height, players: dict):
        """INITIALIZER!!!!!!!!!!!!!!!!!!"""
        self.width = width
        self.height = height
        self.players = players
        self.pallets = []
        self.viruses = []
        self.all_game_objects = [player for player in
                                 players.values()]

        self.client_player = None

    def create_new_player(self, player_id, name, mass, position):
        """Creates a new player"""
        new_player = Player(player_id, name, mass, position)
        self.players[player_id] = new_player
        self.all_game_objects.append(new_player)
        return new_player

    def get_random_player(self):
        """
        :return: a random living player
        """
        random_player = random.choice(list(self.players.values()))
        if len(self.players) > 1:
            while random_player.id == 0:
                random_player = random.choice(list(self.players.values()))

        return random_player

    def check_for_collisions_and_eat(self, game_objects):
        """checks if a player ate a pallet or another player and eats"""
        _have_eaten = False
        try:
            for player_id, player in self.players.items():
                total_mass_to_eat = 0
                radius = mass_to_radius(player.mass)
                mass = player.mass
                for i, game_object in enumerate(game_objects[::-1]):  # We are going backwards to enable popping
                    if not mass >= game_object.mass * 1.25:  # if player's mass is not bigger than game_object's mass by
                        # at least 25%
                        continue

                    distance = get_distance(player.position, game_object.position)
                    if distance < radius:
                        # COLLISION!!!!
                        total_mass_to_eat += game_object.mass
                        if type(game_object) == Pallet:
                            self.remove_pallet(game_object)

                        elif type(game_object) == Player:
                            if player == self.client_player:
                                if str(game_object.id) not in player.players_eaten_id:
                                    player.players_eaten_id.append(str(game_object.id))
                                    _have_eaten = True
                                    self.remove_player(game_object)

                if total_mass_to_eat and player == self.client_player:
                    player.eat(total_mass_to_eat)
            return _have_eaten
        except RuntimeError:  # dictionary changed size during iteration
            return _have_eaten

    def spawn_new_pallet_in_camera_scope(self, camera):
        """Spawn a new pallet in the camera's scope. Just like the function name might suggest"""
        x = random.randint(int(camera.rect.x) - SPAWN_PALLET_EXTRA_RANGE,
                           int(camera.rect.x + camera.width - 1) + SPAWN_PALLET_EXTRA_RANGE)
        y = random.randint(int(camera.rect.y - SPAWN_PALLET_EXTRA_RANGE),
                           int(camera.rect.y + camera.height - 1) + SPAWN_PALLET_EXTRA_RANGE)
        new_pallet = Pallet((x, y))
        self.pallets.append(new_pallet)
        self.all_game_objects.append(new_pallet)
        return new_pallet

    def remove_pallet(self, pallet):
        """Remove a pallet"""
        try:
            self.all_game_objects.remove(pallet)
            self.pallets.remove(pallet)
        except ValueError:
            return

    def x_in_bounds(self, x):
        """Is x in bounds of game width"""
        return 0 < x < self.width

    def y_in_bounds(self, y):
        """Is y in bounds of game height"""
        return 0 < y < self.height

    def update_player_info(self, player_id, player_mass, player_position):
        """update a player's info"""
        player = self.players.get(player_id)
        if player is None:
            self.create_new_player(player_id, "", player_mass, player_position)
            return False
        player.mass = player_mass
        player.position = player_position
        return True

    def remove_player(self, player):
        """KILL A PLAYER!!"""
        del self.players[player.id]
        self.all_game_objects.remove(player)


class Camera:
    """A camera follows a specific player throughout the game."""

    def __init__(self, screen, game, player, camera_initial_width, camera_initial_height):
        """INITIALIZER!!!!!!!!!!!!!!!!!!!!!!!!!!"""
        self.screen = screen
        self.game = game
        self.player = player

        self.camera_initial_width = camera_initial_width
        self.camera_initial_height = camera_initial_height

        self.renderable_game_objects = game.all_game_objects

        self.width, self.height = camera_initial_width, camera_initial_height
        self.rect = pygame.Rect(0, 0, camera_initial_width, camera_initial_height)
        self.update_rect_position()

    def update_rect_position(self):
        """Update camera's rect position"""
        x, y = self.player.position

        rect_x = x - self.width // 2
        rect_x = max(0, rect_x)
        rect_x = min(self.game.width - self.width, rect_x)

        rect_y = y - self.height // 2
        rect_y = max(0, rect_y)
        rect_y = min(self.game.height - self.height, rect_y)

        self.rect.topleft = (rect_x, rect_y)
        return rect_x, rect_y

    def update_size(self):
        """update camera's size"""
        player_size = mass_to_radius(self.player.mass * 2)
        if self.camera_initial_height / player_size >= 2.5:
            return

        if self.height / player_size < 2.5:
            self.height *= 1.03
        elif self.height / player_size > 3:
            self.height /= 1.03

        self.width = self.height * ASPECT_RATIO

    def coords_from_game_to_camera(self, coords):
        """convert coords from the game to where they should be placed on the screen."""
        x, y = coords
        camera_x = self.rect.x
        camera_y = self.rect.y

        new_x = (x - camera_x) / self.width * SCREEN_WIDTH
        new_y = (y - camera_y) / self.height * SCREEN_HEIGHT

        return new_x, new_y

    def mass_to_camera_size(self, mass):
        """Converts a mass to pixel size on the screen"""
        return (mass / self.height) * SCREEN_HEIGHT

    def render(self):
        """Renders the game on the screen. Very important"""
        self.screen.fill(BACKGROUND_COLOR)

        self.renderable_game_objects = []
        for game_object in self.game.all_game_objects:
            if self.is_game_object_in_camera_bounds(game_object):
                game_object.draw(self)
                self.renderable_game_objects.append(game_object)

    def is_game_object_in_camera_bounds(self, game_object):
        """Checks if a game object is in camera bounds"""
        radius = game_object.mass
        x, y = game_object.position
        return self.rect.x - radius <= x <= self.rect.x + self.width + radius and \
            self.rect.y - radius <= y <= self.rect.y + self.height + radius

    def get_random_position_in_scope(self):
        """Gets a random position in the cameras scope"""
        x = random.randint(int(self.rect.x), int(self.rect.x + self.width - 1))
        y = random.randint(int(self.rect.y), int(self.rect.y + self.height - 1))
        return x, y


def get_distance(point1: (int, int), point2: (int, int)) -> float:
    """
    Calculates the distance between 2 points, by using pythagoras' theorem
    :param point1: point1
    :param point2: point2
    :return:
    """
    return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)


def draw_start_screen(screen):
    """Draw the start screen"""
    screen.blit(title_surface, title_rect)
    screen.blit(enter_username_surface, enter_username_rect)


def __input_to_change_player_name():
    global client_player_name
    while not (client_player_name_input := input("Enter username:\n")).isalpha():
        print("Please use alphabetical characters only (no spaces / numbers).")
    client_player_name = client_player_name_input


def async_input_player_name():
    """async input"""
    threading.Thread(target=__input_to_change_player_name).start()


def create_text(text, size, color, center=(0, 0), text_font=None):
    """creates a pygame text surface and a rect."""
    if text_font is None:
        text_font = pygame.font.Font('freesansbold.ttf', int(size))
    text_surface = text_font.render(text, False, color)
    text_rect = text_surface.get_rect()
    text_rect.center = center

    return text_surface, text_rect


# PYGAME SETUP
pygame.display.init()
pygame.font.init()

title_surface, title_rect = create_text("ROY.IO", SCREEN_WIDTH / 10, BLACK,
                                        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 10 * 2))

enter_username_surface, enter_username_rect = create_text("Enter username in console to start!", SCREEN_WIDTH / 30,
                                                          BLACK,
                                                          (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 10 * 3.5))

client_player_name = -1
async_input_player_name()

lock = threading.Lock()


def sync_game_data_with_server(game: Game):
    """sync game data with the server. ALL THE MAGIC HAPPENS HERE"""
    global lock, client, have_eaten, is_alive, client_player

    clock = pygame.time.Clock()
    while True:
        with lock:
            if is_alive:
                try:
                    if have_eaten:
                        client.send_request(
                            protocol.build_request(
                                protocol.Consts.Update.EAT,
                                protocol.VALUE_SEPERATOR.join(client_player.players_eaten_id)
                            )
                        )

                        confirmation = client.get_response()

                        have_eaten = False
                        client_player.players_eaten_id = []

                    # send player updated position
                    new_x, new_y = client_player.position
                    new_mass = client_player.mass
                    client.send_request(
                        protocol.build_request(
                            protocol.Consts.Update.MY_POSITION_AND_MASS,
                            f"{new_x}{protocol.VALUE_SEPERATOR}{new_y}",
                            new_mass
                        )
                    )

                    response = protocol.decrypt_response(client.get_response())
                    flag = int(response[0])
                    if flag == Consts.Error.YOURE_DEAD:
                        is_alive = False
                except TypeError:
                    is_alive = False
            # update players_ids, players_masses, players_positions,
            client.send_request(
                protocol.build_request(
                    protocol.Consts.Request.INFO
                )
            )

            info_response = client.get_response()
            players_ids, players_masses, players_x, players_y = protocol.decrypt_info_response(info_response)

            if len(players_ids) != len(game.players):
                # someone died.
                try:
                    for player in game.players.values():
                        if player == game.client_player:
                            # if the dead player is the client player
                            # if so then skip because it's handled somewhere else.
                            continue
                        if player.id not in players_ids:
                            game.remove_player(player)
                except RuntimeError:  # dictionary changed size during iteration, this is ok!! I promise
                    pass

            new_players = []
            for player_id, player_mass, player_x, player_y in zip(players_ids, players_masses, players_x, players_y):
                is_already_in_game = game.update_player_info(player_id, player_mass, (player_x, player_y))
                if not is_already_in_game:
                    new_players.append(str(player_id))

            # register new players
            if new_players:
                client.send_request(
                    protocol.build_request(
                        protocol.Consts.Request.NAMES,
                        protocol.VALUE_SEPERATOR.join(new_players)
                    )
                )

                response = client.get_response()
                player_names = protocol.decrypt_response(response)
                for player_id, player_name in zip(new_players, player_names):
                    player = game.players[int(player_id)]
                    player.name = player_name
                    player.name_surface, player.name_surface_rect = create_text(player.name, FONT_SIZE, WHITE)
                    player.name_surface_outline, player.name_surface_outline_rect = create_text(player.name,
                                                                                                FONT_SIZE + 1,
                                                                                                BLACK)
                    print("New player connected!")

            clock.tick(SERVER_UPDATE_POSITION_FPS)


def start_syncing_game_with_server(game):
    """Start a thread to sync the game data with the server"""
    t = threading.Thread(target=sync_game_data_with_server, args=[game])
    t.start()


client = Client(protocol.SERVER_IP)
have_eaten = False
is_alive = False
none_player = Player(None, None, None, None)
client_player = none_player


def send_server_quit_request():
    """asks server to quit"""
    client.send_request(
        protocol.build_request(
            Consts.Update.QUIT
        )
    )
    confirmation = client.get_response()


def main():
    """MAIN FUNCTION! WHICH MEANS I'M DONE WRITING COMMENTS AND FINALLY TURN IN THIS PROJECT"""
    global client, have_eaten, is_alive, client_player

    """Connect to server and receive starting data"""

    # request welcome info
    welcome_info_request = protocol.build_request(Consts.Request.WELCOME_INFO)
    client.send_request(welcome_info_request)
    response = client.get_response()
    GAME_WIDTH, GAME_HEIGHT, players_ids, players_names, players_masses = protocol.decrypt_welcome_info_response(
        response)

    """initiate game"""

    players = {player_id: Player(player_id, player_name, player_mass, (-100, -100))
               for player_id, player_name, player_mass in zip(players_ids, players_names, players_masses)}

    game = Game(GAME_WIDTH, GAME_HEIGHT, players)

    start_syncing_game_with_server(game)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ROY.IO")
    clock = pygame.time.Clock()

    CAMERA_INITIAL_HEIGHT = GAME_HEIGHT // 10
    CAMERA_INITIAL_WIDTH = CAMERA_INITIAL_HEIGHT * ASPECT_RATIO

    is_pressed = {'UP': False, 'RIGHT': False, 'DOWN': False, 'LEFT': False}

    random_player = game.get_random_player()

    camera = Camera(screen, game, random_player, CAMERA_INITIAL_WIDTH, CAMERA_INITIAL_HEIGHT)

    client_requests_to_join = True

    # Game loop.
    while True:
        if not is_alive and client_player_name != -1 and client_requests_to_join:
            is_alive = True
            client.send_request(
                protocol.build_request(
                    protocol.Consts.Request.SPAWN_NEW_PLAYER,
                    client_player_name
                )
            )
            response = client.get_response()
            client_player_id, start_mass, start_x, start_y = protocol.decrypt_spawn_a_new_player_response(response)
            client_player = game.create_new_player(client_player_id, client_player_name, start_mass, (start_x, start_y))
            game.client_player = client_player
            camera = Camera(screen, game, client_player, CAMERA_INITIAL_WIDTH, CAMERA_INITIAL_HEIGHT)
            client_requests_to_join = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                with lock:
                    send_server_quit_request()
                    if is_alive:
                        game.remove_player(client_player)
                        client_player = none_player
                        is_alive = False

                    pygame.quit()
                    os._exit(1)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not client_requests_to_join:
                        client_requests_to_join = True

                if event.key == pygame.K_w:
                    is_pressed['UP'] = True
                if event.key == pygame.K_d:
                    is_pressed['RIGHT'] = True
                if event.key == pygame.K_s:
                    is_pressed['DOWN'] = True
                if event.key == pygame.K_a:
                    is_pressed['LEFT'] = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    is_pressed['UP'] = False
                if event.key == pygame.K_d:
                    is_pressed['RIGHT'] = False
                if event.key == pygame.K_s:
                    is_pressed['DOWN'] = False
                if event.key == pygame.K_a:
                    is_pressed['LEFT'] = False

        if is_alive:
            # Update.
            new_pos = client_player.position
            if is_pressed['UP']:
                new_pos = new_pos[0], new_pos[1] - 1
            if is_pressed['RIGHT']:
                new_pos = new_pos[0] + 1, new_pos[1]
            if is_pressed['DOWN']:
                new_pos = new_pos[0], new_pos[1] + 1
            if is_pressed['LEFT']:
                new_pos = new_pos[0] - 1, new_pos[1]

            if game.x_in_bounds(new_pos[0]):
                client_player.position = new_pos[0], client_player.position[1]

            if game.y_in_bounds(new_pos[1]):
                client_player.position = client_player.position[0], new_pos[1]

        else:
            if camera.player == client_player:
                # JUST DIED. LMAO
                game.remove_player(client_player)
                client_player = none_player
                camera.player = game.get_random_player()

        # spawn more pallets
        if random.randint(0, FPS // PALLET_SPAWN_PER_SECOND) == 0:
            game.spawn_new_pallet_in_camera_scope(camera)

        camera.update_size()
        _have_eaten = game.check_for_collisions_and_eat(camera.renderable_game_objects)
        if _have_eaten:
            have_eaten = True
        camera.update_rect_position()

        # Render.
        camera.render()
        if not is_alive:
            draw_start_screen(screen)

        pygame.display.update()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
