# 🚀 Deployment Guide: Stock Market Data Analyzer

This guide explains how to deploy the **Stock Market Data Analyzer** to the cloud so anyone can access your interactive web dashboard and REST API with a public URL.

---

## 🎯 Recommended Free Deployment Platforms

| Platform | Best For | Cost | SSL (HTTPS) | Setup Time |
| :--- | :--- | :--- | :--- | :--- |
| **Render.com** (Recommended) | FastAPI Web Service + Dashboard | **100% Free** | Yes (Automatic) | 3 mins |
| **Railway.app** | Docker / GitHub repo | Free Trial ($5 credit) | Yes | 2 mins |
| **Hugging Face Spaces** | ML / Python Web Demos | **100% Free** | Yes | 4 mins |

---

## 🌟 Method 1: Deploy on Render.com (Easiest & Free)

Render is the best platform for students because it has a **permanent free tier** and connects directly to your GitHub repository.

### Step 1: Push Code to GitHub
Ensure all your files, `Procfile`, and `requirements.txt` are pushed to GitHub:
```powershell
git add .
git commit -m "chore: add deployment configurations"
git push origin main
```

### Step 2: Sign Up on Render
1. Go to [https://render.com](https://render.com).
2. Click **"Get Started for Free"** and sign in using your **GitHub account**.

### Step 3: Create a New Web Service
1. On the Render Dashboard, click **"New +"** and select **"Web Service"**.
2. Choose **"Build and deploy from a Git repository"** and click **Next**.
3. Connect your GitHub account and select your repository: `Stock-Market-Data-Analyzer`.

### Step 4: Configure Service Settings
Fill in the following fields:
- **Name:** `stock-market-data-analyzer` (or your choice)
- **Region:** Closest to you (e.g., `Singapore` or `Frankfurt` or `Oregon`)
- **Branch:** `main`
- **Root Directory:** *(leave blank)*
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn api.main_api:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Select **Free** ($0/month)

### Step 5: Click "Create Web Service"
1. Render will automatically pull your code, install dependencies, and launch your FastAPI application.
2. After 2–3 minutes, the status will show **"Live"** in green!
3. Your live public URL will look like:
   - **Dashboard UI:** `https://stock-market-data-analyzer.onrender.com/dashboard`
   - **Swagger API Docs:** `https://stock-market-data-analyzer.onrender.com/docs`

---

## 🐳 Method 2: Deploy Using Docker (Industry Standard)

If you have Docker Desktop installed locally or want to deploy to any cloud VPS (AWS EC2, DigitalOcean, Azure):

### Build and Run Docker Container Locally:
```bash
# 1. Build the Docker image
docker build -t stock-analyzer .

# 2. Run the container on port 8000
docker run -d -p 8000:8000 --name stock-app stock-analyzer

# 3. Access in your browser:
# http://localhost:8000/dashboard
```

---

## 📌 After Deployment Checklist

1. **Add Live Demo link to GitHub README:**
   Update your `README.md` at the top with:
   ```markdown
   [![Live Demo](https://img.shields.io/badge/Live_Demo-Render-00D084?style=for-the-badge&logo=render&logoColor=white)](https://your-app.onrender.com/dashboard)
   [![API Docs](https://img.shields.io/badge/Swagger-API_Docs-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)](https://your-app.onrender.com/docs)
   ```
2. **Add to LinkedIn Post:**
   Include the live interactive link so recruiters can test it immediately on their phones or laptops!
3. **Include in Resume:**
   Add under Projects:
   - *Stock Market Data Analyzer | Python, FastAPI, Chart.js, Render*
   - *Live Link: `https://your-app.onrender.com/dashboard`*
