import random
import threading
import protocol
from protocol import Consts
from server_server import Server

import pygame

PLAYER_INITIAL_MASS = 100


class GameObject:
    """a parent class that represents a game object."""

    def __init__(self, position):
        """initializer"""
        self.position = position
        self.mass = 0


class Player(GameObject):
    """A player game object"""

    def __init__(self, name, player_id, position):
        """initializer"""
        super().__init__(position)
        self.name = name
        self.id = player_id
        self.mass = PLAYER_INITIAL_MASS

    def eat(self, mass):
        """eat mass"""
        self.mass += mass


class Game:
    """The game itself"""

    def __init__(self, width, height):
        """initializer"""
        self.width = width
        self.height = height
        self.players = []
        self.pallets = []
        self.viruses = []
        self.all_game_objects = []  # sorted from the smallest mass to the highest mass
        self.last_player_id = 0  # initial value should be 0, but starts from 1.

    def create_new_player(self, name):
        """Create a new player with random position, and add it to the game"""
        self.last_player_id += 1

        x = random.randint(self.width // 10, self.width // 10 * 9)
        y = random.randint(self.height // 10, self.height // 10 * 9)
        position = (x, y)
        # print(position)
        new_player = Player(name, self.last_player_id, position)
        self.players.append(new_player)
        self.all_game_objects.append(new_player)
        return new_player

    def create_new_fake_player(self):
        """Create a new player with random spanish name, and add it to the game
        He can not eat other players, but they can eat him. he is a bot.
        """

        random_name = random.choice(
            ["Hola, ¿Qué hora es?", "¿Y tú?", "Mucho gusto por favor", "¿Qué tal?", "Nos vemos", "Por favor", "Gracias",
             "De nada",
             "Disculpa", "No me gusta", "¿Cuánto cuesta?", "¿Dónde está el baño?", "¿Qué hora es?", "Me puede ayudar"])
        fake_player = Player(random_name, 0, (100, 100))
        self.players.append(fake_player)
        self.all_game_objects.append(fake_player)

    def update_player_position(self, player_id, position):
        """updates a given players' position"""
        self.get_player_by_ID(player_id).position = position

    def decrease_all_players_mass(self):
        """Every second, every player's mass decreases by 0.97%"""

        for player in self.players:
            change_in_mass_every_second = player.mass * 0.01
            change_in_mass_every_frame = change_in_mass_every_second / FPS
            if player.mass - change_in_mass_every_frame < PLAYER_INITIAL_MASS:
                continue
            else:
                player.mass -= change_in_mass_every_frame

    def get_random_player(self):
        """
        :return: a random living player
        """
        return self.players[random.randint(0, len(self.players) - 1)]

    def get_player_by_ID(self, player_id):
        """
        :param: player_id: id
        :return: player with this id
        """
        return self.players[player_id]

    def remove_player(self, index=None, player=None):
        """kill a player"""
        if index is not None:
            self.players.pop(index)
        elif player is not None:
            self.players.remove(player)


def start_connecting_clients(server):
    """Start a thread to connect clients"""
    thread = threading.Thread(target=connect_clients_thread, args=[server])
    thread.start()


def connect_clients_thread(server):
    """infinite loop to create connections"""
    while True:
        client_socket, client_address = server.connect_client()
        # print(f"new client: {client_address}")
        create_a_new_client_thread(server, client_socket)


def create_a_new_client_thread(server, client_socket):
    """Create a thread to handle the client"""
    thread = threading.Thread(target=handle_client, args=[server, client_socket])
    thread.start()
    threads.append(thread)


def handle_client(server: Server, client_socket):
    """Handle all client requests"""
    client_player = Player
    is_client_alive = False
    player_quit = False
    while client_socket:
        request = server.receive(client_socket)
        operation_number, par1, par2 = protocol.split_request(request)
        response = None
        if operation_number == Consts.Request.WELCOME_INFO:
            if not game.players:
                game.create_new_fake_player()
            players_ids, players_names, players_masses = [], [], []
            for player in game.players:
                players_ids.append(int(player.id))
                players_names.append(player.name)
                players_masses.append(int(player.mass))

            response = protocol.build_response(
                game.width, game.height, players_ids, players_names, players_masses
            )

        elif operation_number == Consts.Request.SPAWN_NEW_PLAYER:
            new_player_name = par1
            new_player = game.create_new_player(new_player_name)
            client_player = new_player
            is_client_alive = True
            response = protocol.build_response(
                new_player.id, new_player.mass, new_player.position[0], new_player.position[1]
            )

        elif operation_number == Consts.Update.MY_POSITION_AND_MASS:
            if client_player in game.players:
                update_x, update_y = par1.split(protocol.VALUE_SEPERATOR)
                update_x, update_y = int(update_x), int(update_y)
                update_mass = int(par2)

                client_player.position = (update_x, update_y)
                client_player.mass = update_mass
                response = protocol.build_response(protocol.Consts.Confirm.CONFIRM)
            else:
                response = protocol.build_response(protocol.Consts.Error.YOURE_DEAD)

        elif operation_number == Consts.Request.INFO:
            players_ids, players_masses, players_x, players_y = [], [], [], []
            for player in game.players:
                players_ids.append(int(player.id))
                players_masses.append(int(player.mass))
                x, y = player.position
                players_x.append(x)
                players_y.append(y)

            response = protocol.build_response(
                players_ids, players_masses, players_x, players_y
            )

        elif operation_number == Consts.Request.NAMES:
            requested_names_id_list = par1.split(protocol.VALUE_SEPERATOR)
            requested_names_id_list = protocol.string_list_to_other_type_of_list(requested_names_id_list, int)
            players_names = []
            for requested_name_id in requested_names_id_list:
                for player in game.players:
                    if player.id == requested_name_id:
                        players_names.append(player.name)
                        break

            response = protocol.build_response(players_names)

        elif operation_number == Consts.Update.EAT:
            eaten_players_id = par1.split(protocol.VALUE_SEPERATOR)
            eaten_players_id = protocol.string_list_to_other_type_of_list(eaten_players_id, int)
            for i, player in enumerate(game.players):
                if player.id in eaten_players_id:
                    game.remove_player(i)
                    if player == client_player:
                        client_player = Player
                        is_client_alive = False

            response = protocol.build_response(protocol.Consts.Confirm.CONFIRM)

        elif operation_number == Consts.Update.QUIT:
            if is_client_alive:
                game.remove_player(player=client_player)
            response = protocol.build_response(protocol.Consts.Confirm.CONFIRM)
            player_quit = True

        if response is not None:
            # with lock:
            server.send(
                client_socket,
                response
            )
        else:
            print("WOW!!!!!! ERORRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR")
            print(request)
            print(operation_number, par1, par2)

        if player_quit:
            client_socket.close()
            client_socket = None
    print("now i dont handle client anymore :(")


threads = []
lock = threading.Lock()

# CONSTANTS
FPS = 10
GAME_WIDTH, GAME_HEIGHT = 700, 700

game = Game(GAME_WIDTH, GAME_HEIGHT)
game.create_new_fake_player()  # for entertainment


def main():
    global game
    server = Server(host="0.0.0.0", port=protocol.PORT)
    print("Server is up up and running!")

    start_connecting_clients(server)

    pygame.init()
    clock = pygame.time.Clock()
    while True:
        game.decrease_all_players_mass()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
