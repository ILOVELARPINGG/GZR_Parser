# Run this file after installing requirements.txt for Web UI, or run jsonify.py followed by a path to your Ladder Replay if you're fine with reading plain data from .json.
from flask import Flask, request, jsonify, send_from_directory, render_template_string, render_template, send_file
import os
import subprocess
import json
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "src" / "templates"),
    static_folder=str(BASE_DIR / "src" / "static")
)

# This is just for banner backgrounds within match logs, if you don't want them then delete this section, the related functions below, and alter the JS in match_detail.html (otherwise Flask will be requesting something that doesn't exist)
MAP_CONFIG = {
    'mansion': {
        'banner': '/static/assets/banners/mansion_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
    'factory': {
        'banner': '/static/assets/banners/factory_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
    'awp_india': {
        'banner': '/static/assets/banners/awp_india_banner.jpg',
        'font_color': "#ffffff",
        'shadow_color': '0, 0, 0, 0.0'
    },
    'burgh': {
        'banner': '/static/assets/banners/burgh_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'castle': {
        'banner': '/static/assets/banners/castle_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'city': {
        'banner': '/static/assets/banners/city_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'city ii': {
        'banner': '/static/assets/banners/city2_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'control center': {
        'banner': '/static/assets/banners/control_center_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'dungeon': {
        'banner': '/static/assets/banners/ungeon_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'fight club': {
        'banner': '/static/assets/banners/fight_club_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'garden': {
        'banner': '/static/assets/banners/garden_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'high haven': {
        'banner': '/static/assets/banners/high_haven_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'industry': {
        'banner': '/static/assets/banners/industry_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'island': {
        'banner': '/static/assets/banners/island_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'lost shrine': {
        'banner': '/static/assets/banners/lost_shrine_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'port': {
        'banner': '/static/assets/banners/port_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'property': {
        'banner': '/static/assets/banners/property_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'suburbs': {
        'banner': '/static/assets/banners/suburbs_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'temple': {
        'banner': '/static/assets/banners/temple_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'town': {
        'banner': '/static/assets/banners/town_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'town ii': {
        'banner': '/static/assets/banners/town2_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'village': {
        'banner': '/static/assets/banners/village_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'village ii': {
        'banner': '/static/assets/banners/village2_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
        'weaponshop': {
        'banner': '/static/assets/banners/weaponshop_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    },
    'default': {
        'banner': '/static/assets/banners/default_banner.jpg',
        'font_color': '#ffffff',
        'shadow_color': '0, 0, 0, 0.0'
    }
}


UPLOAD_FOLDER = BASE_DIR / 'files' # .gzr files are temporarily stored here when uploaded, then parsed into /decompressed
OUTPUT_FOLDER = BASE_DIR / 'output' # Parsed matches, incrementing match id, player stats, I think I forgot 1 last thing idk+dc.
TEMPLATES_DIR = Path(__file__).resolve().parent / 'templates'  # HTML Files
ALLOWED_EXTENSIONS = {'gzr'}
EXCLUDED_FILES = {'player_stats.json', 'universal_ids.json'}

# Ensures these directories exist.
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_recent_matches(limit=None):
    try:
        json_files = [f for f in OUTPUT_FOLDER.glob('*.json') if f.name not in EXCLUDED_FILES]
        if not json_files:
            return []
       
        # Sort by creation time (most recent first)
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
       
        matches = []
        files_to_process = json_files if limit is None else json_files[:limit]
        
        for json_file in files_to_process:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    match_data = data.get('Match', {})
                   
                    mvp = match_data.get('mvp', 'N/A')
                    if isinstance(mvp, dict) and 'name' in mvp:
                        mvp = mvp['name']
                    elif not isinstance(mvp, str):
                        mvp = 'N/A'
                   
                    score = match_data.get('score', {})
                    score_text = f"{score.get('red', 0)}–{score.get('blue', 0)}"

                    # Match upload logs.
                    matches.append({
                        'id': match_data.get('id', 'N/A'),
                        'map': match_data.get('map', 'Unknown'),
                        'winner': match_data.get('winner', 'Unknown'),
                        'score': score_text,
                        'mvp': mvp,
                        'date': match_data.get('date', 'Unknown')[:10]
                    })
            except (json.JSONDecodeError, KeyError, Exception) as e:
                print(f"Error reading {json_file}: {e}")
                continue
       
        return matches
    except Exception as e:
        print(f"Error getting recent matches: {e}")
        return []


def find_match_file(match_id):
    try:
        # Get all JSON files except both player_stats.json and that other .json file I keep forgetting. (I have them all deleted and can't be bothered to rerun)
        json_files = [f for f in OUTPUT_FOLDER.glob('*.json') if f.name not in EXCLUDED_FILES]
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_match_id = data.get('Match', {}).get('id')
                    
                    if str(file_match_id) == str(match_id) or int(file_match_id) == match_id:
                        return json_file
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
        
        return None
    except Exception as e:
        print(f"Error searching for match {match_id}: {e}")
        return None

def find_round_data(match_id, round_id):
    try:
        match_file = find_match_file(match_id)
        if not match_file:
            return None
        
        # Load the match data.
        with open(match_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rounds = data.get('Match', {}).get('rounds', [])
        
        for round_data in rounds:
            if round_data.get('round_id') == round_id or str(round_data.get('round_id')) == str(round_id):
                return round_data
        
        return None
    except Exception as e:
        print(f"Error finding round data for match {match_id}, round {round_id}: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/stats')
def stats():
    # Opens or creates settings file for your statistics labelled at the header.
    settings_path = 'settings.json'
    
    if not os.path.exists(settings_path):
        default_settings = {
            "username": "" 
        }
        with open(settings_path, 'w') as f:
            json.dump(default_settings, f, indent=4)

    with open(settings_path) as f:
        settings = json.load(f)

    return render_template('stats.html', settings=settings)

@app.route('/banners/<filename>')
def serve_banner(filename):
    return send_from_directory('static/assets/banners', filename)

@app.route('/player_stats')
def get_player_stats():
    return send_file(os.path.join(os.path.dirname(__file__), '../output/player_stats.json'))

@app.route('/player/<username>')
def player_profile(username):
    return render_template('player_stats.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(TEMPLATES_DIR, filename)

@app.route('/api/matches')
def get_matches():
    # Pagination config.
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        page = 1
        per_page = 10
    
    
    all_matches = get_recent_matches()
    total = len(all_matches)
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_matches = all_matches[start:end]
    
    for i, match in enumerate(paginated_matches):
        print(f"[DEBUG] Match {i + 1}: ID={match.get('id')}, Map={match.get('map')}")
    
    # Frontend expects this format.
    return jsonify({
        'matches': paginated_matches,
        'total': total,
        'page': page,
        'per_page': per_page
    })

@app.route('/api/match/<int:match_id>/round/<int:round_id>')
def get_round_detail(match_id, round_id):
    try:
        print(f"Getting round detail for match {match_id}, round {round_id}")
        
        round_data = find_round_data(match_id, round_id)
        if not round_data:
            print(f"Round {round_id} not found in match {match_id}")
            return jsonify({'error': 'Round not found'}), 404
        
        response = {
            'Round': round_data,
            'match_id': match_id,
            'round_id': round_id
        }
        
        print(f"Returning round data: {response}")
        return jsonify(response)
        
    except Exception as e:
        print(f"Error getting round detail: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/match/<int:match_id>/<int:round_id>')
def round_detail_page(match_id, round_id):
    try:
        round_data = find_round_data(match_id, round_id)
        if not round_data:
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head><title>Round Not Found</title></head>
                <body>
                    <h1>Round #{} Not Found</h1>
                    <p>Match #{} Round #{}</p>
                    <p><a href="/match/{}">← Back to Match</a></p>
                    <p><a href="/">← Back to Home</a></p>
                </body>
                </html>
            """.format(round_id, str(match_id).zfill(3), round_id, match_id)), 404
        
        return send_from_directory(TEMPLATES_DIR, 'round_detail.html')
        
    except Exception as e:
        print(f"Error serving round detail page for match {match_id}, round {round_id}: {e}")
        return "Internal Server Error", 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("Upload request received")
        
        if 'file' not in request.files:
            print("No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        print(f"File received: {file.filename}")
        
        if file.filename == '':
            print("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            print(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type. Only .gzr files are allowed.'}), 400
        
        filename = secure_filename(file.filename)
        filepath = UPLOAD_FOLDER / filename
        print(f"Saving uploaded file to: {filepath}")
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        file.save(str(filepath))
        
        # Run jsonify.py on the uploaded file. (Wrapper)
        try:
            jsonify_script = BASE_DIR / 'src' / 'jsonify.py'
            
            result = subprocess.run([
                'python', str(jsonify_script), str(filepath)
            ], capture_output=True, text=True, cwd=str(BASE_DIR / 'src'))
            
            if result.returncode != 0:
                filepath.unlink(missing_ok=True)
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                print(f"Processing failed: {error_msg}")
                return jsonify({'error': f'Processing failed: {error_msg}'}), 400
            
            try:
                # Get the most recent JSON file.
                json_files = [f for f in OUTPUT_FOLDER.glob('*.json') if f.name != 'player_stats.json']
                if json_files:
                    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
                    print(f"Latest JSON file: {latest_file}")
                    
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        match_data = data.get('Match', {})
                        
                        mvp = match_data.get('mvp', 'N/A')
                        if isinstance(mvp, dict) and 'name' in mvp:
                            mvp = mvp['name']
                        elif not isinstance(mvp, str):
                            mvp = 'N/A'
                        
                        score = match_data.get('score', {})
                        score_text = f"{score.get('red', 0)}–{score.get('blue', 0)}"
                        
                        response_data = {
                            'success': True,
                            'match_id': str(match_data.get('id', 'N/A')).zfill(3),
                            'map': match_data.get('map', 'Unknown'),
                            'winner': match_data.get('winner', 'Unknown'),
                            'score': score_text,
                            'mvp': mvp,
                            'date': match_data.get('date', 'Unknown')[:10]
                        }
                        
                        print(f"Extracted match data: {response_data}")
                        
                        filepath.unlink(missing_ok=True)
                        
                        return jsonify(response_data)
                else:
                    print("No JSON files found in output directory")
            except Exception as e:
                print(f"Error extracting match data: {e}")
            
            filepath.unlink(missing_ok=True)
            return jsonify({'success': True, 'message': 'File processed successfully'})
            
        except subprocess.TimeoutExpired:
            print("Subprocess timeout")
            filepath.unlink(missing_ok=True)
            return jsonify({'error': 'Processing timeout'}), 500
        except Exception as e:
            print(f"Subprocess error: {e}")
            filepath.unlink(missing_ok=True)
            return jsonify({'error': f'Processing error: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'Upload error: {str(e)}'}), 500

@app.route('/match/<int:match_id>')
def match_detail(match_id):
    try:
        match_file = find_match_file(match_id)
        if not match_file:
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head><title>Match Not Found</title></head>
                <body>
                    <h1>Match #{} Not Found</h1>
                    <p><a href="/">← Back to Home</a></p>
                </body>
                </html>
            """.format(str(match_id).zfill(3))), 404
        
        # Load the match data.
        with open(match_file, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        
        return send_from_directory(TEMPLATES_DIR, 'match_detail.html')
    except Exception as e:
        print(f"Error loading match {match_id}: {e}")
        return "Internal Server Error", 500

@app.route('/api/match/<int:match_id>')
def get_match_data(match_id):
    try:
        # Find the JSON file with the matching ID.
        match_file = find_match_file(match_id)
        if not match_file:
            return jsonify({'error': 'Match not found'}), 404
        
        # Load it.
        with open(match_file, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        
        # Gets map name + banner that was defined at the top (Remove this if you don't want banners)
        match_info = match_data.get('Match', {})
        map_name = match_info.get('map', '').lower()
        banner_config = MAP_CONFIG.get(map_name, MAP_CONFIG['default'])
        
        match_data['banner'] = {
            'image_url': banner_config['banner'],
            'font_color': banner_config['font_color'],
            'shadow_color': banner_config['shadow_color']
        }
        
        return jsonify(match_data)
    except Exception as e:
        print(f"Error loading match data {match_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    settings_file = 'settings.json'
    
    if request.method == 'GET':
        try:
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return jsonify(settings)
            else:
                # Return default settings.
                return jsonify({'username': ''})
        except Exception as e:
            print(f"Error loading settings: {e}")
            return jsonify({'error': 'Failed to load settings'}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            username = data.get('username', '').strip()
            if not username:
                return jsonify({'error': 'Username cannot be empty'}), 400
            
            settings = {
                'username': username,
                'updated_at': json.dumps(datetime.now(), default=str) if 'datetime' in globals() else 'unknown'
            }
            
            # Save to file.
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            return jsonify({'success': True, 'message': 'Settings saved successfully'})
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return jsonify({'error': 'Failed to save settings'}), 500
        
if __name__ == '__main__':
    print("Starting...")
    print(f"Upload folder exists: {UPLOAD_FOLDER.exists()}")
    print(f"Output folder exists: {OUTPUT_FOLDER.exists()}")
    print(f"Templates folder exists: {TEMPLATES_DIR.exists()}")
    app.run(debug=True, host='0.0.0.0', port=5000)