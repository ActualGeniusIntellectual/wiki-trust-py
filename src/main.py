import logging
import requests
import sqlite3

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        delta INTEGER,
        user_id INTEGER,
        username TEXT
    );
''')
conn.commit()
logging.info("Database setup complete.")

def get_revision_count(page_title):
    logging.debug(f"Fetching revision count for {page_title}.")

    response = requests.get(f'https://en.wikipedia.org/w/rest.php/v1/page/{page_title}/history/counts/edits')
    revision_count = response.json().get('count')

    logging.debug(f"Revision count for {page_title}: {revision_count}")
    return revision_count

# Save revisions to the database
def save_revisions(revisions, page_title):
    for rev in revisions:
        user_id = None
        username = None

        if rev.get('user'):
            if rev['user'].get('id'):
                user_id = rev['user']['id']
            
            if rev['user'].get('username'):
                username = rev['user']['username']

        cursor.execute('''
            INSERT OR IGNORE INTO revisions (id, page, timestamp, minor, size, comment, delta, user_id, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rev.get('id'),
            page_title,
            rev.get('timestamp'),
            rev.get('minor'),
            rev.get('size'),
            rev.get('comment'),
            rev.get('delta'),
            user_id,
            username,
        ))
    conn.commit()
    logging.debug(f"{len(revisions)} revisions for {page_title} stored in the database.")

def fetch_and_store_revisions():
    for page_title in PAGE_TITLES:
        stored_revisions_count = cursor.execute('SELECT COUNT(*) FROM revisions WHERE page = ?', (page_title,)).fetchone()[0]
        logging.info(f'Checking stored revisions for {page_title}: {stored_revisions_count} revisions found.')

        api_revisions_count = get_revision_count(page_title)

        if stored_revisions_count < api_revisions_count:
            logging.info(f'{page_title}. Stored: {stored_revisions_count} API: {api_revisions_count}. Fetching new revisions.')

            api_url = f'https://en.wikipedia.org/w/rest.php/v1/page/{page_title}/history'
            
            response = requests.get(api_url)
            data = response.json()
            revisions = data.get('revisions')
            save_revisions(revisions, page_title)

            while 'older' in data:
                response = requests.get(data['older'])
                data = response.json()
                revisions = data.get('revisions')
                save_revisions(revisions, page_title)

            logging.info(f'All new revisions for {page_title} have been fetched and stored.')
        else:
            logging.debug(f'No new revisions to fetch for {page_title}.')

if __name__ == '__main__':
    fetch_and_store_revisions()
    conn.close()
    logging.info("Database connection closed.")
