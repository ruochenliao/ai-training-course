# Vanna Text2SQL Application

This is a Text2SQL application that allows users to query databases using natural language. The application consists of a FastAPI backend and a modern, Gemini-style frontend interface.

## Directory Structure

```
vanna/
├── app.py              # FastAPI backend application
├── cache.py            # Memory cache implementation
├── server.js           # Development server for frontend
├── static/             # Frontend static files
│   ├── css/            # CSS stylesheets
│   ├── img/            # Images and icons
│   ├── js/             # JavaScript modules
│   └── index.html      # Main HTML file
└── README.md           # This file
```

## Running the Application

### Prerequisites

- Python 3.7+ for the backend
- Node.js for the development server (optional)
- Modern web browser (Chrome, Firefox, Edge, etc.)

### Option 1: Running Backend and Frontend Together

1. Start the FastAPI backend:

```bash
cd vanna_update
python -m uvicorn app:app --reload --port 8000
```

2. Open your browser and navigate to http://localhost:8000

### Option 2: Running Backend and Frontend Separately (for Development)

1. Start the FastAPI backend:

```bash
cd vanna_update
python -m uvicorn app:app --reload --port 8000
```

2. Start the frontend development server:

```bash
cd vanna_update
node server.js
```

3. Open your browser and navigate to http://localhost:9000

### Troubleshooting

1. **404 Errors for CSS/JS Files**:
   - Make sure the server.js file is correctly handling the /static/ prefix
   - Try accessing http://localhost:9000/test.html to check if the server is working
   - Try the simplified interface at http://localhost:9000/simple.html

2. **CORS Issues**:
   - If you see CORS errors in the console, make sure both servers are running
   - Check that the API service is using the correct base URL

3. **Module Loading Errors**:
   - If you see errors about modules, make sure you're using the type="module" attribute in script tags
   - Check that all import paths are correct and use absolute paths

4. **Backend Connection Issues**:
   - Make sure the FastAPI backend is running on port 8000
   - Check that the API service is using the correct base URL

## Features

- Natural language to SQL translation
- Interactive chat interface
- SQL query execution and visualization
- Training data management
- Chat history tracking
- Dark mode support
- Responsive design

## Usage

1. Type a question about your data in the input field at the bottom of the screen
2. The system will:
   - Translate your question to SQL
   - Execute the query
   - Display the results in a table
   - Generate a visualization if appropriate
   - Suggest followup questions

3. You can also:
   - View your chat history in the sidebar
   - Add training data to improve the system
   - Toggle between light and dark mode

## Example Questions

- "Show me the top 10 customers by revenue"
- "What were our sales in the last quarter?"
- "How many products do we have in each category?"
- "Which regions had the highest growth last year?"

## Training the System

You can improve the system's performance by adding training data:

1. Click on "Training Data" in the sidebar
2. Switch to the "Add Training Data" tab
3. Enter a natural language question and its corresponding SQL query
4. Optionally add DDL (table definitions) and documentation
5. Click "Save Training Data"
