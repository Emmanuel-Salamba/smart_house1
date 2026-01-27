# Quick Render Deployment Checklist

Use this checklist when deploying to Render.

## Before Deployment ✓

- [ ] All code changes committed to Git
- [ ] `requirements.txt` updated with all dependencies
- [ ] `.env` file in `.gitignore` (not committed)
- [ ] `DEBUG = False` verified in production environment
- [ ] `SECRET_KEY` configured in Render dashboard
- [ ] CORS origins updated for your frontend domain
- [ ] All database migrations applied locally with `python manage.py migrate`

## Deployment Steps ✓

1. [ ] Go to [Render Dashboard](https://dashboard.render.com)
2. [ ] Click **New** → **Blueprint**
3. [ ] Connect GitHub account
4. [ ] Select repository
5. [ ] Render reads `render.yaml` automatically
6. [ ] Click **Deploy**
7. [ ] Monitor build in **Logs** tab

## Post-Deployment ✓

- [ ] App deployed at: `https://<your-app>.onrender.com`
- [ ] Create superuser if needed (use Render Shell)
- [ ] Test API endpoints
- [ ] Verify database migration ran successfully
- [ ] Check logs for errors
- [ ] Test WebSocket connections (if applicable)
- [ ] Configure custom domain (optional)

## Configuration on Render Dashboard ✓

### Environment Variables to Set:

| Variable | Value | Auto? |
|----------|-------|-------|
| `DEBUG` | `false` | No |
| `SECRET_KEY` | Auto-generate | No |
| `PYTHONUNBUFFERED` | `1` | Yes (in render.yaml) |
| `WEB_CONCURRENCY` | `3` | Yes (in render.yaml) |
| `DATABASE_URL` | Auto-set | Yes (from PostgreSQL) |
| `REDIS_URL` | Auto-set | Yes (from Redis) |
| `RENDER_EXTERNAL_HOSTNAME` | Auto-set | Yes (Render) |

## Troubleshooting ✓

### Build Fails
- Check **Build Logs** tab for errors
- Verify Python version (should be 3.10)
- Ensure all dependencies in `requirements.txt`
- Run locally: `pip install -r requirements.txt`

### Database Connection Error
```bash
# Verify in Render Shell:
python manage.py shell
import os
print(os.environ.get('DATABASE_URL'))
```

### Static Files Not Loading
- Check `STATIC_URL` and `STATIC_ROOT` in settings.py
- Run: `python manage.py collectstatic --no-input`
- WhiteNoise middleware should be active

### WebSocket Issues
- Verify Redis is connected: `redis-cli` in Render Shell
- Check `REDIS_URL` environment variable is set
- Ensure `channels_redis` in requirements.txt

## Useful Commands (via Render Shell)

```bash
# Create superuser
python manage.py createsuperuser

# Check migrations status
python manage.py showmigrations

# Run specific migration
python manage.py migrate app_name

# Connect to PostgreSQL
psql $DATABASE_URL

# Connect to Redis
redis-cli

# Check environment variables
env | grep -E 'DATABASE|REDIS|SECRET'

# Collect static files
python manage.py collectstatic --no-input
```

## Useful Links

- Render Dashboard: https://dashboard.render.com
- PostgreSQL Connection: See connection string in DB settings
- Logs: Dashboard → Your Service → Logs
- Metrics: Dashboard → Your Service → Metrics
- Deployment Guide: `RENDER_DEPLOYMENT.md` in repo root

## Key Files for Render

| File | Purpose | Status |
|------|---------|--------|
| `render.yaml` | Infrastructure config | ✅ Updated |
| `.env` | Dev environment vars | ✅ Updated |
| `settings.py` | Django config | ✅ Updated |
| `requirements.txt` | Python packages | ✅ Verified |
| `build.sh` | Build commands | ✅ Verified |
| `Procfile` | Process definition | ✅ Verified |
| `RENDER_DEPLOYMENT.md` | Full guide | ✅ New |

## Region Selection

Render regions available:
- **Ohio** (US) - Closest to most US users
- **Oregon** (US)
- **Frankfurt** (EU)
- **Singapore** (Asia)
- **Sydney** (Australia)

Choose based on where your users are located.

## Scaling Guide

### When to Upgrade

**Database** (PostgreSQL):
- ⬆️ Free (512MB) → Starter (5GB) when approaching capacity
- Monitor in Render dashboard under resource usage

**Cache** (Redis):
- ⬆️ Free (100MB) → Starter (1GB) for heavy caching loads

**Web Service**:
- Increase `WEB_CONCURRENCY` from 3 to 5-8
- Upgrade plan: Free → Standard → Pro based on load

### Monitor Resource Usage
1. Go to Service → Metrics
2. Check CPU and Memory graphs
3. Upgrade if consistently >80% usage

## Custom Domain Setup

1. Go to Service → Settings
2. Click **Add Custom Domain**
3. Enter your domain (e.g., `api.yourdomain.com`)
4. Follow DNS setup instructions
5. Update `ALLOWED_HOSTS` in `settings.py`:
   ```python
   ALLOWED_HOSTS = [
       'localhost',
       '127.0.0.1',
       '*.onrender.com',
       'api.yourdomain.com',  # Add your domain
   ]
   ```
6. Redeploy

## Rollback to Previous Version

If deployment breaks:
1. Go to Service → Events
2. Find the working deployment
3. Click **Redeploy**
4. Service rolls back to that version

## Cost Estimate

| Service | Tier | Cost/Month |
|---------|------|-----------|
| Web Service | Free | $0 |
| PostgreSQL | Starter | $15 |
| Redis | Starter | $15 |
| **Total** | **Starter** | **~$30** |

*Prices subject to change. See Render pricing page for current rates.*

## Getting Help

- **Render Support**: https://render.com/docs
- **Django Docs**: https://docs.djangoproject.com
- **View Logs**: Dashboard → Logs tab (shows errors)
- **Check Events**: Dashboard → Events tab (shows deployment history)

---

**Last Updated**: January 28, 2026
**Project**: Smart House Backend
**Status**: Ready to Deploy
