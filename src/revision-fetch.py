import logging
import requests
import sqlite3
import threading

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"

# Database setup
conn = sqlite3.connect('revisions.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY,
        revision_id INTEGER,
        content TEXT,
        FOREIGN KEY(revision_id) REFERENCES revisions(id)
    )
''')
conn.commit()

def get_revision_content(rev_id):
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'revisions',
        'rvprop': 'content',
        'revids': rev_id
    }
    response = requests.get(WIKI_API_URL, params=params)
    data = response.json()
    page_id = next(iter(data['query']['pages']))
    content = data['query']['pages'][page_id]['revisions'][0]['*']
    return content

def store_content(rev_id, content):
    cursor.execute('''
        INSERT OR IGNORE INTO content (revision_id, content)
        VALUES (?, ?)
    ''', (rev_id, content))
    conn.commit()

def fetch_and_store_content(rev_id):
    content = get_revision_content(rev_id)
    store_content(rev_id, content)
    logging.info(f'Stored content for revision ID: {rev_id}')

def main():
    cursor.execute('SELECT id FROM revisions')
    revision_ids = cursor.fetchall()

    threads = []
    for rev_id in revision_ids:
        thread = threading.Thread(target=fetch_and_store_content, args=(rev_id[0],))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
    conn.close()
