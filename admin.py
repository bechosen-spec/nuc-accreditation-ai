import sqlite3

email = "bonifacechosen100@gmail.com" 

conn = sqlite3.connect("nuc_app.db")
cur = conn.cursor()
cur.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email.lower(),))
conn.commit()

cur.execute("SELECT id, full_name, email, role FROM users WHERE email = ?", (email.lower(),))
print(cur.fetchone())

conn.close()