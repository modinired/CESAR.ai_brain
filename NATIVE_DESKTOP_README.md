# Atlas Capital Automations - CESAR.ai Native Desktop Console

**a Terry Dellmonaco Co.**

---

## Professional Native Desktop Application

A true desktop application built with PyQt6 - no web browser required. Features professional cyberpunk aesthetics, real-time monitoring, and integrated AI agent chat.

## ✨ Key Features

### 🖥️ **True Native Desktop Experience**
- **No Web Browser**: Pure Qt6 application with native window management
- **macOS Integration**: Full native macOS menubar, window controls, and keyboard shortcuts
- **Professional UI**: Dark cyberpunk theme with smooth animations
- **Hardware Accelerated**: Leverages GPU for smooth rendering

### 🤖 **Mob Character Agent Names**
All agents (except CESAR) have been renamed to iconic mob characters:

| Original Agent | Mob Character | Movie/Show | Role |
|----------------|---------------|------------|------|
| FinPsy | **Paulie Walnuts** | The Sopranos | Financial Intelligence |
| Lex | **Silvio Dante** | The Sopranos | Legal & Compliance |
| Pydini | **Christopher Moltisanti** | The Sopranos | Workflow Automation |
| Inno | **Henry Hill** | Goodfellas | Innovation Tracking |
| Creative | **Calogero** | A Bronx Tale | Content Generation |
| Edu | **Nicky Santoro** | Casino | Educational Content |
| Research | **Jimmy Conway** | Goodfellas | Research & Analysis |
| DataViz | **Tommy DeVito** | Goodfellas | Data Visualization |
| Collab | **Sonny LoSpecchio** | A Bronx Tale | Team Collaboration |
| DevOps | **Ace Rothstein** | Casino | Infrastructure Automation |
| Security | **Furio Giunta** | The Sopranos | Security Monitoring |

### 💬 **Integrated AI Chat**
- Direct chat interface with any agent
- Real-time responses with async processing
- Persistent chat history during session
- Third-person professional responses with NY flavor

### 📊 **Real-Time Monitoring**
- System health dashboard
- Live agent status updates
- Database and cache monitoring
- Auto-refresh every 5 seconds

### 📈 **Financial Intelligence**
- Market overview (S&P 500, NASDAQ, VIX)
- Stock analysis via Paulie Walnuts (FinPsy)
- Real-time financial metrics

## 🚀 Installation

### Prerequisites

```bash
# PyQt6 is already installed in your environment
pip3 show PyQt6

# If needed:
pip3 install PyQt6 PyQt6-WebEngine
```

### Quick Start

1. **Ensure Docker Services are Running**:
```bash
cd "/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem"
docker-compose up -d
```

2. **Launch the Native Desktop App**:
```bash
./launch_desktop.sh
```

The script will:
- Check if API is running
- Start Docker services if needed
- Kill any web-based dashboard (Streamlit)
- Launch the native Qt6 desktop application

## 📋 Manual Launch

```bash
cd "/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem"
python3 atlas_desktop.py
```

## 🎨 UI Components

### 1. **System Dashboard Tab**
Monitor overall system health with live metrics:
- System status (Healthy/Error)
- Active agent count
- API latency
- Uptime statistics
- Database connection pool status
- Redis cache health

### 2. **Agent Chat Tab**
Interactive chat interface:
- Select any agent from dropdown (CESAR, Paulie Walnuts, Silvio Dante, etc.)
- Type messages in natural language
- Receive responses in third-person professional tone with NY flavor
- Background async processing (no UI freezing)
- Persistent chat history during session

**Example Conversation:**
```
You: How's the market looking today?

Paulie Walnuts: The assistant analyzed the current market conditions and found the S&P 500 trending bullish with moderate volatility. The recommendation is to stay cautious with new positions, Bobby-boy.
```

### 3. **Agent Systems Tab**
View all active agents in table format:
- Agent name (with mob character names)
- System category
- Current status (Active/Idle)
- Tasks completed
- Success rate percentage

### 4. **Financial Intel Tab**
Market data and stock analysis:
- Real-time market overview metrics
- Stock symbol search
- Analysis by Paulie Walnuts (FinPsy agent)
- Third-person professional recommendations

## 🎯 Universal Agent Template

All agents now follow the Universal Agent Template specification:

### Core Principles
1. **Third-Person Voice**: Agents always respond in third person (e.g., "The assistant recommends...")
2. **NY Professional Flavor**: Clear, precise, helpful tone with optional subtle NY slang
3. **Self-Reflection**: Agents perform critical self-reflection after each interaction
4. **Verification**: Double-check complex reasoning, math, or code before responding
5. **Memory Integration**: Leverage episodic, semantic, and procedural memory systems

### Template Location
```
/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem/config/universal_agent_template.json
```

### Output Format
Each agent response includes:
- **Answer**: Main structured response
- **Verification**: Summary of double-checks performed
- **Memory Candidates**: Proposed memory updates
- **Questions/Confirmations**: Clarifications needed
- **Self-Reflection**: Critique of reasoning and improvements

## 🔧 Architecture

### Desktop Application Stack
```
┌──────────────────────────────────────────┐
│  PyQt6 Native Desktop Application        │
│  - QMainWindow with custom dark theme    │
│  - 4 tabbed interfaces                   │
│  - Async chat worker threads             │
│  - Auto-refresh timers (5s interval)     │
└──────────────┬───────────────────────────┘
               │
               ↓ HTTP/REST API
┌──────────────────────────────────────────┐
│  CESAR.ai API (Port 8000)                │
│  - 23 AI Agents (with mob names)         │
│  - Universal Agent Template              │
│  - 11 MCP Systems                        │
│  - Episodic/Semantic/Procedural Memory   │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│  Infrastructure                          │
│  - PostgreSQL (Port 5432)                │
│  - Redis (Port 6379)                     │
│  - Prefect (Port 4200)                   │
│  - Grafana (Port 3001)                   │
│  - Prometheus (Port 9091)                │
└──────────────────────────────────────────┘
```

### Technology Stack
- **UI Framework**: PyQt6 (native Qt6 for Python)
- **HTTP Client**: requests library with session management
- **Threading**: QThread for async chat requests
- **Styling**: Qt StyleSheets (CSS-like syntax)
- **Timers**: QTimer for auto-refresh and time updates

## 🎨 Design Philosophy

### Cyberpunk Dark Theme
- **Background**: Gradient from `#0a0e27` to `#1a1f3a`
- **Primary Accent**: `#00d4ff` (Cyan) - Headers, buttons, borders
- **Success Color**: `#00ff88` (Green) - Metrics, positive states
- **Warning Color**: `#ffc107` (Amber) - Warnings, pending states
- **Error Color**: `#ff4757` (Red) - Errors, critical alerts

### Professional SaaS Aesthetic
- Clean, uncluttered interface
- Consistent spacing and padding
- Subtle animations (button hover effects)
- Glass-morphism cards with transparency
- High contrast for readability

### Typography
- **Primary Font**: San Francisco (macOS), Segoe UI (Windows), Arial (fallback)
- **Headings**: 24px, bold, cyan color
- **Subheadings**: 16px, semi-bold
- **Body**: 13px, regular
- **Metrics**: 32px, bold, green color

## ⚡ Performance

- **Startup Time**: ~1-2 seconds
- **Memory Usage**: ~80-150MB
- **CPU Usage**: Minimal (1-3% idle, 5-10% during chat)
- **GPU**: Hardware-accelerated rendering
- **API Response**: 50-200ms average
- **Refresh Rate**: 5 second intervals (configurable)

## 🔐 Security

- Dashboard runs locally (no network exposure)
- API authentication via JWT tokens
- Secure session management
- No sensitive data stored in UI layer
- All communication over HTTP (localhost only)

## 📱 Keyboard Shortcuts

- **Cmd+Q** (macOS) / **Ctrl+Q** (Windows): Quit application
- **Enter** in chat input: Send message
- **Cmd+W**: Close window
- **Cmd+M**: Minimize window
- **Cmd+Tab**: Switch between tabs

## 🐛 Troubleshooting

### Desktop app won't start
```bash
# Check PyQt6 installation
pip3 show PyQt6

# Reinstall if needed
pip3 install --upgrade PyQt6 PyQt6-WebEngine
```

### API connection errors
```bash
# Verify API is running
curl http://localhost:8000/health

# Check Docker containers
docker ps

# Restart if needed
docker-compose restart api
```

### Font warnings
If you see "Populating font family aliases" warning, it's harmless. The app automatically falls back to system fonts.

### Display issues
```bash
# Force Qt platform (if needed)
export QT_QPA_PLATFORM=cocoa  # macOS
python3 atlas_desktop.py
```

## 🆚 Native Desktop vs Web Dashboard

| Feature | Native Desktop | Streamlit Web |
|---------|---------------|---------------|
| **Installation** | PyQt6 | Streamlit |
| **Browser Required** | ❌ No | ✅ Yes |
| **Performance** | ⚡ Native speed | 🌐 Web latency |
| **Offline UI** | ✅ Yes | ❌ No (needs server) |
| **Memory Usage** | 80-150MB | 150-300MB |
| **Aesthetics** | Professional Qt | Web-based |
| **Keyboard Shortcuts** | ✅ Full support | ⚠️ Limited |
| **Window Management** | ✅ Native | 🌐 Browser tabs |
| **File Access** | ✅ Direct | 🌐 Limited |

## 🔮 Future Enhancements

- [ ] System tray icon with notifications
- [ ] Draggable/resizable dashboard widgets
- [ ] Custom dashboard layouts (save/load)
- [ ] Export chat history to file
- [ ] Offline mode with local LLMs only
- [ ] Multi-window support
- [ ] Light theme option
- [ ] Custom keyboard shortcut configuration
- [ ] Voice input/output for agents
- [ ] Screen recording of agent sessions

## 📚 Development

### Project Structure
```
cesar_ecosystem/
├── atlas_desktop.py              # Main desktop application
├── launch_desktop.sh             # Desktop launcher script
├── config/
│   └── universal_agent_template.json  # Universal agent template
├── mcp_agents/                   # Agent implementations
├── api/                          # FastAPI backend
└── docker-compose.yml            # Infrastructure
```

### Extending the Desktop App

To add new tabs:

```python
# In atlas_desktop.py, add to init_ui():
self.tabs.addTab(self.create_my_tab(), "🔧 My Tab")

# Create tab method:
def create_my_tab(self) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    # Add your widgets here
    return widget
```

### Customizing Agent Names

Edit `MOB_CHARACTER_NAMES` dictionary in `atlas_desktop.py`:

```python
MOB_CHARACTER_NAMES = {
    "finpsy": "Your Character Name",  # Your choice
    # ... more mappings
}
```

## 📞 Support

For issues or feature requests:
- GitHub Issues: https://github.com/modinired/CESAR.ai-Ecosystem/issues
- Documentation: See main README.md

---

**Atlas Capital Automations** - *Making AI agents work together, for everyone.*

**a Terry Dellmonaco Co.** | Built with ❤️ and Python + Qt6
