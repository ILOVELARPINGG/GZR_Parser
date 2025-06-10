import sys
import json
from pathlib import Path
from datetime import datetime
from parser import decompress_gzr, extract_map, extract_all_chat_logs, extract_round_stats_with_damage_full, extract_players_from_offsets, extract_gamemode_and_season

ID_TRACKER_FILE = Path("../output/match_id.txt")
OUTPUT_DIR = Path("../output")
OUTPUT_DIR.mkdir(exist_ok=True)
UNIVERSAL_ID_FILE = Path("../output/universal_ids.json")  # This is for all player occurrences with an ID that increments, and their username.
STATS_PATH = Path("../output/player_stats.json")  # Creates a profile for all players that appear in the Ladder .gzr files, and averages their stats based on it. (+ match history, w/l etc.)

def load_universal_ids():
    if UNIVERSAL_ID_FILE.exists():
        with open(UNIVERSAL_ID_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_universal_ids(universal_ids):
    with open(UNIVERSAL_ID_FILE, 'w', encoding='utf-8') as f:
        json.dump(universal_ids, f, indent=2)

def load_player_stats():
    if STATS_PATH.exists():
        with open(STATS_PATH, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_player_stats(player_stats):
    with open(STATS_PATH, 'w', encoding='utf-8') as f:
        json.dump(player_stats, f, indent=2)

def load_match_id():
    if ID_TRACKER_FILE.exists():
        return int(ID_TRACKER_FILE.read_text().strip()) + 1
    return 1

# Saves ID to match_id.txt, start = 0 (Can be manually changed in the .txt to "0" for reset)
def save_match_id(match_id):
    ID_TRACKER_FILE.parent.mkdir(exist_ok=True)
    ID_TRACKER_FILE.write_text(str(match_id))

# Calculates win rate using wins / games x 100
def calculate_win_rate(wins, losses, draws, include_draws_as_half_win=False):
    total_games = wins + losses + draws
    
    if total_games == 0:
        return 0.0
    
    if include_draws_as_half_win:
        effective_wins = wins + (draws * 0.5)
        win_rate = (effective_wins / total_games) * 100
    else:
        games_with_result = wins + losses
        if games_with_result == 0:
            return 0.0
        win_rate = (wins / games_with_result) * 100
    
    return round(win_rate, 2)

def update_player_stats(player_stats, player_combined, mvp, rounds_info, match_id, map_name, chat_logs=None):
    round_mvps = {}
    for round_data in rounds_info:
        if round_data["rvp"]:
            if isinstance(round_data["rvp"], dict) and "name" in round_data["rvp"]:
                rvp_name = round_data["rvp"]["name"]
            elif isinstance(round_data["rvp"], str):
                rvp_name = round_data["rvp"]
            else:
                continue
                
            if rvp_name in round_mvps:
                round_mvps[rvp_name] += 1
            else:
                round_mvps[rvp_name] = 1
    
    # Process chat logs and count messages by player.
    chat_stats_by_player = {}
    if chat_logs:
        for log in chat_logs:
            player_name = log.get("player", "Unknown")
            if player_name != "Unknown":
                if player_name not in chat_stats_by_player:
                    chat_stats_by_player[player_name] = {
                        "total_messages": 0,
                        "all_chat": 0,
                        "team_chat": 0,
                        "messages_this_match": []
                    }
                
                chat_stats_by_player[player_name]["total_messages"] += 1
                
                if log["chat_type"] == "All":
                    chat_stats_by_player[player_name]["all_chat"] += 1
                else:  # Red or Blue team chat
                    chat_stats_by_player[player_name]["team_chat"] += 1
                
                # Store message for this match
                chat_stats_by_player[player_name]["messages_this_match"].append({
                    "type": log["chat_type"],
                    "message": log["message"],
                    "team": log["player_team"]
                })
    
    for player in player_combined:
        player_id = str(player["universal_id"])
        player_name = player["name"]
        
        # Initialize player if they don't exist.
        if player_id not in player_stats:
            player_stats[player_id] = {
                "name": player_name,
                "matches_played": 0,
                "team_counts": {"Red": 0, "Blue": 0},
                "total_damage": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_rate": 0.0,
                "win_rate_with_draws": 0.0,
                "mvp_count": 0,
                "rvp_count": 0,
                "rounds_played": 0,
                "total_average_damage": 0,
                "match_history": [],
                "chat_stats": {
                    "total_messages": 0,
                    "all_chat_messages": 0,
                    "team_chat_messages": 0,
                    "average_messages_per_match": 0.0,
                    "chat_history": []
                }
            }
        
        if player["team"] in player_stats[player_id]["team_counts"]:
            player_stats[player_id]["team_counts"][player["team"]] += 1
        else:
            player_stats[player_id]["team_counts"][player["team"]] = 1
        
        match_result = player["match_result"]
        if match_result == "Win":
            player_stats[player_id]["wins"] += 1
        elif match_result == "Loss":
            player_stats[player_id]["losses"] += 1
        else:
            player_stats[player_id]["draws"] += 1
        
        player_stats[player_id]["total_damage"] += player.get("total_damage", 0)
        player_stats[player_id]["rounds_played"] += player.get("rounds_played", 0)
        
        is_mvp = False
        if mvp:
            if isinstance(mvp, dict) and "name" in mvp:
                is_mvp = player_name == mvp["name"]
            elif isinstance(mvp, str):
                is_mvp = player_name == mvp
                
        if is_mvp:
            player_stats[player_id]["mvp_count"] += 1
        
        if player_name in round_mvps:
            player_stats[player_id]["rvp_count"] += round_mvps[player_name]
        
        # Update chat statistics
        if player_name in chat_stats_by_player:
            chat_data = chat_stats_by_player[player_name]
            player_stats[player_id]["chat_stats"]["total_messages"] += chat_data["total_messages"]
            player_stats[player_id]["chat_stats"]["all_chat_messages"] += chat_data["all_chat"]
            player_stats[player_id]["chat_stats"]["team_chat_messages"] += chat_data["team_chat"]
            
            # Add chat history for this match
            match_chat_record = {
                "match_id": match_id,
                "map": map_name,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "messages_count": chat_data["total_messages"],
                "all_chat_count": chat_data["all_chat"],
                "team_chat_count": chat_data["team_chat"],
                "messages": chat_data["messages_this_match"]
            }
            player_stats[player_id]["chat_stats"]["chat_history"].append(match_chat_record)
        
        player_stats[player_id]["matches_played"] += 1
        
        # Update average messages per match (Arguably the most important stat to track)
        if player_stats[player_id]["matches_played"] > 0:
            player_stats[player_id]["chat_stats"]["average_messages_per_match"] = round(
                player_stats[player_id]["chat_stats"]["total_messages"] / player_stats[player_id]["matches_played"], 2
            )

        if player_stats[player_id]["matches_played"] > 0:
            player_stats[player_id]["total_average_damage"] = (
                player_stats[player_id]["total_damage"] / player_stats[player_id]["rounds_played"] 
                if player_stats[player_id]["rounds_played"] > 0 else 0
            )
        
        player_stats[player_id]["win_rate"] = calculate_win_rate(
            player_stats[player_id]["wins"],
            player_stats[player_id]["losses"],
            player_stats[player_id]["draws"],
            include_draws_as_half_win=False
        )
        
        player_stats[player_id]["win_rate_with_draws"] = calculate_win_rate(
            player_stats[player_id]["wins"],
            player_stats[player_id]["losses"],
            player_stats[player_id]["draws"],
            include_draws_as_half_win=True
        )
        
        match_record = {
            "match_id": match_id,
            "map": map_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "team": player["team"],
            "result": match_result,
            "damage": player.get("total_damage", 0),
            "rounds_played": player.get("rounds_played", 0),
            "average_damage": player.get("average_damage", 0),
            "was_mvp": mvp and (
                (isinstance(mvp, dict) and "name" in mvp and player_name == mvp["name"]) or
                (isinstance(mvp, str) and player_name == mvp)
            ),
            "rvp_count": round_mvps.get(player_name, 0),
            "chat_messages_count": chat_stats_by_player.get(player_name, {}).get("total_messages", 0)
        }
        player_stats[player_id]["match_history"].append(match_record)
    
    return player_stats

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Use: python jsonify.py files/[file], ensure no spaces (E.G on Town II)")
        sys.exit(1)
    
    match_id = load_match_id()
    input_file = sys.argv[1]
    
    decompressed_path, error_message = decompress_gzr(input_file)
    
    universal_ids = load_universal_ids()
    player_stats = load_player_stats()

    if not decompressed_path:
        print(f"Failed to decompress: {error_message}")
        sys.exit(1)
    
    map_name = extract_map(decompressed_path)
    match_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    players, updated_universal_ids = extract_players_from_offsets(decompressed_path, universal_ids)
    save_universal_ids(updated_universal_ids)
    
    # Find the file owner's name.
    file_owner_name = None
    for player in players:
        if player.get("file_owner") == "yes":
            file_owner_name = player["name"]
            break
    
    # NOTE: Season logic isn't correct, I initially thought it was (it incremented from 76 to 77 between a season), but the season afterwards it went back down to 76, not sure. It's commented out in the JSON
    gamemode, season, gamemode_error = extract_gamemode_and_season(decompressed_path)
    if gamemode_error:
        print(f"Error: {gamemode_error}")
        decompressed_path.unlink(missing_ok=True)
        sys.exit(1)
        
    if gamemode != "Ladder":
        print(f"Error: The file contains a '{gamemode}' match, not a Ladder match. Processing stopped.")
        decompressed_path.unlink(missing_ok=True)
        sys.exit(1)
    
    rounds_info, score_red, score_blue, mvp, averages = extract_round_stats_with_damage_full(decompressed_path)
   
    chat_logs_raw = extract_all_chat_logs(decompressed_path)
    chat_logs = [{"type": t, "message": m} for t, m in chat_logs_raw]
   
    # Defining winner since I forgot to in logic.py (Higher score = Winner)
    def determine_winner():
        if score_red > score_blue:
            return "Red"
        elif score_blue > score_red:
            return "Blue"
        else:
            return "Draw"  # You can't draw in Ladder, but in case of player leaving before finish.
   
    average_damages = []
    for player_name, data in averages.items():
        average_damages.append({
            "player": player_name,
            "total_damage": data["total"],
            "rounds_played": data["rounds"],
            "average_damage": round(data["average"], 2)
        })
    match_winner = determine_winner()
    # Combining player_name with players, for a total summary. "if it works, don't fix it"
    player_combined = []
    damage_lookup = {item["player"]: item for item in average_damages}

    for player in players:
        player_name = player["name"]

        combined_player = {
            "universal_id": player["universal_id"],
            "name": player_name,
            "weapon": player["shotgun_type"],
            "team": player["team"]
        }
        
        if match_winner == "Red":
            if player["team"] == "Red":
                combined_player["match_result"] = "Win"
            elif player["team"] == "Blue":
                combined_player["match_result"] = "Loss"
            else:
                combined_player["match_result"] = "Draw"
        elif match_winner == "Blue":
            if player["team"] == "Blue":
                combined_player["match_result"] = "Win"
            elif player["team"] == "Red":
                combined_player["match_result"] = "Loss"
            else:
                combined_player["match_result"] = "Draw"
        else:
            # Once again, can't draw, but in-case player leaves early.
            combined_player["match_result"] = "Draw"
        
        if player_name in damage_lookup:
            damage_data = damage_lookup[player_name]
            combined_player.update({
                "total_damage": damage_data["total_damage"],
                "rounds_played": damage_data["rounds_played"],
                "average_damage": damage_data["average_damage"]
            })
        else:
            combined_player.update({
                "total_damage": 0,
                "rounds_played": 0,
                "average_damage": 0
            })

        player_combined.append(combined_player)
    
    processed_rounds = []
    for round_data in rounds_info:
        processed_players = []
        
        for player in round_data["players"]:
            processed_player = player.copy()
            
            matching_player = next((p for p in player_combined if p["name"] == player["name"]), None)
            
            if matching_player:
                processed_player["team"] = matching_player["team"]
            else:
                # If player isn't within the first 8 players that appear (The actual players, it's at the top of .gzr file hex), but they are elsewhere in the hex, then they're a spectator
                processed_player["team"] = "Spectator"
                # NOTE: Need to add a section in Flask app under match details for Spectators.
            processed_players.append(processed_player)
        
        processed_round = {
            "round_id": round_data["round_id"],
            "winner": round_data["winner"],
            "score": round_data["score"],
            "rvp": round_data["rvp"],
            "players": processed_players
        }
        processed_rounds.append(processed_round)

    if isinstance(mvp, dict) and "name" in mvp:
        dmg_data = damage_lookup.get(mvp["name"])
        if dmg_data:
            mvp["average_damage"] = dmg_data["average_damage"]
    elif isinstance(mvp, str):
        dmg_data = damage_lookup.get(mvp)
        if dmg_data:
            mvp = {
                "name": mvp,
                "average_damage": dmg_data["average_damage"]
            }
            
    updated_player_stats = update_player_stats(player_stats, player_combined, mvp, rounds_info, match_id, map_name, chat_logs_detailed)
    save_player_stats(updated_player_stats)

    match_json = {
        "Match": {
            "id": match_id,
            "date": match_date,
            "map": map_name,
            "gamemode": gamemode,
            "file_owner": file_owner_name,
            # Commented out, see line 164 as to why. "season": season,
            "winner": determine_winner(),
            "score": {
                "red": score_red,
                "blue": score_blue
            },
            "mvp": mvp,
            "players": player_combined,
            "rounds": processed_rounds,
            "chat_logs": chat_logs
        }
    }
   
    output_file = OUTPUT_DIR / f"{match_id}_{map_name}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(match_json, f, indent=2)
   
    print(f"Match JSON saved to {output_file}")
    print(f"Player stats updated in {STATS_PATH}")
    save_match_id(match_id)
