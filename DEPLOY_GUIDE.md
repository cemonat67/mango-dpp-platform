# 🚀 Mango DPP Platform - Railway.app Deployment Guide

## ✅ **Pre-Deployment Checklist**
- ✅ Railway.app configuration (`railway.json`, `Procfile`) - Ready
- ✅ PostgreSQL support in database.py - Ready  
- ✅ All dependencies in requirements.txt - Ready
- ✅ Multi-language support (TR/EN) - Ready
- ✅ Brand colors fully implemented - Ready
- ✅ Sustainability dashboard complete - Ready

## 🌐 **Railway.app Deployment Steps**

### **1. Create Railway.app Account**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub account (recommended)
3. Verify your account

### **2. Deploy from GitHub**
1. Push your code to GitHub repository
2. In Railway dashboard, click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect the configuration

### **3. Environment Variables Setup**
Add these environment variables in Railway dashboard:

**Required:**
- `DATABASE_URL` - Auto-provided by Railway PostgreSQL service
- `PORT` - Auto-provided by Railway

**Optional (for AI features):**
- `OPENAI_API_KEY` - Your OpenAI API key (if you want AI image generation)

### **4. Add PostgreSQL Database**
1. In your Railway project, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically set the `DATABASE_URL` environment variable

### **5. Deploy & Monitor**
1. Railway will automatically build and deploy
2. Check the logs for any issues
3. Access your live URL provided by Railway

## 🔧 **Local to Cloud Migration**

The application automatically handles database differences:
- **Local**: Uses SQLite (`mango_dpp.db`)
- **Cloud**: Uses PostgreSQL (via `DATABASE_URL` environment variable)

All existing data structure and models are compatible with both databases.

## 🌍 **Post-Deployment Testing**

Test these features on the live URL:
1. **Dashboard**: Main overview with statistics
2. **Collections**: Create and manage product collections
3. **Styles**: Add styles with materials and carbon footprint
4. **Sustainability**: All analytics with brand colors
5. **Multi-language**: Switch between TR/EN languages
6. **NFT Passports**: Generate blockchain-based product certificates

## 📊 **Expected Resource Usage**
- **RAM**: ~512MB (fits Railway's free tier)
- **Database**: Starts small, scales as needed
- **Build Time**: ~2-3 minutes
- **Cold Start**: ~30 seconds

## 🚨 **Troubleshooting**

**If deployment fails:**
1. Check Railway logs for specific errors
2. Verify all environment variables are set
3. Ensure PostgreSQL service is running
4. Check that `requirements.txt` includes all dependencies

**Database migration:**
- Tables are created automatically on first run
- No manual migration needed
- Existing SQLite data won't transfer (start fresh on cloud)

## 🎯 **Success Indicators**
- ✅ App loads without errors
- ✅ Database tables created automatically  
- ✅ Sustainability dashboard shows brand colors
- ✅ Language switching works (TR ↔ EN)
- ✅ Can create collections and styles
- ✅ NFT passport generation works