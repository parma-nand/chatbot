# pgAdmin connection (Docker chatbot database)

Use these settings to see the **`users`** table with registered accounts.

## Credentials (same as `docker-compose.yml`)

| Field | Value |
|-------|--------|
| Host | `localhost` |
| Port | `5432` |
| Maintenance database | `chatbot` |
| Username | `chatbot` |
| Password | `chatbot` |

## Do not use

- Server **PostgreSQL 17** (local install) — that is a **different** database
- Database **`postgres`** — default DB, no `users` table for this app
- User **`postgres`** — not the Docker chatbot user

## Register server in pgAdmin

1. Right-click **Servers** → **Register** → **Server**
2. **General** → Name: `Chatbot Docker`
3. **Connection** → fill table above → Save password
4. Open: **Databases → chatbot → Schemas → public → Tables → users**

## SQL

```sql
SELECT id, email, phone, role, is_active, created_at FROM users;
```

## If `users` does not exist

You are on the wrong server or database. Verify with:

```powershell
cd C:\Users\realm\Desktop\AI_ML_Project\chatbot
docker compose exec db psql -U chatbot -d chatbot -c "\dt"
```

You should see table `users`.
