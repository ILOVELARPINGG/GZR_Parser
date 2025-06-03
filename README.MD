# Overview
*(Scroll to bottom for usage guide)*
This is a FxpGunZ specific Replay-File (.gzr) parser, extracting useful and important data seen within the match. I plan to expand this in order to falsify cheating/in-game comm abuse, since these braindead Brazilians can't stay quiet. <3

See: Parsing.MD for parsing info guide.

*Sharp, CO5INE, unban me from your Discord and unmute me in-game, else your Server is DOOMED. I repeat, DOOMED. I will ask Lil B to curse this server for eternity, leaving it to perish.*

## Features
- Player stat profiling for all users that appear within the files (output/player_stats.json)
- Specific match, round and user-specific stats.

## Logged stats
### match
- Map name
- Gamemode (Parsing only supports Ladder, however differentiation in the hex for TDM/DM can be found in the parser)
- Winning team
- Score
- MVP (Player with highest damage)
- Players:
Username, Shotgun Type (Heavy/Small), Team, Win/Loss, Total Damage, Rounds played, Average damage (Also detects spectators)
- Round-logs
Players, RVP (Highest damage gain), Winning team, Current score, Player damage, Player damage gain, Player win/loss, Player team
- Chat-logs
Chat type (Red team, Blue team or All chat), order of which they appear in game. NOTE: Does not include usernames or date (Scroll down for reason)

### user-specific stats
This is for logging of all users that have appeared within the replay files, including these stats:
- Incrementing ID 
- Username
- Matches played
- Win/Losses (Including teams, e.g Blue 2, Red 0)
- Total damage in all Matches
- MVP Count
- RVP Count
- Average damage per round
- Match History (Including: Match ID, Date, Map Name, Gamemode, Win/Loss, Score, Total Damage, Average Damage, Rounds Played, MVP/RVP Count)

## Usage:
*Ensure you run -- pip install -r requirements.txt -- this will install all needed dependencies*
- After installing all dependencies, cd to src/ and run: python main.py, this will open the Web UI allowing you to drag and drop, or select, Ladder .gzr files and get an easily readable output. If it does not automatically open the Web UI and yet you have ran the file, then check your terminal and head to the localhost port that it states. E.G http://localhost:5000
- If you do not want to use the Web UI, then simply cd to src/ again, and run python jsonify.py X, where X is the location of the .gzr file you want to parse, the output is located in output/ with the map name, and ID as the title of the JSON.

*You can find an example .gzr file in files/, this can be used for testing either option. Either select that in the Web UI, or run python main.py ../files/example_replay.gzr*

### Notes:
- The data is mostly gargled nonsense, it contains tons of random dogshit making it somewhat difficult to extract specific events.
- I couldn't find a way to correlate any data to Kills/Deaths, which is why it's lacking in that aspect (despite it being somewhat important), and yet I could quite easily find the difference between Normal SG/Heavy SG, reinforcing my point above.
- Chat logs only state which chat it was sent in (Red/Blue team chat, or all chat), and the message in the order of which it appears. It has no date or user logging as it wasn't obvious in the hex.