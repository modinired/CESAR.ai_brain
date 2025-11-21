"""
Atlas Capital Automations - CESAR.ai Desktop Console
Native Desktop Application for Multi-Agent Ecosystem

a Terry Dellmonaco Co.
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame, QSplitter,
    QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 10

# Mob Character Name Mapping (Sopranos, Goodfellas, Bronx Tale, Casino)
MOB_CHARACTER_NAMES = {
    "finpsy": "Paulie Walnuts",  # Financial wisdom from The Sopranos
    "lex": "Silvio Dante",       # Legal consigliere from The Sopranos
    "pydini": "Christopher Moltisanti",  # Workflow automation (Sopranos)
    "inno": "Henry Hill",        # Innovation/hustle from Goodfellas
    "creative": "Calogero",      # Creative storyteller from Bronx Tale
    "edu": "Nicky Santoro",      # Education/knowledge from Casino
    "research": "Jimmy Conway",  # Research from Goodfellas
    "dataviz": "Tommy DeVito",   # Data visualization from Goodfellas
    "collab": "Sonny LoSpecchio", # Collaboration from Bronx Tale
    "devops": "Ace Rothstein",   # DevOps/operations from Casino
    "security": "Furio Giunta"   # Security from The Sopranos
}

# Reverse mapping for display
AGENT_DISPLAY_NAMES = {v: k for k, v in MOB_CHARACTER_NAMES.items()}
AGENT_DISPLAY_NAMES["CESAR"] = "cesar"  # Keep CESAR as is

# ============================================================================
# Dark Theme Styling
# ============================================================================

DARK_STYLESHEET = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0a0e27, stop:1 #1a1f3a);
}

QWidget {
    background-color: transparent;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'San Francisco', Arial, sans-serif;
    font-size: 13px;
}

QGroupBox {
    background-color: rgba(26, 31, 58, 0.6);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 18px;
    font-weight: 600;
    color: #00d4ff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 10px;
    color: #00d4ff;
}

QLabel {
    background: transparent;
    color: #e0e0e0;
}

QLabel[heading="true"] {
    font-size: 24px;
    font-weight: 700;
    color: #00d4ff;
    padding: 8px 0;
}

QLabel[subheading="true"] {
    font-size: 16px;
    font-weight: 600;
    color: #00d4ff;
}

QLabel[metric="true"] {
    font-size: 32px;
    font-weight: 700;
    color: #00ff88;
}

QLabel[metriclabel="true"] {
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d4ff, stop:1 #0088ff);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00e0ff, stop:1 #00a0ff);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00a0cc, stop:1 #0060cc);
}

QLineEdit, QTextEdit, QComboBox {
    background-color: rgba(26, 31, 58, 0.8);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    selection-background-color: #00d4ff;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #00d4ff;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QTabWidget::pane {
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 8px;
    background-color: rgba(26, 31, 58, 0.4);
    padding: 12px;
}

QTabBar::tab {
    background-color: rgba(26, 31, 58, 0.6);
    color: #888;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: rgba(0, 212, 255, 0.2);
    color: #00d4ff;
    border-bottom: 2px solid #00d4ff;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(0, 212, 255, 0.1);
    color: #00d4ff;
}

QTableWidget {
    background-color: rgba(26, 31, 58, 0.6);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 6px;
    gridline-color: rgba(0, 212, 255, 0.1);
}

QTableWidget::item {
    padding: 8px;
    color: #e0e0e0;
}

QTableWidget::item:selected {
    background-color: rgba(0, 212, 255, 0.3);
}

QHeaderView::section {
    background-color: rgba(0, 212, 255, 0.2);
    color: #00d4ff;
    padding: 8px;
    border: none;
    font-weight: 600;
}

QScrollBar:vertical {
    background-color: rgba(26, 31, 58, 0.4);
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: rgba(0, 212, 255, 0.4);
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(0, 212, 255, 0.6);
}

QScrollBar:horizontal {
    background-color: rgba(26, 31, 58, 0.4);
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: rgba(0, 212, 255, 0.4);
    border-radius: 6px;
    min-width: 20px;
}

QFrame[frameShape="4"], QFrame[frameShape="5"] {
    background-color: rgba(0, 212, 255, 0.2);
    max-height: 1px;
}

QStatusBar {
    background-color: rgba(26, 31, 58, 0.8);
    color: #888;
    border-top: 1px solid rgba(0, 212, 255, 0.3);
}
"""

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
# Chat Worker Thread
# ============================================================================

class ChatWorker(QThread):
    """Background thread for chat requests"""
    response_received = pyqtSignal(str)

    def __init__(self, client: CESARClient, message: str, agent: str):
        super().__init__()
        self.client = client
        self.message = message
        self.agent = agent

    def run(self):
        response = self.client.chat(self.message, self.agent)
        self.response_received.emit(response)

# ============================================================================
# Main Dashboard Window
# ============================================================================

class AtlasDashboard(QMainWindow):
    """Main dashboard window"""

    def __init__(self):
        super().__init__()
        self.client = CESARClient()
        self.chat_history = []
        self.init_ui()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Atlas Capital Automations - CESAR.ai Console")
        self.setGeometry(100, 100, 1400, 900)

        # Apply dark stylesheet
        self.setStyleSheet(DARK_STYLESHEET)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = self.create_header()
        layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs
        self.tabs.addTab(self.create_dashboard_tab(), "📊 System Dashboard")
        self.tabs.addTab(self.create_chat_tab(), "💬 Agent Chat")
        self.tabs.addTab(self.create_agents_tab(), "🤖 Agent Systems")
        self.tabs.addTab(self.create_financial_tab(), "📈 Financial Intel")

        # Status bar
        self.statusBar().showMessage("Ready")

        # Initial data load
        self.refresh_data()

    def create_header(self) -> QWidget:
        """Create header widget"""
        header = QFrame()
        header.setFrameShape(QFrame.Shape.NoFrame)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 212, 255, 0.1), stop:1 rgba(0, 136, 255, 0.1));
                border-bottom: 2px solid rgba(0, 212, 255, 0.5);
                padding: 20px;
            }
        """)
        layout = QHBoxLayout(header)

        # Left: Branding
        left_layout = QVBoxLayout()
        title = QLabel("🏛️ Atlas Capital Automations")
        title.setProperty("heading", True)
        subtitle = QLabel("a Terry Dellmonaco Co.")
        subtitle.setStyleSheet("color: #888; font-size: 12px; font-style: italic;")
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        layout.addLayout(left_layout)

        layout.addStretch()

        # Center: Main title
        main_title = QLabel("CESAR.ai Command Console")
        main_title.setProperty("heading", True)
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(main_title)

        layout.addStretch()

        # Right: Time
        self.time_label = QLabel(datetime.now().strftime("%H:%M:%S"))
        self.time_label.setStyleSheet("color: #00d4ff; font-size: 16px; font-weight: 600;")
        layout.addWidget(self.time_label)

        # Update time every second
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(lambda: self.time_label.setText(datetime.now().strftime("%H:%M:%S")))
        self.time_timer.start(1000)

        return header

    def create_dashboard_tab(self) -> QWidget:
        """Create system dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Metrics row
        metrics_group = QGroupBox("System Metrics")
        metrics_layout = QGridLayout()

        self.status_label = QLabel("HEALTHY")
        self.status_label.setProperty("metric", True)
        self.status_label.setStyleSheet("color: #00ff88;")
        status_container = self.create_metric_card("System Status", self.status_label)
        metrics_layout.addWidget(status_container, 0, 0)

        self.agents_label = QLabel("0")
        self.agents_label.setProperty("metric", True)
        agents_container = self.create_metric_card("Active Agents", self.agents_label)
        metrics_layout.addWidget(agents_container, 0, 1)

        self.latency_label = QLabel("0.0ms")
        self.latency_label.setProperty("metric", True)
        latency_container = self.create_metric_card("API Latency", self.latency_label)
        metrics_layout.addWidget(latency_container, 0, 2)

        self.uptime_label = QLabel("99.9%")
        self.uptime_label.setProperty("metric", True)
        uptime_container = self.create_metric_card("Uptime", self.uptime_label)
        metrics_layout.addWidget(uptime_container, 0, 3)

        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)

        # Database and cache status
        db_cache_layout = QHBoxLayout()

        db_group = QGroupBox("Database Status")
        self.db_text = QTextEdit()
        self.db_text.setReadOnly(True)
        self.db_text.setMaximumHeight(200)
        db_layout = QVBoxLayout()
        db_layout.addWidget(self.db_text)
        db_group.setLayout(db_layout)
        db_cache_layout.addWidget(db_group)

        cache_group = QGroupBox("Cache Status")
        self.cache_text = QTextEdit()
        self.cache_text.setReadOnly(True)
        self.cache_text.setMaximumHeight(200)
        cache_layout = QVBoxLayout()
        cache_layout.addWidget(self.cache_text)
        cache_group.setLayout(cache_layout)
        db_cache_layout.addWidget(cache_group)

        layout.addLayout(db_cache_layout)

        layout.addStretch()

        return widget

    def create_chat_tab(self) -> QWidget:
        """Create agent chat tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Agent selection
        agent_layout = QHBoxLayout()
        agent_layout.addWidget(QLabel("Select Agent:"))
        self.agent_combo = QComboBox()
        self.agent_combo.addItem("CESAR")
        for agent_name in MOB_CHARACTER_NAMES.values():
            self.agent_combo.addItem(agent_name)
        agent_layout.addWidget(self.agent_combo)
        agent_layout.addStretch()
        layout.addLayout(agent_layout)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask anything to the selected agent...")
        self.chat_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.chat_input)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        return widget

    def create_agents_tab(self) -> QWidget:
        """Create agents tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Agents table
        self.agents_table = QTableWidget()
        self.agents_table.setColumnCount(5)
        self.agents_table.setHorizontalHeaderLabels(["Agent Name", "System", "Status", "Tasks", "Success Rate"])
        self.agents_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.agents_table)

        return widget

    def create_financial_tab(self) -> QWidget:
        """Create financial intelligence tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Market overview
        market_group = QGroupBox("Market Overview")
        market_layout = QGridLayout()

        self.sp500_label = QLabel("4,783.45")
        self.sp500_label.setProperty("metric", True)
        sp500_container = self.create_metric_card("S&P 500", self.sp500_label, "+1.2%")
        market_layout.addWidget(sp500_container, 0, 0)

        self.nasdaq_label = QLabel("15,011.35")
        self.nasdaq_label.setProperty("metric", True)
        nasdaq_container = self.create_metric_card("NASDAQ", self.nasdaq_label, "+0.8%")
        market_layout.addWidget(nasdaq_container, 0, 1)

        self.vix_label = QLabel("13.42")
        self.vix_label.setProperty("metric", True)
        vix_container = self.create_metric_card("VIX", self.vix_label, "-2.1%")
        market_layout.addWidget(vix_container, 0, 2)

        market_group.setLayout(market_layout)
        layout.addWidget(market_group)

        # Stock analysis
        analysis_group = QGroupBox("Stock Analysis - Paulie Walnuts (FinPsy)")
        analysis_layout = QVBoxLayout()

        ticker_layout = QHBoxLayout()
        ticker_layout.addWidget(QLabel("Ticker Symbol:"))
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("AAPL")
        ticker_layout.addWidget(self.ticker_input)

        analyze_btn = QPushButton("Analyze")
        analyze_btn.clicked.connect(self.analyze_stock)
        ticker_layout.addWidget(analyze_btn)
        ticker_layout.addStretch()

        analysis_layout.addLayout(ticker_layout)

        self.analysis_result = QTextEdit()
        self.analysis_result.setReadOnly(True)
        analysis_layout.addWidget(self.analysis_result)

        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)

        return widget

    def create_metric_card(self, title: str, value_label: QLabel, delta: str = None) -> QWidget:
        """Create a metric card"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 31, 58, 0.6);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 8px;
                padding: 16px;
            }
        """)
        layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setProperty("metriclabel", True)
        layout.addWidget(title_label)

        layout.addWidget(value_label)

        if delta:
            delta_label = QLabel(delta)
            delta_color = "#00ff88" if delta.startswith("+") else "#ff4757"
            delta_label.setStyleSheet(f"color: {delta_color}; font-size: 14px; font-weight: 600;")
            layout.addWidget(delta_label)

        layout.addStretch()

        return card

    def refresh_data(self):
        """Refresh dashboard data"""
        health = self.client.health_check()

        # Update metrics
        status = health.get("status", "unknown")
        self.status_label.setText(status.upper())
        if status == "healthy":
            self.status_label.setStyleSheet("color: #00ff88;")
            self.statusBar().showMessage("All Systems Operational", 3000)
        else:
            self.status_label.setStyleSheet("color: #ff4757;")
            self.statusBar().showMessage("System Error Detected", 3000)

        # Update database status
        db_health = health.get("database", {})
        self.db_text.setPlainText(json.dumps(db_health, indent=2))

        # Update cache status
        cache_health = health.get("redis", {})
        self.cache_text.setPlainText(json.dumps(cache_health, indent=2))

        # Update agents table
        agents = self.client.get_agents()
        self.agents_table.setRowCount(len(agents))

        for i, agent in enumerate(agents):
            agent_name = agent.get("name", "Unknown")

            # Map to mob character if not CESAR
            if agent_name.lower() in MOB_CHARACTER_NAMES:
                display_name = MOB_CHARACTER_NAMES[agent_name.lower()]
            elif agent_name.upper() == "CESAR":
                display_name = "CESAR"
            else:
                display_name = agent_name

            self.agents_table.setItem(i, 0, QTableWidgetItem(display_name))
            self.agents_table.setItem(i, 1, QTableWidgetItem(agent.get("system", "Unknown")))
            self.agents_table.setItem(i, 2, QTableWidgetItem("Active" if agent.get("active") else "Idle"))
            self.agents_table.setItem(i, 3, QTableWidgetItem(str(agent.get("tasks_completed", 0))))
            self.agents_table.setItem(i, 4, QTableWidgetItem(f"{agent.get('success_rate', 0):.1f}%"))

        self.agents_label.setText(str(len(agents)))

    def send_message(self):
        """Send chat message"""
        message = self.chat_input.text().strip()
        if not message:
            return

        # Get selected agent
        agent_display_name = self.agent_combo.currentText()
        agent_key = AGENT_DISPLAY_NAMES.get(agent_display_name, "cesar")

        # Display user message
        self.chat_display.append(f"<div style='color: #00d4ff; font-weight: 600;'>You:</div>")
        self.chat_display.append(f"<div style='margin-bottom: 12px;'>{message}</div>")

        # Clear input
        self.chat_input.clear()

        # Display thinking
        self.chat_display.append(f"<div style='color: #ffc107; font-weight: 600;'>{agent_display_name} is thinking...</div>")

        # Send request in background
        self.chat_worker = ChatWorker(self.client, message, agent_key)
        self.chat_worker.response_received.connect(lambda resp: self.display_response(agent_display_name, resp))
        self.chat_worker.start()

    def display_response(self, agent_name: str, response: str):
        """Display chat response"""
        # Remove "thinking" message
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.movePosition(cursor.MoveOperation.StartOfBlock, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()  # Remove newline

        # Display response
        self.chat_display.append(f"<div style='color: #00ff88; font-weight: 600;'>{agent_name}:</div>")
        self.chat_display.append(f"<div style='margin-bottom: 16px;'>{response}</div>")
        self.chat_display.append("<hr style='border: 1px solid rgba(0, 212, 255, 0.2);'>")

        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def analyze_stock(self):
        """Analyze stock ticker"""
        ticker = self.ticker_input.text().strip().upper()
        if not ticker:
            self.analysis_result.setPlainText("Please enter a ticker symbol")
            return

        self.analysis_result.setPlainText(f"Analyzing {ticker}...\n\nPaulie Walnuts is crunching the numbers...")

        # In a real implementation, call the FinPsy API
        # For now, show placeholder
        QTimer.singleShot(2000, lambda: self.analysis_result.setPlainText(
            f"{ticker} Analysis by Paulie Walnuts (FinPsy)\n\n"
            f"Hey, lemme tell ya about {ticker}...\n\n"
            f"The assistant analyzed {ticker} and found:\n"
            f"• Current trend: Bullish\n"
            f"• Risk level: Moderate\n"
            f"• Recommendation: Consider for portfolio\n\n"
            f"Fuggedaboutit if you're lookin' for quick money, "
            f"but for long-term? This one's got potential."
        ))

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Atlas Capital - CESAR.ai")
    app.setOrganizationName("Atlas Capital Automations")
    app.setOrganizationDomain("atlascapital.ai")

    dashboard = AtlasDashboard()
    dashboard.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
