/**
 * SocketManager - Handles all WebSocket communication with the backend
 */
class SocketManager {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.eventListeners = {};
        
        this.initialize();
    }
    
    initialize() {
        try {
            // Initialize socket connection
            this.socket = io();
            
            // Set up core event listeners
            this.setupCoreListeners();
            
            console.log('[SocketManager] Initialized');
        } catch (error) {
            console.error('[SocketManager] Failed to initialize:', error);
        }
    }
    
    setupCoreListeners() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('[SocketManager] Connected to server');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('[SocketManager] Disconnected from server');
            this.isConnected = false;
            this.updateConnectionStatus(false);
        });
        
        // Session events
        this.socket.on('connected', (data) => {
            console.log('[SocketManager] Session established:', data.session_id);
            this.sessionId = data.session_id;
            this.emit('session_established', data);
        });
        
        // Conversation events
        this.socket.on('conversation_started', (data) => {
            console.log('[SocketManager] Conversation started');
            this.emit('conversation_started', data);
        });
        
        this.socket.on('agent_conversation_started', (data) => {
            console.log('[SocketManager] Agent conversation started');
            this.emit('agent_conversation_started', data);
        });
        
        this.socket.on('thinking_process', (data) => {
            console.log('[SocketManager] Thinking process update');
            this.emit('thinking_process', data);
        });
        
        this.socket.on('agent_started', (data) => {
            console.log('[SocketManager] Agent started:', data.agent_name);
            this.emit('agent_started', data);
        });
        
        this.socket.on('agent_message', (data) => {
            console.log('[SocketManager] Agent message:', data.agent_name);
            this.emit('agent_message', data);
        });
        
        this.socket.on('custom_agent_thinking', (data) => {
            console.log('[SocketManager] Custom agent thinking:', data.agent);
            this.emit('custom_agent_thinking', data);
        });
        
        // Store internal conversation events
        this.socket.on('store_internal_conversation', (data) => {
            console.log('[SocketManager] Store internal conversation:', data.agent_name, data.step_id);
            this.emit('store_internal_conversation', data);
        });
        
        // ThoughtAgent lifecycle events
        this.socket.on('thought_agent_lifecycle', (data) => {
            console.log('[SocketManager] ThoughtAgent lifecycle event:', data.action, data.thought_agent_id);
            this.emit('thought_agent_lifecycle', data);
        });
        
        this.socket.on('main_conversation_completed', (data) => {
            console.log('[SocketManager] Main conversation completed');
            this.emit('main_conversation_completed', data);
        });
        
        this.socket.on('conversation_completed', (data) => {
            console.log('[SocketManager] Conversation completed');
            this.emit('conversation_completed', data);
        });
        
        // NEW: Response completed (single response finished, conversation continues)
        this.socket.on('response_completed', (data) => {
            console.log('[SocketManager] Response completed');
            this.emit('response_completed', data);
        });
        
        // NEW: Conversation ended (explicitly ended by user)
        this.socket.on('conversation_ended', (data) => {
            console.log('[SocketManager] Conversation ended');
            this.emit('conversation_ended', data);
        });
        
        // Error events
        this.socket.on('error', (data) => {
            console.error('[SocketManager] Error:', data);
            this.emit('error', data);
        });
        
        this.socket.on('conversation_error', (data) => {
            console.error('[SocketManager] Conversation error:', data);
            this.emit('conversation_error', data);
        });
        
        this.socket.on('agent_error', (data) => {
            console.error('[SocketManager] Agent error:', data);
            this.emit('agent_error', data);
        });
    }
    
    // Public API
    startConversation(query) {
        if (!this.sessionId) {
            console.error('[SocketManager] No session ID available');
            return false;
        }
        
        if (!query || query.trim() === '') {
            console.error('[SocketManager] Empty query');
            return false;
        }
        
        console.log('[SocketManager] Starting conversation:', query);
        this.socket.emit('start_conversation', {
            session_id: this.sessionId,
            query: query.trim()
        });
        
        return true;
    }
    
    joinSession(sessionId) {
        this.socket.emit('join_session', {
            session_id: sessionId
        });
    }
    
    endConversation() {
        if (!this.sessionId) {
            console.error('[SocketManager] No session ID available');
            return false;
        }
        
        console.log('[SocketManager] Ending conversation');
        this.socket.emit('end_conversation', {
            session_id: this.sessionId
        });
        
        return true;
    }
    
    // Event listener management
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }
    
    off(event, callback) {
        if (!this.eventListeners[event]) return;
        
        const index = this.eventListeners[event].indexOf(callback);
        if (index > -1) {
            this.eventListeners[event].splice(index, 1);
        }
    }
    
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[SocketManager] Error in event listener for ${event}:`, error);
                }
            });
        }
    }
    
    // UI Updates
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const iconElement = statusElement.querySelector('.fa-circle');
        
        if (connected) {
            statusElement.innerHTML = '<i class="fas fa-circle text-success me-1"></i>Connected';
            iconElement.classList.remove('text-danger');
            iconElement.classList.add('text-success');
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle text-danger me-1"></i>Disconnected';
            iconElement.classList.remove('text-success');
            iconElement.classList.add('text-danger');
        }
    }
    
    // Utility methods
    getSessionId() {
        return this.sessionId;
    }
    
    isSocketConnected() {
        return this.isConnected && this.socket && this.socket.connected;
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
    
    reconnect() {
        if (this.socket) {
            this.socket.connect();
        }
    }
}

// Export for use in other modules
window.SocketManager = SocketManager;
