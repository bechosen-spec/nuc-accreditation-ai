import sqlite3

EMAIL_TO_PROMOTE = "bonifacechosen100@gmail.com"

conn = sqlite3.connect("nuc_app.db")
cur = conn.cursor()

email = EMAIL_TO_PROMOTE.strip().lower()
cur.execute("SELECT id, full_name, email, role FROM users WHERE email = ?", (email,))
user = cur.fetchone()

if user is None:
    print(f"No user found for {email}. Create the account before promoting it to admin.")
else:
    cur.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
    conn.commit()
    cur.execute("SELECT id, full_name, email, role FROM users WHERE email = ?", (email,))
    print(cur.fetchone())

conn.close()
