# One-Click Deploy (Railway)

Deploy your own AugMed instance in under 5 minutes. No programming or server management required.

## What You Get

A fully functional AugMed platform with:

- **Frontend** — the React case review interface
- **API** — the Flask backend handling authentication, case data, and responses
- **RL Service** — adaptive experimentation with Thompson Sampling
- **Database** — PostgreSQL with demo data pre-loaded
- **Demo accounts** ready to log in and review cases

## Cost

Railway charges based on usage. A typical AugMed instance costs **~$5-8/month** for light use (a few researchers running experiments). You can pause or delete the project anytime.

You deploy to **your own Railway account** and pay for your own usage. DHEPLab does not have access to your instance or data.

## Step-by-Step

### 1. Click the Deploy Button

<!-- TODO: Replace with actual Railway template URL after template creation -->
[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/TEMPLATE_ID)

### 2. Create a Railway Account

If you don't have one, Railway will prompt you to sign up. You can sign in with GitHub or email.

### 3. Wait for Build

Railway will:
- Fork the AugMed repositories to your GitHub account
- Build all four services (this takes 3-5 minutes the first time)
- Run database migrations and seed demo data automatically

You'll see a dashboard with four services. When all show a green checkmark, the platform is ready.

### 4. Find Your URL

Click on the **augmed-app** service in the Railway dashboard. Under "Settings" → "Networking", you'll find the public URL (something like `augmed-app-production-xxxx.up.railway.app`).

### 5. Log In

Open the URL in your browser. Log in with the demo credentials:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@demo.augmed.org` | `augmed-demo` |
| Researcher | `researcher@demo.augmed.org` | `augmed-demo` |

### 6. Review Your First Case

Log in as the researcher. You'll see a case assigned to you. Click it to review clinical data and answer the questionnaire.

## After Deployment

### Change Passwords

The demo passwords are public. Change them after your first login:
1. Log in as admin
2. Go to the admin panel to manage users
3. Use the password reset flow for each user

### Load Your Own Data

To replace the demo data with your real (de-identified) clinical cases:
1. Prepare your OMOP-formatted data
2. Use the data loading scripts in `script/sample_data/`
3. Upload display configs to assign cases to participants

See [Creating Experiments](../researcher-guide/creating-experiments.md) for the full workflow.

### Custom Domain

In the Railway dashboard, go to your **augmed-app** service → Settings → Networking → Custom Domain. Follow Railway's instructions to point your domain at the service.

## Troubleshooting

**Build fails:** Check the build logs in the Railway dashboard. The most common issue is a timeout on the free plan — upgrade to the Hobby plan ($5/month) for longer build times.

**Can't log in:** Make sure the API service is running (green checkmark). Check the API logs for migration errors.

**Services can't communicate:** Railway's internal networking uses `*.railway.internal` hostnames. These are configured automatically by the template. If you see connection errors, check that the `API_URL` environment variable in the app service points to the correct internal URL.

## Alternative: Render

If you prefer Render over Railway, this repository includes a `render.yaml` Blueprint. Click "New" → "Blueprint" in the Render dashboard and point it at the `augmed-api-v2` repository.

Render costs ~$21/month (Starter plan for 3 services + database).
