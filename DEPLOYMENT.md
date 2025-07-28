# 🚀 Mango DPP Cloud Deployment Guide

## Ücretsiz Hosting Seçenekleri

### 1. Railway.app (Önerilen) 
- **Plan**: $0/ay - 512MB RAM, 1GB Disk
- **Database**: PostgreSQL ücretsiz dahil
- **Deployment**: GitHub bağlantısı ile otomatik

#### Adımlar:
1. [Railway.app](https://railway.app) hesabı oluştur
2. GitHub repository'sini bağla
3. Environment variables ekle:
   - `DATABASE_URL`: Otomatik PostgreSQL URL
   - `OPENAI_API_KEY`: AI görsel için (opsiyonel)
4. Deploy!

### 2. Render.com
- **Plan**: $0/ay - 512MB RAM
- **Database**: PostgreSQL $7/ay (ya da ElephantSQL ücretsiz)

### 3. Heroku (Alternatif)
- **Plan**: Eco Dynos $5/ay
- **Database**: Heroku PostgreSQL Mini $5/ay

## Environment Variables

```bash
# Production
DATABASE_URL=postgresql://user:pass@host:port/db
OPENAI_API_KEY=sk-your-openai-key

# Development  
DATABASE_URL=sqlite:///./mango_dpp.db
```

## Deployment Commands

```bash
# Local test with production server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Git push for auto-deployment
git push origin main
```

## Database Migration

```python
# Automatic table creation on startup
# No manual migration needed - SQLAlchemy handles it
```

## SSL & Domain

Railway provides:
- **HTTPS**: Otomatik SSL
- **Domain**: app-name.railway.app 
- **Custom Domain**: Ücretsiz (DNS settings)

---
**Next Steps**: Railway hesabı oluştur ve repository'yi bağla!