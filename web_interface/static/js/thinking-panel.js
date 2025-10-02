/**
 * ThinkingPanel - Handles the main thinking process visualization
 */
class ThinkingPanel {
    constructor(socketManager) {
        this.socketManager = socketManager;
        this.agentSteps = new Map(); // Map of step IDs to their step data
        this.currentStepId = 0;
        this.activeAgents = new Set();
        this.lastAgentStep = null; // Track the most recent step ID
        
        // NEW: ThoughtAgent container tracking with enhanced state management
        this.thoughtAgentContainers = new Map(); // Map of thought_agent_id to container data
        this.nestedAgentSteps = new Map(); // Map of nested step IDs to their step data
        this.currentNestedStepId = 0;
        
        // Phase 3: Enhanced container state management
        this.containerStates = new Map(); // Persistent container states (expanded/collapsed)
        this.messageQueue = new Map(); // Queue for out-of-order messages
        this.routingErrors = new Map(); // Track routing errors for recovery
        this.containerCleanupTasks = new Map(); // Cleanup tasks for completed containers
        
        // DOM elements
        this.thinkingContent = document.getElementById('thinkingContent');
        this.expandAllBtn = document.getElementById('expandAllBtn');
        this.collapseAllBtn = document.getElementById('collapseAllBtn');
        
        // Agent metadata - MainAgent level
        this.mainAgentMetadata = {
            'thought_creator_agent': { color: '#9c27b0', displayName: 'Thought Creator', icon: 'fa-lightbulb' },
            'response_analyzer_agent': { color: '#ff5722', displayName: 'Response Analyzer', icon: 'fa-chart-line' },
            'thought_analyzer_agent': { color: '#795548', displayName: 'Thought Analyzer', icon: 'fa-search-plus' },
            'expert_knowledge_agent': { color: '#6f42c1', displayName: 'Expert Knowledge (Main)', icon: 'fa-brain' },
            'user_proxy_agent': { color: '#007bff', displayName: 'User Proxy (Main)', icon: 'fa-user' }
        };
        
        // Agent metadata - ThoughtAgent level
        this.agentMetadata = {
            'user_proxy_agent': { color: '#007bff', displayName: 'User Proxy', icon: 'fa-user' },
            'research_planner_agent': { color: '#28a745', displayName: 'Research Planner', icon: 'fa-search' },
            'expert_knowledge_agent': { color: '#6f42c1', displayName: 'Expert Knowledge', icon: 'fa-brain' },
            'websearch_and_crawl_agent': { color: '#fd7e14', displayName: 'Web Search & Crawl', icon: 'fa-globe' },
            'coder_agent': { color: '#dc3545', displayName: 'Coder', icon: 'fa-code' },
            'code_executor_agent': { color: '#17a2b8', displayName: 'Code Executor', icon: 'fa-play' },
            'send_user_msg_agent': { color: '#6c757d', displayName: 'Response Formatter', icon: 'fa-comment' }
        };
        
        this.initialize();
    }
    
    initialize() {
        this.setupEventListeners();
        this.setupSocketListeners();
        console.log('[ThinkingPanel] Initialized');
    }
    
    setupEventListeners() {
        // Expand/Collapse all buttons
        this.expandAllBtn.addEventListener('click', () => {
            this.expandAll();
        });
        
        this.collapseAllBtn.addEventListener('click', () => {
            this.collapseAll();
        });
    }
    
    setupSocketListeners() {
        // Conversation started
        this.socketManager.on('conversation_started', (data) => {
            this.clearThinkingProcess();
            this.showConversationStarted(data);
        });
        
        // NEW: Main Agent events
        this.socketManager.on('main_agent_started', (data) => {
            this.showMainAgentStarted(data);
        });
        
        this.socketManager.on('main_agent_message', (data) => {
            this.addAgentStep(data);
            this.addAgentMessage(data);
        });
        
        this.socketManager.on('main_agent_thinking', (data) => {
            this.addCustomAgentThinking(data);
        });
        
        // NEW: ThoughtAgent lifecycle events
        this.socketManager.on('thought_agent_lifecycle', (data) => {
            console.log('[ThinkingPanel] *** THOUGHT_AGENT_LIFECYCLE EVENT RECEIVED ***');
            console.log('[ThinkingPanel] Raw event data:', data);
            console.log('[ThinkingPanel] Event data type:', typeof data);
            console.log('[ThinkingPanel] Event data keys:', Object.keys(data || {}));
            try {
                this.handleThoughtAgentLifecycle(data);
                console.log('[ThinkingPanel] *** THOUGHT_AGENT_LIFECYCLE PROCESSING COMPLETED ***');
            } catch (error) {
                console.error('[ERROR] thought_agent_lifecycle processing failed:', error);
                console.error('[ERROR] Stack trace:', error.stack);
            }
        });
        
        // UPDATED: Agent started - now handles both levels with enhanced routing
        this.socketManager.on('agent_started', (data) => {
            try {
                console.log('[ThinkingPanel] Received agent_started:', data);
                if (data.level === 'thought_agent') {
                    console.log('[ThinkingPanel] Processing thought_agent agent_started');
                    this.addNestedAgentStep(data);
                } else {
                    this.addAgentStep(data);
                }
            } catch (error) {
                this.handleRoutingError('agent_started', data, error);
            }
        });
        
        // UPDATED: Agent message - now handles both levels with enhanced routing
        this.socketManager.on('agent_message', (data) => {
            try {
                if (data.level === 'thought_agent') {
                    this.addNestedAgentMessage(data);
                } else {
                    this.addAgentMessage(data);
                }
                // Also check if this message contains internal conversation indicators
                this.detectInternalConversation(data);
            } catch (error) {
                this.handleRoutingError('agent_message', data, error);
            }
        });
        
        // UPDATED: Custom agent thinking events - now handles both levels with enhanced routing
        this.socketManager.on('custom_agent_thinking', (data) => {
            try {
                if (data.level === 'thought_agent') {
                    this.addNestedCustomAgentThinking(data);
                } else {
                    this.addCustomAgentThinking(data);
                }
            } catch (error) {
                this.handleRoutingError('custom_agent_thinking', data, error);
            }
        });
        
        // Internal conversation events (if we get them from backend)
        this.socketManager.on('agent_internal_conversation', (data) => {
            this.addInternalConversationMessage(data);
        });
        
        // UPDATED: Store internal conversation data for button access - now handles context
        this.socketManager.on('store_internal_conversation', (data) => {
            if (data.level === 'thought_agent') {
                this.storeNestedInternalConversationData(data);
            } else {
                this.storeInternalConversationData(data);
            }
        });
        
        // Thinking process updates
        this.socketManager.on('thinking_process', (data) => {
            this.addThinkingUpdate(data);
        });
        
        // Main conversation completed
        this.socketManager.on('main_conversation_completed', (data) => {
            this.showConversationCompleted(data);
        });
        
        // Conversation completed (keep for backward compatibility)
        this.socketManager.on('conversation_completed', (data) => {
            this.finalizeConversation(data);
        });
        
        // NEW: Response completed (single response finished, conversation continues)
        this.socketManager.on('response_completed', (data) => {
            this.showResponseCompleted(data);
        });
        
        // NEW: Conversation ended (explicitly ended by user)
        this.socketManager.on('conversation_ended', (data) => {
            this.showConversationEnded(data);
        });
        
        // Error handling
        this.socketManager.on('conversation_error', (data) => {
            this.showError(data);
        });
        
        this.socketManager.on('main_agent_error', (data) => {
            this.showError(data);
        });

        // DEBUG: Add debug listener specifically for our events
        console.log('[DEBUG] Setting up debug event listeners...');
        console.log('[DEBUG] SocketManager available:', !!this.socketManager);
        console.log('[DEBUG] Socket available:', !!this.socketManager.socket);
    }
    
    clearThinkingProcess() {
        this.agentSteps.clear();
        this.activeAgents.clear();
        this.thoughtAgentContainers.clear(); // Clear ThoughtAgent containers for new conversation
        this.currentStepId = 0;
        this.lastAgentStep = null;
        
        this.thinkingContent.innerHTML = '';
        console.log('[ThinkingPanel] Cleared thinking process and ThoughtAgent containers');
    }
    
    showConversationStarted(data) {
        const startDiv = document.createElement('div');
        startDiv.className = 'conversation-start mb-3';
        startDiv.innerHTML = `
            <div class="alert alert-info border-left-primary">
                <div class="d-flex align-items-center">
                    <i class="fas fa-play-circle fa-2x text-primary me-3"></i>
                    <div>
                        <h6 class="mb-1">Conversation Started</h6>
                        <p class="mb-0"><strong>Query:</strong> ${data.query}</p>
                        <small class="text-muted">${this.formatTimestamp(data.timestamp)}</small>
                    </div>
                </div>
            </div>
        `;
        
        // Remove no-conversation message
        const noConversation = this.thinkingContent.querySelector('.no-conversation');
        if (noConversation) {
            noConversation.remove();
        }
        
        this.thinkingContent.appendChild(startDiv);
    }
    
    addAgentStep(data, timestamp = null, customStepId = null) {
        // Handle both calling patterns:
        // 1. addAgentStep(dataObject) - existing usage
        // 2. addAgentStep(agentName, timestamp, stepId) - new usage for Expert Knowledge Agent
        
        let agentName, stepId, stepTimestamp, level;
        
        if (typeof data === 'string') {
            // New calling pattern: individual parameters
            agentName = data;
            stepTimestamp = timestamp;
            stepId = customStepId;
            level = 'main'; // Default level for backward compatibility
        } else {
            // Original calling pattern: data object
            agentName = data.agent_name;
            stepTimestamp = data.timestamp;
            stepId = `step-${this.currentStepId++}`;
            level = data.level || 'main'; // Use provided level or default to 'main'
        }
        
        // If no custom step ID provided, generate one
        if (!stepId) {
            stepId = `step-${this.currentStepId++}`;
        }
        
        // Choose metadata based on level
        const metadataSource = level === 'thought_agent' ? this.agentMetadata : this.mainAgentMetadata;
        const metadata = metadataSource[agentName] || { 
            color: '#6c757d', 
            displayName: agentName, 
            icon: 'fa-robot' 
        };
        
        // Check if this is a custom agent that might have internal conversations
        // Only ThoughtAgent level agents can have enhanced features
        const isCustomAgent = level === 'thought_agent' && this.isEnhancedAgent(agentName);
        
        // Always create a new step for chronological order
        const stepDiv = document.createElement('div');
        stepDiv.className = 'agent-step';
        stepDiv.id = stepId;
        stepDiv.innerHTML = `
            <div class="agent-header" onclick="window.thinkingPanel.toggleStep('${stepId}')">
                <div class="agent-info">
                    <span class="agent-badge" style="background-color: ${metadata.color}"></span>
                    <div>
                        <h6 class="agent-name">${metadata.displayName}</h6>
                        <p class="agent-status">
                            <span class="status-indicator running"></span>
                            Active
                        </p>
                    </div>
                </div>
                <div class="step-controls d-flex align-items-center">
                    ${isCustomAgent ? `
                        <button class="btn btn-sm btn-outline-info me-2" 
                                onclick="event.stopPropagation(); window.detailsPanel.showInternalConversationFullView('${agentName}', '${stepId}')"
                                title="View internal conversation"
                                id="${stepId}-expand-btn">
                            <i class="fas fa-expand-arrows-alt"></i>
                        </button>
                    ` : ''}
                    <i class="fas fa-chevron-down toggle-icon"></i>
                </div>
            </div>
            <div class="agent-content" id="${stepId}-content">
                <div class="agent-messages" id="${stepId}-messages">
                    <div class="text-muted text-center p-3">
                        <i class="fas fa-spinner fa-spin me-2"></i>
                        Agent is thinking...
                    </div>
                </div>
            </div>
        `;
        
        // Store step data only if it doesn't already exist (avoid overwriting custom step data)
        if (!this.agentSteps.has(stepId)) {
            this.agentSteps.set(stepId, {
                agentName: agentName,
                displayName: metadata.displayName,
                color: metadata.color,
                messages: [],
                startTime: stepTimestamp,
                status: 'running',
                isCustomAgent: isCustomAgent,
                internalConversation: []
            });
        }
        
        // Track this as the most recent step
        this.lastAgentStep = stepId;
        
        this.activeAgents.add(agentName);
        this.thinkingContent.appendChild(stepDiv);
        
        // Scroll to new step
        stepDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        
        console.log(`[ThinkingPanel] Added agent step: ${metadata.displayName} (${stepId})`);
    }
    
    addAgentMessage(data) {
        // Use the most recent step (last agent step that was created)
        let stepId = this.lastAgentStep;
        
        // Fallback: if no recent step exists, or the step doesn't match the agent,
        // create a new step for this agent
        if (!stepId) {
            console.warn(`[ThinkingPanel] No recent step found, creating new step for agent: ${data.agent_name}`);
            this.addAgentStep({ agent_name: data.agent_name, timestamp: data.timestamp });
            stepId = this.lastAgentStep;
        }
        
        // Verify this step exists and belongs to the right agent
        const stepData = this.agentSteps.get(stepId);
        if (!stepData || stepData.agentName !== data.agent_name) {
            console.warn(`[ThinkingPanel] Step ${stepId} doesn't match agent ${data.agent_name}, creating new step`);
            this.addAgentStep({ agent_name: data.agent_name, timestamp: data.timestamp });
            stepId = this.lastAgentStep;
        }
        
        const messagesContainer = document.getElementById(`${stepId}-messages`);
        if (!messagesContainer) {
            console.warn(`[ThinkingPanel] Messages container not found for step: ${stepId}`);
            return;
        }
        
        // Clear "thinking" message if it exists
        const thinkingMsg = messagesContainer.querySelector('.text-muted.text-center');
        if (thinkingMsg) {
            thinkingMsg.remove();
        }
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = 'agent-message mb-2';
        messageDiv.innerHTML = `
            <div class="message-header d-flex justify-content-between align-items-center mb-2">
                <small class="text-muted">
                    <i class="fas fa-clock me-1"></i>
                    ${this.formatTimestamp(data.timestamp)}
                </small>
                <small class="text-muted">
                    Message #${data.message_id || 'N/A'}
                </small>
            </div>
            <div class="message-content markdown-content">
                ${this.formatMessageContent(data.content)}
            </div>
        `;
        
        // Process markdown content if markdown utils are available
        if (window.markdownUtils) {
            window.markdownUtils.processMessageElement(messageDiv);
        }
        
        messagesContainer.appendChild(messageDiv);
        
        // Update step data
        const finalStepData = this.agentSteps.get(stepId);
        if (finalStepData) {
            finalStepData.messages.push(data);
        }
        
        // Update agent status to completed
        this.updateAgentStatus(stepId, 'completed');
        
        // Scroll to show new message
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        
        console.log(`[ThinkingPanel] Added message to step ${stepId} for agent: ${data.agent_name}`);
    }
    
    addThinkingUpdate(data) {
        if (data.type === 'main_conversation_started') {
            const updateDiv = document.createElement('div');
            updateDiv.className = 'thinking-update mb-3';
            updateDiv.innerHTML = `
                <div class="alert alert-success border-left-success">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-cogs fa-lg text-success me-3"></i>
                        <div>
                            <h6 class="mb-1">Main Conversation Started</h6>
                            <p class="mb-0">${data.message}</p>
                        </div>
                    </div>
                </div>
            `;
            this.thinkingContent.appendChild(updateDiv);
        }
    }
    
    showConversationCompleted(data) {
        const completedDiv = document.createElement('div');
        completedDiv.className = 'conversation-summary mb-3';
        completedDiv.innerHTML = `
            <div class="alert alert-info border-left-info">
                <div class="d-flex align-items-center">
                    <i class="fas fa-check-circle fa-2x text-info me-3"></i>
                    <div>
                        <h6 class="mb-1">Main Conversation Completed</h6>
                        <p class="mb-1">Total messages processed: <strong>${data.total_messages}</strong></p>
                        <small class="text-muted">${this.formatTimestamp(data.timestamp)}</small>
                    </div>
                </div>
            </div>
        `;
        
        this.thinkingContent.appendChild(completedDiv);
        
        // Mark all agents as completed
        this.agentSteps.forEach((stepData, stepId) => {
            this.updateAgentStatus(stepId, 'completed');
        });
    }
    
    finalizeConversation(data) {
        const finalDiv = document.createElement('div');
        finalDiv.className = 'conversation-final mb-3';
        finalDiv.innerHTML = `
            <div class="alert alert-success border-left-success">
                <div class="d-flex align-items-center">
                    <i class="fas fa-flag-checkered fa-2x text-success me-3"></i>
                    <div>
                        <h6 class="mb-1">Conversation Completed Successfully!</h6>
                        <p class="mb-0">Final response has been generated and delivered.</p>
                        <small class="text-muted">${this.formatTimestamp(data.timestamp)}</small>
                    </div>
                </div>
            </div>
        `;
        
        this.thinkingContent.appendChild(finalDiv);
        finalDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
    
    // NEW: Show response completed (conversation continues)
    showResponseCompleted(data) {
        const responseDiv = document.createElement('div');
        responseDiv.className = 'response-completed mb-3';
        responseDiv.innerHTML = `
            <div class="alert alert-info border-left-info">
                <div class="d-flex align-items-center">
                    <i class="fas fa-check-circle fa-2x text-info me-3"></i>
                    <div>
                        <h6 class="mb-1">Response Generated (Message ${data.message_count})</h6>
                        <p class="mb-0">Ready for follow-up questions in this conversation.</p>
                        <small class="text-muted">${this.formatTimestamp(data.timestamp)}</small>
                    </div>
                </div>
            </div>
        `;
        
        this.thinkingContent.appendChild(responseDiv);
        responseDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
    
    // NEW: Show conversation ended
    showConversationEnded(data) {
        const endDiv = document.createElement('div');
        endDiv.className = 'conversation-ended mb-3';
        endDiv.innerHTML = `
            <div class="alert alert-warning border-left-warning">
                <div class="d-flex align-items-center">
                    <i class="fas fa-stop-circle fa-2x text-warning me-3"></i>
                    <div>
                        <h6 class="mb-1">Conversation Ended</h6>
                        <p class="mb-0">Chat cleared. Start a new conversation with your next message.</p>
                        <small class="text-muted">${this.formatTimestamp(data.timestamp)}</small>
                    </div>
                </div>
            </div>
        `;
        
        this.thinkingContent.appendChild(endDiv);
        endDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
    
    // NEW: Show conversation ended
    showConversationEnded(data) {
        const endDiv = document.createElement('div');
        endDiv.className = 'conversation-ended mb-3';
        endDiv.innerHTML = `
            <div class="alert alert-warning border-left-warning">
                <div class="d-flex align-items-center">
                    <i class="fas fa-stop-circle fa-2x text-warning me-3"></i>
                    <div>
                        <h6 class="mb-1">Conversation Ended</h6>
                        <p class="mb-0">Chat cleared. Start a new conversation with your next message.</p>
                        <small class="text-muted">${this.formatTimestamp(data.timestamp)}</small>
                    </div>
                </div>
            </div>
        `;
        
        this.thinkingContent.appendChild(endDiv);
        endDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        
        // Clear thinking process after showing end message
        setTimeout(() => {
            this.clearThinkingProcess();
        }, 2000);
    }
    
    showError(data) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'conversation-error mb-3';
        errorDiv.innerHTML = `
            <div class="alert alert-danger border-left-danger">
                <div class="d-flex align-items-center">
                    <i class="fas fa-exclamation-triangle fa-2x text-danger me-3"></i>
                    <div>
                        <h6 class="mb-1">Conversation Error</h6>
                        <p class="mb-0">${data.error || 'Unknown error occurred'}</p>
                        <small class="text-muted">${this.formatTimestamp(data.timestamp)}</small>
                    </div>
                </div>
            </div>
        `;
        
        this.thinkingContent.appendChild(errorDiv);
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        
        // Mark all running agents as error
        this.agentSteps.forEach((stepData, stepId) => {
            if (stepData.status === 'running') {
                this.updateAgentStatus(stepId, 'error');
            }
        });
    }
    
    // NEW: MainAgent specific methods
    showMainAgentStarted(data) {
        const startDiv = document.createElement('div');
        startDiv.className = 'main-agent-start mb-3';
        startDiv.innerHTML = `
            <div class="alert alert-primary border-left-primary">
                <div class="d-flex align-items-center">
                    <i class="fas fa-brain fa-2x text-primary me-3"></i>
                    <div>
                        <h6 class="mb-1">Main Agent Started</h6>
                        <p class="mb-0"><strong>Query:</strong> ${data.user_query}</p>
                        <small class="text-muted">${this.formatTimestamp(data.timestamp)}</small>
                    </div>
                </div>
            </div>
        `;
        
        // Remove no-conversation message
        const noConversation = this.thinkingContent.querySelector('.no-conversation');
        if (noConversation) {
            noConversation.remove();
        }
        
        this.thinkingContent.appendChild(startDiv);
    }
    
    handleThoughtAgentLifecycle(data) {
        console.log('[ThinkingPanel] handleThoughtAgentLifecycle called with:', data);
        console.log('[DEBUG] thought_data structure:', JSON.stringify(data.thought_data, null, 2));
        const { action, thought_agent_id, thought_data, response, error } = data;
        
        switch (action) {
            case 'created':
                console.log('[ThinkingPanel] Creating container for thought agent:', thought_agent_id);
                console.log('[DEBUG] About to call createThoughtAgentContainer with:', thought_agent_id, thought_data);
                try {
                    this.createThoughtAgentContainer(thought_agent_id, thought_data);
                    console.log('[DEBUG] createThoughtAgentContainer completed successfully');
                } catch (error) {
                    console.error('[ERROR] createThoughtAgentContainer failed:', error);
                    console.error('[ERROR] Stack trace:', error.stack);
                }
                break;
            case 'started':
                console.log('[ThinkingPanel] Starting thought agent:', thought_agent_id);
                this.updateThoughtAgentStatus(thought_agent_id, 'running');
                break;
            case 'completed':
                console.log('[ThinkingPanel] Completing thought agent:', thought_agent_id);
                this.updateThoughtAgentStatus(thought_agent_id, 'completed');
                if (response) {
                    this.addThoughtAgentResponse(thought_agent_id, response);
                }
                break;
            case 'discarded':
                console.log('[ThinkingPanel] Discarding thought agent:', thought_agent_id);
                this.updateThoughtAgentStatus(thought_agent_id, 'discarded');
                break;
            case 'finalized':
                this.updateThoughtAgentStatus(thought_agent_id, 'finalized');
                break;
            case 'error':
                this.updateThoughtAgentStatus(thought_agent_id, 'error');
                if (error) {
                    this.addThoughtAgentError(thought_agent_id, error);
                }
                break;
        }
    }
    
    createThoughtAgentContainer(thoughtAgentId, thoughtData) {
        console.log('[DEBUG] createThoughtAgentContainer called with:', thoughtAgentId, thoughtData);
        console.log('[DEBUG] thoughtData type:', typeof thoughtData);
        console.log('[DEBUG] thoughtData content:', JSON.stringify(thoughtData, null, 2));
        
        // Handle the case where thoughtData might be null/undefined or doesn't have expected structure
        const displayName = thoughtData && thoughtData.name ? thoughtData.name : thoughtAgentId;
        const description = thoughtData && thoughtData.description ? thoughtData.description : '';
        
        // Create a sanitized ID for CSS selectors (remove spaces, special chars, etc.)
        const sanitizedId = thoughtAgentId.replace(/[^a-zA-Z0-9-_]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
        
        console.log('[DEBUG] Using displayName:', displayName, 'description:', description);
        console.log('[DEBUG] Original thoughtAgentId:', thoughtAgentId, 'Sanitized ID:', sanitizedId);
        
        const containerDiv = document.createElement('div');
        containerDiv.className = 'thought-agent-container';
        containerDiv.id = `thought-agent-${sanitizedId}`;
        containerDiv.innerHTML = `
            <div class="thought-agent-header" onclick="window.thinkingPanel.toggleThoughtAgent('${thoughtAgentId.replace(/'/g, "\\'")}')">
                <div class="agent-info">
                    <span class="thought-agent-badge">📁</span>
                    <div>
                        <h6 class="thought-agent-name">ThoughtAgent: ${displayName}</h6>
                        <p class="thought-agent-status">
                            <span class="status-indicator running"></span>
                            Initializing...
                        </p>
                        <small class="thought-agent-description text-muted">${description}</small>
                    </div>
                </div>
                <div class="thought-agent-controls d-flex align-items-center">
                    <i class="fas fa-chevron-down toggle-icon"></i>
                </div>
            </div>
            <div class="thought-agent-content collapsed" id="thought-agent-${sanitizedId}-content">
                <div class="nested-agents-container" id="thought-agent-${sanitizedId}-agents">
                    <div class="text-muted text-center p-3">
                        <i class="fas fa-spinner fa-spin me-2"></i>
                        ThoughtAgent is initializing...
                    </div>
                </div>
            </div>
        `;
        
        // Store container data
        this.thoughtAgentContainers.set(thoughtAgentId, {
            thoughtData: thoughtData,
            status: 'running',
            nestedAgents: new Map(),
            element: containerDiv,
            sanitizedId: sanitizedId,
            createdAt: new Date()
        });
        
        console.log('[DEBUG] After storing in thoughtAgentContainers, map size:', this.thoughtAgentContainers.size);
        console.log('[DEBUG] Available containers:', Array.from(this.thoughtAgentContainers.keys()));
        
        // Restore previous state if available
        const shouldExpand = this.restoreContainerState(thoughtAgentId);
        const content = containerDiv.querySelector(`#thought-agent-${sanitizedId}-content`);
        const toggleIcon = containerDiv.querySelector('.toggle-icon');
        
        if (!shouldExpand && content && toggleIcon) {
            content.classList.add('collapsed');
            toggleIcon.classList.add('collapsed');
        } else if (shouldExpand && content && toggleIcon) {
            content.classList.remove('collapsed');
            toggleIcon.classList.remove('collapsed');
        }
        
        this.thinkingContent.appendChild(containerDiv);
        console.log(`[DEBUG] ThoughtAgent container appended to DOM. Display name: ${displayName}, expanded: ${shouldExpand}`);
        console.log('[DEBUG] thinkingContent children count:', this.thinkingContent.children.length);
        console.log(`[ThinkingPanel] Created ThoughtAgent container: ${displayName} (expanded: ${shouldExpand})`);
    }
    
    updateThoughtAgentStatus(thoughtAgentId, status) {
        const container = this.thoughtAgentContainers.get(thoughtAgentId);
        if (!container) return;
        
        const statusElement = container.element.querySelector('.thought-agent-status');
        const statusIndicator = container.element.querySelector('.status-indicator');
        
        if (statusElement && statusIndicator) {
            statusIndicator.className = `status-indicator ${status}`;
            
            const statusText = {
                'running': 'Active',
                'completed': 'Completed',
                'discarded': 'Discarded',
                'finalized': 'Finalized',
                'error': 'Error'
            };
            
            const activeCount = container.nestedAgents.size;
            const statusMessage = status === 'running' && activeCount > 0 
                ? `Active (${activeCount} agents)` 
                : statusText[status] || status;
            
            statusElement.innerHTML = `
                <span class="status-indicator ${status}"></span>
                ${statusMessage}
            `;
        }
        
        // Update container class for visual styling
        container.element.className = `thought-agent-container ${status}`;
        container.status = status;
        
        // Schedule cleanup for completed containers
        if (status === 'completed' || status === 'finalized') {
            this.scheduleContainerCleanup(thoughtAgentId);
        }
    }
    
    addNestedAgentStep(data) {
        console.log('[ThinkingPanel] addNestedAgentStep called with:', data);
        const thoughtAgentId = data.thought_agent_id;
        console.log('[ThinkingPanel] Looking for container for thought agent:', thoughtAgentId);
        console.log('[ThinkingPanel] Available containers:', Array.from(this.thoughtAgentContainers.keys()));
        const container = this.thoughtAgentContainers.get(thoughtAgentId);
        
        if (!container) {
            console.warn(`[ThinkingPanel] No container found for ThoughtAgent: ${thoughtAgentId}`);
            console.warn(`[ThinkingPanel] Available containers:`, this.thoughtAgentContainers);
            return;
        }
        
        // Generate nested step ID
        const nestedStepId = `nested-${thoughtAgentId}-${this.currentNestedStepId++}`;
        
        // Get ThoughtAgent-level metadata
        const metadata = this.agentMetadata[data.agent_name] || { 
            color: '#6c757d', 
            displayName: data.agent_name, 
            icon: 'fa-robot' 
        };
        
        // Check if this is a custom agent
        const isCustomAgent = this.isEnhancedAgent(data.agent_name);
        
        // Create nested agent step
        const stepDiv = document.createElement('div');
        stepDiv.className = 'agent-step nested-agent-step';
        stepDiv.id = nestedStepId;
        stepDiv.innerHTML = `
            <div class="agent-header" onclick="window.thinkingPanel.toggleStep('${nestedStepId}')">
                <div class="agent-info">
                    <span class="agent-badge" style="background-color: ${metadata.color}"></span>
                    <div>
                        <h6 class="agent-name">${metadata.displayName}</h6>
                        <p class="agent-status">
                            <span class="status-indicator running"></span>
                            Active
                        </p>
                    </div>
                </div>
                <div class="step-controls d-flex align-items-center">
                    ${isCustomAgent ? `
                        <button class="btn btn-sm btn-outline-info me-2" 
                                onclick="event.stopPropagation(); window.detailsPanel.showInternalConversationFullView('${data.agent_name}', '${nestedStepId}', {level: 'thought_agent', thought_agent_id: '${thoughtAgentId}'})"
                                title="View internal conversation"
                                id="${nestedStepId}-expand-btn">
                            <i class="fas fa-expand-arrows-alt"></i>
                        </button>
                    ` : ''}
                    <i class="fas fa-chevron-down toggle-icon"></i>
                </div>
            </div>
            <div class="agent-content" id="${nestedStepId}-content">
                <div class="agent-messages" id="${nestedStepId}-messages">
                    <div class="text-muted text-center p-3">
                        <i class="fas fa-spinner fa-spin me-2"></i>
                        Agent is thinking...
                    </div>
                </div>
            </div>
        `;
        
        // Add to nested container
        const sanitizedId = container.sanitizedId;
        const agentsContainer = container.element.querySelector(`#thought-agent-${sanitizedId}-agents`);
        
        if (!agentsContainer) {
            console.error(`[ThinkingPanel] Could not find agents container for ThoughtAgent: ${thoughtAgentId}`);
            console.error(`[ThinkingPanel] Container element:`, container.element);
            console.error(`[ThinkingPanel] Looking for selector: #thought-agent-${sanitizedId}-agents`);
            console.error(`[ThinkingPanel] Container innerHTML:`, container.element.innerHTML);
            console.error(`[ThinkingPanel] All nested containers in DOM:`, document.querySelectorAll('.nested-agents-container'));
            return;
        }
        
        // Remove "initializing" message if it exists
        const initializingMsg = agentsContainer.querySelector('.text-muted.text-center');
        if (initializingMsg) {
            initializingMsg.remove();
        }
        
        agentsContainer.appendChild(stepDiv);
        
        // Store nested step data
        this.nestedAgentSteps.set(nestedStepId, {
            agentName: data.agent_name,
            displayName: metadata.displayName,
            color: metadata.color,
            messages: [],
            startTime: data.timestamp,
            status: 'running',
            isCustomAgent: isCustomAgent,
            thoughtAgentId: thoughtAgentId,
            internalConversation: []
        });
        
        // Update container nested agents tracking
        container.nestedAgents.set(data.agent_name, nestedStepId);
        
        // Update ThoughtAgent status to show active agents count
        this.updateThoughtAgentStatus(thoughtAgentId, 'running');
        
        console.log(`[ThinkingPanel] Added nested agent step: ${metadata.displayName} in ${thoughtAgentId}`);
    }
    
    addNestedAgentMessage(data) {
        const thoughtAgentId = data.thought_agent_id;
        const container = this.thoughtAgentContainers.get(thoughtAgentId);
        
        if (!container) {
            console.warn(`[ThinkingPanel] No container found for ThoughtAgent: ${thoughtAgentId}`);
            return;
        }
        
        // Find the most recent nested step for this agent in this ThoughtAgent
        let targetStepId = null;
        for (const [stepId, stepData] of this.nestedAgentSteps) {
            if (stepData.agentName === data.agent_name && stepData.thoughtAgentId === thoughtAgentId) {
                targetStepId = stepId;
            }
        }
        
        if (!targetStepId) {
            console.warn(`[ThinkingPanel] No nested step found for agent ${data.agent_name} in ${thoughtAgentId}`);
            return;
        }
        
        // Add message to the nested step (reuse existing addAgentMessage logic)
        const messagesContainer = document.getElementById(`${targetStepId}-messages`);
        if (!messagesContainer) return;
        
        // Clear "thinking" message if it exists
        const thinkingMsg = messagesContainer.querySelector('.text-muted.text-center');
        if (thinkingMsg) {
            thinkingMsg.remove();
        }
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = 'agent-message mb-2';
        messageDiv.innerHTML = `
            <div class="message-header d-flex justify-content-between align-items-center mb-2">
                <small class="text-muted">
                    <i class="fas fa-clock me-1"></i>
                    ${this.formatTimestamp(data.timestamp)}
                </small>
                <small class="text-muted">
                    Message #${data.message_id || 'N/A'}
                </small>
            </div>
            <div class="message-content markdown-content">
                ${this.formatMessageContent(data.content)}
            </div>
        `;
        
        // Process markdown content if markdown utils are available
        if (window.markdownUtils) {
            window.markdownUtils.processMessageElement(messageDiv);
        }
        
        messagesContainer.appendChild(messageDiv);
        
        // Update nested step data
        const stepData = this.nestedAgentSteps.get(targetStepId);
        if (stepData) {
            stepData.messages.push(data);
            this.updateNestedAgentStatus(targetStepId, 'completed');
        }
        
        console.log(`[ThinkingPanel] Added nested message to ${targetStepId} for agent: ${data.agent_name}`);
    }
    
    addNestedCustomAgentThinking(data) {
        // Similar to addCustomAgentThinking but for nested agents
        const thoughtAgentId = data.thought_agent_id;
        
        if (thoughtAgentId) {
            // This is a nested thinking event
            // You can add specific logic here for nested custom thinking
            console.log(`[ThinkingPanel] Nested custom thinking for ${data.agent} in ${thoughtAgentId}: ${data.content}`);
        }
    }
    
    storeNestedInternalConversationData(data) {
        const backendStepId = data.step_id;
        const thoughtAgentId = data.thought_agent_id;
        const backendAgentName = data.agent_name;
        
        console.log(`[ThinkingPanel] storeNestedInternalConversationData called with backend stepId: ${backendStepId}, thoughtAgent: ${thoughtAgentId}, backend agent: ${backendAgentName}`);
        
        // Map backend agent names to frontend agent names
        const frontendAgentName = this.mapCustomAgentName(backendAgentName);
        console.log(`[ThinkingPanel] Mapped backend agent '${backendAgentName}' to frontend agent '${frontendAgentName}'`);
        
        // Find the actual nested step ID for this agent in this thought agent
        let actualStepId = null;
        const container = this.thoughtAgentContainers.get(thoughtAgentId);
        
        if (container && container.nestedAgents) {
            // Try both backend and frontend agent names
            actualStepId = container.nestedAgents.get(frontendAgentName) || container.nestedAgents.get(backendAgentName);
            console.log(`[ThinkingPanel] Found actual step ID from container mapping: ${actualStepId}`);
        }
        
        // If we don't have the mapping, search through nested steps
        if (!actualStepId) {
            for (const [stepId, stepData] of this.nestedAgentSteps) {
                // Try matching with both frontend and backend agent names
                if ((stepData.agentName === frontendAgentName || stepData.agentName === backendAgentName) && 
                    stepData.thoughtAgentId === thoughtAgentId) {
                    actualStepId = stepId;
                    console.log(`[ThinkingPanel] Found actual step ID from nested steps search: ${actualStepId}`);
                    break;
                }
            }
        }
        
        if (!actualStepId) {
            console.warn(`[ThinkingPanel] Could not find actual step ID for backend agent '${backendAgentName}' (mapped to '${frontendAgentName}') in thought agent ${thoughtAgentId}`);
            return;
        }
        
        // Find the nested step data using the actual step ID
        const stepData = this.nestedAgentSteps.get(actualStepId);
        if (stepData) {
            stepData.internalConversation = data.internal_conversation;
            
            // Update the expand button to show data is available
            const expandBtn = document.getElementById(`${actualStepId}-expand-btn`);
            if (expandBtn) {
                expandBtn.classList.add('btn-info');
                expandBtn.classList.remove('btn-outline-info');
                expandBtn.title = 'View internal conversation (data loaded)';
                
                // Add notification badge
                let badge = expandBtn.querySelector('.notification-badge');
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'notification-badge badge bg-success position-absolute';
                    badge.style.cssText = 'top: -5px; right: -5px; font-size: 0.6em;';
                    expandBtn.style.position = 'relative';
                    expandBtn.appendChild(badge);
                }
                badge.textContent = data.internal_conversation.length;
            }
            
            console.log(`[ThinkingPanel] Stored nested internal conversation for actual step ${actualStepId} (backend sent ${backendStepId})`);
        } else {
            console.warn(`[ThinkingPanel] Could not find step data for actual step ID ${actualStepId}`);
        }
    }
    
    updateNestedAgentStatus(stepId, status) {
        const stepElement = document.getElementById(stepId);
        if (!stepElement) return;
        
        const statusElement = stepElement.querySelector('.agent-status');
        const statusIndicator = stepElement.querySelector('.status-indicator');
        
        if (statusElement && statusIndicator) {
            statusIndicator.className = `status-indicator ${status}`;
            
            const statusText = {
                'running': 'Active',
                'waiting': 'Waiting',
                'completed': 'Completed',
                'error': 'Error'
            };
            
            statusElement.innerHTML = `
                <span class="status-indicator ${status}"></span>
                ${statusText[status] || status}
            `;
        }
        
        // Update nested step data
        const stepData = this.nestedAgentSteps.get(stepId);
        if (stepData) {
            stepData.status = status;
        }
    }
    
    // Enhanced toggle with state persistence
    toggleThoughtAgent(thoughtAgentId) {
        const container = this.thoughtAgentContainers.get(thoughtAgentId);
        if (!container) {
            console.warn(`[ThinkingPanel] No container found for toggleThoughtAgent: ${thoughtAgentId}`);
            return;
        }
        
        const sanitizedId = container.sanitizedId;
        const content = document.getElementById(`thought-agent-${sanitizedId}-content`);
        const toggleIcon = document.querySelector(`#thought-agent-${sanitizedId} .toggle-icon`);
        
        if (content && toggleIcon) {
            const isCollapsed = content.classList.contains('collapsed');
            const newState = isCollapsed; // If currently collapsed, will become expanded
            
            if (isCollapsed) {
                content.classList.remove('collapsed');
                toggleIcon.classList.remove('collapsed');
            } else {
                content.classList.add('collapsed');
                toggleIcon.classList.add('collapsed');
            }
            
            // Save the new state
            this.saveContainerState(thoughtAgentId, newState);
            
            console.log(`[ThinkingPanel] Toggled container ${thoughtAgentId} to ${newState ? 'expanded' : 'collapsed'}`);
        }
    }
    
    addThoughtAgentResponse(thoughtAgentId, response) {
        const container = this.thoughtAgentContainers.get(thoughtAgentId);
        if (!container) return;
        
        const agentsContainer = container.element.querySelector(`#thought-agent-${thoughtAgentId}-agents`);
        
        // Add response section
        const responseDiv = document.createElement('div');
        responseDiv.className = 'thought-agent-response mt-3 p-3 border rounded';
        responseDiv.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-check-circle text-success me-2"></i>
                <h6 class="mb-0">ThoughtAgent Response</h6>
            </div>
            <div class="response-content markdown-content">
                ${this.formatMessageContent(response)}
            </div>
        `;
        
        // Process markdown if available
        if (window.markdownUtils) {
            window.markdownUtils.processMessageElement(responseDiv);
        }
        
        agentsContainer.appendChild(responseDiv);
    }
    
    addThoughtAgentError(thoughtAgentId, error) {
        const container = this.thoughtAgentContainers.get(thoughtAgentId);
        if (!container) return;
        
        const agentsContainer = container.element.querySelector(`#thought-agent-${thoughtAgentId}-agents`);
        
        // Add error section
        const errorDiv = document.createElement('div');
        errorDiv.className = 'thought-agent-error mt-3 p-3 border border-danger rounded';
        errorDiv.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-exclamation-triangle text-danger me-2"></i>
                <h6 class="mb-0 text-danger">ThoughtAgent Error</h6>
            </div>
            <div class="error-content">
                <pre class="text-danger mb-0">${error}</pre>
            </div>
        `;
        
        agentsContainer.appendChild(errorDiv);
    }
    
    // ========== PHASE 3: Enhanced Container State Management & Routing ==========
    
    handleRoutingError(eventType, data, error) {
        console.error(`[ThinkingPanel] Routing error in ${eventType}:`, error, data);
        
        // Store error for potential recovery
        const errorKey = `${eventType}_${data.thought_agent_id || 'main'}_${Date.now()}`;
        this.routingErrors.set(errorKey, {
            eventType,
            data,
            error: error.message,
            timestamp: new Date(),
            retryCount: 0
        });
        
        // Try to queue message for later processing
        this.queueMessage(eventType, data);
        
        // Show user-friendly error notification
        this.showRoutingErrorNotification(eventType, data);
    }
    
    showRoutingErrorNotification(eventType, data) {
        console.warn(`[ThinkingPanel] Routing error for ${eventType}:`, data);
        // Could add UI notification here if needed
        // For now, just log the error to avoid breaking the application
    }
    
    queueMessage(eventType, data) {
        const queueKey = data.thought_agent_id || 'main';
        
        if (!this.messageQueue.has(queueKey)) {
            this.messageQueue.set(queueKey, []);
        }
        
        this.messageQueue.get(queueKey).push({
            eventType,
            data,
            timestamp: new Date()
        });
        
        // Process queue after a short delay
        setTimeout(() => this.processMessageQueue(queueKey), 1000);
    }
    
    processMessageQueue(queueKey) {
        const queue = this.messageQueue.get(queueKey);
        if (!queue || queue.length === 0) return;
        
        console.log(`[ThinkingPanel] Processing message queue for ${queueKey}, ${queue.length} messages`);
        
        const processedMessages = [];
        
        for (const queuedMessage of queue) {
            try {
                // Retry the original routing logic
                this.retryMessageRouting(queuedMessage);
                processedMessages.push(queuedMessage);
            } catch (error) {
                console.warn(`[ThinkingPanel] Still unable to process queued message:`, error);
                
                // If it's been too long, create a placeholder
                const messageAge = Date.now() - queuedMessage.timestamp.getTime();
                if (messageAge > 30000) { // 30 seconds
                    this.createPlaceholderForFailedMessage(queuedMessage);
                    processedMessages.push(queuedMessage);
                }
            }
        }
        
        // Remove processed messages from queue
        const remainingQueue = queue.filter(msg => !processedMessages.includes(msg));
        if (remainingQueue.length === 0) {
            this.messageQueue.delete(queueKey);
        } else {
            this.messageQueue.set(queueKey, remainingQueue);
        }
    }
    
    retryMessageRouting(queuedMessage) {
        const { eventType, data } = queuedMessage;
        
        switch (eventType) {
            case 'agent_started':
                if (data.level === 'thought_agent') {
                    this.addNestedAgentStep(data);
                } else {
                    this.addAgentStep(data);
                }
                break;
            case 'agent_message':
                if (data.level === 'thought_agent') {
                    this.addNestedAgentMessage(data);
                } else {
                    this.addAgentMessage(data);
                }
                break;
            case 'custom_agent_thinking':
                if (data.level === 'thought_agent') {
                    this.addNestedCustomAgentThinking(data);
                } else {
                    this.addCustomAgentThinking(data);
                }
                break;
        }
    }
    
    saveContainerState(thoughtAgentId, isExpanded) {
        this.containerStates.set(thoughtAgentId, {
            expanded: isExpanded,
            timestamp: new Date()
        });
        
        // Persist to localStorage for session recovery
        try {
            const allStates = Object.fromEntries(this.containerStates);
            localStorage.setItem('thinkingPanel_containerStates', JSON.stringify(allStates));
        } catch (e) {
            console.warn('[ThinkingPanel] Failed to save container states to localStorage:', e);
        }
    }
    
    restoreContainerState(thoughtAgentId) {
        // Try to restore from memory first
        if (this.containerStates.has(thoughtAgentId)) {
            return this.containerStates.get(thoughtAgentId).expanded;
        }
        
        // Try to restore from localStorage
        try {
            const stored = localStorage.getItem('thinkingPanel_containerStates');
            if (stored) {
                const allStates = JSON.parse(stored);
                if (allStates[thoughtAgentId]) {
                    return allStates[thoughtAgentId].expanded;
                }
            }
        } catch (e) {
            console.warn('[ThinkingPanel] Failed to restore container states from localStorage:', e);
        }
        
        // Default to expanded for new containers
        return true;
    }
    
    scheduleContainerCleanup(thoughtAgentId, delayMs = 300000) { // 5 minutes default
        // Cancel existing cleanup task if any
        if (this.containerCleanupTasks.has(thoughtAgentId)) {
            clearTimeout(this.containerCleanupTasks.get(thoughtAgentId));
        }
        
        // Schedule new cleanup
        const timeoutId = setTimeout(() => {
            this.cleanupCompletedContainer(thoughtAgentId);
        }, delayMs);
        
        this.containerCleanupTasks.set(thoughtAgentId, timeoutId);
        console.log(`[ThinkingPanel] Scheduled cleanup for container ${thoughtAgentId} in ${delayMs}ms`);
    }
    
    cleanupCompletedContainer(thoughtAgentId) {
        const container = this.thoughtAgentContainers.get(thoughtAgentId);
        if (!container || container.status !== 'completed') {
            return;
        }
        
        console.log(`[ThinkingPanel] Cleaning up completed container: ${thoughtAgentId}`);
        
        // Add fade-out animation
        container.element.style.transition = 'opacity 0.5s ease-out';
        container.element.style.opacity = '0.7';
        container.element.classList.add('completed-cleanup');
        
        // Clean up associated data
        this.containerCleanupTasks.delete(thoughtAgentId);
        
        // Remove container state after additional delay
        setTimeout(() => {
            this.containerStates.delete(thoughtAgentId);
            // Note: We keep the container in thoughtAgentContainers for reference
            // but mark it as cleaned up
            container.cleanedUp = true;
        }, 30000); // 30 seconds
    }
    
    // Helper method for retry button in failed message placeholders
    retryFailedMessage(timestamp) {
        // Find the error by timestamp
        for (const [errorKey, errorData] of this.routingErrors) {
            if (errorData.timestamp.getTime().toString() === timestamp) {
                console.log(`[ThinkingPanel] Retrying failed message: ${errorKey}`);
                
                try {
                    this.retryMessageRouting({
                        eventType: errorData.eventType,
                        data: errorData.data
                    });
                    
                    // Remove error from tracking
                    this.routingErrors.delete(errorKey);
                    
                    // Remove placeholder
                    const placeholders = document.querySelectorAll('.routing-error-placeholder');
                    placeholders.forEach(placeholder => {
                        if (placeholder.innerHTML.includes(timestamp)) {
                            placeholder.remove();
                        }
                    });
                    
                } catch (error) {
                    console.error(`[ThinkingPanel] Retry failed for ${errorKey}:`, error);
                    errorData.retryCount++;
                }
                break;
            }
        }
    }
    
    // Utility methods
    findStepByAgent(agentName) {
        // Note: This function finds the FIRST step for an agent, not the most recent one
        // It's kept for potential utility purposes but main logic now uses lastAgentStep
        for (const [stepId, stepData] of this.agentSteps) {
            if (stepData.agentName === agentName) {
                return stepId;
            }
        }
        return null;
    }
    
    findMostRecentStepByAgent(agentName) {
        // Find the most recent step for a given agent by searching both agent names and timestamps
        let mostRecentStepId = null;
        let mostRecentTime = 0;
        
        const mappedAgentName = this.mapCustomAgentName(agentName);
        
        for (const [stepId, stepData] of this.agentSteps) {
            if (stepData.agentName === agentName || stepData.agentName === mappedAgentName) {
                const stepTime = new Date(stepData.startTime).getTime();
                if (stepTime > mostRecentTime) {
                    mostRecentTime = stepTime;
                    mostRecentStepId = stepId;
                }
            }
        }
        
        // Also check nested agent steps
        for (const [stepId, stepData] of this.nestedAgentSteps) {
            if (stepData.agentName === agentName || stepData.agentName === mappedAgentName) {
                const stepTime = new Date(stepData.startTime || Date.now()).getTime();
                if (stepTime > mostRecentTime) {
                    mostRecentTime = stepTime;
                    mostRecentStepId = stepId;
                }
            }
        }
        
        return mostRecentStepId;
    }
    
    // Data Bridge Method: Expose internal conversation data to DetailsPanel
    getInternalConversationForAgent(agentName, stepId = null, context = null) {
        console.log(`[ThinkingPanel] getInternalConversationForAgent called with agentName: ${agentName}, stepId: ${stepId}, context:`, context);
        
        // Map agent name to handle both backend and frontend naming conventions
        const mappedAgentName = this.mapCustomAgentName(agentName);
        console.log(`[ThinkingPanel] Mapped agent name '${agentName}' to '${mappedAgentName}'`);
        
        // Handle ThoughtAgent level context - search in nested agents
        if (context && context.level === 'thought_agent') {
            console.log(`[ThinkingPanel] Searching for nested agent data with stepId: ${stepId}`);
            
            // Look in nested agent steps
            if (stepId) {
                const nestedStepData = this.nestedAgentSteps.get(stepId);
                console.log(`[ThinkingPanel] Found nested step data:`, nestedStepData);
                
                if (nestedStepData && nestedStepData.isCustomAgent && nestedStepData.internalConversation) {
                    console.log(`[ThinkingPanel] Returning nested internal conversation with ${nestedStepData.internalConversation.length} messages`);
                    return nestedStepData.internalConversation;
                }
            }
            
            // Fallback: Search for the agent in all nested steps for this thought agent
            if (context.thought_agent_id) {
                for (const [nestedStepId, stepData] of this.nestedAgentSteps) {
                    // Try matching with both original and mapped agent names
                    if ((stepData.agentName === agentName || stepData.agentName === mappedAgentName) && 
                        stepData.thoughtAgentId === context.thought_agent_id && 
                        stepData.isCustomAgent && stepData.internalConversation) {
                        console.log(`[ThinkingPanel] Found fallback nested conversation for ${agentName}/${mappedAgentName} in ${context.thought_agent_id}`);
                        return stepData.internalConversation;
                    }
                }
            }
            
            console.log(`[ThinkingPanel] No nested conversation found for ${agentName}/${mappedAgentName} in ThoughtAgent context`);
        }
        
        // Original logic for main agent level
        // If step ID is provided, get conversation for that specific step
        if (stepId) {
            const stepData = this.agentSteps.get(stepId);
            if (stepData && stepData.isCustomAgent && stepData.internalConversation) {
                console.log(`[ThinkingPanel] Found conversation by stepId: ${stepId}`);
                return stepData.internalConversation;
            }
        }
        
        // NEW: Check global agent-based lookup first (most reliable)
        if (this.agentInternalConversations) {
            let globalData = this.agentInternalConversations.get(agentName);
            if (!globalData) {
                globalData = this.agentInternalConversations.get(mappedAgentName);
            }
            if (globalData && globalData.internalConversation) {
                console.log(`[ThinkingPanel] Found conversation in global lookup for ${agentName}/${mappedAgentName} with ${globalData.internalConversation.length} messages`);
                return globalData.internalConversation;
            } else {
                console.log(`[ThinkingPanel] Global lookup exists but no data found for ${agentName}/${mappedAgentName}. Available keys:`, Array.from(this.agentInternalConversations.keys()));
            }
        } else {
            console.log(`[ThinkingPanel] No global agent conversations map available`);
        }
        
        // NEW: Search through ALL nested agent steps for any matching agent
        console.log(`[ThinkingPanel] Searching through all nested steps for agent: ${agentName}/${mappedAgentName}`);
        for (const [nestedStepId, stepData] of this.nestedAgentSteps) {
            if ((stepData.agentName === agentName || stepData.agentName === mappedAgentName) && 
                stepData.internalConversation && stepData.internalConversation.length > 0) {
                console.log(`[ThinkingPanel] Found conversation in nested step ${nestedStepId} for ${agentName}/${mappedAgentName}`);
                return stepData.internalConversation;
            }
        }
        console.log(`[ThinkingPanel] No conversation found in nested steps for ${agentName}/${mappedAgentName}`);
        
        // NEW: Search through ALL main agent steps for any matching agent
        console.log(`[ThinkingPanel] Searching through all main steps for agent: ${agentName}/${mappedAgentName}`);
        for (const [mainStepId, stepData] of this.agentSteps) {
            if ((stepData.agentName === agentName || stepData.agentName === mappedAgentName) && 
                stepData.internalConversation && stepData.internalConversation.length > 0) {
                console.log(`[ThinkingPanel] Found conversation in main step ${mainStepId} for ${agentName}/${mappedAgentName}`);
                return stepData.internalConversation;
            }
        }
        console.log(`[ThinkingPanel] No conversation found in main steps for ${agentName}/${mappedAgentName}`);
        
        
        // Fallback: Find the most recent step for this agent (backward compatibility)
        const fallbackStepId = this.findMostRecentStepByAgent(agentName);
        if (fallbackStepId) {
            const stepData = this.agentSteps.get(fallbackStepId);
            if (stepData && stepData.isCustomAgent && stepData.internalConversation) {
                console.log(`[ThinkingPanel] Found conversation by fallback stepId: ${fallbackStepId}`);
                return stepData.internalConversation;
            }
        }
        
        // NEW: Also try with mapped agent name
        const mappedFallbackStepId = this.findMostRecentStepByAgent(mappedAgentName);
        if (mappedFallbackStepId) {
            const stepData = this.agentSteps.get(mappedFallbackStepId);
            if (stepData && stepData.isCustomAgent && stepData.internalConversation) {
                console.log(`[ThinkingPanel] Found conversation by mapped fallback stepId: ${mappedFallbackStepId}`);
                return stepData.internalConversation;
            }
        }
        
        console.log(`[ThinkingPanel] No internal conversation found for agent: ${agentName}/${mappedAgentName}`);
        return [];
    }
    
    // Get all internal conversation data for agent (all steps)
    getAllInternalConversationForAgent(agentName) {
        const allConversations = [];
        const mappedAgentName = this.mapCustomAgentName(agentName);
        
        for (const [stepId, stepData] of this.agentSteps) {
            if ((stepData.agentName === agentName || stepData.agentName === mappedAgentName) && 
                stepData.isCustomAgent && stepData.internalConversation) {
                allConversations.push(...stepData.internalConversation);
            }
        }
        
        // Sort by timestamp
        return allConversations.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    }
    
    storeInternalConversationData(data) {
        // Store internal conversation data from backend for button click access
        try {
            const stepId = data.step_id;
            const backendAgentName = data.agent_name; // This is what backend sends (e.g., 'expert_knowledge')
            const internalConversation = data.internal_conversation;
            
            // CRITICAL FIX: Convert backend agent name to standard frontend format
            const standardAgentName = this.mapCustomAgentName(backendAgentName);
            
            console.log(`[ThinkingPanel] storeInternalConversationData called with stepId: ${stepId}, backendAgent: ${backendAgentName}, standardAgent: ${standardAgentName}, conversations: ${internalConversation?.length || 0}`);
            
            if (!stepId) {
                console.warn(`[ThinkingPanel] No step_id provided in storage data for agent ${backendAgentName}`);
                return;
            }
            
            // Find the step data using the step ID from the thinking panel
            let targetStepData = null;
            for (const [currentStepId, stepData] of this.agentSteps) {
                if (currentStepId === stepId) {
                    targetStepData = stepData;
                    break;
                }
            }
            
            // NEW: Also check nested agent steps
            let nestedTargetStepData = null;
            for (const [nestedStepId, stepData] of this.nestedAgentSteps) {
                if (nestedStepId === stepId || stepData.stepId === stepId) {
                    nestedTargetStepData = stepData;
                    console.log(`[ThinkingPanel] Found nested step data for stepId: ${stepId}`);
                    break;
                }
            }
            
            // If step not found by exact ID, try to find the most recent step for this agent
            if (!targetStepData) {
                for (const [currentStepId, stepData] of this.agentSteps) {
                    // Try both backend and standard agent names
                    if ((stepData.agentName === backendAgentName || stepData.agentName === standardAgentName) && 
                        currentStepId.includes('expert_knowledge')) {
                        // Check if this step doesn't already have internal conversation data
                        if (!stepData.internalConversation) {
                            targetStepData = stepData;
                            break;
                        }
                    }
                }
            }
            
            // Store in nested agent steps if found
            if (nestedTargetStepData) {
                nestedTargetStepData.internalConversation = internalConversation;
                nestedTargetStepData.stepId = stepId;
                // IMPORTANT: Update agent name to standard format for consistency
                nestedTargetStepData.agentName = standardAgentName;
                console.log(`[ThinkingPanel] Stored ${internalConversation.length} messages in nested step ${stepId} for agent ${backendAgentName} -> ${standardAgentName}`);
                
                // Update UI for nested step
                const expandBtn = document.getElementById(`${stepId}-expand-btn`);
                if (expandBtn) {
                    expandBtn.classList.add('btn-info');
                    expandBtn.classList.remove('btn-outline-info');
                    expandBtn.title = 'View internal conversation (data loaded)';
                    
                    let badge = expandBtn.querySelector('.notification-badge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'notification-badge badge bg-success position-absolute';
                        badge.style.cssText = 'top: -5px; right: -5px; font-size: 0.6em;';
                        expandBtn.style.position = 'relative';
                        expandBtn.appendChild(badge);
                    }
                    badge.textContent = internalConversation.length;
                }
            }
            
            // Store in main agent steps if found
            if (targetStepData) {
                // Store the complete internal conversation data with step ID reference
                targetStepData.internalConversation = internalConversation;
                targetStepData.stepId = stepId; // Store the step ID for later reference
                // IMPORTANT: Update agent name to standard format for consistency
                targetStepData.agentName = standardAgentName;
                
                // Update the expand button to show data is available
                const expandBtn = document.getElementById(`${stepId}-expand-btn`);
                if (expandBtn) {
                    expandBtn.classList.add('btn-info');
                    expandBtn.classList.remove('btn-outline-info');
                    expandBtn.title = 'View internal conversation (data loaded)';
                    
                    // Add notification badge
                    let badge = expandBtn.querySelector('.notification-badge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'notification-badge badge bg-success position-absolute';
                        badge.style.cssText = 'top: -5px; right: -5px; font-size: 0.6em;';
                        expandBtn.style.position = 'relative';
                        expandBtn.appendChild(badge);
                    }
                    badge.textContent = internalConversation.length;
                }
                
                console.log(`[ThinkingPanel] Stored ${internalConversation.length} internal conversation messages for step ${stepId} with standardized agent name: ${standardAgentName}`);
            }
            
            // NEW: Create a global agent-based lookup for easy access
            if (!this.agentInternalConversations) {
                this.agentInternalConversations = new Map();
            }
            
            // CRITICAL FIX: Store by BOTH backend and standard agent names for maximum compatibility
            this.agentInternalConversations.set(backendAgentName, {
                stepId: stepId,
                internalConversation: internalConversation,
                timestamp: Date.now(),
                standardName: standardAgentName
            });
            this.agentInternalConversations.set(standardAgentName, {
                stepId: stepId,
                internalConversation: internalConversation,
                timestamp: Date.now(),
                originalName: backendAgentName
            });
            
            console.log(`[ThinkingPanel] Global storage updated for backend agent: ${backendAgentName} and standard agent: ${standardAgentName} with ${internalConversation.length} messages`);
            console.log(`[ThinkingPanel] Global storage now contains keys:`, Array.from(this.agentInternalConversations.keys()));
            
            if (!targetStepData && !nestedTargetStepData) {
                console.warn(`[ThinkingPanel] No step found for step_id ${stepId} to store internal conversation data, but stored in global lookup`);
            }
            
        } catch (error) {
            console.error('[ThinkingPanel] Error storing internal conversation data:', error);
        }
    }
    
    updateAgentStatus(stepId, status) {
        const stepElement = document.getElementById(stepId);
        if (!stepElement) return;
        
        const statusElement = stepElement.querySelector('.agent-status');
        const statusIndicator = stepElement.querySelector('.status-indicator');
        
        if (statusElement && statusIndicator) {
            statusIndicator.className = `status-indicator ${status}`;
            
            const statusText = {
                'running': 'Active',
                'waiting': 'Waiting',
                'completed': 'Completed',
                'error': 'Error'
            };
            
            statusElement.innerHTML = `
                <span class="status-indicator ${status}"></span>
                ${statusText[status] || status}
            `;
        }
        
        // Update stored data
        const stepData = this.agentSteps.get(stepId);
        if (stepData) {
            stepData.status = status;
        }
    }
    
    toggleStep(stepId) {
        const content = document.getElementById(`${stepId}-content`);
        const toggleIcon = document.querySelector(`#${stepId} .toggle-icon`);
        
        if (content && toggleIcon) {
            const isCollapsed = content.classList.contains('collapsed');
            
            if (isCollapsed) {
                content.classList.remove('collapsed');
                toggleIcon.classList.remove('collapsed');
            } else {
                content.classList.add('collapsed');
                toggleIcon.classList.add('collapsed');
            }
        }
    }
    
    expandAll() {
        this.agentSteps.forEach((_, stepId) => {
            const content = document.getElementById(`${stepId}-content`);
            const toggleIcon = document.querySelector(`#${stepId} .toggle-icon`);
            
            if (content && toggleIcon) {
                content.classList.remove('collapsed');
                toggleIcon.classList.remove('collapsed');
            }
        });
    }
    
    collapseAll() {
        this.agentSteps.forEach((_, stepId) => {
            const content = document.getElementById(`${stepId}-content`);
            const toggleIcon = document.querySelector(`#${stepId} .toggle-icon`);
            
            if (content && toggleIcon) {
                content.classList.add('collapsed');
                toggleIcon.classList.add('collapsed');
            }
        });
    }
    
    formatMessageContent(content) {
        // Check if content is long enough to need expansion
        if (content.length > 300) {
            return this.renderExpandableContent(content, `thinking-msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, 300);
        }
        
        // Use the enhanced markdown utilities for proper rendering
        if (window.markdownUtils) {
            return window.markdownUtils.renderMarkdown(content);
        }
        
        // Fallback to basic formatting if markdown utils not available
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                return `<div class="code-block"><pre><code>${code.trim()}</code></pre></div>`;
            })
            .replace(/\n/g, '<br>')
            .trim();
    }
    
    renderExpandableContent(content, messageId, maxLength = 300) {
        if (content.length <= maxLength) {
            // Use markdown rendering for short content
            if (window.markdownUtils) {
                return `<div class="message-content">${window.markdownUtils.renderMarkdown(content)}</div>`;
            }
            return `<div class="message-content">${content}</div>`;
        }
        
        const truncated = content.substring(0, maxLength);
        const remaining = content.substring(maxLength);
        
        return `
            <div class="message-content expandable-content">
                <div class="content-preview" id="preview-${messageId}">
                    ${window.markdownUtils ? window.markdownUtils.renderMarkdown(truncated) : truncated}
                    <span class="text-muted">...</span>
                </div>
                <div class="content-full" id="full-${messageId}" style="display: none;">
                    ${window.markdownUtils ? window.markdownUtils.renderMarkdown(content) : content}
                </div>
                <div class="content-controls mt-2">
                    <button class="btn btn-sm btn-outline-primary expand-btn" 
                            onclick="window.thinkingPanel.toggleContent('${messageId}')"
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
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
    
    // Internal conversation methods
    addCustomAgentThinking(data) {
        // Simplified approach: each step_id gets its own entry
        const agentName = this.mapCustomAgentName(data.agent);
        let stepId = null;
        
        // Use step_id from backend if provided (for expert knowledge agent unique calls)
        if (data.step_id) {
            stepId = data.step_id;
            
            // Check if this step already exists, if not create it
            if (!this.agentSteps.get(stepId)) {
                this.createStepForEnhancedAgent(stepId, agentName, data);
            }
            
            // Add this thinking message to the specific step
            const stepData = this.agentSteps.get(stepId);
            if (stepData) {
                stepData.internalConversation.push({
                    type: 'thinking_phase',
                    phase: data.phase,
                    content: data.content,
                    timestamp: data.timestamp
                });
                
                console.log(`[ThinkingPanel] Added thinking to step ${stepId}: ${data.content}`);
            }
        } else {
            // Existing behavior for other agents without step_id
            stepId = this.lastAgentStep;
            
            if (!stepId || !this.agentSteps.get(stepId) || this.agentSteps.get(stepId).agentName !== agentName) {
                for (const [sId, stepData] of this.agentSteps) {
                    if (stepData.agentName === agentName) {
                        stepId = sId;
                        break;
                    }
                }
            }
            
            if (stepId) {
                const stepData = this.agentSteps.get(stepId);
                if (stepData && stepData.isCustomAgent) {
                    stepData.internalConversation.push({
                        type: 'thinking_phase',
                        phase: data.phase,
                        content: data.content,
                        timestamp: data.timestamp
                    });
                }
            }
        }
        
        // Update expand button to show there's content
        if (stepId) {
            const expandBtn = document.getElementById(`${stepId}-expand-btn`);
            if (expandBtn) {
                expandBtn.classList.add('btn-info');
                expandBtn.classList.remove('btn-outline-info');
                expandBtn.title = 'View internal conversation (new activity)';
                
                // Update badge count
                const stepData = this.agentSteps.get(stepId);
                if (stepData && stepData.internalConversation) {
                    let badge = expandBtn.querySelector('.notification-badge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'notification-badge badge bg-success position-absolute';
                        badge.style.cssText = 'top: -5px; right: -5px; font-size: 0.6em;';
                        expandBtn.style.position = 'relative';
                        expandBtn.appendChild(badge);
                    }
                    badge.textContent = stepData.internalConversation.length;
                }
            }
        }
    }
    
    createStepForEnhancedAgent(stepId, agentName, data) {
        // Create a new step for enhanced agents (expert knowledge, websearch, etc.) with unique step ID
        const stepData = {
            agentName: agentName,
            startTime: data.timestamp || new Date().toISOString(),
            isCustomAgent: true,
            internalConversation: [],
            stepId: stepId // Store the unique step ID
        };
        
        this.agentSteps.set(stepId, stepData);
        this.lastAgentStep = stepId;
        
        // Create the visual step in the UI using the corrected method signature
        this.addAgentStep(agentName, data.timestamp || new Date().toISOString(), stepId);
        
        console.log(`[ThinkingPanel] Created new enhanced agent step ${stepId} for ${agentName}`);
    }
    
    addInternalConversationMessage(data) {
        // Handle explicit internal conversation messages from enhanced backend
        // Use the most recent step or find by agent
        let stepId = this.lastAgentStep;
        
        // Verify this step belongs to the right agent, otherwise find the right one
        if (!stepId || !this.agentSteps.get(stepId) || this.agentSteps.get(stepId).agentName !== data.agent_name) {
            // Find the most recent step for this specific agent
            for (const [sId, stepData] of this.agentSteps) {
                if (stepData.agentName === data.agent_name) {
                    stepId = sId;
                    break;
                }
            }
        }
        
        if (stepId) {
            const stepData = this.agentSteps.get(stepId);
            if (stepData && stepData.isCustomAgent) {
                let messageType = 'internal_message';
                let content = data.content;
                let iconClass = 'fa-comment';
                let messageClass = 'internal-message';
                
                // Handle different types of internal messages from Enhanced Expert Knowledge Agent
                if (data.type === 'rag_initialization') {
                    messageType = 'rag_initialization';
                    iconClass = 'fa-database';
                    messageClass = 'internal-message rag-init';
                    content = `🔧 **Knowledge System Initialization**\n\n${data.content}`;
                    if (data.metadata && data.metadata.query) {
                        content += `\n\n**Query:** ${data.metadata.query}`;
                    }
                } else if (data.type === 'assistant_initialization') {
                    messageType = 'assistant_initialization';
                    iconClass = 'fa-robot';
                    messageClass = 'internal-message assistant-init';
                    content = `🤖 **Assistant Setup**\n\n${data.content}`;
                } else if (data.type === 'rag_search_start') {
                    messageType = 'rag_search_start';
                    iconClass = 'fa-search';
                    messageClass = 'internal-message rag-search';
                    content = `🔍 **Knowledge Search Started**\n\n${data.content}`;
                    if (data.metadata && data.metadata.query) {
                        content += `\n\n**Search Query:** "${data.metadata.query}"`;
                    }
                } else if (data.type === 'rag_retrieval_start') {
                    messageType = 'rag_retrieval_start';
                    iconClass = 'fa-download';
                    messageClass = 'internal-message rag-retrieval';
                    content = `📥 **Document Retrieval**\n\n${data.content}`;
                } else if (data.type === 'rag_processing') {
                    messageType = 'rag_processing';
                    iconClass = 'fa-cogs';
                    messageClass = 'internal-message rag-processing';
                    content = `⚙️ **Processing Retrieved Data**\n\n${data.content}`;
                    if (data.metadata && data.metadata.message_count) {
                        content += `\n\n**Messages to Process:** ${data.metadata.message_count}`;
                    }
                } else if (data.type === 'rag_query') {
                    messageType = 'rag_query';
                    iconClass = 'fa-question-circle';
                    messageClass = 'internal-message rag-query';
                    content = `❓ **RAG Query**\n\n${data.content}`;
                    if (data.metadata && data.metadata.full_content) {
                        content += `\n\n<details><summary>Full Query</summary>\n\n${data.metadata.full_content}\n\n</details>`;
                    }
                } else if (data.type === 'rag_response') {
                    messageType = 'rag_response';
                    iconClass = 'fa-lightbulb';
                    messageClass = 'internal-message rag-response';
                    content = `💡 **RAG Response**\n\n${data.content}`;
                    if (data.metadata && data.metadata.full_content) {
                        content += `\n\n<details><summary>Full Response</summary>\n\n${data.metadata.full_content}\n\n</details>`;
                    }
                } else if (data.type === 'rag_completion') {
                    messageType = 'rag_completion';
                    iconClass = 'fa-check-circle';
                    messageClass = 'internal-message rag-completion';
                    content = `✅ **Knowledge Retrieval Complete**\n\n${data.content}`;
                    if (data.metadata && data.metadata.final_response_preview) {
                        content += `\n\n**Response Preview:** ${data.metadata.final_response_preview}...`;
                    }
                } else if (data.type === 'final_response') {
                    messageType = 'final_response';
                    iconClass = 'fa-check';
                    messageClass = 'internal-message final-response';
                    content = `✨ **Final Expert Response Generated**\n\n${data.content}`;
                    if (data.metadata && data.metadata.response_length) {
                        content += `\n\n**Response Length:** ${data.metadata.response_length} characters`;
                    }
                } else if (data.type === 'rag_error' || data.type === 'agent_error') {
                    messageType = 'internal_error';
                    iconClass = 'fa-exclamation-triangle';
                    messageClass = 'internal-message internal-error';
                    content = `⚠️ **Error in Knowledge Processing**\n\n${data.content}`;
                    if (data.metadata && data.metadata.error) {
                        content += `\n\n**Error Details:** ${data.metadata.error}`;
                    }
                } else if (data.type === 'tool_call') {
                    messageType = 'tool_call';
                    iconClass = 'fa-tools';
                    messageClass = 'internal-message tool-call';
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
                }
                
                stepData.internalConversation.push({
                    type: messageType,
                    content: content,
                    internal_agent: data.internal_agent || 'expert_knowledge',
                    role: data.role || 'assistant',
                    timestamp: data.timestamp,
                    messageId: data.message_id || data.step,
                    step: data.step,
                    tool_calls: data.tool_calls || [],
                    metadata: data.metadata || {},
                    iconClass: iconClass,
                    messageClass: messageClass
                });
                
                // Update expand button to show there's new content
                const expandBtn = document.getElementById(`${stepId}-expand-btn`);
                if (expandBtn) {
                    expandBtn.classList.add('btn-info');
                    expandBtn.classList.remove('btn-outline-info');
                    expandBtn.title = 'View internal conversation (live activity detected!)';
                    
                    // Add a notification badge
                    let badge = expandBtn.querySelector('.notification-badge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'notification-badge badge bg-warning position-absolute';
                        badge.style.cssText = 'top: -5px; right: -5px; font-size: 0.6em;';
                        expandBtn.style.position = 'relative';
                        expandBtn.appendChild(badge);
                    }
                    badge.textContent = stepData.internalConversation.length;
                }
                
                console.log(`[ThinkingPanel] Added internal conversation message for ${data.agent_name}: ${messageType}`);
                
                // Also add as a sub-message in the thinking panel for immediate visibility
                this.addSubMessage(stepId, {
                    type: messageType,
                    content: content,
                    iconClass: iconClass,
                    messageClass: messageClass,
                    timestamp: data.timestamp
                });
            }
        }
    }
    
    addSubMessage(stepId, messageData) {
        // Add a sub-message directly to the agent step in thinking panel
        const messagesContainer = document.getElementById(`${stepId}-messages`);
        if (!messagesContainer) return;
        
        // Remove the "thinking..." placeholder if it exists
        const placeholder = messagesContainer.querySelector('.text-muted.text-center');
        if (placeholder) {
            placeholder.remove();
        }
        
        // Create sub-message element
        const subMessageDiv = document.createElement('div');
        subMessageDiv.className = `sub-message ${messageData.messageClass}`;
        subMessageDiv.innerHTML = `
            <div class="sub-message-header">
                <i class="fas ${messageData.iconClass} me-2"></i>
                <span class="sub-message-type">${messageData.type.toUpperCase().replace(/_/g, ' ')}</span>
                <span class="sub-message-time text-muted ms-auto">${this.formatTimestamp(messageData.timestamp)}</span>
            </div>
            <div class="sub-message-content">
                ${this.formatMarkdownContent(messageData.content)}
            </div>
        `;
        
        messagesContainer.appendChild(subMessageDiv);
        
        // Scroll to bottom of messages
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    formatMarkdownContent(content) {
        // Simple markdown to HTML conversion for sub-messages
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```json\n([\s\S]*?)\n```/g, '<pre class="json-code">$1</pre>')
            .replace(/```([\s\S]*?)```/g, '<pre class="code-block">$1</pre>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^(.*)$/, '<p>$1</p>');
    }
    
    formatTimestamp(timestamp) {
        // Format timestamp for sub-messages
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
    }
    
    detectInternalConversation(data) {
        // Try to detect internal conversation patterns in regular messages
        const agentName = data.agent_name;
        const content = data.content;
        
        if (this.isEnhancedAgent(agentName)) {
            // Use the most recent step or find by agent
            let stepId = this.lastAgentStep;
            
            // Verify this step belongs to the right agent, otherwise find the right one
            if (!stepId || !this.agentSteps.get(stepId) || this.agentSteps.get(stepId).agentName !== agentName) {
                // Find the most recent step for this specific agent
                for (const [sId, stepData] of this.agentSteps) {
                    if (stepData.agentName === agentName) {
                        stepId = sId;
                        break;
                    }
                }
            }
            
            if (stepId) {
                const stepData = this.agentSteps.get(stepId);
                if (stepData && stepData.isCustomAgent) {
                    // Parse content for internal conversation indicators
                    const internalSteps = this.parseInternalConversation(content);
                    
                    if (internalSteps.length > 0) {
                        stepData.internalConversation.push(...internalSteps);
                        
                        // Update expand button
                        const expandBtn = document.getElementById(`${stepId}-expand-btn`);
                        if (expandBtn) {
                            expandBtn.classList.add('btn-info');
                            expandBtn.classList.remove('btn-outline-info');
                            expandBtn.title = 'View internal conversation (detected activity)';
                        }
                    }
                }
            }
        }
    }
    
    parseInternalConversation(content) {
        const internalSteps = [];
        
        // Look for patterns that indicate internal processes
        const patterns = [
            { regex: /Searching knowledge base for: (.+)/gi, type: 'knowledge_search' },
            { regex: /Found (\d+) relevant documents/gi, type: 'knowledge_results' },
            { regex: /Performing web search: (.+)/gi, type: 'web_search' },
            { regex: /Crawling URL: (.+)/gi, type: 'web_crawl' },
            { regex: /Retrieved content from: (.+)/gi, type: 'content_retrieval' },
            { regex: /Processing documents: (.+)/gi, type: 'document_processing' },
            { regex: /Query: (.+)/gi, type: 'query_processing' }
        ];
        
        patterns.forEach(pattern => {
            let match;
            while ((match = pattern.regex.exec(content)) !== null) {
                internalSteps.push({
                    type: 'detected_step',
                    stepType: pattern.type,
                    content: match[0],
                    details: match[1] || '',
                    timestamp: new Date().toISOString()
                });
            }
        });
        
        return internalSteps;
    }
    
    mapCustomAgentName(customAgentName) {
        // Legacy short name mapping - convert to standard backend names
        // Backend always uses full names like 'expert_knowledge_agent'
        const legacyMapping = {
            'expert_knowledge': 'expert_knowledge_agent',
            'websearch_crawl': 'websearch_and_crawl_agent',
            'websearch_and_crawl': 'websearch_and_crawl_agent', // Keep backward compatibility
            'code_executor': 'code_executor_agent'
        };
        
        // Return mapped name or original name (backend names pass through unchanged)
        return legacyMapping[customAgentName] || customAgentName;
    }
    
    isEnhancedAgent(agentName) {
        // Map legacy names to standard names and check if it's an enhanced agent
        const standardName = this.mapCustomAgentName(agentName);
        return ['expert_knowledge_agent', 'websearch_and_crawl_agent'].includes(standardName);
    }
    
    getInternalConversation(stepId) {
        const stepData = this.agentSteps.get(stepId);
        return stepData ? stepData.internalConversation || [] : [];
    }
    
    // Debug methods for troubleshooting
    debugAgentStorage() {
        console.log('=== AGENT STORAGE DEBUG ===');
        console.log('Global Agent Conversations:', this.agentInternalConversations);
        console.log('Available keys:', this.agentInternalConversations ? Array.from(this.agentInternalConversations.keys()) : 'None');
        
        console.log('Main Agent Steps:');
        for (const [stepId, stepData] of this.agentSteps) {
            if (stepData.internalConversation) {
                console.log(`  - ${stepId}: ${stepData.agentName} (${stepData.internalConversation.length} messages)`);
            }
        }
        
        console.log('Nested Agent Steps:');
        for (const [stepId, stepData] of this.nestedAgentSteps) {
            if (stepData.internalConversation) {
                console.log(`  - ${stepId}: ${stepData.agentName} (${stepData.internalConversation.length} messages)`);
            }
        }
        console.log('=== END DEBUG ===');
    }
    
    // Public API
    getStepData(stepId) {
        return this.agentSteps.get(stepId);
    }
    
    getAllSteps() {
        return Array.from(this.agentSteps.entries());
    }
    
    getActiveAgents() {
        return Array.from(this.activeAgents);
    }
    
    // DEBUG: Method to inspect current internal conversation data state
    debugInternalConversationState(agentName = null) {
        console.log('=== DEBUG: Internal Conversation State ===');
        
        if (agentName) {
            const mappedName = this.mapCustomAgentName(agentName);
            console.log(`Checking for agent: ${agentName} (mapped: ${mappedName})`);
            
            // Check global storage
            if (this.agentInternalConversations) {
                const globalData1 = this.agentInternalConversations.get(agentName);
                const globalData2 = this.agentInternalConversations.get(mappedName);
                console.log(`Global storage for '${agentName}':`, globalData1);
                console.log(`Global storage for '${mappedName}':`, globalData2);
            }
            
            // Check main steps
            console.log('Main agent steps:');
            for (const [stepId, stepData] of this.agentSteps) {
                if (stepData.agentName === agentName || stepData.agentName === mappedName) {
                    console.log(`  Step ${stepId}:`, {
                        agentName: stepData.agentName,
                        hasInternalConversation: !!stepData.internalConversation,
                        conversationLength: stepData.internalConversation?.length || 0
                    });
                }
            }
            
            // Check nested steps
            console.log('Nested agent steps:');
            for (const [stepId, stepData] of this.nestedAgentSteps) {
                if (stepData.agentName === agentName || stepData.agentName === mappedName) {
                    console.log(`  Nested Step ${stepId}:`, {
                        agentName: stepData.agentName,
                        hasInternalConversation: !!stepData.internalConversation,
                        conversationLength: stepData.internalConversation?.length || 0
                    });
                }
            }
        } else {
            // Show all data
            console.log('Global agent conversations:', this.agentInternalConversations);
            console.log('Main agent steps count:', this.agentSteps.size);
            console.log('Nested agent steps count:', this.nestedAgentSteps.size);
            
            console.log('All agents with internal conversations:');
            for (const [stepId, stepData] of this.agentSteps) {
                if (stepData.internalConversation) {
                    console.log(`  Main Step ${stepId}: ${stepData.agentName} (${stepData.internalConversation.length} messages)`);
                }
            }
            for (const [stepId, stepData] of this.nestedAgentSteps) {
                if (stepData.internalConversation) {
                    console.log(`  Nested Step ${stepId}: ${stepData.agentName} (${stepData.internalConversation.length} messages)`);
                }
            }
        }
        
        console.log('=== END DEBUG ===');
    }
}

// Export for use in other modules
window.ThinkingPanel = ThinkingPanel;
