# Run main.py files/{file name}.gzr for Web UI, or jsonify.py if you're fine with reading plain JSON, output is in: ../output/
# TerryDavis/Fakecel/7erryDavis/Brad764IsACuck/egoist best GunZer to ever live, best programmer to ever live, best RE to ever live, best cybersec expert to ever live, best Xitter warrior to ever live, best Discordian to ever live, best com-kid to ever live, best music taste ever.
import zlib
import sys
from pathlib import Path

def is_gzr_file(file_path: str) -> bool:
    return Path(file_path).suffix.lower() == ".gzr"

def decompress_gzr(file_path):
    """Decompress the GZR file and return the path to the decompressed file or error message."""
    try:
        with open(file_path, 'rb') as f:
            compressed_data = f.read()
       
        try:
            # Decompress (zlib).
            decompressed_data = zlib.decompress(compressed_data)
           
            decompressed_dir = Path("../files/decompressed")
            decompressed_dir.mkdir(parents=True, exist_ok=True)
            
            original_path = Path(file_path)
            decompressed_filename = original_path.stem + '.bin'
            decompressed_path = decompressed_dir / decompressed_filename
            
            with open(decompressed_path, 'wb') as f:
                f.write(decompressed_data)
           
            return decompressed_path, None
           
        except zlib.error as e:
            return None, f"Zlib decompression failed: {e}"
        except Exception as e:
            return None, f"Decompression error: {str(e)}"
           
    except Exception as e:
        return None, f"File reading error: {str(e)}"

def extract_gamemode_and_season(file_path):
    # See Parsing.md for more info.
    ladder_pattern = b'\x00\x00\x00\x01\x00\x00\x00\xE7\x03\x00\x00\xC0\xD4\x01\x00'
    tdm_pattern = b'\x01\x00\x00\x00\x14\x00\x00\x00\xE0\x93\x04\x00'
    dm_patterns = [
        b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x01',
        b'\x1E\x00\x00\x00\x80\xEE\x36\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x01'
    ]
    gamemode = "Unknown"
    season = None
    try:
        with open(file_path, "rb") as f:
            f.seek(0x30)
            buffer = f.read(0x80 - 0x30)
            if ladder_pattern in buffer:
                gamemode = "Ladder"
            elif tdm_pattern in buffer:
                gamemode = "Team Deathmatch"
            elif any(pat in buffer for pat in dm_patterns):
                gamemode = "Deathmatch"
            f.seek(0x83)
            season_bytes = f.read(1)
            if season_bytes:
                season = season_bytes.hex()
            else:
                print("No bytes found at the extract_gamemode_and_season location.")
           
            return gamemode, season, None
       
    except Exception as e:
        return None, None, f"Error extracting gamemode or season: {e}"


def extract_map(file_path: Path):
    with open(file_path, 'rb') as f:
        data = f.read()

    # Map name starts at offset 0x10 and ends at the first null byte (00), then saves it for damage extraction afterwards.
    start = 0x10
    end = data.find(b'\x00', start)
    map_name = data[start:end].decode('utf-8', errors='ignore')
    
    return map_name

marker = b'\x00\x6D\xC3\x00'

def extract_round_stats_with_damage_full(file_path: Path):
    with open(file_path, 'rb') as f:
        data = f.read()

    marker = b'\xDD\x05\x00\x00\x00\x00\x00'
    rounds = {}
    round_damage_data = {}
    i = 0
    first_skipped = False
    player_rounds = {}  # For average damage calculation.
    score_red = 0
    score_blue = 0
    previous_damages = {}
    rounds_info = []

    while i < len(data):
        i = data.find(marker, i)
        if i == -1:
            break

        try:
            round_info_start = i + len(marker)
            round_id = data[round_info_start + 4]
            team_win = data[round_info_start + 12]

            if not first_skipped:
                first_skipped = True
                i += len(marker)
                continue

            if round_id not in rounds:
                rounds[round_id] = team_win

                username_start = round_info_start
                while username_start < len(data):
                    if 0x20 <= data[username_start] <= 0x7E:
                        if all(0x20 <= b <= 0x7E for b in data[username_start:username_start+3]):
                            break
                    username_start += 1

                usernames = []
                name_bytes = b""
                j = username_start

                while j < len(data):
                    byte = data[j]
                    if byte == 0x20:
                        try:
                            name = name_bytes.decode('utf-8').strip()
                            if name:
                                usernames.append(name)
                        except:
                            pass
                        name_bytes = b""
                    elif byte == 0x00:
                        if name_bytes:
                            try:
                                name = name_bytes.decode('utf-8').strip()
                                if name:
                                    usernames.append(name)
                            except:
                                pass
                        break
                    else:
                        name_bytes += bytes([byte])
                    j += 1

                damage_start = j + 4
                damage_values = []
                damage_bytes = b""
                k = damage_start

                while k < len(data):
                    byte = data[k]
                    if byte == 0x20:
                        try:
                            num = damage_bytes.decode('utf-8').strip()
                            if num.isdigit():
                                damage_values.append(int(num))
                        except:
                            pass
                        damage_bytes = b""
                    elif byte == 0x00:
                        if damage_bytes:
                            try:
                                num = damage_bytes.decode('utf-8').strip()
                                if num.isdigit():
                                    damage_values.append(int(num))
                            except:
                                pass
                        break
                    else:
                        damage_bytes += bytes([byte])
                    k += 1

                if damage_values:
                    round_damage_data[round_id] = {
                        'usernames': usernames,
                        'damage': damage_values
                    }

        except IndexError:
            break

        i += len(marker)

    for rid in sorted(rounds):
        winner_code = rounds[rid]
        winner = "Red" if winner_code == 0x01 else "Blue" if winner_code == 0x02 else f"Unknown ({winner_code:02X})"

        if winner == "Red":
            score_red += 1
        elif winner == "Blue":
            score_blue += 1

        if rid in round_damage_data:
            data = round_damage_data[rid]
            usernames = data['usernames']
            damage_values = data['damage']
            count = min(len(usernames), len(damage_values))

            leap = {}
            for i in range(count):
                name = usernames[i]
                dmg = damage_values[i]
                prev = previous_damages.get(name, 0)
                leap[name] = dmg - prev
                previous_damages[name] = dmg

            players = []
            for i in range(count):
                name = usernames[i]
                dmg = damage_values[i]
                
                players.append({ 
                    "name": name, 
                    "damage": dmg,
                    "damage_gain": leap[name]
                })

                if name not in player_rounds:
                    player_rounds[name] = 0
                player_rounds[name] += 1

            # Find RVP (Round Valuable Player) - highest damage gain in this round.
            if leap:
                rvp_name = max(leap.items(), key=lambda x: x[1])[0]
                rvp_damage = leap[rvp_name]
            else:
                rvp_name = ""
                rvp_damage = 0

            rounds_info.append({
                "round_id": rid,
                "winner": winner,
                "score": f"{score_blue}-{score_red}",
                "players": players,
                "rvp": { "name": rvp_name, "damage_gain": rvp_damage }
            })

    latest_total_damage = {}
    for round_data in round_damage_data.values():
        usernames = round_data["usernames"]
        damages = round_data["damage"]
        for i in range(min(len(usernames), len(damages))):
            name = usernames[i]
            dmg = damages[i]
            latest_total_damage[name] = dmg

    averages = {}
    for name, total in latest_total_damage.items():
        rounds = player_rounds.get(name, 1)
        avg = total / rounds
        averages[name] = {
            "total": total,
            "rounds": rounds,
            "average": avg
        }

    if latest_total_damage:
        mvp_name = max(latest_total_damage.items(), key=lambda x: x[1])[0]
        mvp = {
            "name": mvp_name,
            "damage": latest_total_damage[mvp_name]
        }
    else:
        mvp = { "name": "", "damage": 0 }

    return rounds_info, score_red, score_blue, mvp, averages


def extract_chat_logs(data: bytes, players):
    if not players:
        raise ValueError("Players list is required for chat log extraction")
    
    marker = b'\x00\x6D\xC3\x00'
    chat_logs = []
    pos = 0
    total = len(data)
    
    # Create lookup for player markers
    player_markers = {}
    for player in players:
        if player.get('five_bytes_data') and player['five_bytes_data'] != "N/A":
            try:
                marker_bytes = bytes.fromhex(player['five_bytes_data'])
                player_markers[marker_bytes] = player
            except ValueError:
                continue
    
    while pos < total - 12:
        idx = data.find(marker, pos)
        if idx == -1:
            break
            
        chat_type = data[idx + 4]
        if chat_type not in (0x00, 0x02, 0x03):
            pos = idx + 1
            continue
            
        label = {
            0x00: 'All',
            0x02: 'Red',
            0x03: 'Blue'
        }[chat_type]
        
        # The message typically starts after 00 6D C3 00 [label] 00 00 00 ?? 00 => offset + 10
        message_start = idx + 10
        message_bytes = b''
        message_end = message_start
        
        while message_end < total and data[message_end] != 0x00:
            message_bytes += bytes([data[message_end]])
            message_end += 1
        
        words = message_bytes.split(b'\x20')
        message = ' '.join(w.decode('utf-8', errors='ignore') for w in words if w)
        
        # Search for player marker near chat message (The same ID defined in the extract_players_from_offsets function)
        player = None
        search_start = message_end + 1
        search_end = min(search_start + 28, total)
        
        for search_pos in range(search_start, search_end - 4):
            for marker_bytes, player_info in player_markers.items():
                if len(marker_bytes) == 5:
                    if data[search_pos:search_pos + 5] == marker_bytes:
                        player = player_info
                        break
            if player:
                break
        
        # Create chat log entry with player info.
        chat_log = {
            "chat_type": label,
            "message": message,
            "marker_position": f"0x{idx:X}",
            "message_start": f"0x{message_start:X}",
            "message_end": f"0x{message_end:X}",
            "message_length": len(message_bytes),
            "player": player['name'] if player else "Unknown",
            "player_team": player['team'] if player else "Unknown",
            "player_universal_id": player['universal_id'] if player else "Unknown",
            "player_marker": player['five_bytes_data'] if player else "N/A"
        }
        
        chat_logs.append(chat_log)
        pos = message_end + 1
    
    return chat_logs

def extract_all_chat_logs(file_path, players):
    if not players:
        raise ValueError("Players list is required for chat log extraction")
        
    with open(file_path, 'rb') as f:
        data = f.read()
    
    chat_logs = extract_chat_logs(data, players)
    return chat_logs

def extract_complete_match_data(file_path):
    # First extract players.
    players, universal_ids = extract_players_from_offsets(file_path)
    
    # Then extract chat logs with player correlation.
    chat_logs = extract_all_chat_logs(file_path, players)
    
    return players, chat_logs

def extract_players_from_offsets(file_path, universal_ids=None):
    if universal_ids is None:
        universal_ids = {}
    offsets = [0x110, 0x500, 0x900, 0xCF0, 0x10E0, 0x14E0, 0x18D0, 0x1CC0]
    pattern_1 = b'\x00\x00\x00\x00\x18\x00\x00\x00\x06\x00\x00\x00\x18\x00\x00\x00\x06' # Normal SG (6/24, I think 96 max dmg)
    pattern_2 = b'\x00\x00\x00\x00\x0C\x00\x00\x00\x03\x00\x00\x00\x0C\x00\x00\x00\x03' # Heavy sg (3/12 I think, not sure max dmg)
    
    def check_file_owner(f, name_start_pos):
        """Check if there's a 01 byte 65 positions before the player name start"""
        try:
            # 65 bytes before the name start position.
            check_pos = name_start_pos - 65 
            if check_pos < 0:
                return "no"
            
            current_pos = f.tell()
            f.seek(check_pos)
            byte_value = f.read(1)
            f.seek(current_pos)
            
            return "yes" if byte_value == b'\x01' else "no"
        except:
            return "no"
    
    players = []
    with open(file_path, "rb") as f:
        for offset in offsets:
            try:
                f.seek(offset)
               
                while True:
                    byte = f.read(1)
                    if not byte or byte != b'\x00':
                        break
                
                # 1st byte already read (So -1)
                name_start_pos = f.tell() - 1
                
                name_bytes = bytearray()
                if byte and byte != b'\x00':
                    name_bytes += byte
               
                max_length = 32
                for _ in range(max_length):
                    byte = f.read(1)
                    if not byte or byte == b'\x00':
                        break
                    name_bytes += byte
               
                def decode_name(nb):
                    return nb.decode('utf-8', errors='replace').strip()

                player_name = decode_name(name_bytes)

                if not player_name or len(player_name) < 3:
                    f.seek(offset)
                    while True:
                        byte = f.read(1)
                        if not byte or byte != b'\x00':
                            break
                    while byte and byte < b'\x20':
                        byte = f.read(1)
                    
                    name_start_pos = f.tell() - 1
                    
                    name_bytes = bytearray()
                    if byte and byte >= b'\x20':
                        name_bytes += byte
                    for _ in range(max_length):
                        byte = f.read(1)
                        if not byte or byte == b'\x00':
                            break
                        name_bytes += byte

                    player_name = decode_name(name_bytes)

                    if not player_name or len(player_name) < 3:
                        continue

                current_pos = f.tell()
                max_search = 1000
                pattern_found = False
                which_pattern = None
               
                for _ in range(max_search):
                    current_pos = f.tell()
                    search_buffer = f.read(len(pattern_1))
                    
                    if not search_buffer or len(search_buffer) < len(pattern_1):
                        break
                   
                    if search_buffer == pattern_1: # Normal SG.
                        pattern_found = True
                        which_pattern = 1
                        break
                    elif search_buffer == pattern_2: # Heavy SG.
                        pattern_found = True
                        which_pattern = 2
                        break
                   
                    f.seek(current_pos + 1)
               
                player_team = None
                shotgun_type = None
                if pattern_found:
                    if which_pattern == 1:
                        shotgun_type = "Normal SG (6/24)"
                    elif which_pattern == 2:
                        shotgun_type = "Heavy SG (3/12)"

                    f.seek(f.tell() + 91)  # The pattern + 92 bytes = 02 (Red) or 03 (Blue) indicating team.
                    team_byte = f.read(1)
                    if team_byte == b'\x02':
                        player_team = "Red"
                    elif team_byte == b'\x03':
                        player_team = "Blue"
                    else:
                        player_team = f"Unknown ({int.from_bytes(team_byte, byteorder='little') if team_byte else 'null'})"

                # Seeks 537 bytes after the name start position, this is for player identification across the file.
                marker_pos = name_start_pos + 537
                f.seek(marker_pos)
                five_bytes = f.read(5)
                five_bytes_hex = five_bytes.hex().upper() if five_bytes else "N/A"

                if player_name not in universal_ids:
                    next_id = 1
                    if universal_ids:
                        next_id = max(int(id) for id in universal_ids.values()) + 1
                    universal_ids[player_name] = str(next_id)
                
                file_owner_status = check_file_owner(f, name_start_pos)
                   
                player_info = {
                    "name": player_name,
                    "team": player_team,
                    "universal_id": universal_ids[player_name],
                    "shotgun_type": shotgun_type,
                    "five_bytes_data": five_bytes_hex,
                    "file_owner": file_owner_status # File owner = Player name that recorded the .gzr file, I had to speculate considering nobody else would respond to my begging of a FxpGunZ Ladder .gzr file (Fuck you guys)
                }
                players.append(player_info)
           
            except Exception as e:
                print(f"Error reading offset 0x{offset:X}: {e}")
                continue
   
    return players, universal_ids

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please use main.py, if you insist on running this then: cd src -> python parser.py path_to_gzr_file/")
    else:
        file_path = sys.argv[1]
       
        if not is_gzr_file(file_path):
            print(f"Error: '{file_path}' is not a .gzr file. Processing stopped.")
            sys.exit(1)
           
        decompressed_path, decompress_error = decompress_gzr(file_path)
        if not decompressed_path:
            print(f"Failed to decompress the file: {decompress_error}. Processing stopped.")
            sys.exit(1)
           
        # Checking if gamemode = ladder.
        gamemode, season, gamemode_error = extract_gamemode_and_season(decompressed_path)
        if gamemode_error:
            print(f"Error: {gamemode_error}. Processing stopped.")
            decompressed_path.unlink(missing_ok=True)
            sys.exit(1)
            
        if gamemode != "Ladder":
            print(f"Error: The file contains a '{gamemode}' match, not a Ladder match. Processing stopped.")
            decompressed_path.unlink(missing_ok=True)  
            sys.exit(1)
           
        # Continue with processing since file is .gzr and gamemode is Ladder.
        print(f"Processing Ladder match.")
        
        map_name = extract_map(decompressed_path)
        print(f"Map: {map_name}")
        
        rounds_info, score_red, score_blue, mvp, averages = extract_round_stats_with_damage_full(decompressed_path)
        
        print("\nExtracted Round Results:")
        for round_info in rounds_info:
            print(f"Round {round_info['round_id']}: {round_info['winner']} won ({round_info['score']})")
            print(f"  RVP: {round_info['rvp']['name']} (+{round_info['rvp']['damage_gain']})")
            print(f"  Players ({len(round_info['players'])}):")
            for i, player in enumerate(round_info['players'], 1):
                print(f"    {i}. {player['name']:<20} → {player['damage']} dmg (+{player['damage_gain']})")
        
        print(f"\nFinal Score: {score_blue}-{score_red}")
        
        print(f"MVP: {mvp['name']} with {mvp['damage']} total damage")
        
        print("\nAverage Damage Per Round:")
        for name, data in averages.items():
            print(f"  {name:<20} → {data['average']:.2f} dmg/round (Total: {data['total']} over {data['rounds']} rounds)")
        
        chat_logs = extract_all_chat_logs(decompressed_path)
        print(f"\nChat Logs ({len(chat_logs)}):")
        for label, message in chat_logs:
            print(f"  [{label}] {message}")
