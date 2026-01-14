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

from google import genai
from google.genai import types
import json
import re
import math
import random

# create console logger and file logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler1 = logging.StreamHandler()
handler1.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler1)
handler2 = logging.FileHandler('congress-lookup-dashboard.txt')
handler2.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler2)


app = Flask(__name__, static_folder='congress-lookup-frontend/dist', static_url_path='')
CORS(app)

load_dotenv()
db_conn_string = os.getenv("DATABASE_CONN_STRING")
db_conn = psycopg2.connect(db_conn_string)

_ = load_dotenv(find_dotenv())


@app.route('/')
def hello():
    return redirect("/index.html", code=302)

SYSTEM_INSTRUCTION = """
You are a political data analyst assistant. Your task is to provide accurate, up-to-date information about members of the U.S. Congress.
When a user searches for a member, you must:
1. Identify the correct member (Senator or Representative).
2. Retrieve their current standing committees.
3. Identify top 5 industries they are most involved with (based on campaign contributions or legislative focus).

CRITICAL: Return your response ONLY in the following JSON format within your text response. Do not include any other conversational text.
{
  "name": "Full Name",
  "title": "Senator / Representative",
  "party": "Democrat / Republican / Independent",
  "state": "State Code",
  "district": "District Number (if applicable)",
  "committees": ["Committee 1", "Committee 2"],
  "industries": [
    {"name": "Industry Name", "involvementScore": 85, "amount": 100000}
  ]
}
"""

@app.route('/api/search', methods=['POST'])
def search_congress_member():
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return {"error": "Query string is required"}, 400

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return {"error": "Server configuration error"}, 500

    # 1. Check Cache
    try:
        # We need a new cursor for this request logic preferably, 
        # but let's use the global one carefully or make a new one. 
        # Flask is threaded, using a single global connection without pooling is unsafe for concurrent requests.
        # However, looking at lines 35-36, it seems db_conn is global.
        # For this refactor, I will create a new cursor from the global connection, 
        # but ideally we should handle connections better.
        # Let's commit to using the global connection logic present in the file.
        
        with db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Check if we have a fresh record for a member matching the query
            # We search for a name similar to the query.
            search_query = f"%{query}%"
            cur.execute("""
                SELECT * FROM congress_members_cache 
                WHERE name ILIKE %s 
                AND last_updated > NOW() - INTERVAL '90 days'
                LIMIT 1
            """, (search_query,))
            cached_result = cur.fetchone()
            
            if cached_result:
                logger.info(f"Cache hit for query '{query}' -> '{cached_result['name']}'")
                return cached_result['data']
    
    except Exception as e:
        logger.error(f"Error checking cache: {e}")
        # Proceed to API if cache check fails
        db_conn.rollback()


    try:
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Search for this member of Congress: {query}. Provide their current committees and industry involvement.",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1,
            )
        )
        
        text = response.text
        if not text:
            return {"error": "No response text received"}, 500

        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
             return {"error": "Failed to parse JSON from response"}, 500
        
        raw_data = json.loads(json_match.group(0))
        
        # Extract grounding sources
        sources = []
        # Check if grounding metadata exists and structurize it
        # The python SDK structure for candidates and grounding metadata:
        if response.candidates and response.candidates[0].grounding_metadata:
            chunks = response.candidates[0].grounding_metadata.grounding_chunks
            if chunks:
                for chunk in chunks:
                    if chunk.web and chunk.web.uri:
                        sources.append({
                            "title": chunk.web.title or chunk.web.uri,
                            "uri": chunk.web.uri
                        })

        # Map to internal type structure expected by frontend
        member = {
            "id": "".join([random.choice("0123456789abcdefghijklmnopqrstuvwxyz") for _ in range(9)]),
            "name": raw_data.get("name"),
            "title": raw_data.get("title"),
            "party": raw_data.get("party"),
            "state": raw_data.get("state"),
            "district": raw_data.get("district"),
            "imageUrl": f"https://picsum.photos/400/400?random={random.randint(0, 1000)}",
            "committees": raw_data.get("committees", []),
            "industries": raw_data.get("industries", []),
            "sources": sources
        }

        # 2. Save to Cache
        try:
            with db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO congress_members_cache (name, data, last_updated)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (name) 
                    DO UPDATE SET data = EXCLUDED.data, last_updated = NOW()
                """, (member['name'], json.dumps(member)))
                db_conn.commit()
                logger.info(f"Cached result for '{member['name']}'")
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            db_conn.rollback()

        return member

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return {"error": str(e)}, 500
