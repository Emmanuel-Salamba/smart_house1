# Smart Home System - Django Backend

## Deployment to Vercel

### Environment Variables Needed:
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection URL (for WebSocket/cache)
- `DEBUG`: Set to "False" in production
- `ALLOWED_HOSTS`: .vercel.app,your-domain.com

### Setup Steps:
1. Push to GitHub
2. Import to Vercel
3. Add environment variables
4. Deploy!