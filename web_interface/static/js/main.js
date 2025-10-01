/**
 * Main Application - Initializes and coordinates all components
 */
class ThoughtAgentApp {
    constructor() {
        this.socketManager = null;
        this.chatInterface = null;
        this.thinkingPanel = null;
        this.detailsPanel = null;
        this.isInitialized = false;
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.initialize();
            });
        } else {
            this.initialize();
        }
    }
    
    initialize() {
        try {
            console.log('[ThoughtAgentApp] Initializing application...');
            
            // Initialize core components
            this.socketManager = new SocketManager();
            this.chatInterface = new ChatInterface(this.socketManager);
            this.thinkingPanel = new ThinkingPanel(this.socketManager);
            this.detailsPanel = new DetailsPanel(this.socketManager, this.thinkingPanel);
            
            // Make components globally accessible for event handlers
            window.thinkingPanel = this.thinkingPanel;
            window.detailsPanel = this.detailsPanel;
            window.chatInterface = this.chatInterface; // Make chat interface globally accessible
            
            // Setup application-level event listeners
            this.setupApplicationEvents();
            
            // Setup keyboard shortcuts
            this.setupKeyboardShortcuts();
            
            // Initialize UI state
            this.initializeUIState();
            
            this.isInitialized = true;
            console.log('[ThoughtAgentApp] Application initialized successfully');
            
        } catch (error) {
            console.error('[ThoughtAgentApp] Failed to initialize:', error);
            this.showInitializationError(error);
        }
    }
    
    setupApplicationEvents() {
        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
        
        // Handle beforeunload (page close/refresh)
        window.addEventListener('beforeunload', (e) => {
            if (this.chatInterface && this.chatInterface.isActive()) {
                e.preventDefault();
                e.returnValue = 'A conversation is currently active. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
        
        // Global error handling
        window.addEventListener('error', (e) => {
            console.error('[ThoughtAgentApp] Global error:', e.error);
            this.handleGlobalError(e.error);
        });
        
        // Unhandled promise rejections
        window.addEventListener('unhandledrejection', (e) => {
            console.error('[ThoughtAgentApp] Unhandled promise rejection:', e.reason);
            this.handleGlobalError(e.reason);
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K - Focus on input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const userInput = document.getElementById('userInput');
                if (userInput) {
                    userInput.focus();
                }
            }
            
            // Escape - Clear focus/close modals
            if (e.key === 'Escape') {
                document.activeElement?.blur();
            }
            
            // Ctrl/Cmd + / - Show keyboard shortcuts
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.showKeyboardShortcuts();
            }
        });
    }
    
    initializeUIState() {
        // Set initial focus
        const userInput = document.getElementById('userInput');
        if (userInput) {
            userInput.focus();
        }
        
        // Initialize tooltips if Bootstrap is available
        if (typeof bootstrap !== 'undefined') {
            const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            tooltips.forEach(tooltip => {
                new bootstrap.Tooltip(tooltip);
            });
        }
        
        // Add version info or other initialization UI updates
        this.addVersionInfo();
    }
    
    handleWindowResize() {
        // Adjust layout if needed
        // This could be extended for responsive layout adjustments
    }
    
    handleVisibilityChange() {
        if (document.hidden) {
            console.log('[ThoughtAgentApp] Page hidden');
        } else {
            console.log('[ThoughtAgentApp] Page visible');
            // Optionally refresh connection status
            if (this.socketManager && !this.socketManager.isSocketConnected()) {
                console.log('[ThoughtAgentApp] Attempting to reconnect...');
                this.socketManager.reconnect();
        }
    }

    // initializeMarkdown() {
    //     // Initialize Highlight.js for code syntax highlighting
    //     if (typeof hljs !== 'undefined') {
    //         hljs.highlightAll();
    //         console.log('[ThoughtAgentApp] Highlight.js initialized');
    //     } else {
    //         console.warn('[ThoughtAgentApp] Highlight.js not available');
    //     }
        
    //     // Configure marked.js if available
    //     if (typeof marked !== 'undefined') {
    //         marked.setOptions({
    //             highlight: function(code, lang) {
    //                 if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
    //                     try {
    //                         return hljs.highlight(code, { language: lang }).value;
    //                     } catch (err) {
    //                         console.warn('[ThoughtAgentApp] Highlight.js error:', err);
    //                     }
    //                 }
    //                 return code;
    //             },
    //             breaks: true,
    //             gfm: true,
    //             tables: true,
    //             sanitize: false,
    //             smartLists: true,
    //             smartypants: false
    //         });
    //         console.log('[ThoughtAgentApp] Marked.js configured');
    //     } else {
    //         console.warn('[ThoughtAgentApp] Marked.js not available');
    //     }
    // }
}

    handleGlobalError(error) {
        // Show user-friendly error message
        const errorMessage = error?.message || 'An unexpected error occurred';
        this.showErrorNotification(errorMessage);
    }
    
    showInitializationError(error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger position-fixed top-0 start-50 translate-middle-x mt-3';
        errorDiv.style.zIndex = '9999';
        errorDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle fa-2x text-danger me-3"></i>
                <div>
                    <h6 class="mb-1">Application Failed to Initialize</h6>
                    <p class="mb-0">${error.message || 'Unknown error'}</p>
                    <small class="text-muted">Please refresh the page to try again.</small>
                </div>
            </div>
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 10000);
    }
    
    showErrorNotification(message) {
        // Create toast notification for errors
        const toastDiv = document.createElement('div');
        toastDiv.className = 'position-fixed top-0 end-0 p-3';
        toastDiv.style.zIndex = '9999';
        toastDiv.innerHTML = `
            <div class="toast show" role="alert">
                <div class="toast-header bg-danger text-white">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong class="me-auto">Error</strong>
                    <button type="button" class="btn-close btn-close-white" onclick="this.closest('.position-fixed').remove()"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        document.body.appendChild(toastDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toastDiv.parentNode) {
                toastDiv.remove();
            }
        }, 5000);
    }
    
    showKeyboardShortcuts() {
        const shortcuts = [
            { key: 'Ctrl + K', description: 'Focus on input field' },
            { key: 'Ctrl + Enter', description: 'Send message' },
            { key: 'Escape', description: 'Clear focus' },
            { key: 'Ctrl + /', description: 'Show keyboard shortcuts' }
        ];
        
        const shortcutsHTML = shortcuts.map(s => 
            `<tr><td><kbd>${s.key}</kbd></td><td>${s.description}</td></tr>`
        ).join('');
        
        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = `
            <div class="modal fade" id="shortcutsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-keyboard me-2"></i>
                                Keyboard Shortcuts
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <table class="table table-sm">
                                <tbody>
                                    ${shortcutsHTML}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modalDiv);
        
        if (typeof bootstrap !== 'undefined') {
            const modal = new bootstrap.Modal(document.getElementById('shortcutsModal'));
            modal.show();
            
            // Clean up modal when hidden
            document.getElementById('shortcutsModal').addEventListener('hidden.bs.modal', () => {
                modalDiv.remove();
            });
        }
    }
    
    addVersionInfo() {
        // Add version or build info to the footer or somewhere appropriate
        const versionInfo = {
            version: '1.0.0',
            buildDate: new Date().toISOString().split('T')[0]
        };
        
        // This could be displayed in a footer or about section
        console.log('[ThoughtAgentApp] Version:', versionInfo.version, 'Build:', versionInfo.buildDate);
    }
    
    // Public API
    getSocketManager() {
        return this.socketManager;
    }
    
    getChatInterface() {
        return this.chatInterface;
    }
    
    getThinkingPanel() {
        return this.thinkingPanel;
    }
    
    getDetailsPanel() {
        return this.detailsPanel;
    }
    
    isAppInitialized() {
        return this.isInitialized;
    }
}

/**
 * DetailsPanel - Handles the right panel showing detailed agent information
 */
class DetailsPanel {
    constructor(socketManager, thinkingPanel) {
        this.socketManager = socketManager;
        this.thinkingPanel = thinkingPanel;
        this.customAgentData = new Map();
        this.selectedAgent = null;
        
        // DOM elements
        this.detailsContent = document.getElementById('detailsContent');
        this.refreshDetailsBtn = document.getElementById('refreshDetailsBtn');
        
        this.initialize();
    }
    
    initialize() {
        this.setupEventListeners();
        this.setupSocketListeners();
        console.log('[DetailsPanel] Initialized');
    }
    
    setupEventListeners() {
        // Refresh button
        this.refreshDetailsBtn.addEventListener('click', () => {
            this.refreshDetails();
        });
    }
    
    setupSocketListeners() {
        // Custom agent thinking events
        this.socketManager.on('custom_agent_thinking', (data) => {
            this.addCustomAgentThinking(data);
        });
        
        // Internal conversation events for custom agents
        this.socketManager.on('agent_internal_conversation', (data) => {
            this.addInternalConversationMessage(data);
        });
        
        // Agent started events for selection
        this.socketManager.on('agent_started', (data) => {
            this.addAgentForSelection(data);
        });
        
        // Conversation completed
        this.socketManager.on('conversation_completed', (data) => {
            this.showConversationSummary(data);
        });
    }
    
    addCustomAgentThinking(data) {
        const agentName = data.agent;
        
        if (!this.customAgentData.has(agentName)) {
            this.customAgentData.set(agentName, {
                name: agentName,
                phases: [],
                internalConversation: [],
                displayName: this.getAgentDisplayName(agentName)
            });
        }
        
        const agentData = this.customAgentData.get(agentName);
        agentData.phases.push({
            phase: data.phase,
            content: data.content,
            timestamp: data.timestamp
        });
        
        // Update display if this agent is selected
        if (this.selectedAgent === agentName) {
            this.displayAgentDetails(agentName);
        }
        
        // Add to selection list
        this.updateAgentSelectionList();

        console.log(`[DetailsPanel] Added custom agent thinking: ${agentName} - ${data.phase} - ${JSON.stringify(data)}`);
    }

    addInternalConversationMessage(data) {
        const agentName = data.agent_name;
        
        // Initialize agent data if not exists
        if (!this.customAgentData.has(agentName)) {
            this.customAgentData.set(agentName, {
                name: agentName,
                phases: [],
                internalConversation: [],
                displayName: this.getAgentDisplayName(agentName)
            });
        }
        
        const agentData = this.customAgentData.get(agentName);
        
        // Process different types of internal messages
        let messageType = 'internal_message';
        let content = data.content;
        
        if (data.type === 'internal_start') {
            messageType = 'internal_start';
        } else if (data.type === 'tool_call') {
            messageType = 'tool_call';
            // Extract tool call details
            if (data.tool_calls && data.tool_calls.length > 0) {
                const toolCall = data.tool_calls[0];
                content = `🔧 **Tool Call: ${toolCall.function?.name || 'Unknown'}**\n\n`;
                if (toolCall.function?.arguments) {
                    try {
                        const args = JSON.parse(toolCall.function.arguments);
                        content += `**Parameters:**\n\`\`\`json\n${JSON.stringify(args, null, 2)}\n\`\`\`\n\n`;
                    } catch (e) {
                        content += `**Parameters:** ${toolCall.function.arguments}\n\n`;
                    }
                }
                content += `**Original Content:**\n${data.content}`;
            }
        } else if (data.type === 'internal_error') {
            messageType = 'internal_error';
        }
        
        // Add to internal conversation
        agentData.internalConversation.push({
            type: messageType,
            content: content,
            internal_agent: data.internal_agent || 'internal',
            role: data.role || 'assistant',
            timestamp: data.timestamp,
            messageId: data.message_id,
            tool_calls: data.tool_calls || []
        });
        
        // Update current view if showing this agent's conversation
        if (this.currentView && this.currentView.type === 'agent_conversation' && 
            this.currentView.agentName === agentName) {
            this.updateInternalConversationView(agentName);
        }
        
        // Update display if this agent is selected in main view
        if (this.selectedAgent === agentName) {
            this.displayAgentDetails(agentName);
        }
        
        console.log(`[DetailsPanel] Added internal conversation message for ${agentName}: ${messageType}`);
    }
    
    addAgentForSelection(data) {
        // This ensures all agents are available for selection
        this.updateAgentSelectionList();
    }
    
    updateAgentSelectionList() {
        // Remove no-details message
        const noDetails = this.detailsContent.querySelector('.no-details');
        if (noDetails) {
            noDetails.remove();
        }
        
        // Remove agent selection div if it exists
        const selectionDiv = this.detailsContent.querySelector('.agent-selection');
        if (selectionDiv) {
            selectionDiv.remove();
        }
    }
    
    selectAgent(agentName) {
        this.selectedAgent = agentName;
        this.displayAgentDetails(agentName);
        
        // Update button states
        const buttons = this.detailsContent.querySelectorAll('.btn-outline-primary');
        buttons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.onclick.toString().includes(agentName)) {
                btn.classList.add('active');
            }
        });
    }
    
    displayAgentDetails(agentName) {
        // Get existing details container or create it
        let detailsDiv = this.detailsContent.querySelector('.agent-details');
        if (!detailsDiv) {
            detailsDiv = document.createElement('div');
            detailsDiv.className = 'agent-details';
            this.detailsContent.appendChild(detailsDiv);
        }
        
        const displayName = this.getAgentDisplayName(agentName);
        const customData = this.customAgentData.get(agentName);
        const stepData = this.thinkingPanel.findStepByAgent?.(agentName);
        
        let detailsHTML = `
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="fas fa-info-circle me-2"></i>
                            ${displayName} Details
                        </h6>
                        <button class="btn btn-sm btn-outline-light" onclick="window.detailsPanel.refreshDetails()" title="Refresh">
                            <i class="fas fa-sync"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
        `;
        
        // Show basic agent info
        detailsHTML += `
            <div class="mb-3">
                <h6>Agent Information</h6>
                <p><strong>Name:</strong> ${displayName}</p>
                <p><strong>Internal Name:</strong> <code>${agentName}</code></p>
                <p><strong>Type:</strong> ${this.isCustomAgent(agentName) ? 'Custom Agent' : 'Standard Agent'}</p>
            </div>
        `;
        
        // Show internal conversation if available (for custom agents)
        if (customData && customData.internalConversation && customData.internalConversation.length > 0) {
            const conversationCount = customData.internalConversation.length;
            detailsHTML += `
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6>Internal Conversation 
                            <span class="badge bg-info ms-2">${conversationCount} messages</span>
                        </h6>
                        <button class="btn btn-sm btn-primary" 
                                onclick="window.detailsPanel.showInternalConversationFullView('${agentName}')" 
                                title="View Full Internal Conversation">
                            <i class="fas fa-expand me-1"></i>
                            Full View
                        </button>
                    </div>
                    <div class="internal-conversation-preview" style="max-height: 300px; overflow-y: auto;">
                        ${this.renderInternalConversationPreview(customData.internalConversation)}
                    </div>
                </div>
            `;
        } else if (this.isCustomAgent(agentName)) {
            detailsHTML += `
                <div class="mb-3">
                    <h6>Internal Conversation</h6>
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        This is a custom agent. Internal conversation messages will appear here in real-time when the agent starts working.
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-primary" 
                                    onclick="window.detailsPanel.monitorInternalConversation('${agentName}')"
                                    title="Start monitoring">
                                <i class="fas fa-eye me-1"></i>
                                Monitor Internal Activity
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Show custom agent thinking if available
        if (customData && customData.phases.length > 0) {
            detailsHTML += `
                <div class="mb-3">
                    <h6>Detailed Thinking Process</h6>
                    ${customData.phases.map((phase, index) => `
                        <div class="custom-agent-section mb-2">
                            <div class="custom-agent-header">
                                <strong>${phase.phase.replace(/_/g, ' ').toUpperCase()}</strong>
                                <small class="text-muted ms-2">${this.formatTimestamp(phase.timestamp)}</small>
                            </div>
                            <div class="custom-agent-content">
                                <div class="thinking-phase">
                                    <div class="phase-content">${phase.content}</div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Show placeholder for other agents
        if (!customData || (customData.phases.length === 0 && (!customData.internalConversation || customData.internalConversation.length === 0))) {
            detailsHTML += `
                <div class="mb-3">
                    <div class="alert alert-secondary">
                        <i class="fas fa-info-circle me-2"></i>
                        ${this.isCustomAgent(agentName) ? 
                            'This custom agent hasn\'t started working yet. Detailed thinking process and internal conversations will appear here once the agent becomes active.' :
                            'No detailed thinking process available for this agent.'}
                    </div>
                </div>
            `;
        }
        
        detailsHTML += `
                </div>
            </div>
        `;
        
        detailsDiv.innerHTML = detailsHTML;
    }
    
    showConversationSummary(data) {
        // Add conversation summary at the top
        let summaryDiv = this.detailsContent.querySelector('.conversation-summary');
        if (!summaryDiv) {
            summaryDiv = document.createElement('div');
            summaryDiv.className = 'conversation-summary mb-3';
            this.detailsContent.insertBefore(summaryDiv, this.detailsContent.firstChild);
        }
        
        summaryDiv.innerHTML = `
            <div class="card border-success">
                <div class="card-header bg-success text-white">
                    <h6 class="mb-0">
                        <i class="fas fa-check-circle me-2"></i>
                        Conversation Summary
                    </h6>
                </div>
                <div class="card-body">
                    <p><strong>Status:</strong> Completed Successfully</p>
                    <p><strong>Custom Agents Used:</strong> ${this.customAgentData.size}</p>
                    <p><strong>Completion Time:</strong> ${this.formatTimestamp(data.timestamp)}</p>
                </div>
            </div>
        `;
    }
    
    refreshDetails() {
        if (this.selectedAgent) {
            this.displayAgentDetails(this.selectedAgent);
        } else {
            this.updateAgentSelectionList();
        }
    }
    
    getAgentDisplayName(agentName) {
        const displayNames = {
            'expert_knowledge': 'Expert Knowledge',
            'websearch_and_crawl': 'Web Search & Crawl',
            'code_executor': 'Code Executor',
            'user_proxy_agent': 'User Proxy',
            'research_planner_agent': 'Research Planner',
            'expert_knowledge_agent': 'Expert Knowledge',
            'websearch_and_crawl_agent': 'Web Search & Crawl',
            'coder_agent': 'Coder',
            'code_executor_agent': 'Code Executor',
            'send_user_msg_agent': 'Response Formatter'
        };
        
        return displayNames[agentName] || agentName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
    
    showAgentConversation(agentName, displayName, stepId) {
        // Get internal conversation data from thinking panel
        const internalConversation = this.thinkingPanel.getInternalConversation(stepId);
        const stepData = this.thinkingPanel.getStepData(stepId);
        
        console.log(`[DetailsPanel] Showing internal conversation for ${displayName} (${stepId})`);
        
        // Clear current content and show internal conversation
        this.detailsContent.innerHTML = '';
        
        // Create header with back button
        const headerDiv = document.createElement('div');
        headerDiv.className = 'internal-conversation-header mb-3';
        headerDiv.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center">
                    <button class="btn btn-sm btn-outline-secondary me-3" 
                            onclick="window.detailsPanel.showMainView()" 
                            title="Back to main view">
                        <i class="fas fa-arrow-left"></i>
                    </button>
                    <div>
                        <h5 class="mb-0">
                            <span class="agent-badge" style="background-color: ${stepData?.color || '#6c757d'}"></span>
                            ${displayName} - Internal Conversation
                        </h5>
                        <small class="text-muted">Step ID: ${stepId}</small>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-info" 
                        onclick="window.detailsPanel.refreshConversation('${stepId}')"
                        title="Refresh conversation">
                    <i class="fas fa-sync"></i>
                </button>
            </div>
        `;
        this.detailsContent.appendChild(headerDiv);
        
        // Create conversation container
        const conversationDiv = document.createElement('div');
        conversationDiv.className = 'internal-conversation-content';
        conversationDiv.id = `internal-conversation-${stepId}`;
        
        if (internalConversation && internalConversation.length > 0) {
            // Show the internal conversation in a similar format to the thinking panel
            conversationDiv.innerHTML = this.renderInternalConversation(internalConversation);
        } else {
            // Show placeholder with real-time updates
            conversationDiv.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Monitoring Internal Conversation</strong><br>
                    This panel will show the internal thinking process and conversations of ${displayName} as they happen.
                    <div class="mt-2 text-muted">
                        <small>Internal activities will appear here in real-time...</small>
                    </div>
                </div>
                <div class="internal-conversation-placeholder">
                    <div class="text-center text-muted p-4">
                        <i class="fas fa-comments fa-2x mb-3"></i>
                        <p>Waiting for internal conversation...</p>
                        <div class="spinner-border spinner-border-sm" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        this.detailsContent.appendChild(conversationDiv);
        
        // Store current view state
        this.currentView = {
            type: 'agent_conversation',
            agentName: agentName,
            displayName: displayName,
            stepId: stepId
        };
        
        // Set up real-time updates for this conversation
        this.setupInternalConversationUpdates(stepId);
        
        console.log(`[DetailsPanel] Internal conversation view set up for ${displayName}`);
    }
    
    renderInternalConversation(conversation) {
        if (!conversation || conversation.length === 0) {
            return '<div class="alert alert-info">No internal conversation data available yet. Internal activities will appear here as they happen.</div>';
        }
        
        let html = '<div class="internal-conversation-timeline">';
        
        conversation.forEach((item, index) => {
            const timestamp = this.formatTimestamp(item.timestamp);
            const messageId = `internal-full-${Date.now()}-${index}`;
            
            if (item.type === 'thinking_phase') {
                html += `
                    <div class="internal-step thinking-phase-step">
                        <div class="step-header">
                            <span class="step-badge thinking-phase">
                                <i class="fas fa-brain"></i>
                            </span>
                            <div class="step-info">
                                <h6 class="step-title">${item.phase.replace(/_/g, ' ').toUpperCase()}</h6>
                                <small class="text-muted">${timestamp}</small>
                            </div>
                        </div>
                        <div class="step-content">
                            ${this.renderExpandableContent(item.content, messageId, 300)}
                        </div>
                    </div>
                `;
            } else if (item.type === 'internal_start') {
                html += `
                    <div class="internal-step internal-start-step">
                        <div class="step-header">
                            <span class="step-badge internal-start">
                                <i class="fas fa-play"></i>
                            </span>
                            <div class="step-info">
                                <h6 class="step-title">INTERNAL PROCESS STARTED</h6>
                                <small class="text-muted">${timestamp}</small>
                            </div>
                        </div>
                        <div class="step-content">
                            ${this.renderExpandableContent(item.content, messageId, 300)}
                        </div>
                    </div>
                `;
            } else if (item.type === 'tool_call') {
                html += `
                    <div class="internal-step tool-call-step">
                        <div class="step-header">
                            <span class="step-badge tool-call">
                                <i class="fas fa-tools"></i>
                            </span>
                            <div class="step-info">
                                <h6 class="step-title">TOOL CALL</h6>
                                <small class="text-muted">${timestamp} • Agent: ${item.internal_agent || 'Internal'}</small>
                            </div>
                        </div>
                        <div class="step-content">
                            ${this.renderExpandableContent(item.content, messageId, 300)}
                        </div>
                    </div>
                `;
            } else if (item.type === 'internal_message') {
                html += `
                    <div class="internal-step message-step">
                        <div class="step-header">
                            <span class="step-badge message">
                                <i class="fas fa-comment"></i>
                            </span>
                            <div class="step-info">
                                <h6 class="step-title">${(item.internal_agent || 'Internal Agent').toUpperCase()}</h6>
                                <small class="text-muted">${timestamp} • Role: ${item.role || 'assistant'}</small>
                            </div>
                        </div>
                        <div class="step-content">
                            ${this.renderExpandableContent(item.content, messageId, 300)}
                        </div>
                    </div>
                `;
            } else if (item.type === 'internal_error') {
                html += `
                    <div class="internal-step error-step">
                        <div class="step-header">
                            <span class="step-badge error">
                                <i class="fas fa-exclamation-triangle"></i>
                            </span>
                            <div class="step-info">
                                <h6 class="step-title">INTERNAL ERROR</h6>
                                <small class="text-muted">${timestamp}</small>
                            </div>
                        </div>
                        <div class="step-content">
                            <div class="alert alert-danger">
                                ${this.renderExpandableContent(item.content, messageId, 300)}
                            </div>
                        </div>
                    </div>
                `;
            } else if (item.type === 'detected_step') {
                html += `
                    <div class="internal-step detected-step">
                        <div class="step-header">
                            <span class="step-badge detected">
                                <i class="fas fa-search"></i>
                            </span>
                            <div class="step-info">
                                <h6 class="step-title">${item.stepType.replace(/_/g, ' ').toUpperCase()}</h6>
                                <small class="text-muted">${timestamp}</small>
                            </div>
                        </div>
                        <div class="step-content">
                            ${this.renderExpandableContent(item.content, messageId, 300)}
                            ${item.details ? `<div class="step-details text-muted mt-2"><small>Details: ${item.details}</small></div>` : ''}
                        </div>
                    </div>
                `;
            } else {
                // Generic fallback for unknown message types
                html += `
                    <div class="internal-step generic-step">
                        <div class="step-header">
                            <span class="step-badge generic">
                                <i class="fas fa-question"></i>
                            </span>
                            <div class="step-info">
                                <h6 class="step-title">${(item.type || 'Unknown').toUpperCase().replace(/_/g, ' ')}</h6>
                                <small class="text-muted">${timestamp}</small>
                            </div>
                        </div>
                        <div class="step-content">
                            ${this.renderExpandableContent(item.content, messageId, 300)}
                        </div>
                    </div>
                `;
            }
        });
        
        html += '</div>';
        return html;
    }
    
    setupInternalConversationUpdates(stepId) {
        // Set up polling or real-time updates for the internal conversation
        if (this.conversationUpdateInterval) {
            clearInterval(this.conversationUpdateInterval);
        }
        
        this.conversationUpdateInterval = setInterval(() => {
            if (this.currentView && this.currentView.type === 'agent_conversation' && this.currentView.stepId === stepId) {
                this.refreshConversation(stepId);
            }
        }, 2000); // Update every 2 seconds
    }
    
    refreshConversation(stepId) {
        const internalConversation = this.thinkingPanel.getInternalConversation(stepId);
        const conversationDiv = document.getElementById(`internal-conversation-${stepId}`);
        
        if (conversationDiv && internalConversation) {
            const currentContent = conversationDiv.innerHTML;
            const newContent = this.renderInternalConversation(internalConversation);
            
            // Only update if content has changed
            if (currentContent !== newContent) {
                conversationDiv.innerHTML = newContent;
                
                // Process markdown
                if (window.markdownUtils) {
                    window.markdownUtils.processMessageElement(conversationDiv);
                }
                
                // Scroll to bottom
                conversationDiv.scrollTop = conversationDiv.scrollHeight;
            }
        }
    }
    
    showMainView() {
        // Return to the main agent selection view
        if (this.conversationUpdateInterval) {
            clearInterval(this.conversationUpdateInterval);
        }
        
        this.currentView = null;
        this.updateAgentSelectionList();
    }
    
    renderMarkdown(content) {
        if (window.markdownUtils) {
            return window.markdownUtils.renderMarkdown(content);
        }
        return content.replace(/\n/g, '<br>');
    }
    
    // Public API
    clearDetails() {
        this.customAgentData.clear();
        this.selectedAgent = null;
        this.detailsContent.innerHTML = `
            <div class="no-details">
                <div class="text-center text-muted p-3">
                    <i class="fas fa-search fa-2x mb-3"></i>
                    <p>Select an agent to see detailed thinking process</p>
                </div>
            </div>
        `;
    }
    
    getCustomAgentData(agentName) {
        return this.customAgentData.get(agentName);
    }
    
    // Helper methods for new functionality
    isCustomAgent(agentName) {
        return ['expert_knowledge_agent', 'websearch_and_crawl_agent'].includes(agentName);
    }
    
    renderInternalConversationPreview(conversation) {
        if (!conversation || conversation.length === 0) {
            return '<div class="text-muted">No internal messages yet...</div>';
        }
        
        return conversation.slice(-5).map((item, index) => {
            const timestamp = this.formatTimestamp(item.timestamp);
            const messageId = `internal-msg-${Date.now()}-${index}`;
            let icon = item.iconClass || 'fa-comment';
            let badgeClass = 'bg-secondary';
            let title = 'Internal Message';
            
            // Enhanced handling for expert knowledge agent internal messages
            if (item.type === 'rag_initialization') {
                icon = 'fa-database';
                badgeClass = 'bg-success';
                title = 'Knowledge System Init';
            } else if (item.type === 'assistant_initialization') {
                icon = 'fa-robot';
                badgeClass = 'bg-info';
                title = 'Assistant Setup';
            } else if (item.type === 'rag_search_start') {
                icon = 'fa-search';
                badgeClass = 'bg-warning';
                title = 'Knowledge Search';
            } else if (item.type === 'rag_retrieval_start') {
                icon = 'fa-download';
                badgeClass = 'bg-primary';
                title = 'Document Retrieval';
            } else if (item.type === 'rag_processing') {
                icon = 'fa-cogs';
                badgeClass = 'bg-secondary';
                title = 'Processing Data';
            } else if (item.type === 'rag_query') {
                icon = 'fa-question-circle';
                badgeClass = 'bg-info';
                title = 'RAG Query';
            } else if (item.type === 'rag_response') {
                icon = 'fa-lightbulb';
                badgeClass = 'bg-warning';
                title = 'RAG Response';
            } else if (item.type === 'rag_completion') {
                icon = 'fa-check-circle';
                badgeClass = 'bg-success';
                title = 'Retrieval Complete';
            } else if (item.type === 'final_response') {
                icon = 'fa-check';
                badgeClass = 'bg-success';
                title = 'Final Response';
            } else if (item.type === 'internal_start') {
                icon = 'fa-play';
                badgeClass = 'bg-success';
                title = 'Process Started';
            } else if (item.type === 'tool_call') {
                icon = 'fa-tools';
                badgeClass = 'bg-warning';
                title = 'Tool Call';
            } else if (item.type === 'internal_error' || item.type === 'rag_error' || item.type === 'agent_error') {
                icon = 'fa-exclamation-triangle';
                badgeClass = 'bg-danger';
                title = 'Error';
            }
            
            return `
                <div class="internal-conversation-step mb-3">
                    <div class="row align-items-start">
                        <div class="col-auto">
                            <div class="internal-step-icon" style="background-color: ${this.getBadgeColor(badgeClass)}">
                                <i class="fas ${icon}"></i>
                            </div>
                        </div>
                        <div class="col">
                            <div class="internal-step-content">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <div class="internal-step-title fw-bold">${title}</div>
                                    <div class="internal-step-timestamp text-muted small">${timestamp}</div>
                                </div>
                                <div class="internal-step-description">
                                    ${this.renderExpandableContent(item.content, messageId, 150)}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    getBadgeColor(badgeClass) {
        const colorMap = {
            'bg-primary': '#007bff',
            'bg-secondary': '#6c757d',
            'bg-success': '#28a745',
            'bg-danger': '#dc3545',
            'bg-warning': '#ffc107',
            'bg-info': '#17a2b8'
        };
        return colorMap[badgeClass] || '#6c757d';
    }
    
    truncateContent(content, maxLength) {
        if (content.length <= maxLength) {
            return content;
        }
        return content.substring(0, maxLength) + '...';
    }
    
    renderExpandableContent(content, messageId, maxLength = 150) {
        if (content.length <= maxLength) {
            return `<div class="message-content">${this.renderMarkdown(content)}</div>`;
        }
        
        const truncated = content.substring(0, maxLength);
        const remaining = content.substring(maxLength);
        
        return `
            <div class="message-content expandable-content">
                <div class="content-preview" id="preview-${messageId}">
                    ${this.renderMarkdown(truncated)}
                    <span class="text-muted">...</span>
                </div>
                <div class="content-full" id="full-${messageId}" style="display: none;">
                    ${this.renderMarkdown(content)}
                </div>
                <div class="content-controls mt-2">
                    <button class="btn btn-sm btn-outline-primary expand-btn" 
                            onclick="window.detailsPanel.toggleContent('${messageId}')"
                            id="toggle-${messageId}">
                        <i class="fas fa-expand-alt me-1"></i>
                        Show More
                    </button>
                </div>
            </div>
        `;
    }
    
    toggleContent(messageId) {
        const preview = document.getElementById(`preview-${messageId}`);
        const full = document.getElementById(`full-${messageId}`);
        const toggleBtn = document.getElementById(`toggle-${messageId}`);
        
        if (preview && full && toggleBtn) {
            if (preview.style.display === 'none') {
                // Show preview, hide full
                preview.style.display = 'block';
                full.style.display = 'none';
                toggleBtn.innerHTML = '<i class="fas fa-expand-alt me-1"></i>Show More';
                toggleBtn.classList.remove('btn-outline-secondary');
                toggleBtn.classList.add('btn-outline-primary');
            } else {
                // Show full, hide preview
                preview.style.display = 'none';
                full.style.display = 'block';
                toggleBtn.innerHTML = '<i class="fas fa-compress-alt me-1"></i>Show Less';
                toggleBtn.classList.remove('btn-outline-primary');
                toggleBtn.classList.add('btn-outline-secondary');
            }
        }
    }
    
    showInternalConversationFullView(agentName, stepId = null, context = null) {
        // First try to get data from our own storage
        let customData = this.customAgentData.get(agentName);
        let internalConversation = [];
        
        if (customData && customData.internalConversation && customData.internalConversation.length > 0) {
            // Use our own data if available
            internalConversation = customData.internalConversation;
        } else {
            // Fallback: Use data bridge to get data from ThinkingPanel with optional step ID and context
            if (this.thinkingPanel) {
                internalConversation = this.thinkingPanel.getInternalConversationForAgent(agentName, stepId, context);
                
                // If we got data from thinking panel, initialize our own storage for future use
                if (internalConversation.length > 0) {
                    if (!customData) {
                        customData = {
                            name: agentName,
                            phases: [],
                            internalConversation: [],
                            displayName: this.getAgentDisplayName(agentName)
                        };
                        this.customAgentData.set(agentName, customData);
                    }
                    // Sync the data
                    customData.internalConversation = [...internalConversation];
                }
            }
        }
        
        if (!internalConversation || internalConversation.length === 0) {
            console.warn('No internal conversation data found for agent:', agentName);
            // Show an informative message instead of just returning
            this.showNoInternalConversationMessage(agentName);
            return;
        }
        
        const displayName = this.getAgentDisplayName(agentName);
        
        // Clear current content and show internal conversation
        this.detailsContent.innerHTML = '';
        
        // Create header with back button
        const headerDiv = document.createElement('div');
        headerDiv.className = 'internal-conversation-header mb-3';
        headerDiv.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center">
                    <button class="btn btn-sm btn-outline-secondary me-3" 
                            onclick="window.detailsPanel.showMainView()" 
                            title="Back to main view">
                        <i class="fas fa-arrow-left"></i>
                    </button>
                    <div>
                        <h5 class="mb-0">
                            <i class="fas fa-comments me-2 text-primary"></i>
                            ${displayName} - Internal Conversation
                        </h5>
                        <small class="text-muted">${internalConversation.length} messages</small>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-info" 
                        onclick="window.detailsPanel.refreshInternalConversation('${agentName}')"
                        title="Refresh conversation">
                    <i class="fas fa-sync"></i>
                </button>
            </div>
        `;
        this.detailsContent.appendChild(headerDiv);
        
        // Create conversation container
        const conversationDiv = document.createElement('div');
        conversationDiv.className = 'internal-conversation-content';
        conversationDiv.id = `internal-conversation-${agentName}`;
        
        if (internalConversation.length > 0) {
            conversationDiv.innerHTML = this.renderFullInternalConversation(internalConversation);
        } else {
            conversationDiv.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No internal conversation messages yet. This panel will update in real-time as the agent works.
                </div>
            `;
        }
        
        this.detailsContent.appendChild(conversationDiv);
        
        // Store current view state
        this.currentView = {
            type: 'agent_conversation',
            agentName: agentName,
            displayName: displayName
        };
        
        console.log(`[DetailsPanel] Showing full internal conversation for ${displayName}`);
    }
    
    showNoInternalConversationMessage(agentName) {
        const displayName = this.getAgentDisplayName(agentName);
        
        // Clear current content and show no data message
        this.detailsContent.innerHTML = '';
        
        // Create header with back button
        const headerDiv = document.createElement('div');
        headerDiv.className = 'internal-conversation-header mb-3';
        headerDiv.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center">
                    <button class="btn btn-sm btn-outline-secondary me-3" 
                            onclick="window.detailsPanel.showMainView()" 
                            title="Back to main view">
                        <i class="fas fa-arrow-left"></i>
                    </button>
                    <div>
                        <h5 class="mb-0">
                            <i class="fas fa-comments me-2 text-muted"></i>
                            ${displayName} - Internal Conversation
                        </h5>
                        <small class="text-muted">No data available</small>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-info" 
                        onclick="window.detailsPanel.refreshInternalConversation('${agentName}')"
                        title="Refresh conversation">
                    <i class="fas fa-sync"></i>
                </button>
            </div>
        `;
        this.detailsContent.appendChild(headerDiv);
        
        // Create no data message
        const noDataDiv = document.createElement('div');
        noDataDiv.className = 'no-internal-conversation-content';
        noDataDiv.innerHTML = `
            <div class="alert alert-warning">
                <div class="d-flex align-items-center">
                    <i class="fas fa-exclamation-triangle fa-2x text-warning me-3"></i>
                    <div>
                        <h6 class="mb-1">No Internal Conversation Data Found</h6>
                        <p class="mb-2">This could happen if:</p>
                        <ul class="mb-2">
                            <li>The agent hasn't started processing yet</li>
                            <li>The agent doesn't have internal conversation features enabled</li>
                            <li>The internal conversation data is still being processed</li>
                        </ul>
                        <small class="text-muted">Try refreshing or check back after the agent completes its task.</small>
                    </div>
                </div>
            </div>
        `;
        this.detailsContent.appendChild(noDataDiv);
        
        // Store current view state
        this.currentView = {
            type: 'agent_conversation',
            agentName: agentName,
            displayName: displayName
        };
        
        console.log(`[DetailsPanel] Showing no data message for ${displayName}`);
    }
    
    renderFullInternalConversation(conversation) {
        if (!conversation || conversation.length === 0) {
            return '<div class="alert alert-info">No internal conversation messages yet.</div>';
        }
        
        let html = '<div class="internal-conversation-timeline">';
        
        conversation.forEach((item, index) => {
            const timestamp = this.formatTimestamp(item.timestamp);
            
            // Get display information for any message type
            const messageInfo = this.getMessageDisplayInfo(item);
            
            html += `
                <div class="internal-step ${messageInfo.cssClass}">
                    <div class="step-header">
                        <span class="step-badge ${messageInfo.badgeClass}">
                            <i class="fas ${messageInfo.icon}"></i>
                        </span>
                        <div class="step-info">
                            <h6 class="step-title">${messageInfo.title}</h6>
                            <small class="text-muted">${timestamp}${messageInfo.subtitle ? ' • ' + messageInfo.subtitle : ''}</small>
                        </div>
                    </div>
                    <div class="step-content">
                        <div class="alert ${messageInfo.alertClass}">
                            <div class="markdown-content">${this.renderSimpleMarkdown(item.content)}</div>
                            ${this.renderMessageMetadata(item)}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    getMessageDisplayInfo(item) {
        // Generic message type configurations
        const messageTypes = {
            'rag_initialization': {
                title: 'KNOWLEDGE SYSTEM INITIALIZATION',
                icon: 'fa-database',
                badgeClass: 'bg-primary text-white',
                alertClass: 'alert-primary border-primary',
                cssClass: 'rag-init-step'
            },
            'rag_search_start': {
                title: 'KNOWLEDGE SEARCH STARTED',
                icon: 'fa-search',
                badgeClass: 'bg-info text-white',
                alertClass: 'alert-info border-info',
                cssClass: 'rag-search-step'
            },
            'rag_query': {
                title: 'RAG QUERY',
                icon: 'fa-question-circle',
                badgeClass: 'bg-secondary text-white',
                alertClass: 'alert-secondary border-secondary',
                cssClass: 'rag-query-step'
            },
            'rag_response': {
                title: 'RAG RESPONSE',
                icon: 'fa-lightbulb',
                badgeClass: 'bg-success text-white',
                alertClass: 'alert-success border-success',
                cssClass: 'rag-response-step'
            },
            'rag_completion': {
                title: 'KNOWLEDGE RETRIEVAL COMPLETE',
                icon: 'fa-check-circle',
                badgeClass: 'bg-success text-white',
                alertClass: 'alert-success border-success',
                cssClass: 'rag-completion-step'
            },
            'final_response': {
                title: 'FINAL EXPERT RESPONSE',
                icon: 'fa-check',
                badgeClass: 'bg-dark text-white',
                alertClass: 'alert-dark border-dark',
                cssClass: 'final-response-step'
            },
            'rag_processing': {
                title: 'PROCESSING RETRIEVED DATA',
                icon: 'fa-cogs',
                badgeClass: 'bg-warning text-dark',
                alertClass: 'alert-warning border-warning',
                cssClass: 'rag-processing-step'
            },
            'rag_retrieval_start': {
                title: 'DOCUMENT RETRIEVAL',
                icon: 'fa-download',
                badgeClass: 'bg-info text-white',
                alertClass: 'alert-info border-info',
                cssClass: 'rag-retrieval-step'
            },
            'assistant_initialization': {
                title: 'ASSISTANT SETUP',
                icon: 'fa-robot',
                badgeClass: 'bg-primary text-white',
                alertClass: 'alert-primary border-primary',
                cssClass: 'assistant-init-step'
            },
            'internal_start': {
                title: 'INTERNAL PROCESS STARTED',
                icon: 'fa-play',
                badgeClass: 'bg-success text-white',
                alertClass: 'alert-success border-success',
                cssClass: 'internal-start-step'
            },
            'tool_call': {
                title: 'TOOL CALL',
                icon: 'fa-tools',
                badgeClass: 'bg-warning text-dark',
                alertClass: 'alert-warning border-warning',
                cssClass: 'tool-call-step'
            },
            'thinking_phase': {
                title: 'THINKING PHASE',
                icon: 'fa-brain',
                badgeClass: 'bg-info text-white',
                alertClass: 'alert-info border-info',
                cssClass: 'thinking-phase-step'
            }
        };
        
        // Error types
        if (item.type && (item.type.includes('error') || item.type.includes('Error'))) {
            return {
                title: 'ERROR IN PROCESSING',
                icon: 'fa-exclamation-triangle',
                badgeClass: 'bg-danger text-white',
                alertClass: 'alert-danger border-danger',
                cssClass: 'error-step',
                subtitle: `Type: ${item.type}`
            };
        }
        
        // Get predefined config or create generic one
        const config = messageTypes[item.type] || {
            title: item.type ? item.type.toUpperCase().replace(/_/g, ' ') : 'INTERNAL MESSAGE',
            icon: 'fa-comment',
            badgeClass: 'bg-secondary text-white',
            alertClass: 'alert-light border-secondary',
            cssClass: 'generic-message-step'
        };
        
        // Add common subtitle information
        let subtitle = '';
        if (item.internal_agent) subtitle += `Agent: ${item.internal_agent}`;
        if (item.role) subtitle += subtitle ? ` • Role: ${item.role}` : `Role: ${item.role}`;
        if (item.type && !messageTypes[item.type]) subtitle += subtitle ? ` • Type: ${item.type}` : `Type: ${item.type}`;
        
        return {
            ...config,
            subtitle: subtitle
        };
    }
    
    renderMessageMetadata(item) {
        let metadataHtml = '';
        
        // Render metadata if available
        if (item.metadata && Object.keys(item.metadata).length > 0) {
            metadataHtml += '<div class="mt-2 pt-2 border-top">';
            metadataHtml += '<small class="text-muted"><strong>Metadata:</strong></small><br>';
            
            Object.entries(item.metadata).forEach(([key, value]) => {
                if (value && typeof value === 'string' && value.length < 200) {
                    metadataHtml += `<small class="text-muted"><strong>${key}:</strong> ${value}</small><br>`;
                } else if (value && typeof value === 'object') {
                    metadataHtml += `<small class="text-muted"><strong>${key}:</strong> <code>${JSON.stringify(value)}</code></small><br>`;
                }
            });
            
            metadataHtml += '</div>';
        }
        
        // Render tool calls if available
        if (item.tool_calls && item.tool_calls.length > 0) {
            metadataHtml += '<div class="mt-2 pt-2 border-top">';
            metadataHtml += '<small class="text-muted"><strong>Tool Calls:</strong></small>';
            item.tool_calls.forEach(toolCall => {
                if (toolCall.function) {
                    metadataHtml += `<div class="mt-1"><code class="small">${toolCall.function.name || 'Unknown Function'}</code></div>`;
                }
            });
            metadataHtml += '</div>';
        }
        
        return metadataHtml;
    }
    
    renderSimpleMarkdown(content) {
        if (!content) return '';
        
        return content
            // Handle code blocks with language specification
            .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                const language = lang ? ` class="language-${lang}"` : '';
                return `<div class="code-block mb-3"><pre class="bg-dark text-light p-3 rounded"><code${language}>${code.trim()}</code></pre></div>`;
            })
            // Handle inline code
            .replace(/`([^`]+)`/g, '<code class="bg-light px-2 py-1 rounded text-dark">$1</code>')
            // Handle bold text
            .replace(/\*\*(.*?)\*\*/g, '<strong class="text-primary">$1</strong>')
            // Handle italic text
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Handle HTML details/summary tags (for expandable content)
            .replace(/<details><summary>(.*?)<\/summary>\n\n([\s\S]*?)\n\n<\/details>/g, 
                '<details class="mt-2"><summary class="btn btn-sm btn-outline-info mb-2">$1</summary><div class="ms-3 mt-2">$2</div></details>')
            // Handle bullet points
            .replace(/^\• (.+)$/gm, '<li class="mb-1">$1</li>')
            .replace(/(<li.*<\/li>)/s, '<ul class="mb-2">$1</ul>')
            // Handle line breaks
            .replace(/\n\n/g, '</p><p class="mb-2">')
            .replace(/\n/g, '<br>')
            // Wrap in paragraph tags
            .replace(/^(.*)$/, '<p class="mb-2">$1</p>')
            // Clean up empty paragraphs
            .replace(/<p class="mb-2"><\/p>/g, '');
    }
    
    monitorInternalConversation(agentName) {
        this.showInternalConversationFullView(agentName);
    }
    
    updateInternalConversationView(agentName) {
        if (this.currentView && this.currentView.type === 'agent_conversation' && 
            this.currentView.agentName === agentName) {
            const conversationDiv = document.getElementById(`internal-conversation-${agentName}`);
            if (conversationDiv) {
                const customData = this.customAgentData.get(agentName);
                if (customData && customData.internalConversation) {
                    conversationDiv.innerHTML = this.renderFullInternalConversation(customData.internalConversation);
                    // Auto-scroll to bottom
                    conversationDiv.scrollTop = conversationDiv.scrollHeight;
                }
            }
        }
    }
    
    refreshInternalConversation(agentName) {
        // Force refresh by getting latest data from thinking panel
        if (this.thinkingPanel) {
            const latestConversation = this.thinkingPanel.getInternalConversationForAgent(agentName);
            
            // Update our storage
            let customData = this.customAgentData.get(agentName);
            if (!customData) {
                customData = {
                    name: agentName,
                    phases: [],
                    internalConversation: [],
                    displayName: this.getAgentDisplayName(agentName)
                };
                this.customAgentData.set(agentName, customData);
            }
            customData.internalConversation = [...latestConversation];
        }
        
        // Re-show the conversation view with refreshed data
        this.showInternalConversationFullView(agentName);
    }
    
    showMainView() {
        // Clear current view and show main details view
        this.currentView = null;
        this.detailsContent.innerHTML = '';
        
        // Show no-details message or agent selection
        if (this.selectedAgent) {
            this.displayAgentDetails(this.selectedAgent);
        } else {
            this.detailsContent.innerHTML = `
                <div class="no-details">
                    <div class="text-center text-muted p-3">
                        <i class="fas fa-search fa-2x mb-3"></i>
                        <p>Select an agent to see detailed thinking process</p>
                    </div>
                </div>
            `;
        }
    }
    
    getAllCustomAgentData() {
        return Array.from(this.customAgentData.entries());
    }
}

// Initialize the application
const app = new ThoughtAgentApp();

// Export for debugging purposes
window.ThoughtAgentApp = app;
