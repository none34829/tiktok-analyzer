# TikTok Analyzer

A full-stack application to search for TikTok users based on specific criteria and analyze their relevance to your search query using AI.

## Features

- Search TikTok users by keyword
- Filter users based on followers, following, likes, and verification status
- AI-powered analysis of user profiles for relevance to search queries
- Image analysis of profile pictures
- Export results to JSON or CSV format
- Modern responsive UI

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **APIs**: ScrapTik (TikTok data), OpenAI (for AI-powered analysis)

## Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn
- RapidAPI account with access to ScrapTik API
- OpenAI API key

## Setup

### 1. Clone this repository

```bash
git clone https://github.com/yourusername/tiktok-analyzer.git
cd tiktok-analyzer
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install fastapi uvicorn python-multipart python-dotenv requests pillow openai

# Configure your API keys
# Edit the .env file and add your API keys
```

Edit `backend/.env` file:
```
RAPID_API_KEY=your_rapidapi_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Start the Development Servers

#### Start the Backend Server

For Windows PowerShell:
```powershell
cd backend
python run.py
```

For Linux/Mac:
```bash
cd backend
python run.py
```

The FastAPI server will start at http://localhost:8000

#### Start the Frontend Server

Open a new terminal window and run:

For Windows PowerShell:
```powershell
cd frontend
npm run dev
```

For Linux/Mac:
```bash
cd frontend
npm run dev
```

The Next.js application will be available at http://localhost:3000

## Usage

1. Open http://localhost:3000 in your browser
2. Enter a search query (e.g., "fashion", "fitness", "cooking")
3. Set any desired filters using the "Advanced Filters" option
4. Click "Search" to find relevant TikTok users
5. View the AI-powered analysis of each user's relevance to your query
6. Export the results as JSON or CSV if needed

## Deployment

### Backend Deployment (Example for a VPS)

```bash
cd backend

# Install production dependencies
pip install gunicorn

# Create a systemd service
sudo nano /etc/systemd/system/tiktok-analyzer-api.service
```

Add the following content:
```
[Unit]
Description=TikTok Analyzer API
After=network.target

[Service]
User=yourusername
WorkingDirectory=/path/to/tiktok-analyzer/backend
ExecStart=/path/to/python -m gunicorn main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl enable tiktok-analyzer-api
sudo systemctl start tiktok-analyzer-api
```

### Frontend Deployment

You can deploy the Next.js application to Vercel, Netlify, or any other platform that supports Next.js.

Example for Vercel:
```bash
cd frontend
npm install -g vercel
vercel
```

## License

MIT 