*Information about parsing .gzr files will be stored here if you ever wish to expand on the current approach, or add more.*
*0x02 refers to Red, 0x03 refers to Blue (teams)*
*Ensure the .gzr file has been decompressed (uses zlib)*

## Pattern identification (parser.py)
*Offset 0x10 (First byte)*
- Map name appears here in ASCII, parses from first valid byte until the next null byte (00)

*Offsets 0x30-0x80*
- Ladder:             \x00\x00\x00\x01\x00\x00\x00\xE7\x03\x00\x00\xC0\xD4\x01\x00
- Team Deathmatch:    \x01\x00\x00\x00\x14\x00\x00\x00\xE0\x93\x04\x00
- Deathmatch:         \x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x01
- Deathmatch:         \x1E\x00\x00\x00\x80\xEE\x36\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x01
- Season: *I originally thought this was accurate as it incremented from one season to another, however looking at files from the season afterwards, it went backwards again. I have it commented out in jsonify.py, I'm sure it represents something else that's somewhat important, I just don't know what.*

*Offsets, 0x110, 0x500, 0x900, 0xCF0, 0x10E0, 0x14E0, 0x18D0, 0x1CC0*
- These are fixed offsets in a Ladder 4v4 game for each player
- Skips null bytes
- Reads up to 32 characters until first null (00)
- Decode as UTF-8
- If name is under 3 characters, it doesn't include it
*Reads from the start of the player name, then 537 bytes forward for a 5 byte hex pattern. This is a player identification used in the match for tracking events.*

*Reads from the player name, up to 1000 bytes forward (this is more than enough), until it finds one of these*
- Normal SG (6/24):   \x00\x00\x00\x00\x18\x00\x00\x00\x06\x00\x00\x00\x18\x00\x00\x00\x06
- Heavy SG (3/12):    \x00\x00\x00\x00\x0C\x00\x00\x00\x03\x00\x00\x00\x0C\x00\x00\x00\x03

*Teams are located 91 bytes after shotgun pattern, either displayed with 0x02 or 0x03*
*Rounds can be detected with the pattern below, they appear many times throughout the file and hold important info in the header, IIRC the first 2 appearences will be the same round, so 1 is skipped*
- Round header:       \xDD\x05\x00\x00\x00\x00\x00
- Round ID is byte at marker, skip 11 bytes.
- Team winner is byte at marker, + 19 bytes where 0x01 = Red winning, 0x02 = Blue winning
*Also looks 65 bytes before the player name starts, if a 01 is found then that player is the file owner (player that recorded the replay), else not.*

*User extraction from rounds is done from looking after round header, and finding printable ASCII characters (0x20-0x7E), that follow a pattern as so:
- Printable character name, 0x20 (Space), Printable character name, 0x20 (Space) etc, until eventually we hit 0x00 (a null byte), which is when we stop parsing.
*This can be compared with the player names at the fixed offsets 2 blocks above, as spectators are included in this, and for some reason spectators sometimes have damage logged, meaning we can differentiate between spectators and actual players using this method*
- Damage value extraction is located 4 bytes after the username section ends (where the null byte was hit), and they're once again separated from spaces (0x20), and they appear in the same order as the usernames. E.G 7erryDavis JenKlopez    1000 200, in this example 7erryDavis would have 1000 damage, JenKlopez 200. (index positioning)

*Damage calculation*
- Total Damage: Look for the final appearing round in the .gzr file, and label it as the final round saving everyones damage. (this will break if player leaves early, so I might change it to instead look for a round where one side has 4 wins)
- Damage Gain: Current round damage - previous round damage, this is used for RVP (Round Valuable Player, player with the highest dmg increase)
- Average damage: Total damage divided by rounds played.

*Chat logs*
- Search for marker: \x00\x6D\xC3\x00
- The byte that follows this marker will be either:
- 0x00 (All chat)
- 0x02 (Red chat)
- 0x03 (Blue chat)
*To extract the message itself, look 10 bytes after the marker, and extract everything converting it to ASCII, until the first null byte (0x00)*

*Then search up to 28 bytes forward for a pattern that matches a players identification (00 {?? ?? ??} 00), the chat message belongs to this player*

---

## Jsonify.py
*This does calculations, it doesn't extract any information from the decompressed .gzr file itself, but instead use the already found data to make some more connections, including:*
- Match ID Tracking
- Universal Player IDs
- Player statistics with match history
- Round/Match team winner
- + Other data

## Main.py
*This is just a Flask file for the Web UI, if you don't want to use the Web UI then you can just run: python jsonify.py path/to/your/file, however it looks a lot cleaner if you just run main.py*
*Summary: Jsonify.py wrapper, with Web UI (pretty formatting)*
