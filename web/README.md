# Aero-SEA Web Interface

Web-based GUI for Statistical Energy Analysis (SEA) built with React, FastAPI, and Three.js.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React + Vite)                 │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │  Header  │  │  Sidebar │  │  Editor  │  │   Results    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              GeometryViewer (Three.js)               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   REST API Endpoints                  │  │
│  │  /projects  /materials  /structures  /junctions      │  │
│  │  /analyze  /geometry  /energy  /modal-density        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              SEA Engine (sea_engine)                 │  │
│  │     Pyva wrapper for vibroacoustic simulation        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **3D Geometry Viewer**: Interactive Three.js viewer with orbit controls
- **Project Management**: Create, edit, and manage SEA projects
- **Parameter Configuration**: Add plates, rooms, junctions, loads
- **Templates**: Quick-start with wall-room, double wall, enclosure templates
- **Analysis**: Run SEA analysis from the web interface
- **Results Visualization**: Energy, modal density, SEA matrix plots
- **Export**: Download results as JSON for external tools

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Conda (recommended for sea_engine)

### Installation

1. Install backend dependencies:
```bash
cd web/backend
pip install -r requirements.txt
```

2. Install frontend dependencies:
```bash
cd web/frontend
npm install
```

3. Install sea_engine (from parent directory):
```bash
cd ../..
pip install -e .
```

### Running

Development mode (both frontend and backend):
```bash
cd web
npm run dev
```

This starts:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

Production build:
```bash
cd web/frontend
npm run build
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Projects
- `POST /projects` - Create project
- `GET /projects/{id}` - Get project info
- `DELETE /projects/{id}` - Delete project

### Materials
- `GET /materials` - List available materials

### Systems
- `POST /projects/{id}/structures` - Add structural element
- `POST /projects/{id}/acoustic-spaces` - Add acoustic space

### Junctions
- `POST /projects/{id}/junctions` - Add junction

### Analysis
- `POST /projects/{id}/analyze` - Run SEA analysis
- `GET /projects/{id}/geometry` - Get 3D geometry data
- `GET /projects/{id}/energy` - Get energy results
- `GET /projects/{id}/modal-density` - Get modal density
- `POST /projects/{id}/export-results` - Export results

## Technology Stack

### Frontend
- React 18 with TypeScript
- Vite for build
- Three.js for 3D rendering
- Recharts for data visualization
- React Router for navigation
- Lucide React for icons

### Backend
- FastAPI for REST API
- Pydantic for data validation
- Uvicorn ASGI server

## Project Structure

```
web/
├── backend/
│   ├── main.py           # FastAPI application
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── GeometryViewer.tsx
│   │   ├── pages/        # Page components
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectEditor.tsx
│   │   │   └── ResultsViewer.tsx
│   │   ├── utils/
│   │   │   └── api.ts    # API client
│   │   └── styles/       # CSS styles
│   ├── index.html
│   └── package.json
└── package.json          # Root package.json
```

## Screenshots

### Project Editor
- 3D geometry viewer
- System/junction management
- Quick actions panel

### Results Viewer
- Energy plots
- Modal density charts
- Export functionality
