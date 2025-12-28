# server.py - Backend Python pour PropStats NBA
# Installation: pip install flask flask-cors nba_api

from flask import Flask, jsonify
from flask_cors import CORS
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster, playergamelog
import time
import os

app = Flask(__name__)
CORS(app)

# Route de test
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'OK',
        'message': 'Backend Python NBA fonctionne! 🏀',
        'season': '2025-26'
    })

# Route pour récupérer les équipes NBA
@app.route('/api/teams')
def get_teams():
    try:
        print('📡 Récupération des équipes NBA...')
        nba_teams = teams.get_teams()
        
        formatted_teams = []
        for team in nba_teams:
            formatted_teams.append({
                'id': team['id'],
                'name': team['full_name'],
                'abbreviation': team['abbreviation'],
                'city': team['city']
            })
        
        print(f'✅ {len(formatted_teams)} équipes chargées')
        return jsonify({
            'response': formatted_teams,
            'results': len(formatted_teams)
        })
    except Exception as e:
        print(f'❌ Erreur: {e}')
        return jsonify({'error': str(e)}), 500

# Route pour récupérer les joueurs d'une équipe
@app.route('/api/players/<int:team_id>')
def get_players(team_id):
    try:
        print(f'📡 Récupération des joueurs pour l\'équipe {team_id}...')
        
        time.sleep(0.6)
        
        roster = commonteamroster.CommonTeamRoster(
            team_id=team_id,
            season='2025-26'
            timeout=60
        )
        
        players_data = roster.get_data_frames()[0]
        
        formatted_players = []
        for _, player in players_data.iterrows():
            player_name = str(player['PLAYER'])
            name_parts = player_name.split()
            player_id = int(player['PLAYER_ID'])
            
            formatted_players.append({
                'id': player_id,
                'firstname': name_parts[0] if len(name_parts) > 0 else '',
                'lastname': ' '.join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0] if len(name_parts) == 1 else '',
                'position': str(player['POSITION']) if player['POSITION'] else 'N/A',
                'number': str(player['NUM']) if player['NUM'] else '0',
                'photo': f'https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png'
            })
        
        print(f'✅ {len(formatted_players)} joueurs trouvés')
        return jsonify({
            'response': formatted_players,
            'results': len(formatted_players)
        })
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Route pour récupérer les stats d'un joueur
@app.route('/api/stats/<int:player_id>')
def get_stats(player_id):
    try:
        print(f'📡 Récupération des stats pour le joueur {player_id}...')
        
        time.sleep(0.6)
        
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season='2025-26'
            timeout=60
        )
        
        games_data = gamelog.get_data_frames()[0]
        
        # Récupérer 30 matchs pour avoir assez après filtrage home/away
        formatted_games = []
        for _, game in games_data.head(30).iterrows():
            # Calculer les minutes (convertir "MM:SS" en minutes décimales)
            minutes = 0
            if 'MIN' in game and game['MIN']:
                min_str = str(game['MIN'])
                if ':' in min_str:
                    parts = min_str.split(':')
                    minutes = float(parts[0]) + float(parts[1]) / 60
                else:
                    minutes = float(min_str) if min_str else 0
            
            formatted_games.append({
                # Stats de base
                'points': int(game['PTS']) if game['PTS'] else 0,
                'totReb': int(game['REB']) if game['REB'] else 0,
                'assists': int(game['AST']) if game['AST'] else 0,
                'steals': int(game['STL']) if game['STL'] else 0,
                'blocks': int(game['BLK']) if game['BLK'] else 0,
                
                # Stats de tir
                'threes': int(game['FG3M']) if 'FG3M' in game and game['FG3M'] else 0,
                'threesAttempted': int(game['FG3A']) if 'FG3A' in game and game['FG3A'] else 0,
                'fgPct': float(game['FG_PCT'] * 100) if 'FG_PCT' in game and game['FG_PCT'] else 0,
                'fg3Pct': float(game['FG3_PCT'] * 100) if 'FG3_PCT' in game and game['FG3_PCT'] else 0,
                'ftPct': float(game['FT_PCT'] * 100) if 'FT_PCT' in game and game['FT_PCT'] else 0,
                
                # Autres stats
                'minutesPlayed': round(minutes, 1),
                'turnovers': int(game['TOV']) if 'TOV' in game and game['TOV'] else 0,
                'fouls': int(game['PF']) if 'PF' in game and game['PF'] else 0,
                'plusMinus': int(game['PLUS_MINUS']) if 'PLUS_MINUS' in game and game['PLUS_MINUS'] else 0,
                'oreb': int(game['OREB']) if 'OREB' in game and game['OREB'] else 0,
                'dreb': int(game['DREB']) if 'DREB' in game and game['DREB'] else 0,
                
                # Info du match
                'game': {
                    'date': {
                        'start': game['GAME_DATE']
                    },
                    'result': game['WL'] if 'WL' in game else 'N/A',
                    'matchup': game['MATCHUP'] if 'MATCHUP' in game else ''
                },
                'team': {
                    'name': game['MATCHUP'].split()[0] if 'MATCHUP' in game else 'N/A'
                }
            })
        
        print(f'✅ {len(formatted_games)} matchs récupérés')
        return jsonify({
            'response': formatted_games,
            'results': len(formatted_games)
        })
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 3001))
    print(f'🚀 Serveur sur port {port}')
    app.run(host='0.0.0.0', port=port, debug=False)

