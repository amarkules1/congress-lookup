from flask import Flask, request, redirect
import psycopg2
import psycopg2.extras
from flask_cors import CORS
import logging
from dotenv import load_dotenv, find_dotenv
import sqlalchemy
import os
import pandas as pd
from pandas.core.dtypes.common import is_numeric_dtype

# create console logger and file logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler1 = logging.StreamHandler()
handler1.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler1)
handler2 = logging.FileHandler('nfl-stats-tracker-dashboard.txt')
handler2.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler2)


app = Flask(__name__, static_folder='nfl-stats-tracker-frontend/dist', static_url_path='')
CORS(app)

load_dotenv()
db_conn_string = os.getenv("DATABASE_CONN_STRING")
db_conn = psycopg2.connect(db_conn_string)

_ = load_dotenv(find_dotenv())


@app.route('/')
def hello():
    return redirect("/index.html", code=302)

# --- Gemini Service Integration ---
from google import genai
from google.genai import types
import json
import time
import uuid

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("API Key not found in environment variables")
        raise ValueError("API Key not found")
    return genai.Client(api_key=api_key)

def extract_json(text):
    """Cleans Markdown code blocks from the response string to extract raw JSON."""
    import re
    json_match = re.search(r'```json\n([\s\S]*?)\n```', text) or re.search(r'```\n([\s\S]*?)\n```', text)
    raw_json = json_match.group(1) if json_match else text
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from Gemini response: {raw_json}")
        raise ValueError("Failed to parse AI response as JSON.")

def retry_with_backoff(operation, retries=3, delay=2):
    """Retries an operation with exponential backoff."""
    try:
        return operation()
    except Exception as e:
        # Check for rate limit errors (429) or service unavailable (503)
        # The python SDK might raise specific exceptions, but we'll catch general Exception for now and check attributes/message
        is_retryable = False
        if hasattr(e, 'status_code') and e.status_code in [429, 503]:
            is_retryable = True
        elif hasattr(e, 'code') and e.code in [429, 503]:
            is_retryable = True
        elif "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            is_retryable = True
            
        if retries > 0 and is_retryable:
            logger.warning(f"API rate limit hit. Retrying in {delay}s... (Retries left: {retries})")
            time.sleep(delay)
            return retry_with_backoff(operation, retries - 1, delay * 2)
        raise e

@app.route('/api/schedule', methods=['POST'])
def get_schedule():
    data = request.json
    season = data.get('season')
    week = data.get('week')
    
    if not season or not week:
        return {"error": "Missing season or week"}, 400

    # 1. Check Cache
    try:
        cached_schedule = get_schedule_from_db(season, week)
        if cached_schedule and len(cached_schedule) > 5:
            logger.info(f"Schedule Cache HIT for {season} Week {week} ({len(cached_schedule)} games)")
            return json.dumps(cached_schedule, default=str), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Schedule Cache Check Error: {e}")
        # Continue to fetch from API if cache check fails

    logger.info(f"Schedule Cache MISS for {season} Week {week}. Fetching from Gemini...")
    print(f"DEBUG: Schedule Cache MISS for {season} Week {week}", flush=True)

    client = get_gemini_client()
    prompt = f"""
    Find the full schedule of NFL games for the {season} season, Week {week}.
    
    Return a JSON Array of objects. Each object must have:
    - "homeTeam": Name of home team
    - "awayTeam": Name of away team
    - "date": Date of the game
    - "scoreSummary": The final score if the game has been played (e.g. "KC 21 - DET 20"), or "TBD" if not.
    
    The output must be ONLY the JSON array.
    """

    try:
        def call_api():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    thinking_config=types.ThinkingConfig(include_thoughts=False, budget_token_count=0) if hasattr(types, 'ThinkingConfig') else None 
                )
            )
        
        response = retry_with_backoff(lambda: client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            )
        ))

        text = response.text
        if not text:
            return {"error": "No schedule generated"}, 500
            
        schedule_data = extract_json(text)
        if not isinstance(schedule_data, list):
             return {"error": "Invalid schedule format returned"}, 500
        
        # 2. Save to DB
        try:
            save_schedule_to_db(season, week, schedule_data)
            logger.info(f"Saved {len(schedule_data)} games to DB for schedule")
        except Exception as db_err:
            logger.error(f"Failed to save schedule to DB: {db_err}")

        return json.dumps(schedule_data), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        logger.error(f"Schedule Fetch Error: {e}")
        return {"error": str(e)}, 500

# ... (existing code) ...

def get_schedule_from_db(season, week):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        query = """
            SELECT home_team, away_team, date, summary 
            FROM sports_data.games 
            WHERE season = %s AND week = %s
            ORDER BY date ASC
        """
        cur.execute(query, (season, week))
        rows = cur.fetchall()
        
        schedule = []
        for row in rows:
            schedule.append({
                "homeTeam": row['home_team'],
                "awayTeam": row['away_team'],
                "date": row['date'],
                "scoreSummary": row['summary'] or "TBD" # Use summary field for scoreSummary
            })
            
        return schedule
    except Exception as e:
        logger.error(f"DB Schedule Fetch Error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def save_schedule_to_db(season, week, schedule_data):
    print(f"DEBUG: Saving schedule to DB for {season} Week {week}. Items: {len(schedule_data)}", flush=True)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        for game in schedule_data:
            # Check if game exists to avoid duplicates (simple check by teams/season/week)
            # We use a simplified query here.
            check_query = """
                SELECT id FROM sports_data.games 
                WHERE season = %s AND week = %s AND home_team = %s AND away_team = %s
            """
            cur.execute(check_query, (season, week, game.get('homeTeam'), game.get('awayTeam')))
            if cur.fetchone():
                continue # Skip if exists
            
            # Insert basic info
            cur.execute("""
                INSERT INTO sports_data.games (
                    season, week, date, home_team, away_team, summary
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                season,
                week,
                game.get('date'),
                game.get('homeTeam'),
                game.get('awayTeam'),
                game.get('scoreSummary')
            ))
            
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

@app.route('/api/game-data', methods=['POST'])
def get_game_data_endpoint():
    request_data = request.json
    season = request_data.get('season')
    week = request_data.get('week')
    team = request_data.get('team')
    specific_matchup = request_data.get('specificMatchup')
    
    if not season or not week:
        return {"error": "Missing season or week"}, 400

    client = get_gemini_client()
    
    query_context = ""
    if specific_matchup:
        query_context = f"the {season} NFL season, Week {week} game between {specific_matchup.get('away')} (Away) and {specific_matchup.get('home')} (Home)"
    elif team:
        query_context = f"the {season} NFL season, Week {week} game involving the {team}"
    else:
        query_context = f"the {season} NFL season, Week {week} games. Choose the most high-profile game."

    prompt = f"""
    I need detailed statistical data for {query_context}.
    You must use Google Search to find the box score, advanced stats, game conditions, and historical betting odds.
    
    I need a JSON response containing:
    1. Date of the game.
    2. Home and Away team names.
    3. Final Score for both.
    4. Total Possessions (approximate if exact not found) for both.
    5. Rushing Yards, Passing Yards, Total Plays, Turnovers, and Sacks for both teams.
    6. Venue Information: Stadium Name, Location (City, State), and whether it is Indoors (Dome/Retractable Closed) or Outdoors.
    7. Weather Conditions (If venue is Outdoors): Temperature, Wind Speed, Condition (e.g., Sunny, Rain, Snow), and Chance of Rain/Precipitation. If Indoors, leave weather null.
    8. Betting Odds: Find the 'Opening' (approx 3 days prior to kickoff) and 'Closing' (day of game) odds. Include Spread, Over/Under, and Moneyline for both home and away.
    9. Top statistical performers: Quarterbacks (passing yds/tds/int), Top 2 Rushers (yds/tds), Top 2 Receivers (rec/yds/tds).

    Output MUST be a valid JSON object matching this structure exactly (no extra text outside JSON):
    {{
      "date": "YYYY-MM-DD",
      "season": "{season}",
      "week": "{week}",
      "homeTeam": {{
        "teamName": "String",
        "score": Number,
        "rushingYards": Number,
        "passingYards": Number,
        "totalPlays": Number,
        "possessions": Number,
        "turnovers": Number,
        "sacks": Number
      }},
      "awayTeam": {{
        "teamName": "String",
        "score": Number,
        "rushingYards": Number,
        "passingYards": Number,
        "totalPlays": Number,
        "possessions": Number,
        "turnovers": Number,
        "sacks": Number
      }},
      "venue": {{
        "name": "String",
        "location": "String",
        "isIndoor": Boolean
      }},
      "weather": {{
        "temperature": "String",
        "condition": "String",
        "windSpeed": "String",
        "chanceOfRain": "String"
      }},
      "odds": {{
        "opening": {{
          "spread": "String",
          "overUnder": "String",
          "moneyline": {{ "home": "String", "away": "String" }}
        }},
        "closing": {{
          "spread": "String",
          "overUnder": "String",
          "moneyline": {{ "home": "String", "away": "String" }}
        }}
      }},
      "playerStats": [
        {{
          "name": "String",
          "position": "QB" | "RB" | "WR" | "TE",
          "team": "String",
          "passingYards": Number (optional),
          "passingTDs": Number (optional),
          "interceptions": Number (optional),
          "rushingYards": Number (optional),
          "rushingTDs": Number (optional),
          "receivingYards": Number (optional),
          "receivingTDs": Number (optional),
          "receptions": Number (optional)
        }}
      ],
      "summary": "A brief 1-sentence summary of the game outcome."
    }}
    """

    try:
        # 1. Check Cache
        cached_game = get_game_from_db(season, week, team, specific_matchup)
        if cached_game and cached_game.get('venue'):
            logger.info(f"Cache HIT for {season} Week {week}")
            return json.dumps(cached_game, default=str), 200, {'Content-Type': 'application/json'}
        
        logger.info(f"Cache MISS for {season} Week {week}. Fetching from Gemini...")

        # 2. Fetch from Gemini
        response = retry_with_backoff(lambda: client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            )
        ))

        text = response.text
        if not text:
            return {"error": "No content generated"}, 500

        parsed_data = extract_json(text)
        
        # Extract source URLs from grounding metadata
        source_urls = []
        if response.candidates and response.candidates[0].grounding_metadata:
             chunks = response.candidates[0].grounding_metadata.grounding_chunks
             if chunks:
                 for chunk in chunks:
                     if chunk.web and chunk.web.uri:
                         source_urls.append(chunk.web.uri)
        
        parsed_data['sourceUrls'] = list(set(source_urls))
        
        # 3. Save to DB
        try:
            save_game_to_db(parsed_data)
            logger.info("Saved game data to DB")
        except Exception as db_err:
            logger.error(f"Failed to save to DB: {db_err}")
            # Don't fail the request if saving fails, just return the data
            
        # Ensure ID is consistent if we just saved it (though save_game_to_db might generate a new UUID, 
        # for the response we can just use what we have or re-fetch. 
        # For simplicity, we'll return the parsed_data. 
        # If we want the DB ID, we'd need to return it from save_game_to_db)
        if 'id' not in parsed_data:
             parsed_data['id'] = str(uuid.uuid4())

        return json.dumps(parsed_data, default=str), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        logger.error(f"Gemini Service Error: {e}")
        return {"error": str(e)}, 500

# --- Database Helpers ---

def get_db_connection():
    conn_string = os.getenv("DATABASE_CONN_STRING")
    if not conn_string:
        raise ValueError("DATABASE_CONN_STRING not set")
    return psycopg2.connect(conn_string)

def get_game_from_db(season, week, team=None, specific_matchup=None):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        query = """
            SELECT * FROM sports_data.games 
            WHERE season = %s AND week = %s
        """
        params = [str(season), str(week)]
        
        if specific_matchup:
            # This is tricky because we need to match both teams. 
            # We can check if home/away matches either combination.
            # Using ILIKE for case-insensitive partial match might be safer but specific matchup usually implies full names or close to it.
            # Let's stick to exact or close match for specific matchup to avoid wrong games.
            # But for single team lookup, partial match is essential.
            query += """ AND version is not null AND (
                (home_team = %s AND away_team = %s) OR 
                (home_team = %s AND away_team = %s)
            )"""
            params.extend([specific_matchup['home'], specific_matchup['away'], specific_matchup['away'], specific_matchup['home']])
        elif team:
            query += " AND (home_team ILIKE %s OR away_team ILIKE %s)"
            wildcard_team = f"%{team}%"
            params.extend([wildcard_team, wildcard_team])
            
        # Order by created_at desc to get latest if duplicates exist
        query += " ORDER BY created_at DESC LIMIT 1"
        
        cur.execute(query, params)
        game = cur.fetchone()
        
        if not game:
            return None
            
        # Fetch team stats
        cur.execute("SELECT * FROM sports_data.team_stats WHERE game_id = %s", (game['id'],))
        team_stats = cur.fetchall()
        
        # Fetch player stats
        cur.execute("SELECT * FROM sports_data.player_stats WHERE game_id = %s", (game['id'],))
        player_stats = cur.fetchall()
        
        # Reconstruct the JSON structure
        result = dict(game)
        
        # Map snake_case DB columns to camelCase JSON fields
        if 'source_urls' in result:
            result['sourceUrls'] = result.pop('source_urls')
            
        # Remove other snake_case keys that might confuse frontend or clutter response
        result.pop('home_team', None)
        result.pop('away_team', None)
        result.pop('created_at', None)
        result.pop('updated_at', None)
        
        # Map team stats
        home_stats = next((s for s in team_stats if s['is_home']), None)
        away_stats = next((s for s in team_stats if not s['is_home']), None)
        
        if home_stats:
            result['homeTeam'] = {
                'teamName': home_stats['team_name'],
                'score': home_stats['score'],
                'rushingYards': home_stats['rushing_yards'],
                'passingYards': home_stats['passing_yards'],
                'totalPlays': home_stats['total_plays'],
                'possessions': home_stats['possessions'],
                'turnovers': home_stats['turnovers'],
                'sacks': home_stats['sacks']
            }
        
        if away_stats:
            result['awayTeam'] = {
                'teamName': away_stats['team_name'],
                'score': away_stats['score'],
                'rushingYards': away_stats['rushing_yards'],
                'passingYards': away_stats['passing_yards'],
                'totalPlays': away_stats['total_plays'],
                'possessions': away_stats['possessions'],
                'turnovers': away_stats['turnovers'],
                'sacks': away_stats['sacks']
            }
            
        # Map player stats
        result['playerStats'] = []
        for p in player_stats:
            result['playerStats'].append({
                'name': p['player_name'],
                'position': p['position'],
                'team': p['team_name'],
                'passingYards': p['passing_yards'],
                'passingTDs': p['passing_tds'],
                'interceptions': p['interceptions'],
                'rushingYards': p['rushing_yards'],
                'rushingTDs': p['rushing_tds'],
                'receivingYards': p['receiving_yards'],
                'receivingTDs': p['receiving_tds'],
                'receptions': p['receptions']
            })
            
        return result

    except Exception as e:
        logger.error(f"DB Fetch Error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def save_game_to_db(data):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert Game
        cur.execute("""
            INSERT INTO sports_data.games (
                season, week, date, home_team, away_team, venue, weather, odds, summary, source_urls
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('season'),
            data.get('week'),
            data.get('date'),
            data.get('homeTeam', {}).get('teamName'),
            data.get('awayTeam', {}).get('teamName'),
            json.dumps(data.get('venue')),
            json.dumps(data.get('weather')),
            json.dumps(data.get('odds')),
            data.get('summary'),
            data.get('sourceUrls')
        ))
        game_id = cur.fetchone()[0]
        
        # Insert Team Stats (Home)
        home = data.get('homeTeam', {})
        cur.execute("""
            INSERT INTO sports_data.team_stats (
                game_id, team_name, is_home, score, rushing_yards, passing_yards, 
                total_plays, possessions, turnovers, sacks
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            game_id, home.get('teamName'), True, home.get('score'), home.get('rushingYards'),
            home.get('passingYards'), home.get('totalPlays'), home.get('possessions'),
            home.get('turnovers'), home.get('sacks')
        ))
        
        # Insert Team Stats (Away)
        away = data.get('awayTeam', {})
        cur.execute("""
            INSERT INTO sports_data.team_stats (
                game_id, team_name, is_home, score, rushing_yards, passing_yards, 
                total_plays, possessions, turnovers, sacks
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            game_id, away.get('teamName'), False, away.get('score'), away.get('rushingYards'),
            away.get('passingYards'), away.get('totalPlays'), away.get('possessions'),
            away.get('turnovers'), away.get('sacks')
        ))
        
        # Insert Player Stats
        for p in data.get('playerStats', []):
            cur.execute("""
                INSERT INTO sports_data.player_stats (
                    game_id, player_name, position, team_name, passing_yards, passing_tds,
                    interceptions, rushing_yards, rushing_tds, receiving_yards, receiving_tds, receptions
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                game_id, p.get('name'), p.get('position'), p.get('team'),
                p.get('passingYards'), p.get('passingTDs'), p.get('interceptions'),
                p.get('rushingYards'), p.get('rushingTDs'),
                p.get('receivingYards'), p.get('receivingTDs'), p.get('receptions')
            ))
            
        conn.commit()
        return game_id

    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

    
if __name__ == '__main__':
    app.run(port=5000, debug=True)
