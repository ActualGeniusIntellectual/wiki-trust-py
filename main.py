import logging
import requests
import json
import os
import time
import sqlite3

# Set up logging. Include the time, level, and message
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "Python_(programming_language)"  # Example Wikipedia page

# Database setup
conn = sqlite3.connect('revisions.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS revisions (
        id INTEGER PRIMARY KEY,
        page TEXT,
        timestamp TEXT,
        minor BOOLEAN,
        size INTEGER,
        comment TEXT,
        user TEXT
    )
''')

conn.commit()

def get_revision_count():
    params = {
        'action': 'query',
        'format': 'json',
        'titles': PAGE_TITLE,
        'prop': 'revisions',
        'rvprop': 'ids',
        'rvlimit': '1'
    }
    response = requests.get(WIKI_API_URL, params=params)
    data = response.json()
    page_id = next(iter(data['query']['pages']))
    return len(data['query']['pages'][page_id]['revisions'])

def fetch_and_store_revisions():
    stored_revisions_count = cursor.execute('SELECT COUNT(*) FROM revisions').fetchone()[0]
    # Log the number of stored revisions
    logging.info(f'Number of stored revisions: {stored_revisions_count}')

    api_revisions_count = get_revision_count()

    if stored_revisions_count < api_revisions_count:
        params = {
            'action': 'query',
            'format': 'json',
            'titles': PAGE_TITLE,
            'prop': 'revisions',
            'rvprop': 'ids|timestamp|size|flags|comment|user',
            'rvlimit': '500'  # Adjust as needed, max is 500 for non-bots
        }

        while True:
            response = requests.get(WIKI_API_URL, params=params)
            data = response.json()
            page_id = next(iter(data['query']['pages']))
            revisions = data['query']['pages'][page_id]['revisions']

            # Insert revisions into the database
            for rev in revisions:
                cursor.execute('''
                    INSERT OR IGNORE INTO revisions (id, page, timestamp, minor, size, comment, user)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rev['revid'],
                    PAGE_TITLE,
                    rev.get('timestamp'),
                    'minor' in rev,  # True if 'minor' flag exists
                    rev.get('size'),
                    rev.get('comment'),
                    rev.get('user')
                ))
            
            conn.commit()

            if 'continue' in data:
                params['rvcontinue'] = data['continue']['rvcontinue']
            else:
                break

if __name__ == '__main__':
    fetch_and_store_revisions()
    conn.close()
