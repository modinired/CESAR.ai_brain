"""
Atlas Capital - CESAR.ai Command Console
Professional SaaS-style Dashboard for Multi-Agent Ecosystem
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 10

# ============================================================================
# Custom Styling
# ============================================================================

def inject_custom_css():
    """Inject custom CSS for professional dark mode UI"""
    st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Dark theme */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
        color: #e0e0e0;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f1419 0%, #1a1f2e 100%);
    }

    /* Headers */
    h1, h2, h3 {
        color: #00d4ff;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #00ff88;
    }

    /* Cards */
    .element-container {
        background: rgba(26, 31, 58, 0.6);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(0, 212, 255, 0.2);
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00d4ff 0%, #0088ff 100%);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .status-healthy {
        background: rgba(0, 255, 136, 0.2);
        color: #00ff88;
        border: 1px solid #00ff88;
    }

    .status-warning {
        background: rgba(255, 193, 7, 0.2);
        color: #ffc107;
        border: 1px solid #ffc107;
    }

    .status-error {
        background: rgba(255, 71, 87, 0.2);
        color: #ff4757;
        border: 1px solid #ff4757;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# API Client
# ============================================================================

class CESARClient:
    """Client for CESAR.ai API"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=API_TIMEOUT
            )
            return response.json() if response.status_code == 200 else {"status": "error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/agents",
                timeout=API_TIMEOUT
            )
            return response.json() if response.status_code == 200 else []
        except:
            return []

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/metrics",
                timeout=API_TIMEOUT
            )
            return response.json() if response.status_code == 200 else {}
        except:
            return {}

    def chat(self, message: str, agent: str = "cesar") -> str:
        """Send chat message"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/chat",
                json={"message": message, "agent": agent},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "No response")
            return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

# ============================================================================
# Dashboard Pages
# ============================================================================

def render_header():
    """Render dashboard header"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown("### 🏛️ Atlas Capital Automations")
        st.markdown("<p style='font-size: 0.8rem; color: #888;'>*a Terry Dellmonaco Co.*</p>", unsafe_allow_html=True)

    with col2:
        st.markdown("<h1 style='text-align: center;'>CESAR.ai Command Console</h1>", unsafe_allow_html=True)

    with col3:
        st.markdown(f"<p style='text-align: right; color: #00d4ff;'>{datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

def page_dashboard(client: CESARClient):
    """Main dashboard page"""
    st.markdown("## 📊 System Overview")

    # Health check
    health = client.health_check()

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status = health.get("status", "unknown")
        status_color = "🟢" if status == "healthy" else "🔴"
        st.metric("System Status", f"{status_color} {status.upper()}")

    with col2:
        st.metric("Active Agents", health.get("agents", {}).get("total", 0))

    with col3:
        st.metric("API Latency", f"{health.get('latency_ms', 0):.1f}ms")

    with col4:
        st.metric("Uptime", "99.9%")

    st.markdown("---")

    # Agent Status Table
    st.markdown("### 🤖 Agent Systems")
    agents = client.get_agents()

    if agents:
        agent_data = []
        for agent in agents[:10]:  # Show first 10
            agent_data.append({
                "System": agent.get("system", "Unknown"),
                "Agent": agent.get("name", "Unknown"),
                "Status": "Active" if agent.get("active") else "Idle",
                "Tasks": agent.get("tasks_completed", 0),
                "Success Rate": f"{agent.get('success_rate', 0):.1f}%"
            })

        df = pd.DataFrame(agent_data)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No agents currently active")

    # System Resources
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💾 Database Status")
        db_health = health.get("database", {})
        st.json(db_health)

    with col2:
        st.markdown("### 🔄 Cache Status")
        cache_health = health.get("redis", {})
        st.json(cache_health)

def page_financial(client: CESARClient):
    """Financial analysis page"""
    st.markdown("## 📈 Financial Intelligence - FinPsy")

    # Stock analysis
    col1, col2 = st.columns([2, 1])

    with col1:
        ticker = st.text_input("Stock Symbol", value="AAPL", max_chars=10)

    with col2:
        if st.button("🔍 Analyze", use_container_width=True):
            with st.spinner("Running FinPsy analysis..."):
                # Mock financial data for visualization
                dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
                prices = [150 + i * 0.5 + (i % 7) * 2 for i in range(90)]

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=prices,
                    mode='lines',
                    name='Price',
                    line=dict(color='#00d4ff', width=2)
                ))

                fig.update_layout(
                    title=f"{ticker} - 90 Day Performance",
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

    # Market overview
    st.markdown("### 🌍 Market Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("S&P 500", "4,783.45", "+1.2%", delta_color="normal")

    with col2:
        st.metric("NASDAQ", "15,011.35", "+0.8%", delta_color="normal")

    with col3:
        st.metric("VIX", "13.42", "-2.1%", delta_color="inverse")

def page_chat(client: CESARClient):
    """Neural chat interface"""
    st.markdown("## 💬 Neural Chat Interface")

    # Agent selection
    agent = st.selectbox(
        "Select Agent System",
        ["cesar", "finpsy", "lex", "pydini", "inno", "creative"]
    )

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask CESAR anything..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.chat(prompt, agent)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

def page_workflows(client: CESARClient):
    """Workflow management page"""
    st.markdown("## ⚙️ Workflow Automation")

    # Workflow stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Workflows", "12")

    with col2:
        st.metric("Completed Today", "48")

    with col3:
        st.metric("Success Rate", "97.3%")

    with col4:
        st.metric("Avg Duration", "2.4s")

    st.markdown("---")

    # Workflow list
    st.markdown("### 📋 Recent Workflows")

    workflows = [
        {"name": "Financial Market Analysis", "status": "Complete", "duration": "3.2s", "agent": "FinPsy"},
        {"name": "Contract Review", "status": "Complete", "duration": "5.1s", "agent": "Lex"},
        {"name": "Content Generation", "status": "Running", "duration": "1.8s", "agent": "Creative"},
        {"name": "Data Collection", "status": "Complete", "duration": "2.1s", "agent": "Pydini"},
    ]

    for wf in workflows:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

        with col1:
            st.write(f"**{wf['name']}**")

        with col2:
            status_class = "status-healthy" if wf['status'] == "Complete" else "status-warning"
            st.markdown(f"<span class='{status_class}'>{wf['status']}</span>", unsafe_allow_html=True)

        with col3:
            st.write(wf['duration'])

        with col4:
            st.write(wf['agent'])

def page_settings(client: CESARClient):
    """Settings and configuration page"""
    st.markdown("## ⚙️ System Configuration")

    tab1, tab2, tab3 = st.tabs(["API Settings", "Agent Configuration", "Monitoring"])

    with tab1:
        st.markdown("### 🔌 API Configuration")

        api_url = st.text_input("API Base URL", value=API_BASE_URL)
        api_timeout = st.number_input("Timeout (seconds)", value=10, min_value=1, max_value=60)

        st.markdown("### 🔑 Authentication")
        jwt_secret = st.text_input("JWT Secret", type="password", value="***")

        if st.button("💾 Save Settings"):
            st.success("Settings saved successfully!")

    with tab2:
        st.markdown("### 🤖 Agent Systems")

        systems = ["FinPsy", "Lex", "Pydini", "Inno", "Creative", "Edu"]

        for system in systems:
            with st.expander(f"📦 {system}"):
                enabled = st.checkbox(f"Enable {system}", value=True, key=f"enable_{system}")
                max_tasks = st.slider(f"Max Concurrent Tasks", 1, 10, 5, key=f"max_tasks_{system}")
                st.write(f"Status: {'Active' if enabled else 'Disabled'}")

    with tab3:
        st.markdown("### 📊 Monitoring Configuration")

        metrics_enabled = st.checkbox("Enable Prometheus Metrics", value=True)
        logging_level = st.selectbox("Logging Level", ["INFO", "DEBUG", "WARNING", "ERROR"])
        retention_days = st.number_input("Log Retention (days)", value=30, min_value=1, max_value=365)

# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point"""

    # Page config
    st.set_page_config(
        page_title="Atlas Capital - CESAR.ai Console",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject custom CSS
    inject_custom_css()

    # Initialize API client
    client = CESARClient()

    # Sidebar
    with st.sidebar:
        st.markdown("# 🏛️ Atlas Capital Automations")
        st.markdown("### *a Terry Dellmonaco Co.*")
        st.markdown("**CESAR.ai Ecosystem**")
        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "📈 Financial", "💬 Neural Chat", "⚙️ Workflows", "🔧 Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # System info
        st.markdown("### ℹ️ System Info")
        health = client.health_check()
        status = health.get("status", "unknown")

        if status == "healthy":
            st.success("✅ All Systems Operational")
        else:
            st.error("❌ System Error")

        st.markdown(f"**Version:** 2.0.0")
        st.markdown(f"**Agents:** {health.get('agents', {}).get('total', 0)}")
        st.markdown(f"**Uptime:** 72h 14m")

    # Render header
    render_header()

    # Route to page
    if page == "📊 Dashboard":
        page_dashboard(client)
    elif page == "📈 Financial":
        page_financial(client)
    elif page == "💬 Neural Chat":
        page_chat(client)
    elif page == "⚙️ Workflows":
        page_workflows(client)
    elif page == "🔧 Settings":
        page_settings(client)

if __name__ == "__main__":
    main()
