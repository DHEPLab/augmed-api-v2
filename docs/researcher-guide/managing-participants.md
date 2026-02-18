# Managing Participants

This guide covers creating participant accounts, activating them, and monitoring their status.

## User Account Lifecycle

1. **Created (inactive)** — Account exists in the database but the participant cannot log in. The `active` flag is `false` and no password is set.
2. **Activated** — An administrator activates the account and the participant receives a password reset link.
3. **Active** — Participant can log in, review cases, and submit answers.
4. **Password reset** — If a participant forgets their password, an admin initiates a reset.

## Bulk User Creation

Use `POST /admin/users` to create multiple participants at once. This does not require authentication in the current version.

**Request:**

```bash
curl -X POST https://your-augmed-server/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {
        "name": "Jane Smith",
        "email": "jsmith@hospitalname.org",
        "position": "Attending Physician",
        "employer": "Memorial Hospital",
        "area_of_clinical_ex": "Internal Medicine"
      },
      {
        "name": "Robert Chen",
        "email": "rchen@clinic.org",
        "position": "Nurse Practitioner",
        "employer": "Community Clinic",
        "area_of_clinical_ex": "Primary Care"
      }
    ]
  }'
```

**Response:**

```json
{
  "data": {
    "jsmith@hospitalname.org": "added",
    "rchen@clinic.org": "added"
  },
  "status": "success"
}
```

If an email address already exists in the system, that entry will show `"failed: already existed"` rather than returning an error for the entire batch. Other users in the same request will still be processed.

**Required fields:**

| Field | Description |
|-------|-------------|
| `email` | Participant's email address (must be unique) |

**Optional fields:**

| Field | Description |
|-------|-------------|
| `name` | Full name |
| `position` | Clinical role (e.g., "Physician", "Nurse Practitioner") |
| `employer` | Institution or organization |
| `area_of_clinical_ex` | Clinical specialty or area of expertise |

The optional fields appear in the admin user list and help track participant demographics. They are not displayed to participants during case review.

## Activation Flow

New users cannot log in until activated. Activation requires:

1. Setting `active = true` in the database
2. Ensuring the user has a way to set their password

### Setting an Initial Password via Reset Flow

The recommended approach is to send participants a password reset link:

**Step 1 — Request a password reset token:**

```bash
curl -X POST https://your-augmed-server/api/auth/reset-password-request \
  -H "Content-Type: application/json" \
  -d '{"email": "jsmith@hospitalname.org"}'
```

This returns a reset token `id`:

```json
{
  "data": {"id": "abc123def456"},
  "status": "success"
}
```

**Step 2 — Activate the user and set the password using the token:**

```bash
curl -X POST https://your-augmed-server/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"password": "SecurePassword123!", "resetToken": "abc123def456"}'
```

The user account is activated when `active` is set to `true`. Currently this requires a direct database update or a separate admin action. In practice, the DHEP team has managed this through a combination of the database and a recruitment survey that collects emails, after which participants set their passwords through the reset flow.

### Direct Database Activation

For local testing or when the email system is not configured:

```sql
UPDATE "user"
SET active = true
WHERE email = 'jsmith@hospitalname.org';
```

> **Note:** Never do this in production without also ensuring the user has a password set through the proper reset flow.

## Viewing All Users

Retrieve the full participant list:

```bash
curl https://your-augmed-server/admin/users
```

**Response:**

```json
{
  "data": {
    "users": [
      {
        "id": 1,
        "name": "Jane Smith",
        "email": "jsmith@hospitalname.org",
        "position": "Attending Physician",
        "employer": "Memorial Hospital",
        "area_of_clinical_ex": "Internal Medicine",
        "active": true,
        "admin_flag": false
      },
      {
        "id": 2,
        "name": "Robert Chen",
        "email": "rchen@clinic.org",
        "position": "Nurse Practitioner",
        "employer": "Community Clinic",
        "area_of_clinical_ex": "Primary Care",
        "active": false,
        "admin_flag": false
      }
    ]
  },
  "status": "success"
}
```

The `active` field shows whether each participant can log in. The `admin_flag` field shows whether they have administrative access.

## Password Management

### Resetting a Participant's Password

If a participant cannot log in or has forgotten their password:

```bash
# Step 1: Request a reset token
curl -X POST https://your-augmed-server/api/auth/reset-password-request \
  -H "Content-Type: application/json" \
  -d '{"email": "jsmith@hospitalname.org"}'

# Step 2: Set new password with the token returned in step 1
curl -X POST https://your-augmed-server/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"password": "NewSecurePassword!", "resetToken": "{token_from_step_1}"}'
```

Share the new password with the participant through a secure channel (not email in plaintext).

## Monitoring Completion

### Which Participants Have Completed Cases

Query the database to see which participants have submitted answers:

```sql
SELECT
    u.email,
    u.name,
    COUNT(a.id) AS cases_completed,
    MIN(a.created_timestamp) AS first_submission,
    MAX(a.modified_timestamp) AS last_submission
FROM "user" u
LEFT JOIN answer a ON a.user_email = u.email
WHERE u.active = true
GROUP BY u.email, u.name
ORDER BY cases_completed DESC;
```

### Assigned vs. Completed Cases

```sql
SELECT
    dc.user_email,
    COUNT(DISTINCT dc.id) AS cases_assigned,
    COUNT(DISTINCT a.task_id) AS cases_completed,
    COUNT(DISTINCT dc.id) - COUNT(DISTINCT a.task_id) AS cases_remaining
FROM display_config dc
LEFT JOIN answer a ON a.task_id = dc.id AND a.user_email = dc.user_email
GROUP BY dc.user_email
ORDER BY cases_remaining DESC;
```

### Participants Who Have Not Logged In

If you need to identify participants who have been created but have never logged in (and therefore have no analytics records):

```sql
SELECT u.email, u.name, u.active, u.created_timestamp
FROM "user" u
WHERE u.active = false
   OR NOT EXISTS (
       SELECT 1 FROM answer a WHERE a.user_email = u.email
   )
ORDER BY u.created_timestamp;
```

## Removing Case Assignments

If you need to clear case assignments (e.g., to re-upload a corrected config), the `script/assign_cases/remove_all_case_assignments.py` script removes all display configs:

```bash
cd script/assign_cases
python remove_all_case_assignments.py
```

> **Warning:** This deletes all display config records. Do not run this unless you are sure no in-progress participants will be affected. Export data first.

## Related Documentation

- [Creating Experiments](creating-experiments.md) — Building the display config CSV
- [Monitoring Progress](monitoring-progress.md) — Tracking timing and completion rates
- [API Reference](../reference/api-reference.md) — Full user and auth endpoint documentation
