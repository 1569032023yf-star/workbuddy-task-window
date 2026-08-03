import shutil, hashlib, os, sqlite3

p = 'data/bd_leads.db'
d = 'data/production_acceptance_backup_20260727/bd_leads_post_migration_20260727_1428.db'
shutil.copy2(p, d)

h = hashlib.sha256(open(d, 'rb').read()).hexdigest()
print(f'Backup: {os.path.abspath(d)}')
print(f'SHA-256: {h}')
print(f'Size: {os.path.getsize(d)}')

c = sqlite3.connect(d).cursor()
print(f'quick_check: {c.execute("PRAGMA quick_check").fetchone()}')
print(f'integrity: {c.execute("PRAGMA integrity_check").fetchone()}')
print(f'fk: {c.execute("PRAGMA foreign_key_check").fetchall()}')
c.close()
print('Done')
