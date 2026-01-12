# Vue LLM Chat with SSE & MCP

A modern, dual-mode chat application built with Vue.js 3 and FastAPI. This project demonstrates advanced LLM integration features including Server-Sent Events (SSE), multi-modal file attachments, and Model Context Protocol (MCP) tool visualizations.

![Chat Interface](./docs/screenshot.png)

## Features

- **Real-time Streaming**: Uses Server-Sent Events (SSE) for robust, event-driven communication.
- **Multi-modal Support**: Upload and send images/files to the LLM.
- **Tool Visualization (MCP)**: Visual interface for backend tool execution (e.g., "Checking Weather...").
- **Clean UI**: A polished, ChatGPT-like interface using specific CSS styling (no Tailwind dependency).
- **Markdown Support**: Renders robust markdown with syntax highlighting.

## Prerequisites

- **Node.js**: v16+
- **Python**: v3.10+
- **OpenAI API Key**: You will need a valid API key.

## Setup

### 1. Backend (FastAPI)

Navigate to the `backend` directory:

```bash
cd backend
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn openai python-dotenv
```

Create a `.env` file in the `backend` folder:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

Run the server:

```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`.

### 2. Frontend (Vue 3)

Navigate to the `frontend` directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

Open `http://localhost:5173` in your browser.

## Usage

1.  **Chat**: Type messages and receive streaming responses.
2.  **Attachments**: Click the paperclip icon to attach images.
3.  **Tools**: Ask about the weather (e.g., "What is the weather in Tokyo?") to see the Tool Invocation UI in action.

## Project Structure

- `frontend/`: Vue.js 3 application + Vite.
  - `components/ChatInterface.vue`: Main chat logic (SSE parsing, UI).
- `backend/`: FastAPI application.
  - `main.py`: API endpoints, SSE generator, and Mock Tools.
