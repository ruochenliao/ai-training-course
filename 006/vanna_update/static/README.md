# Vanna Text2SQL Frontend

This is the frontend for the Vanna Text2SQL application. It provides a modern, Gemini-style chat interface for interacting with your database using natural language.

## Features

- Natural language to SQL translation
- Interactive chat interface
- SQL query execution and visualization
- Training data management
- Chat history tracking
- Dark mode support
- Responsive design

## Usage

1. Start the backend server (FastAPI application)
2. Open your browser and navigate to the server URL (default: http://localhost:8000)
3. Start asking questions about your data in natural language

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

## Development

The frontend is built using vanilla JavaScript with a modular architecture:

- `app.js` - Main application entry point
- `api-service.js` - Handles API communication with the backend
- `chat-ui.js` - Manages the chat interface
- `history-manager.js` - Handles chat history
- `training-manager.js` - Manages training data

## License

This project is licensed under the MIT License.
