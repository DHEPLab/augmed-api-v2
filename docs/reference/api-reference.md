# API Reference

All endpoints are served by the Flask API. The base URL for the production instance is `https://augmed1.dhep.org`.

## Authentication

AugMed uses two authentication mechanisms:

### JWT Authentication (Participants and Admin Panel)

Most endpoints require a valid JWT token. Obtain a token by logging in (`POST /api/auth/login`). The token is returned in the `Authorization` response header as a `Bearer` token.

```bash
curl -H "Authorization: Bearer <your-token>" https://your-server/api/cases
```

Tokens expire based on the `JWT_ACCESS_TOKEN_EXPIRES` environment variable (default: 3 days).

### API Key Authentication (Service-to-Service)

Export and experiment endpoints also accept an API key for service-to-service communication (e.g., the RL service calling the export API):

```bash
curl -H "X-API-Key: <your-api-key>" https://your-server/api/v1/export/answers
```

The API key is configured via the `EXPORT_API_KEY` environment variable.

**Dual auth:** Export and experiment endpoints accept either authentication method. This allows the admin panel (JWT) and the RL service (API key) to use the same endpoints.

---

## Authentication Endpoints

### POST /api/auth/login

Authenticate a participant and receive a JWT token.

**Request body:**

```json
{
  "email": "participant@example.com",
  "password": "their-password"
}
```

**Response:** HTTP 200 with JWT in the `Authorization` header.

```json
{"message": "Login Successfully"}
```

The token is in the response header: `Authorization: Bearer eyJ...`

**Errors:**
- 401: Invalid credentials or inactive account

---

### POST /api/auth/signup

Register a new account (self-serve signup). Creates an **inactive** account; the user must be activated by an admin before they can log in through the normal flow.

**Request body:**

```json
{
  "email": "newuser@example.com",
  "password": "chosen-password"
}
```

**Response:** HTTP 201

```json
{"data": "Sign up successfully", "status": "success"}
```

---

### POST /api/auth/reset-password-request

Initiate a password reset. Returns a token ID that is used in the follow-up `reset-password` call.

**Request body:**

```json
{"email": "participant@example.com"}
```

**Response:** HTTP 200

```json
{"data": {"id": "reset-token-string"}, "status": "success"}
```

---

### POST /api/auth/reset-password

Set a new password using a reset token.

**Request body:**

```json
{
  "password": "new-secure-password",
  "resetToken": "reset-token-string-from-previous-call"
}
```

**Response:** HTTP 200

```json
{"data": "password updated", "status": "success"}
```

---

## Case Endpoints

### GET /api/cases

Returns the participant's next incomplete case. Requires JWT.

**Headers:** `Authorization: Bearer <token>`

**Response:** HTTP 200

```json
{
  "data": [
    {
      "configId": "550e8400-e29b-41d4-a716-446655440000",
      "caseId": 17,
      "age": "58",
      "gender": "MALE",
      "patientChiefComplaint": "Abdominal Pain"
    }
  ],
  "status": "success"
}
```

Returns an empty array `[]` if all assigned cases have been completed.

---

### GET /api/case-reviews/{case_config_id}

Returns the full case detail for a specific display config assignment. Requires JWT. The calling user must own the specified `case_config_id`.

**URL parameters:**
- `case_config_id` — The `display_config.id` (UUID string)

**Headers:** `Authorization: Bearer <token>`

**Response:** HTTP 200

```json
{
  "data": {
    "personId": "P12345",
    "caseId": "17",
    "caseDetails": [
      {
        "key": "BACKGROUND",
        "values": [
          {
            "key": "Patient Demographics",
            "values": [
              {"key": "Age", "values": "58"},
              {"key": "Gender", "values": "MALE"}
            ]
          },
          {
            "key": "Family History",
            "values": ["No", "Yes"]
          },
          {
            "key": "Medical History",
            "values": ["Fatigue: Present", "Constipation: Present"]
          }
        ]
      },
      {
        "key": "PATIENT COMPLAINT",
        "values": [...]
      },
      {
        "key": "PHYSICAL EXAMINATION",
        "values": [...]
      }
    ],
    "importantInfos": [
      {
        "key": "AI CRC Risk Score (<6: Low; 6-11: Medium; >11: High)",
        "values": ["Predicted Colorectal Cancer Score: 12"]
      }
    ]
  },
  "status": "success"
}
```

**Errors:**
- 403: User does not own this case config, or config does not exist

---

## Answer Endpoints

### POST /api/answer/{task_id}

Submit a questionnaire response for a case. Requires JWT.

**URL parameters:**
- `task_id` — The `display_config.id` (UUID string) for the case being answered

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request body:**

```json
{
  "How would you assess this patient's risk for colorectal cancer?": "Moderate Risk",
  "How confident are you in your screening recommendation?": "2 - Somewhat Confident",
  "What colorectal cancer screening options would you recommend?": "Colonoscopy"
}
```

The keys are the question titles from the answer config. The values are the participant's responses.

**Response:** HTTP 200

```json
{
  "data": {"id": 42},
  "status": "success"
}
```

**Errors:**
- 409: Answer already submitted for this task_id (unique constraint)

---

## Answer Config Endpoints

### GET /api/config/answer

Returns the current active questionnaire configuration. For authenticated users, may include an attention check question if this is their 10th, 20th, etc. case.

**Headers:** `Authorization: Bearer <token>` (optional — attention check only injected for authenticated users)

**Response:** HTTP 200

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "config": [
      {
        "type": "SingleChoice",
        "title": "How would you assess this patient's risk for colorectal cancer?",
        "options": ["Very Low Risk", "Low Risk", "Moderate Risk", "High Risk", "Very High Risk"],
        "required": true
      },
      {
        "type": "SingleChoice",
        "title": "How confident are you in your screening recommendation?",
        "options": ["1 - Not Confident", "2 - Somewhat Confident", "3 - Very Confident"],
        "required": true
      }
    ],
    "created_timestamp": "2024-09-01T12:00:00"
  },
  "status": "success"
}
```

---

## Analytics Endpoints

### POST /api/analytics/

Record timing data for a case review session. Requires JWT. Called automatically by the frontend when a participant submits an answer.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request body:**

```json
{
  "caseConfigId": "550e8400-e29b-41d4-a716-446655440000",
  "caseOpenTime": "2024-10-15T14:23:01.000Z",
  "answerOpenTime": "2024-10-15T14:25:47.000Z",
  "answerSubmitTime": "2024-10-15T14:28:33.000Z"
}
```

All timestamps must be in ISO 8601 format (`YYYY-MM-DDTHH:MM:SS.sssZ`).

**Response:** HTTP 200

```json
{
  "data": {"id": 123},
  "status": "success"
}
```

**Errors:**
- 400: Missing required fields or invalid timestamp format

---

## Admin: User Endpoints

### POST /admin/users

Create one or more participant accounts (inactive by default).

**Request body:**

```json
{
  "users": [
    {
      "name": "Jane Smith",
      "email": "jsmith@hospital.org",
      "position": "Attending Physician",
      "employer": "Memorial Hospital",
      "area_of_clinical_ex": "Internal Medicine"
    }
  ]
}
```

**Response:** HTTP 201

```json
{
  "data": {
    "jsmith@hospital.org": "added"
  },
  "status": "success"
}
```

Possible status values per user: `"added"`, `"failed: already existed"`, `"failed: save failed"`.

---

### GET /admin/users

List all user accounts.

**Response:** HTTP 200

```json
{
  "data": {
    "users": [
      {
        "id": 1,
        "name": "Jane Smith",
        "email": "jsmith@hospital.org",
        "position": "Attending Physician",
        "employer": "Memorial Hospital",
        "area_of_clinical_ex": "Internal Medicine",
        "active": true,
        "admin_flag": false
      }
    ]
  },
  "status": "success"
}
```

---

### GET /admin/users/{user_id}

Get a single user by ID. Requires JWT.

**URL parameters:**
- `user_id` — integer user ID

**Headers:** `Authorization: Bearer <token>`

**Response:** HTTP 200

```json
{
  "data": {"name": "Jane Smith", "email": "jsmith@hospital.org"},
  "status": "success"
}
```

**Errors:**
- 404: User not found

---

## Admin: Config Endpoints

### POST /admin/config/upload

Upload a display config CSV file. **Replaces all existing display configs.**

**Request:** `multipart/form-data` with a `file` field containing the CSV.

```bash
curl -X POST https://your-server/admin/config/upload \
  -F "file=@experiment_config.csv"
```

**Response:** HTTP 200

```json
{
  "data": [
    {"user_case_key": "alice@example.com-1", "status": "added"},
    {"user_case_key": "alice@example.com-2", "status": "added"}
  ],
  "status": "success"
}
```

**Errors:**
- 400: No file in request, or file is not a CSV

---

### POST /admin/config/answer

Create a new answer config (questionnaire). The new config becomes the active one immediately.

**Request body:**

```json
{
  "config": [
    {
      "type": "SingleChoice",
      "title": "Question title here",
      "options": ["Option A", "Option B"],
      "required": true
    }
  ]
}
```

**Response:** HTTP 200

```json
{
  "data": {"id": "new-uuid-here"},
  "status": "success"
}
```

---

## Export Endpoints

All export endpoints accept two forms of authentication:
- **API Key:** `X-API-Key: <your-key>` header (for service-to-service use)
- **JWT:** `Authorization: Bearer <token>` header (for admin panel use)

All export endpoints support `?limit=` (default 1000, max 10000), `?offset=` (default 0), and where noted `?since=` (ISO 8601 timestamp).

Set `Accept: text/csv` for CSV output, or `Accept: application/json` (default) for JSON.

---

### GET /api/v1/export/answers

Export answer data with OMOP demographics, AI scores, and timing.

**Query parameters:** `limit`, `offset`, `since`

**Response:** HTTP 200

```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 1000,
    "offset": 0,
    "has_more": false
  }
}
```

---

### GET /api/v1/export/display-configs

Export current case assignments (display configurations).

**Query parameters:** `limit`, `offset`

**Response:** HTTP 200 (same pagination format as above)

---

### GET /api/v1/export/analytics

Export timing analytics.

**Query parameters:** `limit`, `offset`, `since`

**Response:** HTTP 200 (same pagination format as above)

---

### GET /api/v1/export/participants

Export anonymized participant metadata with completion stats.

**Query parameters:** `limit`, `offset`

**Response:** HTTP 200 (same pagination format as above)

---

## Experiment Endpoints

All experiment endpoints accept the same dual authentication as export endpoints (API key or JWT).

---

### POST /api/v1/experiments

Create a new experiment with arm definitions and optional case pool.

**Request body:**

```json
{
  "name": "CRC Risk Display Study",
  "description": "Testing impact of lab data on diagnostic accuracy",
  "arms": [
    {"name": "control", "path_config": [{"path": "BACKGROUND.Demographics"}]},
    {"name": "treatment", "path_config": [{"path": "BACKGROUND.Demographics"}, {"path": "BACKGROUND.Labs"}]}
  ],
  "case_pool": [
    {"user_email": "clinician1@hospital.org", "case_id": 101}
  ]
}
```

**Response:** HTTP 201

```json
{
  "data": {
    "id": 1,
    "experiment_id": "exp-a1b2c3d4e5f6",
    "name": "CRC Risk Display Study",
    "status": "active",
    "arms": [...],
    "case_pool": [...],
    "created_at": "2025-10-15T14:00:00",
    "updated_at": "2025-10-15T14:00:00"
  },
  "status": "success"
}
```

**Errors:**
- 400: Missing `name` or `arms`

---

### GET /api/v1/experiments

List all experiments. Optionally filter by status.

**Query parameters:**
- `status` (optional): `active`, `paused`, `completed`, or `archived`

**Response:** HTTP 200

```json
{
  "data": {"experiments": [...]},
  "status": "success"
}
```

---

### GET /api/v1/experiments/{experiment_id}

Get experiment details by ID.

**Response:** HTTP 200

**Errors:**
- 404: Experiment not found

---

### PATCH /api/v1/experiments/{experiment_id}/status

Update experiment status (active, paused, completed, archived).

**Request body:**

```json
{"status": "paused"}
```

**Response:** HTTP 200

**Errors:**
- 400: Invalid status transition
- 404: Experiment not found

---

### POST /api/v1/experiments/{experiment_id}/runs

Create a new RL run for an experiment.

**Request body:**

```json
{
  "triggered_by": "manual",
  "run_params": {"reward_config": {"accuracy_weight": 0.8, "time_weight": 0.2}}
}
```

**Response:** HTTP 201

**Errors:**
- 400: Experiment is not active
- 404: Experiment not found

---

### GET /api/v1/experiments/{experiment_id}/runs

List all RL runs for an experiment.

**Response:** HTTP 200

```json
{
  "data": {
    "runs": [
      {
        "id": 1,
        "experiment_id": "exp-a1b2c3d4e5f6",
        "status": "completed",
        "triggered_by": "manual",
        "configs_generated": 10,
        "answers_consumed": 5,
        "started_at": "2025-10-15T14:00:00",
        "completed_at": "2025-10-15T14:00:30"
      }
    ]
  },
  "status": "success"
}
```

---

### POST /api/v1/configs/batch

Programmatically create display configurations in bulk (used by the RL service).

**Request body:**

```json
{
  "configs": [
    {
      "user_email": "clinician1@hospital.org",
      "case_id": 101,
      "path_config": [{"path": "BACKGROUND.Demographics"}],
      "experiment_id": "exp-a1b2c3d4e5f6",
      "rl_run_id": 1,
      "arm": "control"
    }
  ]
}
```

**Response:** HTTP 201

```json
{
  "data": {
    "results": [
      {"status": "added", "user_email": "clinician1@hospital.org", "case_id": 101}
    ],
    "total": 1
  },
  "status": "success"
}
```

---

## Health Check

### GET /api/healthcheck

Check if the API is running. No authentication required.

**Response:** HTTP 200

```json
{"status": "OK", "message": "Service is up and running."}
```

---

## Error Response Format

All errors follow this format:

```json
{
  "status": "fail",
  "message": "Description of the error"
}
```

Common HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad request (invalid input)
- 401: Unauthorized (missing or invalid JWT)
- 403: Forbidden (valid JWT but wrong user)
- 404: Not found
- 409: Conflict (duplicate record)
- 500: Internal server error
