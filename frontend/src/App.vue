<script setup>
import ChatInterface from './components/ChatInterface.vue'
</script>

<template>
  <div class="chat-wrapper">
    <!-- Header -->
    <header class="chat-header">
      <div class="header-content">
        <h1>✨ AI Assistant</h1>
        <span class="status-dot"></span>
      </div>
    </header>
    
    <!-- Chat Interface (SSE Only) -->
    <ChatInterface protocol="sse" />

  </div>
</template>

<style>
/* Global Resets & Fonts */
:root {
  --bg-color: #f8fafc;        /* Slate 50 */
  --chat-bg: #ffffff;         /* White */
  --primary: #4f46e5;         /* Indigo 600 */
  --primary-hover: #4338ca;   /* Indigo 700 */
  --text-primary: #1e293b;    /* Slate 800 */
  --text-secondary: #64748b;  /* Slate 500 */
  --user-bubble: #4f46e5;     /* Primary color for user */
  --ai-bubble: #ffffff;       /* White for AI */
  --border-color: #e2e8f0;    /* Slate 200 */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

body {
  margin: 0;
  background-color: var(--bg-color);
  color: var(--text-primary);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.chat-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1000px;
  margin: 0 auto;
  background: var(--bg-color);
  position: relative;
  box-shadow: 0 0 20px rgba(0,0,0,0.05);
}

.chat-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

h1 {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
  /* margin-right: auto; REMOVED since no switcher */
  background: linear-gradient(to right, #4f46e5, #9333ea);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.status-dot {
  width: 8px;
  height: 8px;
  background-color: #22c55e;
  border-radius: 50%;
  box-shadow: 0 0 8px #22c55e;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
