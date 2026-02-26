const Database = require('better-sqlite3');
const path = require('path');

const dbPath = path.join(process.env.HOME, 'Library/Application Support/anime1-desktop-electron/anime1.db');
const db = new Database(dbPath);

const row = db.prepare('SELECT * FROM cover_cache WHERE anime_id = ?').get('1782');
console.log('cover_url column:', row.cover_url);
console.log('cover_data JSON:', JSON.parse(row.cover_data).coverUrl);

db.close();
