/**
 * ChatInterface - Handles the chat UI and user interactions
 */
class ChatInterface {
    constructor(socketManager) {
        this.socketManager = socketManager;
        this.messageHistory = [];
        this.isConversationActive = false;
        this.hasOngoingConversation = false;  // NEW: Track if conversation is ongoing
        
        // DOM elements
        this.chatMessages = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.clearChatBtn = document.getElementById('clearChatBtn');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingStatus = document.getElementById('loadingStatus');
        
        this.initialize();
    }
    
    initialize() {
        this.setupEventListeners();
        this.setupSocketListeners();
        console.log('[ChatInterface] Initialized');
    }
    
    setupEventListeners() {
        // Send button click
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Enter key handling
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (e.ctrlKey) {
                    // Ctrl+Enter sends message
                    e.preventDefault();
                    this.sendMessage();
                } else if (!e.shiftKey) {
                    // Prevent default Enter behavior in textarea
                    // (Allow Shift+Enter for new lines)
                    e.preventDefault();
                }
            }
        });
        
        // Clear chat button
        this.clearChatBtn.addEventListener('click', () => {
            this.clearChat();
        });
        
        // Auto-resize textarea
        this.userInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });
    }
    
    setupSocketListeners() {
        // Session established
        this.socketManager.on('session_established', (data) => {
            this.showSystemMessage('Connected! Session ID: ' + data.session_id.slice(0, 8) + '...');
        });
        
        // Conversation started
        this.socketManager.on('conversation_started', (data) => {
            this.isConversationActive = true;
            this.hasOngoingConversation = true;  // NEW
            this.showLoading(true, 'Starting conversation...');
            this.disableInput();
        });
        
        // Agent conversation started
        this.socketManager.on('agent_conversation_started', (data) => {
            this.updateLoadingStatus('Agents are processing your query...');
        });
        
        // Thinking process updates
        this.socketManager.on('thinking_process', (data) => {
            if (data.type === 'main_conversation_started') {
                this.updateLoadingStatus('Main conversation started...');
            }
        });
        
        // Main conversation completed
        this.socketManager.on('main_conversation_completed', (data) => {
            this.updateLoadingStatus('Generating final response...');
        });
        
        // OLD: Final conversation completed (keep for backward compatibility)
        this.socketManager.on('conversation_completed', (data) => {
            this.isConversationActive = false;
            this.showLoading(false);
            this.enableInput();
            this.addAgentMessage(data.final_response, null);
            this.showSystemMessage('Conversation completed!');
        });
        
        // NEW: Response completed (single response finished, conversation continues)
        this.socketManager.on('response_completed', (data) => {
            this.isConversationActive = false;  // Ready for next message
            this.showLoading(false);
            this.enableInput();
            this.addAgentMessage(data.final_response, null);
            // Don't show "conversation completed" - it's ongoing
            if (data.message_count === 1) {
                this.showSystemMessage('Response received! Ask follow-up questions to continue.');
            }
        });
        
        // NEW: Conversation ended (explicitly ended by user)
        this.socketManager.on('conversation_ended', (data) => {
            this.isConversationActive = false;
            this.hasOngoingConversation = false;
            this.showLoading(false);
            this.enableInput();
            this.showSystemMessage('Conversation ended. Start a new conversation!');
        });
        
        // Error handling
        this.socketManager.on('error', (data) => {
            this.handleError(data.message || 'An error occurred');
        });
        
        this.socketManager.on('conversation_error', (data) => {
            this.handleError('Conversation error: ' + (data.error || 'Unknown error'));
        });
        
        this.socketManager.on('agent_error', (data) => {
            this.handleError('Agent error: ' + (data.error || 'Unknown error'));
        });
    }
    
    sendMessage() {
        const message = this.userInput.value.trim();
        
        if (!message) {
            this.showError('Please enter a message');
            return;
        }
        
        if (this.isConversationActive) {
            this.showError('Please wait for the current conversation to complete');
            return;
        }
        
        if (!this.socketManager.isSocketConnected()) {
            this.showError('Not connected to server');
            return;
        }
        
        // Add user message to chat
        this.addUserMessage(message);
        
        // Clear input
        this.userInput.value = '';
        this.autoResizeTextarea();
        
        // Send to backend
        const success = this.socketManager.startConversation(message);
        if (!success) {
            this.showError('Failed to start conversation');
            this.enableInput();
        }
    }
    
    addUserMessage(message) {
        const messageData = {
            type: 'user',
            content: message,
            timestamp: new Date().toISOString()
        };
        
        this.messageHistory.push(messageData);
        this.renderMessage(messageData);
        this.scrollToBottom();
    }
    
    addAgentMessage(message, agentName = 'Assistant') {
        const messageData = {
            type: 'agent',
            content: message,
            agentName: agentName,
            timestamp: new Date().toISOString()
        };
        
        this.messageHistory.push(messageData);
        this.renderMessage(messageData);
        this.scrollToBottom();
    }
    
    addSystemMessage(message) {
        const messageData = {
            type: 'system',
            content: message,
            timestamp: new Date().toISOString()
        };
        
        this.messageHistory.push(messageData);
        this.renderMessage(messageData);
        this.scrollToBottom();
    }
    
    renderMessage(messageData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${messageData.type}`;
        
        let messageHTML = '';
        
        if (messageData.type === 'user') {
            messageHTML = `
                <div class="message-bubble">
                    <div class="message-content markdown-content">
                        ${this.formatMessage(messageData.content)}
                    </div>
                </div>
                <div class="message-timestamp">
                    ${this.formatTimestamp(messageData.timestamp)}
                </div>
            `;
        } else if (messageData.type === 'agent') {
            // Only show agent name if it exists and is not null/empty
            const hasAgentName = messageData.agentName && messageData.agentName.trim() !== '';
            messageHTML = `
                <div class="message-bubble">
                    ${hasAgentName ? `<div class="agent-name-header"><strong>${messageData.agentName}</strong></div>` : ''}
                    <div class="message-content markdown-content">
                        ${this.formatMessage(messageData.content)}
                    </div>
                </div>
                <div class="message-timestamp">
                    ${this.formatTimestamp(messageData.timestamp)}
                </div>
            `;
        } else if (messageData.type === 'system') {
            messageHTML = `
                <div class="alert alert-info alert-sm">
                    <i class="fas fa-info-circle me-2"></i>
                    <span class="system-message-content">${messageData.content}</span>
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageHTML;
        
        // Process markdown content if markdown utils are available
        if (window.markdownUtils) {
            window.markdownUtils.processMessageElement(messageDiv);
        }
        
        // Remove welcome message if it exists
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.chatMessages.appendChild(messageDiv);
    }
    
    formatMessage(content) {
        // Handle empty or null content
        if (!content || typeof content !== 'string') {
            return '';
        }
        
        // Use the enhanced markdown utilities for proper rendering
        if (window.markdownUtils) {
            return window.markdownUtils.renderMarkdown(content.trim());
        }
        
        // Fallback to basic formatting if markdown utils not available
        let formatted = content.trim()
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code class="inline-code">$1</code>')
            .replace(/\n/g, '<br>');
        
        // Handle code blocks with better formatting
        formatted = formatted.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
            const langClass = lang ? ` class="language-${lang}"` : '';
            return `<div class="code-block-wrapper"><pre><code${langClass}>${code.trim()}</code></pre></div>`;
        });
        
        return formatted;
    }
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
    
    showSystemMessage(message) {
        this.addSystemMessage(message);
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        this.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    handleError(message) {
        this.isConversationActive = false;
        this.showLoading(false);
        this.enableInput();
        this.showError(message);
    }
    
    showLoading(show, status = 'Processing...') {
        if (show) {
            this.loadingStatus.textContent = status;
            this.loadingOverlay.classList.add('show');
        } else {
            this.loadingOverlay.classList.remove('show');
        }
    }
    
    updateLoadingStatus(status) {
        this.loadingStatus.textContent = status;
    }
    
    disableInput() {
        this.userInput.disabled = true;
        this.sendBtn.disabled = true;
        this.sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }
    
    enableInput() {
        this.userInput.disabled = false;
        this.sendBtn.disabled = false;
        this.sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        this.userInput.focus();
    }
    
    autoResizeTextarea() {
        this.userInput.style.height = 'auto';
        this.userInput.style.height = Math.min(this.userInput.scrollHeight, 100) + 'px';
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    clearChat() {
        if (this.isConversationActive) {
            if (!confirm('A conversation is currently active. Are you sure you want to clear the chat?')) {
                return;
            }
        }
        
        // NEW: End conversation on backend if ongoing
        if (this.hasOngoingConversation) {
            this.socketManager.endConversation();
        }
        
        // Clear frontend state
        this.messageHistory = [];
        this.hasOngoingConversation = false;
        this.isConversationActive = false;
        
        this.chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    Welcome to the Thought Agent Interface! Ask any question to get started.
                </div>
            </div>
        `;
        
        this.showSystemMessage('Chat cleared');
    }
    
    // Public API
    getMessageHistory() {
        return [...this.messageHistory];
    }
    
    isActive() {
        return this.isConversationActive;
    }
}

// Export for use in other modules
window.ChatInterface = ChatInterface;
