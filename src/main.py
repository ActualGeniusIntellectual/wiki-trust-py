import logging
import requests
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"

# Import page titles from list.py
from list import PAGE_TITLES

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
logging.info("Database setup complete.")

def get_revision_count(page_title):
    logging.debug(f"Fetching revision count for {page_title}.")
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
    revision_count = len(data['query']['pages'][page_id]['revisions'])
    logging.debug(f"Revision count for {page_title}: {revision_count}")
    return revision_count

def fetch_and_store_revisions():
    for page_title in PAGE_TITLES:
        stored_revisions_count = cursor.execute('SELECT COUNT(*) FROM revisions WHERE page = ?', (page_title,)).fetchone()[0]
        logging.info(f'Checking stored revisions for {page_title}: {stored_revisions_count} revisions found.')

        api_revisions_count = get_revision_count(page_title)

        if stored_revisions_count < api_revisions_count:
            logging.info(f'{page_title}. Stored: {stored_revisions_count} API: {api_revisions_count}. Fetching new revisions.')
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
                logging.debug(f"Revisions for {page_title} stored in the database.")

                if 'continue' in data:
                    params['rvcontinue'] = data['continue']['rvcontinue']
                else:
                    break
            logging.info(f'All new revisions for {page_title} have been fetched and stored.')
        else:
            logging.debug(f'No new revisions to fetch for {page_title}.')

if __name__ == '__main__':
    fetch_and_store_revisions()
    conn.close()
    logging.info("Database connection closed.")
