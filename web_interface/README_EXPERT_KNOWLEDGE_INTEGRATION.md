# Expert Knowledge Agent Internal Messages Integration Guide

This document provides a comprehensive guide for integrating internal message streaming from the Expert Knowledge Agent to the web interface UI. This same approach can be replicated for any other agent that needs internal conversation visibility.

## Overview

The Expert Knowledge Agent was enhanced to stream its internal RAG (Retrieval-Augmented Generation) conversation in real-time to the web interface, allowing users to see the detailed thinking process including database searches, document retrieval, and response generation.

## Key Components Modified

### 1. Enhanced Expert Knowledge Agent Implementation

**File Created**: `web_interface/agents_enhanced/enhanced_expert_knowledge.py`

This is a new agent class that inherits from `autogen.ConversableAgent` and adds WebSocket streaming capabilities.

#### Key Features:
- **Real-time streaming**: Emits internal conversation steps via WebSocket
- **Conversation tracking**: Maintains internal conversation history
- **RAG monitoring**: Monitors and streams RAG proxy agent interactions
- **Error handling**: Streams error states and recovery processes

#### Critical Methods:

```python
def _emit_internal_message(self, message_type: str, content: str, metadata: dict = None):
    """Emit internal conversation message to UI via WebSocket"""
    # Emits 'agent_internal_conversation' events
    # Stores conversation for later reference
```

```python
def _monitor_rag_conversation(self, ragproxyagent, assistant, user_question):
    """Monitor and stream the RAG conversation in real-time"""
    # Hooks into RAG agent's initiate_chat method
    # Streams search, retrieval, and processing phases
```

```python
def _capture_rag_messages(self, ragproxyagent, assistant):
    """Capture and stream messages from the RAG conversation"""
    # Extracts individual messages from RAG conversation
    # Streams query/response pairs
```

### 2. Agent Service Integration

**File Modified**: `web_interface/services/agent_service.py`

#### Key Modifications:

1. **Import Enhanced Agent**:
```python
from web_interface.agents_enhanced.enhanced_expert_knowledge import EnhancedExpertKnowledgeAgent
```

2. **Enhanced ThoughtAgent Constructor**:
```python
def __init__(self, session_id: str, socketio_instance, agent_metadata: dict):
    super().__init__()
    # ... existing code ...
    
    # Track enhanced agents
    self.enhanced_expert_knowledge_active = False
    self.enhanced_expert_agent_instance = None
    
    # Replace the expert knowledge agent with enhanced version
    self._replace_expert_knowledge_agent()
```

3. **Agent Replacement Method**:
```python
def _replace_expert_knowledge_agent(self):
    """Replace the original expert knowledge agent with enhanced version"""
    # Creates enhanced agent with WebSocket capabilities
    # Replaces in the groupchat agents list
    # Recreates groupchat with enhanced agent
```

4. **Enhanced Thinking Process Detection**:
```python
def _detect_and_emit_thinking_process(self, agent_name: str, content: str):
    # Handle enhanced Expert Knowledge Agent
    if agent_name == 'expert_knowledge_agent' and self.enhanced_expert_knowledge_active:
        self._emit_enhanced_expert_summary()
        return
```

5. **Summary Emission Method**:
```python
def _emit_enhanced_expert_summary(self):
    """Emit all internal conversation messages from enhanced expert agent for thinking panel"""
    # Processes internal conversation messages
    # Emits 'custom_agent_thinking' events for UI display
    # Emits 'store_internal_conversation' for detailed view
```

### 3. Frontend Integration

**File Modified**: `web_interface/static/js/thinking-panel.js`

#### Socket Event Handlers Added:

```javascript
// Internal conversation events
this.socketManager.on('agent_internal_conversation', (data) => {
    this.addInternalConversationMessage(data);
});

// Store internal conversation data for button access
this.socketManager.on('store_internal_conversation', (data) => {
    this.storeInternalConversationData(data);
});
```

#### UI Enhancement Methods:

```javascript
addInternalConversationMessage(data) {
    // Displays internal conversation steps in thinking panel
    // Shows phases like "rag_search", "rag_processing", etc.
}

storeInternalConversationData(data) {
    // Stores detailed conversation for expandable view
    // Associates with step ID for retrieval
}
```

### 4. Enhanced Agent Directory Structure

**Directory Created**: `web_interface/agents_enhanced/`

```
web_interface/agents_enhanced/
├── __init__.py
└── enhanced_expert_knowledge.py
```

**File**: `web_interface/agents_enhanced/__init__.py`
```python
from .enhanced_expert_knowledge import EnhancedExpertKnowledgeAgent
```

## Step-by-Step Integration Process for Any Agent

### Step 1: Create Enhanced Agent Class

1. Create new file: `web_interface/agents_enhanced/enhanced_[agent_name].py`

2. Basic structure:
```python
import sys
import os
from datetime import datetime
from autogen import ConversableAgent

# Add parent directory for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class Enhanced[AgentName]Agent(ConversableAgent):
    def __init__(self, session_id: str, socketio_instance, **kwargs):
        super().__init__(**kwargs)
        self.session_id = session_id
        self.socketio = socketio_instance
        self.internal_conversation = []
        self.conversation_step = 0
        
        # Register the reply function
        self.register_reply([Agent, None], reply_func=Enhanced[AgentName]Agent._reply_user, position=0)

    def _emit_internal_message(self, message_type: str, content: str, metadata: dict = None):
        """Emit internal conversation message to UI via WebSocket"""
        try:
            self.socketio.emit('agent_internal_conversation', {
                'agent_name': '[agent_name]_agent',
                'type': message_type,
                'content': content,
                'metadata': metadata or {},
                'step': self.conversation_step,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            
            # Store for later reference
            self.internal_conversation.append({
                'type': message_type,
                'content': content,
                'metadata': metadata or {},
                'step': self.conversation_step,
                'timestamp': datetime.now().isoformat()
            })
            
            self.conversation_step += 1
            
        except Exception as e:
            print(f"[Enhanced{AgentName}] Error emitting internal message: {e}")

    def _reply_user(self, messages=None, sender=None, config=None):
        """Enhanced reply method with real-time streaming"""
        # Reset conversation tracking
        self.internal_conversation = []
        self.conversation_step = 0
        
        # Get user question
        user_question = messages[-1]["content"]
        
        try:
            # Emit starting message
            self._emit_internal_message(
                "processing_start",
                f"Starting {self.__class__.__name__} processing...",
                {"query": user_question}
            )
            
            # Your agent's core logic here
            # Emit internal messages at key processing steps
            self._emit_internal_message(
                "step_1",
                "Description of what agent is doing in step 1...",
                {"step_details": "..."}
            )
            
            # ... more processing steps ...
            
            # Final response
            response = "Your agent's final response"
            self._emit_internal_message(
                "final_response",
                "Processing completed successfully",
                {"response_length": len(response)}
            )
            
            return True, response
            
        except Exception as e:
            self._emit_internal_message(
                "agent_error",
                f"Error in {self.__class__.__name__} processing: {str(e)}",
                {"error": str(e)}
            )
            return True, f"Error in agent processing: {str(e)}"
```

### Step 2: Update Agent Service

1. **Import the enhanced agent**:
```python
from web_interface.agents_enhanced.enhanced_[agent_name] import Enhanced[AgentName]Agent
```

2. **Add tracking variables to EnhancedThoughtAgent.__init__**:
```python
def __init__(self, session_id: str, socketio_instance, agent_metadata: dict):
    # ... existing code ...
    
    # Track enhanced agents
    self.enhanced_[agent_name]_active = False
    self.enhanced_[agent_name]_instance = None
    
    # Replace the agent with enhanced version
    self._replace_[agent_name]_agent()
```

3. **Create replacement method**:
```python
def _replace_[agent_name]_agent(self):
    """Replace the original [agent_name] with enhanced version"""
    if Enhanced[AgentName]Agent is None:
        print(f"[EnhancedThoughtAgent] Enhanced {agent_name} not available, using original")
        return
        
    try:
        from agents.prompts.thought_agent.[agent_name] import [agent_name]
        
        # Create enhanced agent
        enhanced_agent = Enhanced[AgentName]Agent(
            session_id=self.session_id,
            socketio_instance=self.socketio,
            name=[agent_name]["name"],
            system_message=[agent_name]["system_message"],
            description=[agent_name]["description"],
            llm_config=model_config,
            human_input_mode=[agent_name]["human_input_mode"],
            code_execution_config=[agent_name]["code_execution_config"]
        )
        
        # Replace the agent in the instance
        self.[agent_name]_agent.agent = enhanced_agent
        
        # Recreate groupchat with enhanced agent
        self.groupchat = GroupChat(agents_list=[
            # ... all agents including the enhanced one ...
        ], 
        initiator_agent=self.user_proxy_agent.agent,
        last_message_agent=self.send_user_msg_agent.agent,
        custom_speaker_selection_func=self.custom_speaker_selection_func
        )
        
        print(f"[EnhancedThoughtAgent] Successfully replaced {agent_name} with enhanced version")
        self.enhanced_[agent_name]_active = True
        self.enhanced_[agent_name]_instance = enhanced_agent
        
    except Exception as e:
        print(f"[EnhancedThoughtAgent] Warning: Could not replace {agent_name}: {e}")
```

4. **Update thinking process detection**:
```python
def _detect_and_emit_thinking_process(self, agent_name: str, content: str):
    # Handle enhanced [Agent Name]
    if agent_name == '[agent_name]_agent' and self.enhanced_[agent_name]_active:
        self._emit_enhanced_[agent_name]_summary()
        return
        
    # ... existing detection logic ...
```

5. **Create summary emission method**:
```python
def _emit_enhanced_[agent_name]_summary(self):
    """Emit all internal conversation messages from enhanced [agent_name] for thinking panel"""
    try:
        if not self.enhanced_[agent_name]_instance or not hasattr(self.enhanced_[agent_name]_instance, 'internal_conversation'):
            return
        
        internal_messages = self.enhanced_[agent_name]_instance.internal_conversation
        
        if not internal_messages:
            return
        
        # Generate unique step ID
        import uuid
        unique_step_id = f"[agent_name]_{str(uuid.uuid4())[:8]}"
        
        # Emit each internal message as a thinking phase
        for i, message in enumerate(internal_messages):
            message_type = message.get('type', 'processing')
            content = message.get('content', 'Processing...')
            
            phase_content = f"Step {i+1}: {content}"
            
            self.socketio.emit('custom_agent_thinking', {
                'agent': '[agent_name]',
                'phase': self._map_internal_type_to_phase(message_type),
                'content': phase_content,
                'timestamp': message.get('timestamp', datetime.now().isoformat()),
                'step_id': unique_step_id
            }, room=self.session_id)
        
        # Store the full internal conversation data
        self.socketio.emit('store_internal_conversation', {
            'step_id': unique_step_id,
            'agent_name': '[agent_name]',
            'internal_conversation': internal_messages,
            'timestamp': datetime.now().isoformat()
        }, room=self.session_id)
        
    except Exception as e:
        print(f"[EnhancedThoughtAgent] Error emitting enhanced {agent_name} summary: {e}")
```

### Step 3: Frontend Integration

1. **Add socket event handlers in thinking-panel.js**:
```javascript
// Internal conversation events
this.socketManager.on('agent_internal_conversation', (data) => {
    this.addInternalConversationMessage(data);
});

// Store internal conversation data
this.socketManager.on('store_internal_conversation', (data) => {
    this.storeInternalConversationData(data);
});
```

2. **Update agent metadata** (in agent_service.py):
```python
self.agent_metadata = {
    # ... existing agents ...
    '[agent_name]_agent': {'color': '#your_color', 'display_name': 'Your Agent Display Name'},
}
```

## Socket Events Reference

### Emitted by Enhanced Agent:
- `agent_internal_conversation`: Real-time internal messages during processing
- `custom_agent_thinking`: Summary thinking phases for UI display
- `store_internal_conversation`: Complete conversation data for detailed view

### Event Data Structures:

#### agent_internal_conversation:
```javascript
{
    agent_name: string,
    type: string,           // Message type (e.g., 'rag_search', 'processing')
    content: string,        // Human-readable description
    metadata: object,       // Additional data
    step: number,          // Step number in conversation
    timestamp: string      // ISO timestamp
}
```

#### custom_agent_thinking:
```javascript
{
    agent: string,         // Agent identifier
    phase: string,         // Processing phase
    content: string,       // Display content
    timestamp: string,     // ISO timestamp
    step_id: string       // Unique identifier for this agent call
}
```

#### store_internal_conversation:
```javascript
{
    step_id: string,              // Unique identifier
    agent_name: string,           // Agent name
    internal_conversation: array, // Full conversation data
    timestamp: string             // ISO timestamp
}
```

## Message Types and Phases

### Common Message Types:
- `initialization`: Agent setup
- `processing_start`: Begin processing
- `search_start`: Begin search operation
- `retrieval_start`: Begin data retrieval
- `processing`: General processing step
- `analysis`: Data analysis phase
- `response_generation`: Creating response
- `completion`: Processing complete
- `final_response`: Final result ready
- `error`: Error occurred
- `agent_error`: Critical agent error

### UI Phase Mapping:
```python
def _map_internal_type_to_phase(self, message_type: str) -> str:
    phase_map = {
        'initialization': 'setup',
        'processing_start': 'initialization',
        'search_start': 'search',
        'retrieval_start': 'retrieval',
        'processing': 'processing',
        'analysis': 'analysis',
        'response_generation': 'generation',
        'completion': 'completion',
        'final_response': 'final',
        'error': 'error_handling',
        'agent_error': 'error_handling'
    }
    return phase_map.get(message_type, 'processing')
```

## Best Practices

1. **Error Handling**: Always wrap internal message emission in try-catch blocks
2. **Performance**: Limit internal message frequency to avoid UI spam
3. **Content Length**: Keep message content concise for UI display
4. **Metadata**: Use metadata for detailed information that doesn't need UI display
5. **Unique IDs**: Generate unique step IDs for each agent invocation
6. **Backward Compatibility**: Enhanced agents should fall back gracefully if WebSocket is unavailable

## Testing

1. **Unit Tests**: Test enhanced agent in isolation
2. **Integration Tests**: Test with full ThoughtAgent conversation
3. **UI Tests**: Verify real-time message display
4. **Error Tests**: Test error handling and recovery
5. **Performance Tests**: Ensure no significant latency increase

## Troubleshooting

### Common Issues:

1. **Messages not appearing**: Check WebSocket connection and session ID
2. **Duplicate messages**: Ensure conversation tracking is reset properly
3. **Performance issues**: Reduce message frequency or content size
4. **Agent replacement fails**: Check import paths and agent configuration
5. **UI not updating**: Verify frontend event handlers are registered

### Debug Commands:
```python
# Check if enhanced agent is active
print(f"Enhanced active: {self.enhanced_[agent_name]_active}")

# Check internal conversation
print(f"Internal messages: {len(self.enhanced_[agent_name]_instance.internal_conversation)}")

# Check WebSocket emission
print(f"Session ID: {self.session_id}")
```

## Conclusion

This integration pattern allows any agent to provide detailed internal visibility while maintaining the original agent architecture. The enhanced agents are drop-in replacements that add WebSocket streaming capabilities without breaking existing functionality.

The key insight is to **wrap rather than modify** the original agent behavior, ensuring backward compatibility while adding powerful real-time UI capabilities.
