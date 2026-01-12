<script setup>
import { ref, watch, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import highlightjs from 'highlight.js'
import 'highlight.js/styles/github.css'

const props = defineProps({
  protocol: {
    type: String,
    default: 'sse'
  }
})
// ... (keep MarkdownIt setup) ...

// State
const messages = ref([])
// ... (keep state) ...

// ... (keep helper functions) ...

const handleCustomSubmit = async () => {
  if ((!input.value.trim() && files.value.length === 0) || isLoading.value) return

  const userText = input.value
  const attachedFiles = [...files.value]
  
  // Clear input
  input.value = ''
  files.value = []
  if (fileInput.value) fileInput.value.value = ''

  isLoading.value = true

  // ... (keep message construction logic) ... 
  
  // Construct User Message & History (same as before)
  let userContent = userText
  if (attachedFiles.length > 0) {
    userContent = []
    if (userText) userContent.push({ type: 'text', text: userText })
    for (const file of attachedFiles) {
      const b64 = await fileToBase64(file)
      userContent.push({ type: 'image_url', image_url: { url: b64 } })
    }
  }

  const userMsgId = Date.now().toString()
  const userMessageObj = {
    id: userMsgId,
    role: 'user',
    content: typeof userContent === 'string' ? userContent : userText,
    experimental_attachments: attachedFiles.map(f => ({
      name: f.name,
      contentType: f.type,
      url: URL.createObjectURL(f)
    }))
  }
  
  if (Array.isArray(userContent)) userMessageObj.content = userText
  messages.value.push(userMessageObj)

  const aiMsgId = (Date.now() + 1).toString()
  messages.value.push({
    id: aiMsgId,
    role: 'assistant',
    content: '',
    toolInvocations: [] 
  })

  // Prepare Payload
  const payloadMessages = messages.value.slice(0, -1).map(m => {
    if (m.id === userMsgId && attachedFiles.length > 0) {
      return { role: m.role, content: userContent }
    }
    return { role: m.role, content: m.content }
  })

  // SSE ONLY Endpoint
  const endpoint = 'http://localhost:8000/api/chat/sse'

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: payloadMessages })
    })

    if (!response.ok) throw new Error(response.statusText)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value, { stream: true })
      
      buffer += chunk
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6).trim()
          if (dataStr === '[DONE]') continue
          
          try {
            const data = JSON.parse(dataStr)
            const lastMsg = messages.value[messages.value.length - 1]

            // Handle Text Delta
            if (data.type === 'text' && data.text) {
              lastMsg.content += data.text
            }
            // Handle Legacy/Simple Text
            else if (data.text) {
                lastMsg.content += data.text
            }
            
            // Handle Tool Start
            if (data.type === 'tool_start') {
              if (!lastMsg.toolInvocations) lastMsg.toolInvocations = []
              lastMsg.toolInvocations.push({
                toolCallId: data.toolCallId,
                toolName: data.toolName,
                state: 'running'
              })
            }

            // Handle Tool Result
            if (data.type === 'tool_result') {
                const toolCall = lastMsg.toolInvocations?.find(t => t.toolCallId === data.toolCallId)
                if (toolCall) {
                  toolCall.state = 'result'
                  toolCall.result = data.result
                }
            }

          } catch (e) {
            console.error('SSE Parse Error', e)
          }
        }
      }
      scrollToBottom()
    }

  } catch (err) {
    console.error('Chat Error:', err)
    messages.value.push({
      id: Date.now().toString(),
      role: 'system',
      content: 'Error submitting message: ' + err.message
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="chat-interface">
    <!-- Messages Area -->
    <div class="messages-container" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="welcome-text">
          <h2>How can I help you today?</h2>
          <p>Ask me anything about code, writing, or analysis.</p>
        </div>
      </div>
      <!-- ... (rest of template same) ... -->

      <div 
        v-for="m in messages" 
        :key="m.id" 
        class="message-row"
        :class="m.role"
      >
        <div class="avatar">
          {{ m.role === 'user' ? '👤' : '🤖' }}
        </div>
        
        <div class="message-bubble">
          <div class="role-name">{{ m.role === 'user' ? 'You' : 'Assistant' }}</div>
          
          <!-- Local Attachments Display -->
          <div v-if="m.experimental_attachments?.length" class="message-attachments">
            <div 
              v-for="(attachment, index) in m.experimental_attachments" 
              :key="index"
              class="attachment-preview"
            >
              <img 
                v-if="attachment.contentType?.startsWith('image/')"
                :src="attachment.url" 
                :alt="attachment.name"
              />
              <div v-else class="file-attachment-icon">
                📄 {{ attachment.name }}
              </div>
            </div>
          </div>

          <!-- Tool Invocations (Placeholder for custom logic if needed) -->
          <div v-if="m.toolInvocations?.length" class="tool-invocations">
            <div class="tool-block">Tool usage not fully implemented in Custom Mode yet</div>
          </div>

          <!-- Text Content -->
          <div class="markdown-body" v-html="md.render(m.content)"></div>
        </div>
      </div>
      
      <div v-if="isLoading" class="loading-indicator">
        Thinking...
      </div>
    </div>

    <!-- Input Area -->
    <div class="input-container">
      <div v-if="files.length > 0" class="file-previews">
        <div v-for="(file, index) in files" :key="index" class="preview-item">
          <span class="file-name">{{ file.name }}</span>
          <button @click="removeFile(index)" class="remove-file-btn">×</button>
        </div>
      </div>

      <form @submit.prevent="handleCustomSubmit" class="input-box">
        <input 
          type="file" 
          ref="fileInput"
          multiple
          class="hidden-input"
          @change="handleFileChange"
        />
        
        <button type="button" class="action-btn" @click="triggerFileInput" title="Attach file">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
        </button>

        <input 
          v-model="input" 
          placeholder="Type your message..." 
          class="chat-input" 
          :disabled="isLoading"
        />
        <button type="submit" class="send-btn" :disabled="isLoading || (!input.trim() && files.length === 0)">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.protocol-badge {
  font-size: 0.7rem;
  background: #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 5px;
  color: #64748b;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  background-color: var(--bg-color);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--text-secondary);
}

.message-row {
  display: flex;
  gap: 1rem;
  max-width: 85%;
  animation: fadeIn 0.3s ease;
}

.message-row.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-row.assistant {
  align-self: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--chat-bg);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

.message-bubble {
  padding: 1rem 1.25rem;
  border-radius: 12px;
  position: relative;
  line-height: 1.6;
  font-size: 0.95rem;
  min-width: 100px;
  text-align: left;
}

.message-row.user .message-bubble {
  background: var(--user-bubble);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: var(--shadow-md);
}

.message-row.assistant .message-bubble {
  background: var(--ai-bubble);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 4px;
  box-shadow: var(--shadow-sm);
  color: var(--text-primary);
}

/* Attachments Styles */
.message-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.8rem;
}

.attachment-preview img {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.2);
}

.file-attachment-icon {
  background: rgba(0,0,0,0.05);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Tool Invocations Styles (MCP) */
.tool-invocations {
  margin-bottom: 0.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tool-block {
  background: #f1f5f9;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0.5rem 0.8rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tool-name {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: var(--text-primary);
}

.tool-state.running::after {
  content: '...';
  animation: dots 1.5s infinite;
}

.tool-result {
  margin-top: 0.5rem;
  font-family: monospace;
  background: rgba(255,255,255,0.5);
  padding: 0.25rem;
  border-radius: 4px;
  font-size: 0.75rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@keyframes dots {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}

/* Markdown Styles */
:deep(.markdown-body p) { margin: 0 0 0.8rem 0; }
:deep(.markdown-body p:last-child) { margin-bottom: 0; }
:deep(.message-row.user .markdown-body a) { color: #e0e7ff; }
:deep(.message-row.assistant .markdown-body a) { color: var(--primary); }
:deep(.markdown-body pre) { background: #f1f5f9; padding: 1rem; border-radius: 8px; overflow-x: auto; margin: 0.8rem 0; }
:deep(.markdown-body code) { font-family: 'Fira Code', monospace; background-color: rgba(0,0,0,0.05); padding: 2px 4px; border-radius: 4px; }

/* Input Area */
.input-container {
  padding: 1.5rem;
  background: var(--bg-color);
  border-top: 1px solid var(--border-color);
}

.file-previews {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.preview-item {
  background: #e2e8f0;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.remove-file-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 1rem;
  line-height: 1;
  color: #64748b;
}

.input-box {
  display: flex;
  gap: 0.75rem;
  background: var(--chat-bg);
  padding: 0.5rem;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
  align-items: flex-end; /* Align bottom for multi-line */
}

.input-box:focus-within {
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
  border-color: var(--primary);
}

.hidden-input {
  display: none;
}

.action-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f1f5f9;
  color: var(--text-primary);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  padding: 0.8rem 0.2rem;
  font-size: 1rem;
  font-family: inherit;
  resize: none;
  height: 24px; /* Basic height, ideally auto-grow */
}

.chat-input:focus {
  outline: none;
}

.send-btn {
  background: var(--primary);
  border: none;
  border-radius: 8px;
  width: 36px;
  height: 36px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: default;
  background: #cbd5e1;
  color: #64748b;
}

.loading-indicator {
  padding: 1rem;
  font-style: italic;
  color: #64748b;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
