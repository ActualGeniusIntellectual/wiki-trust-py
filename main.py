import logging
import requests
import json
import sqlite3

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLES = ["Python_(programming_language)", "Java_(programming_language)", "C++"]  # Example list of Wikipedia pages

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

def get_revision_count(page_title):
    params = {
        'action': 'query',
        'format': 'json',
        'titles': page_title,
        'prop': 'revisions',
        'rvprop': 'ids',
        'rvlimit': '1'
    }
    response = requests.get(WIKI_API_URL, params=params)
    data = response.json()
    page_id = next(iter(data['query']['pages']))
    return len(data['query']['pages'][page_id]['revisions'])

def fetch_and_store_revisions():
    for page_title in PAGE_TITLES:
        stored_revisions_count = cursor.execute('SELECT COUNT(*) FROM revisions WHERE page = ?', (page_title,)).fetchone()[0]
        logging.info(f'Number of stored revisions for {page_title}: {stored_revisions_count}')

        api_revisions_count = get_revision_count(page_title)

        if stored_revisions_count < api_revisions_count:
            params = {
                'action': 'query',
                'format': 'json',
                'titles': page_title,
                'prop': 'revisions',
                'rvprop': 'ids|timestamp|size|flags|comment|user',
                'rvlimit': '500'
            }

            while True:
                response = requests.get(WIKI_API_URL, params=params)
                data = response.json()
                page_id = next(iter(data['query']['pages']))
                revisions = data['query']['pages'][page_id]['revisions']

                for rev in revisions:
                    cursor.execute('''
                        INSERT OR IGNORE INTO revisions (id, page, timestamp, minor, size, comment, user)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        rev['revid'],
                        page_title,
                        rev.get('timestamp'),
                        'minor' in rev,
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
