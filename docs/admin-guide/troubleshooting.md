# Troubleshooting

This guide covers common issues encountered when running AugMed, with diagnostics and solutions.

## Health Check

The first step for any production issue is to check the health endpoint:

```bash
curl https://your-augmed-server/api/healthcheck
```

Expected:
```json
{"status": "OK", "message": "Service is up and running."}
```

If this fails:
- HTTP 502/503: The ECS task is not healthy or has crashed — check ECS service events and CloudWatch logs
- Connection refused: The server is not running — check ECS task status
- Timeout: Network/load balancer issue — check ALB target group health

## Common Issues

### Issue: Participants Cannot Log In

**Symptom:** Login returns 401 or "Invalid credentials" error.

**Causes and solutions:**

1. **Account is inactive** — The `active` field is false:
   ```sql
   SELECT email, active FROM "user" WHERE email = 'participant@example.com';
   ```
   Fix: `UPDATE "user" SET active = true WHERE email = 'participant@example.com';`

2. **Wrong password** — Initiate a password reset:
   ```bash
   curl -X POST https://your-augmed-server/api/auth/reset-password-request \
     -H "Content-Type: application/json" \
     -d '{"email": "participant@example.com"}'
   ```

3. **Account does not exist** — Check the user table and create the account if missing.

---

### Issue: Participant Sees No Cases

**Symptom:** `GET /api/cases` returns an empty list.

**Causes and solutions:**

1. **No display config for this user** — The participant has no assignments:
   ```sql
   SELECT COUNT(*) FROM display_config WHERE user_email = 'participant@example.com';
   ```
   Fix: Upload a display config CSV that includes this participant.

2. **All cases already completed** — The participant has answered all assigned cases:
   ```sql
   SELECT
       COUNT(DISTINCT dc.id) AS assigned,
       COUNT(DISTINCT a.id) AS completed
   FROM display_config dc
   LEFT JOIN answer a ON a.task_id = dc.id AND a.user_email = dc.user_email
   WHERE dc.user_email = 'participant@example.com';
   ```
   Fix: Assign additional cases by uploading an updated display config.

3. **Case data not in OMOP tables** — The `case_id` in the display config does not exist in `visit_occurrence`:
   ```sql
   SELECT dc.case_id
   FROM display_config dc
   WHERE dc.user_email = 'participant@example.com'
     AND NOT EXISTS (
         SELECT 1 FROM visit_occurrence v WHERE v.visit_occurrence_id = dc.case_id
     );
   ```
   Fix: Load the missing OMOP data or correct the case IDs in the display config.

---

### Issue: Config Upload Fails

**Symptom:** `POST /admin/config/upload` returns an error.

**Causes and solutions:**

1. **Not a CSV file** — The endpoint only accepts `.csv` files. Ensure your file has a `.csv` extension.

2. **Missing required columns** — The CSV must have headers: `User`, `Case No.`, `Path`, `Collapse`, `Highlight`, `Top`. Check for typos or extra spaces in column names.

3. **Invalid case ID** — `Case No.` must be an integer. Check for non-numeric values:
   ```bash
   # Check CSV for non-numeric case IDs
   awk -F',' 'NR>1 && $2 !~ /^[0-9]+$/ {print NR": "$0}' your_config.csv
   ```

4. **Empty path** — Rows with an empty `Path` column are silently skipped.

5. **Database error** — Check CloudWatch logs for SQL errors. Common cause: the database is unreachable from the API.

---

### Issue: Case Detail Fails to Load

**Symptom:** `GET /api/case-reviews/{id}` returns 403 or 500.

**403 — Access denied:**
- The JWT token's email does not match the `user_email` in the display config for this `case_config_id`
- The display config ID does not exist

Check the display config:
```sql
SELECT id, user_email, case_id FROM display_config WHERE id = 'the-config-id';
```

**500 — Internal server error:**
- OMOP data missing for the case — check that `visit_occurrence_id` exists and has associated `person`, `observation`, `measurement` records
- `system_config` missing `page_config` entry — check:
  ```sql
  SELECT * FROM system_config WHERE id = 'page_config';
  ```

---

### Issue: Analytics Not Recording

**Symptom:** The `analytics` table is empty or missing records for recent submissions.

**Cause:** Analytics are recorded by a separate `POST /api/analytics/` call from the frontend, distinct from the answer submission. If the frontend failed to call this endpoint, analytics will be missing.

**Diagnosis:**
```sql
-- Find answers without analytics
SELECT a.user_email, a.task_id, a.created_timestamp
FROM answer a
WHERE NOT EXISTS (
    SELECT 1 FROM analytics an WHERE an.case_config_id = a.task_id
)
ORDER BY a.created_timestamp DESC;
```

**Note:** Missing analytics does not mean the answer was not recorded — the `answer` table is independent. Export data will show empty timing columns for these records.

---

### Issue: Database Connection Fails

**Symptom:** API returns 500 errors and CloudWatch logs show database connection errors.

**Diagnosis steps:**

1. Check the `DATABASE_URL` environment variable in the ECS task definition — verify host, port, username, password, and database name.

2. Check RDS instance status in the AWS console — it should show "Available."

3. Check RDS security group — the ECS task's security group must have an inbound rule allowing it to connect to the RDS security group on port 5432.

4. Test connectivity from a local machine (if VPN access allows):
   ```bash
   psql "postgresql://user:pass@host:5432/augmed"
   ```

---

### Issue: JWT Token Expiry

**Symptom:** Participants report being logged out frequently.

**Solution:** Increase the JWT expiry in environment variables:

```env
JWT_ACCESS_TOKEN_EXPIRES=604800   # 7 days in seconds
JWT_REFRESH_TOKEN_EXPIRES=604800
```

Update the ECS task definition and redeploy.

---

## Log Locations

| Environment | Log Location |
|-------------|-------------|
| Production | AWS CloudWatch → Log Groups → `/ecs/augmed-api` |
| Local (Flask) | stdout (terminal where `flask run` is running) |
| Local (Docker) | `docker logs postgres_container` for database logs |

**Filtering CloudWatch logs for errors:**

In the CloudWatch console, use this filter pattern:
```
ERROR
```

Or for a specific endpoint:
```
"500" "Internal Server Error"
```

---

## Database Maintenance

### Checking Table Sizes

```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(quote_ident(tablename))) AS total_size,
    pg_total_relation_size(quote_ident(tablename)) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;
```

### Vacuuming

PostgreSQL handles vacuuming automatically on RDS. If you observe performance degradation, manually trigger:

```sql
VACUUM ANALYZE answer;
VACUUM ANALYZE analytics;
VACUUM ANALYZE display_config;
```

### Backup

RDS automated backups run daily. To create a manual snapshot in the AWS console: RDS → Databases → augmed-db → Actions → Take snapshot.

## Related Documentation

- [Deployment](deployment.md) — Infrastructure setup and CI/CD
- [Database](database.md) — Schema reference
- [API Reference](../reference/api-reference.md) — Endpoint documentation
