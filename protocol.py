
PORT = 8821
SERVER_IP = "127.0.0.1"
board_length, board_height = 49, 41

FIELD_SEPERATOR = '/'
VALUE_SEPERATOR = '*'


class Consts:
    class Update:
        """client sends something to the server to update. returns none (only confirmation)."""

        MY_POSITION_AND_MASS = 9
        """
        updates client's position.
        """
        EAT = 8
        """
        Sends the server a list of player ids that client has eaten.
        """
        QUIT = 5
        """
        Client quit the game :(
        """

    class Request:
        WELCOME_INFO = 1
        """
        Inform that we are joining, and asks to add us to the game and receive all the info needed to start. 
        
        
        RETURNS:
        GAME_WIDTH, GAME_HEIGHT, players_ids, players_names, players_masses
        """

        SPAWN_NEW_PLAYER = 2
        """
        Request server to create a new player.
        par1= username
        
        RETURNS:
        new_player_id, start_mass, start_x, start_y
        """

        INFO = 3
        """
        client should request info every frame. consists of basic information of the current state of the game.
        
        RETURNS:
        players_ids, players_masses, players_x, players_y
        """
        NAMES = 4
        """
        when a new client joins, other clients have only ids of a him but not the name. they
        recognise it, and should ask the server for a name match to the id.
        
        par1= list of ids
        RETURNS:
        list of names (corresponding to the list of ids) 
        """

    class Confirm:
        CONFIRM = 7
        """
        Confirm that the data has indeed passed.
        """

    class Error:
        YOURE_DEAD = 6
        """
        error code: Client tried to update its location / mass when he is dead.
        """


def encrypt_players(players):
    """Encrypt the list of players"""
    encrypted_players = ""
    for player in players:
        encrypted_players += f"{player.name}|{player.color}|{player.mass}"
    return encrypted_players


def decrypt_board(encrypted_board):
    """Encrypt the board"""
    decrypted_board = []
    for y in range(board_height):
        line = []
        for x in range(board_length):
            line.append(encrypted_board[y * board_length + x])
        decrypted_board.append(line)
    return decrypted_board


def split_request(request):
    """Splits a request into OPERATION_NUMBER, ARG1, ARG2"""
    if len(request) < 2:
        return None, None, None

    OPERATION_NUMBER = request[0]
    arguments = request[1:].split(FIELD_SEPERATOR)
    if len(arguments) != 2:
        return None, None, None

    ARG1, ARG2 = arguments
    if not OPERATION_NUMBER.isdigit():
        return None, None, None

    return int(OPERATION_NUMBER), ARG1, ARG2


def build_request(operation_number, arg1="", arg2=""):
    """Build a general-purpose request. operation number must be 1 digit."""
    return f"{operation_number}{arg1}/{arg2}"


def is_iterable(arg) -> bool:
    """is arg iterable"""
    try:
        _ = iter(arg)
    except TypeError:
        return False
    return True


def build_response(*args):
    """Build a general-purpose response. Can not handle 2d arrays or more"""
    response = ""
    for arg in args:
        if is_iterable(arg):
            response += VALUE_SEPERATOR.join([str(element) for element in arg])
        else:
            response += str(arg)
        response += FIELD_SEPERATOR

    if response:
        return response[:-1]  # remove the last field seperator
    else:
        return response


def decrypt_response(response):
    """Decrypt a general-purpose response. Can not handle 2d arrays or more"""
    values = response.split(FIELD_SEPERATOR)
    for i, value in enumerate(values):
        if VALUE_SEPERATOR in value:
            values[i] = value.split(VALUE_SEPERATOR)
    return values


def string_list_to_other_type_of_list(string_list, type_of_value):
    """
    Turn a list of strings to a list of another type.
    For example:
    string_list: ['123', '0708'], type_of_value: int --> [123, 708]
    """
    if not string_list:
        return []
    if not type(string_list) == list:
        return [type_of_value(string_list)]
    return [type_of_value(value) for value in string_list]


def decrypt_welcome_info_response(response):
    """GAME_WIDTH, GAME_HEIGHT, players_ids, players_names, players_masses, client_player_id, start_x, start_y"""
    GAME_WIDTH, GAME_HEIGHT, players_ids, players_names, players_masses = decrypt_response(response)

    GAME_WIDTH = int(GAME_WIDTH)
    GAME_HEIGHT = int(GAME_HEIGHT)

    players_ids = string_list_to_other_type_of_list(players_ids, int)
    players_names = string_list_to_other_type_of_list(players_names, str)
    players_masses = string_list_to_other_type_of_list(players_masses, int)

    return GAME_WIDTH, GAME_HEIGHT, players_ids, players_names, players_masses


def decrypt_spawn_a_new_player_response(response):
    """Decrypt the spawn a new player response. it's in the name of the function"""
    client_player_id, start_mass, start_x, start_y = decrypt_response(response)

    client_player_id = int(client_player_id)
    start_mass = int(start_mass)
    start_x = int(start_x)
    start_y = int(start_y)

    return client_player_id, start_mass, start_x, start_y


def decrypt_info_response(info_response):
    """players_ids, players_masses, players_x, players_y"""
    players_ids, players_masses, players_x, players_y = decrypt_response(info_response)
    players_ids = string_list_to_other_type_of_list(players_ids, int)
    players_masses = string_list_to_other_type_of_list(players_masses, int)
    players_x = string_list_to_other_type_of_list(players_x, int)
    players_y = string_list_to_other_type_of_list(players_y, int)

    return players_ids, players_masses, players_x, players_y
