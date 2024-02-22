import logging
import requests
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"

# Database setup
conn = sqlite3.connect('revisions.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY,
        revision_id INTEGER UNIQUE,
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

def main():
    # Select revision IDs that are not present in the content table
    cursor.execute('''
        SELECT id FROM revisions WHERE id NOT IN (SELECT revision_id FROM content)
    ''')
    revision_ids = cursor.fetchall()

    for rev_id in revision_ids:
        content = get_revision_content(rev_id[0])
        store_content(rev_id[0], content)
        logging.info(f'Stored content for revision ID: {rev_id[0]}')

if __name__ == '__main__':
    main()
    conn.close()
