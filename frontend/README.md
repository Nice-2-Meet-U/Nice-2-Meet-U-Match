# Nice 2 Meet U - Frontend

A simple web interface for the User Match microservices.

## Features

- 👤 **User Management**: Generate and manage user IDs
- 📍 **Pool Management**: Join pools by location with coordinates
- 💕 **Match Generation**: Generate matches with other pool members
- ✅ **Decision Making**: Accept or reject matches
- 📊 **View Data**: See pool members, matches, and decision history

## Setup

### Prerequisites

- The backend API must be running (default: `http://localhost:8000`)
- A modern web browser
- CORS must be enabled on the backend

### Enable CORS on Backend

Add CORS middleware to your `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Running the Frontend

You can serve the frontend in multiple ways:

#### Option 1: Using Python's HTTP Server

```bash
cd frontend
python3 -m http.server 8080
```

Then open http://localhost:8080 in your browser.

#### Option 2: Using Node.js HTTP Server

```bash
cd frontend
npx http-server -p 8080
```

#### Option 3: Using VS Code Live Server

1. Install the "Live Server" extension in VS Code
2. Right-click on `index.html`
3. Select "Open with Live Server"

#### Option 4: Direct File Access

Simply open `index.html` directly in your browser (may have CORS limitations).

## Configuration

Update the API base URL in `app.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000'; // Change to your deployed URL
```

For production deployment, update this to your actual API endpoint:
```javascript
const API_BASE_URL = 'https://matches-service-870022169527.us-central1.run.app';
```

## Usage Guide

### 1. Generate a User ID
- Click "Generate New UUID" to create a unique user identifier
- Or paste an existing UUID if you already have one

### 2. Join a Pool
- Enter a location name (e.g., "New York")
- Provide latitude and longitude coordinates
- Click "Join Pool"

### 3. View Pool Information
- Click "Get Pool Info" to see your current pool
- Click "View Pool Members" to see other users in your pool

### 4. Generate and View Matches
- Click "Generate New Matches" to create matches with pool members
- Click "View My Matches" to see all your matches
- Copy a Match ID for making decisions

### 5. Make Decisions
- Paste a Match ID into the decision field
- Click "✅ Accept" or "❌ Reject"
- View your decision history with "View Decisions"

## API Endpoints Used

The frontend interacts with these endpoints:

- `POST /users/{user_id}/pool` - Join a pool
- `GET /users/{user_id}/pool` - Get pool information
- `GET /users/{user_id}/pool/members` - Get pool members
- `DELETE /users/{user_id}/pool` - Leave pool
- `POST /users/{user_id}/matches` - Generate matches
- `GET /users/{user_id}/matches` - Get user matches
- `GET /users/{user_id}/decisions` - Get user decisions
- `POST /users/{user_id}/matches/{match_id}/decisions` - Submit decision

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console, make sure you've added the CORS middleware to your backend as described above.

### Connection Refused
Make sure your backend API is running on the configured port (default: 8000).

### Invalid UUID Format
Use the "Generate New UUID" button to create valid UUIDs, or ensure your manual UUIDs follow the standard format.

## Development Notes

This is a **draft UI** for demonstration and testing purposes. For production use, consider:

- Adding user authentication
- Input validation and sanitization
- Better error handling
- Loading states and spinners
- Responsive design improvements
- Real-time updates with WebSockets
- Form validation feedback
- Pagination for large lists
- State management (React/Vue)
- Environment configuration
