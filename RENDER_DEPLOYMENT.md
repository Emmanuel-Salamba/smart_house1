# Smart House Backend - Render Deployment Guide

This guide provides step-by-step instructions for deploying the Smart House Django backend on Render instead of Fly.io.

## Prerequisites

- GitHub account with your repository
- Render account (sign up at https://render.com)
- Your Django project with `render.yaml` configured

## Deployment Steps

### 1. Connect Your Repository to Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Blueprint** or **Web Service**
3. Connect your GitHub account
4. Select your repository

### 2. Automatic Deployment from render.yaml

If you push a `render.yaml` file to your repository, Render will automatically read it and create all services:

- **Web Service** (Django app)
- **PostgreSQL Database**
- **Redis Service**

Simply push the updated files to GitHub:

```bash
git add render.yaml Procfile settings.py .env
git commit -m "Configure for Render deployment"
git push origin main
```

### 3. Set Environment Variables (if not using render.yaml)

In the Render dashboard for your web service:

1. Go to **Environment** section
2. Add these environment variables:

| Variable | Value | Source |
|----------|-------|--------|
| `DEBUG` | `false` | Manual |
| `PYTHONUNBUFFERED` | `1` | Manual |
| `DATABASE_URL` | Auto-set by PostgreSQL | Service |
| `REDIS_URL` | Auto-set by Redis | Service |
| `SECRET_KEY` | Auto-generated | Render |

### 4. Configure Build and Start Commands

The `render.yaml` includes:

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
```

**Start Command:**
```bash
gunicorn smart_house_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --worker-class sync --timeout 120 --access-logfile -
```

### 5. Database Initialization

1. Render automatically runs migrations during build
2. Create a superuser after first deployment:

```bash
# Via Render Shell (in dashboard)
python manage.py createsuperuser

# Or SSH into the service and run the command
```

### 6. First Deployment

1. Commit and push your code to GitHub
2. Render automatically builds and deploys
3. Monitor the **Logs** tab for any errors
4. Access your app at: `https://<your-render-app>.onrender.com`

## Environment Variables

### Automatically Set by Render
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `RENDER_EXTERNAL_HOSTNAME`: Your app's public domain

### Required Manual Setup
- `SECRET_KEY`: Set to auto-generate in Render dashboard
- `DEBUG`: Set to `false` for production

### Optional Configuration
- `CUSTOM_DOMAIN`: Add after setup for custom domains
- `FRONTEND_URL`: For CORS configuration
- `WEB_CONCURRENCY`: Already set to 3 in render.yaml

## CORS Configuration

Update allowed origins in `smart_house_backend/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://<your-render-app>.onrender.com",
    "https://your-custom-domain.com",
    "https://your-flutter-app-domain.com",
]
```

## Static Files

The `render.yaml` includes:
- `collectstatic` during build
- WhiteNoise middleware in Django for serving static files

## Connecting Services

Services are automatically linked in `render.yaml`:
- Web service connects to PostgreSQL via `DATABASE_URL`
- Web service connects to Redis via `REDIS_URL`

## Health Checks

Health check is configured at `/admin/` endpoint. To create a dedicated health endpoint:

```python
# In devices/views.py or similar
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'healthy'})

# In urls.py
path('health/', health_check),
```

Then update `render.yaml`:
```yaml
healthCheckPath: /health/
```

## Scaling

### Increase Worker Count
Edit `render.yaml`:
```yaml
envVars:
  - key: WEB_CONCURRENCY
    value: 5  # Increase from 3
```

### Database Upgrades
- Free tier: 512MB
- Starter: 5GB (recommended minimum for production)
- Standard: 100GB+

### Redis Upgrades
- Free tier: 100MB
- Starter: 1GB (recommended)

## Monitoring and Logs

1. **Logs Tab**: View real-time application logs
2. **Metrics Tab**: Monitor CPU, memory, and requests
3. **Events Tab**: Track deployment history

## Troubleshooting

### Database Connection Issues
```bash
# Check DATABASE_URL is set correctly
python manage.py shell
import os
print(os.environ.get('DATABASE_URL'))
```

### Static Files Not Loading
- Run: `python manage.py collectstatic --no-input`
- Check `STATIC_ROOT` and `STATIC_URL` in settings.py
- Ensure WhiteNoise middleware is installed

### WebSocket Connection Issues
- Verify Redis is connected
- Check `REDIS_URL` is set
- Ensure `channels_redis` is in requirements.txt

### Import Errors After Deployment
- Check `requirements.txt` has all dependencies
- Run `pip install -r requirements.txt` locally to verify

## Comparison: Render vs Fly.io

| Feature | Render | Fly.io |
|---------|--------|--------|
| **Free Tier** | Web + DB (limited) | Less generous |
| **Scaling** | Easy UI controls | More DevOps-focused |
| **Databases** | Managed PostgreSQL | PostgreSQL available |
| **Redis** | Built-in option | Available |
| **Static Files** | WhiteNoise recommended | Build-time with Dockerfile |
| **Persistent Storage** | Volumes available | Volumes available |
| **Cost** | Starter: ~$12/month | More variable |

## Rollback

To rollback to a previous deployment:
1. Go to **Events** tab
2. Find the previous successful deployment
3. Click **Redeploy**

## Custom Domain

1. Go to **Settings** → **Custom Domain**
2. Add your domain
3. Update DNS records as instructed
4. Update `ALLOWED_HOSTS` in settings.py

## Support

- **Render Docs**: https://render.com/docs
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/
- **Your Repository Issues**: [Link to your repo]

---

**Last Updated**: January 2026
**Django Version**: 5.1.14
**Python Version**: 3.10
