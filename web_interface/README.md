# Thought Agent Web Interface

A modern, real-time web interface for the Thought Agent system. This interface provides a comprehensive view of the multi-agent conversation process with hierarchical thinking visualization.

## Features

### 🎯 **Three-Panel Layout**
- **Left Panel**: Chat interface for user interaction
- **Center Panel**: Main thinking process showing all agent activities  
- **Right Panel**: Detailed view of custom agent internal processes

### 🔄 **Real-Time Updates**
- Live streaming of agent conversations via WebSocket
- Real-time status indicators for each agent
- Progressive disclosure of thinking processes

### 🧠 **Agent Visualization**
- Color-coded agents for easy identification
- Hierarchical display of agent interactions
- Collapsible sections for detailed exploration
- Custom agent thinking process deep-dive

### 🎨 **Modern UI/UX**
- Bootstrap-based responsive design
- Smooth animations and transitions
- Keyboard shortcuts for power users
- Mobile-friendly responsive layout

## Architecture

### Backend (Flask + SocketIO)
```
services/
├── agent_service.py       # ThoughtAgent integration
├── session_manager.py     # User session management
└── __init__.py

app.py                     # Main Flask application
```

### Frontend (Vanilla JavaScript + Bootstrap)
```
static/
├── js/
│   ├── main.js           # Application coordinator
│   ├── socket-manager.js  # WebSocket communication
│   ├── chat-interface.js  # Chat UI management
│   └── thinking-panel.js  # Agent visualization
├── css/
│   └── style.css         # Custom styles
└── templates/
    └── index.html        # Main template
```

## Quick Start

### 1. Install Dependencies
```bash
cd web_interface
pip install -r requirements.txt
```

### 2. Start the Application
**Windows:**
```bash
start_web_interface.bat
```

**Manual start:**
```bash
cd web_interface
python app.py
```

### 3. Access the Interface
Open your browser to: http://localhost:5000

## How It Works

### 1. **User Interaction**
- User types a question in the left chat panel
- Message is sent via WebSocket to the Flask backend
- Backend creates an enhanced ThoughtAgent instance

### 2. **Real-Time Processing**
- EnhancedThoughtAgent integrates with existing ThoughtAgent
- All agent messages are intercepted and streamed live
- Custom agents emit detailed thinking processes

### 3. **Hierarchical Display**
- **Main Flow**: Center panel shows primary agent conversation
- **Agent Details**: Right panel shows internal custom agent processes
- **Interactive**: Click on agents to dive into their thinking

### 4. **Custom Agent Deep-Dive**
When custom agents are triggered:
- **Expert Knowledge Agent**: Shows RAG search processes
- **Web Search Agent**: Shows crawling and search activities  
- **Code Executor**: Shows code execution steps

## Agent Integration

The system seamlessly integrates with existing agents:

```python
# Enhanced agents emit real-time updates
class EnhancedThoughtAgent(ThoughtAgent):
    def _stream_messages(self, messages):
        # Streams messages to frontend in real-time
        
    def _detect_custom_agent_activity(self, agent_name, content):
        # Detects and emits custom agent thinking
```

### Custom Agent Thinking Events
```javascript
// Frontend receives detailed thinking processes
socket.on('custom_agent_thinking', (data) => {
    // data.agent - which custom agent
    // data.phase - current thinking phase  
    // data.content - detailed process info
});
```

## UI Components

### Chat Interface
- **Input**: Multi-line textarea with Ctrl+Enter to send
- **Messages**: Formatted user and agent messages
- **Status**: Connection and conversation status indicators

### Thinking Process Panel
- **Agent Steps**: Expandable sections for each agent
- **Status Indicators**: Running, completed, error states
- **Message Flow**: Real-time message streaming
- **Controls**: Expand/collapse all sections

### Agent Details Panel
- **Agent Selection**: Buttons to select specific agents
- **Custom Thinking**: Deep-dive into internal processes
- **Hierarchical View**: Multi-level thinking exploration
- **Summary**: Conversation completion summary

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + K` | Focus on input field |
| `Ctrl + Enter` | Send message |
| `Escape` | Clear focus |
| `Ctrl + /` | Show keyboard shortcuts |

## Configuration

### Agent Metadata
Customize agent colors and display names in `agent_service.py`:

```python
self.agent_metadata = {
    'expert_knowledge_agent': {
        'color': '#6f42c1', 
        'displayName': 'Expert Knowledge'
    },
    # ... other agents
}
```

### WebSocket Events
All real-time communication happens through these events:

**Server → Client:**
- `connected` - Session established
- `agent_started` - New agent activated
- `agent_message` - Agent sent message
- `custom_agent_thinking` - Internal agent process
- `conversation_completed` - Final response ready

**Client → Server:**
- `start_conversation` - Begin new query
- `join_session` - Join existing session

## Development

### Adding New Custom Agent Integration
1. Enhance the custom agent to emit thinking events
2. Add event handling in `agent_service.py`
3. Update frontend to display new thinking types

### Extending UI Components
- Modify JavaScript classes in `static/js/`
- Update CSS styles in `static/css/style.css`
- Add new HTML templates in `templates/`

## Troubleshooting

### Common Issues

**WebSocket Connection Failed**
- Check if Flask app is running on correct port
- Verify firewall settings
- Check browser console for errors

**Agents Not Responding**
- Verify existing ThoughtAgent imports are working
- Check Python console for backend errors
- Ensure all required dependencies are installed

**UI Not Updating**
- Check browser console for JavaScript errors
- Verify WebSocket connection status (top-right indicator)
- Try refreshing the page

### Debug Mode
Start with debug enabled:
```bash
python app.py  # Debug is enabled by default
```

### Log Files
- Backend logs: Console output
- Agent conversations: `../agent_outputs/groupchat_log_*.json`
- Browser logs: Developer Console (F12)

## Integration with Existing System

This web interface is completely **non-intrusive**:

✅ **Zero modifications** to existing `entry_thought.py`  
✅ **Direct imports** of existing ThoughtAgent classes  
✅ **Parallel operation** with CLI interface  
✅ **Same environment** and dependencies  
✅ **Modular architecture** for easy maintenance  

The system simply wraps the existing ThoughtAgent with WebSocket capabilities while preserving all original functionality.

## Future Enhancements

Potential improvements:
- [ ] Save/export conversation history
- [ ] Multiple concurrent conversations
- [ ] Agent performance metrics
- [ ] Custom agent configuration UI
- [ ] Dark/light theme toggle
- [ ] Mobile app version
