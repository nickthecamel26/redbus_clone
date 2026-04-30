# RedBus Clone

Full-stack bus booking application with FastAPI backend and React frontend.

## Project Structure

```
redbus-clone/
├── backend/          # FastAPI + PostgreSQL
├── frontend/         # React + Vite + Tailwind CSS
└── docker-compose.yml
```

## Quick Start

### 1. Start Infrastructure

```bash
docker-compose up -d
```

Services:
- **PostgreSQL**: `localhost:5432` (user: postgres, pass: postgres, db: redbus)
- **PgAdmin**: `http://localhost:5050` (email: admin@redbus.com, pass: admin)
- **Backend API**: `http://localhost:8000`

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

## API Documentation

Once running, view interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database Connection via PgAdmin

1. Open `http://localhost:5050`
2. Login: `admin@redbus.com` / `admin`
3. Add new server:
   - Name: redbus
   - Host: `postgres`
   - Port: `5432`
   - Username: `postgres`
   - Password: `postgres`
