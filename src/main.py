import logging
import requests
import sqlite3
import typing
from typing import List, Tuple, Optional
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import page titles from list.py
from list import PAGE_TITLES

# Database setup
conn = sqlite3.connect('revisions.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS revisions (
        id INTEGER PRIMARY KEY,
        page TEXT,
        timestamp TIMESTAMP,
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

def get_most_revision_timestamp(page_title, op) -> Optional[int]:
    result = cursor.execute(f'SELECT {op}(timestamp) FROM revisions WHERE page = ?', (page_title,)).fetchone()
    if result[0]:
        logging.info(f"{op} revision timestamp for {page_title}: {result[0]}")
        # Convert timestamp to datetime object
        obj = datetime.datetime.strptime(result[0], '%Y-%m-%dT%H:%M:%SZ')

        # Convert datetime object to unix timestamp
        return int(obj.timestamp())
    else:
        logging.info(f"No {op} revisions found for {page_title}.")
        return None

# src/main.py
def get_oldest_revision_timestamp(page_title) -> Optional[int]:
    return get_most_revision_timestamp(page_title, 'MIN')


def get_newest_revision_timestamp(page_title):
    return get_most_revision_timestamp(page_title, 'MAX')

def get_revision_count(page_title):
    logging.debug(f"Fetching revision count for {page_title}.")

    response = requests.get(f'https://en.wikipedia.org/w/rest.php/v1/page/{page_title}/history/counts/edits')
    revision_count = response.json().get('count')

    if revision_count is None:
        logging.error(f"Failed to fetch revision count for {page_title}.")
        exit(1)

    logging.debug(f"Revision count for {page_title}: {revision_count}")
    return revision_count

def get_stored_revision_count(page_title):
    result = cursor.execute('SELECT COUNT(*) FROM revisions WHERE page = ?', (page_title,)).fetchone()
    count = result[0]
    return count

# Save revisions to the database
def save_revisions(revisions, page_title):
    for rev in revisions:
        user_id = None
        username = None

        if rev.get('user'):
            if rev['user'].get('id'):
                user_id = rev['user']['id']
            
            if rev['user'].get('name'):
                username = rev['user']['name']

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


def fetch_general(page_title, timestamp, key, key2, api_count):
    api_url = f'https://en.wikipedia.org/w/rest.php/v1/page/{page_title}/history'

    if timestamp:
        response = requests.get(api_url)
    else:
        response = requests.get(api_url, params={key: timestamp})
    
    data = response.json()
    revisions = data.get('revisions')

    count = get_stored_revision_count(page_title)
    save_revisions(revisions, page_title)
    logging.info(f"{page_title}: {count}/{api_count}")
    

    while key2 in data and len(revisions) != 0 and count < api_count:
        response = requests.get(data[key2])
        data = response.json()
        revisions = data.get('revisions')

        count = get_stored_revision_count(page_title)
        save_revisions(revisions, page_title)
        logging.info(f"{page_title}: {count}/{api_count}")

def fetch_old_revisions(page_title, oldest_stored_timestamp, api_count):
    fetch_general(page_title, oldest_stored_timestamp, 'older_than', 'older', api_count)

# Keep fetching revisions until we have all of them
def fetch_all_revisions(page_title, api_count):
    fetch_general(page_title, None, 'older_than', 'older', api_count)


def fetch_new_revisions(page_title, newest_stored_timestamp, api_count):
    fetch_general(page_title, newest_stored_timestamp, 'newer_than', 'newer', api_count)

def fetch_and_store_revision(page, api_count, oldest_stored_timestamp, newest_stored_timestamp):
    # Fetch revisions older than the oldest stored revision
    if oldest_stored_timestamp:
        # Debugging
        logging.info(f"Fetching revisions older than {oldest_stored_timestamp} for {page}.")
        fetch_old_revisions(page, oldest_stored_timestamp, api_count)

    # Fetch revisions newer than the newest stored revision
    elif newest_stored_timestamp:
        # Debugging
        logging.info(f"Fetching revisions newer than {newest_stored_timestamp} for {page}.")
        fetch_new_revisions(page, newest_stored_timestamp, api_count)

    # Otherwise, fetch all revisions, newest to oldest
    else:
        # Debugging
        logging.info(f"Fetching all revisions for {page}.")
        fetch_all_revisions(page, api_count)

def fetch(page_title):
        oldest_stored_timestamp = get_oldest_revision_timestamp(page_title)
        newest_stored_timestamp = get_newest_revision_timestamp(page_title)
        api_count = get_revision_count(page_title)

        fetch_and_store_revision(page_title, api_count, oldest_stored_timestamp, newest_stored_timestamp)

# src/main.py
def fetch_and_store_revisions():
    for page_title in PAGE_TITLES:
        fetch(page_title)

if __name__ == '__main__':
    fetch_and_store_revisions()
    conn.close()
    logging.info("Database connection closed.")
