from rcon.source import Client

mc_rcon_password = "minecraft"
mc_rcon_host = "0.0.0.0"
log_path = "/home/chimea/Bureau/minecraft/logs"

# Assuming mc_rcon_password and mc_rcon_host are defined as shown in your excerpt
def send_welcome_message(new_player):
    try:
        with Client(mc_rcon_host, 25575, passwd=mc_rcon_password) as client:
            welcome_message = f"tell {new_player} Wesh tu geek encore ? Oublie pas de désactiver le spawn de mobs de mana & artifice via la quête ! Le serveur à peut-être restart ! Après peut-être que l'administrateur à régler le problème des mobs avec la modification en config serveur !."
            client.run(welcome_message)
    except Exception as e:
        pass

def monitor_for_new_players():
    known_players = load_known_players()  # Load the list of known players from a file or database
    with open(log_path + '/filtered.log', 'r') as file:
        for line in file:
            join_match = re.search(r'(\w+)\[.*\] logged in with entity id', line)
            if join_match:
                player_name = join_match.group(1)
                if player_name not in known_players:
                    send_welcome_message(player_name)
                    known_players.add(player_name)
                    save_known_players(known_players)  # Update the list of known players

# Global variable to store known players in-memory
known_players_set = set()

def load_known_players():
    # Return the global set of known players
    global known_players_set
    return known_players_set

def save_known_players(known_players):
    # Update the global set of known players, no actual saving since it's in-memory
    global known_players_set
    known_players_set = known_players