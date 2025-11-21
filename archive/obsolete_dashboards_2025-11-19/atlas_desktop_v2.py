"""
Atlas Capital - CESAR.ai Command Console V2
ENHANCED: Beige/Cream Theme, Live Financial Data, Forecasting & Modeling

a Terry Dellmonaco Co.
"""

import sys
import json
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QScrollArea, QFrame, QSplitter,
    QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Voice chat imports
import speech_recognition as sr
import pyttsx3

# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 10

# Mob Character Name Mapping with Department/MCP References
# Format: "mcp_key": {"name": "Character Name", "dept": "Department/Function", "original": "Original Name"}
MOB_CHARACTER_MAPPING = {
    "finpsy": {
        "name": "Paulie Gualtieri",
        "dept": "Financial Intelligence & Psychology",
        "original": "FinPsy Agent",
        "show": "The Sopranos"
    },
    "lex": {
        "name": "Silvio Dante",
        "dept": "Legal & Compliance",
        "original": "Lex Agent",
        "show": "The Sopranos"
    },
    "pydini": {
        "name": "Christopher Moltisanti",
        "dept": "Workflow Automation & Python Magic",
        "original": "Pydini Agent",
        "show": "The Sopranos"
    },
    "inno": {
        "name": "Henry Hill",
        "dept": "Innovation & Strategy",
        "original": "Innovation Agent",
        "show": "Goodfellas"
    },
    "creative": {
        "name": "Sonny LoSpecchio",
        "dept": "Creative Solutions",
        "original": "Creative Agent",
        "show": "A Bronx Tale"
    },
    "edu": {
        "name": "Nicky Santoro",
        "dept": "Education & Training",
        "original": "Education Agent",
        "show": "Casino"
    },
    "research": {
        "name": "Jimmy Conway",
        "dept": "Research & Intelligence",
        "original": "Research Agent",
        "show": "Goodfellas"
    },
    "dataviz": {
        "name": "Tommy DeVito",
        "dept": "Data Visualization",
        "original": "DataViz Agent",
        "show": "Goodfellas"
    },
    "collab": {
        "name": "Tony Soprano",
        "dept": "Collaboration & Coordination",
        "original": "Collaboration Agent",
        "show": "The Sopranos"
    },
    "devops": {
        "name": "Sam Rothstein",
        "dept": "DevOps & Infrastructure",
        "original": "DevOps Agent",
        "show": "Casino"
    },
    "security": {
        "name": "Furio Giunta",
        "dept": "Security & Protection",
        "original": "Security Agent",
        "show": "The Sopranos"
    },
    "email": {
        "name": "Bobby Baccalieri",
        "dept": "Email & Communications",
        "original": "Email Agent",
        "show": "The Sopranos"
    },
    "workflow": {
        "name": "Junior Soprano",
        "dept": "Workflow Management",
        "original": "Workflow Agent",
        "show": "The Sopranos"
    },
    "memory": {
        "name": "Carmine Lupertazzi Sr.",
        "dept": "Memory & Knowledge Management",
        "original": "Memory Agent",
        "show": "The Sopranos"
    },
    "integration": {
        "name": "Johnny Sacrimoni",
        "dept": "System Integration",
        "original": "Integration Agent",
        "show": "The Sopranos"
    }
}

# Legacy simplified mapping for backward compatibility
MOB_CHARACTER_NAMES = {k: v["name"] for k, v in MOB_CHARACTER_MAPPING.items()}

AGENT_DISPLAY_NAMES = {v["name"]: k for k, v in MOB_CHARACTER_MAPPING.items()}
AGENT_DISPLAY_NAMES["CESAR"] = "cesar"

# ============================================================================
# BEIGE/CREAM Theme Styling
# ============================================================================

BEIGE_STYLESHEET = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #F5F5DC, stop:1 #FAF0E6);
}

QWidget {
    background-color: transparent;
    color: #2C1810;
    font-family: 'Segoe UI', 'San Francisco', Arial, sans-serif;
    font-size: 13px;
}

QGroupBox {
    background-color: rgba(255, 248, 220, 0.8);
    border: 2px solid #D2691E;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 18px;
    font-weight: 700;
    color: #8B4513;
    font-size: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 6px 15px;
    background-color: #DEB887;
    border-radius: 5px;
    color: #4A2511;
}

QLabel {
    background: transparent;
    color: #2C1810;
}

QLabel[heading="true"] {
    font-size: 26px;
    font-weight: 800;
    color: #8B4513;
    padding: 10px 0;
}

QLabel[subheading="true"] {
    font-size: 17px;
    font-weight: 700;
    color: #A0522D;
}

QLabel[metric="true"] {
    font-size: 36px;
    font-weight: 800;
    color: #CD853F;
}

QLabel[metriclabel="true"] {
    font-size: 11px;
    color: #8B7355;
    text-transform: uppercase;
    font-weight: 600;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #D2691E, stop:1 #CD853F);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 28px;
    font-weight: 700;
    font-size: 14px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #A0522D, stop:1 #B8860B);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8B4513, stop:1 #996515);
}

QLineEdit, QTextEdit, QComboBox {
    background-color: rgba(255, 255, 255, 0.9);
    border: 2px solid #D2B48C;
    border-radius: 8px;
    padding: 10px 14px;
    color: #2C1810;
    selection-background-color: #DEB887;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 2px solid #CD853F;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QTabWidget::pane {
    border: 2px solid #D2B48C;
    border-radius: 10px;
    background-color: rgba(255, 248, 220, 0.6);
    padding: 15px;
}

QTabBar::tab {
    background-color: rgba(222, 184, 135, 0.7);
    color: #4A2511;
    padding: 12px 24px;
    margin-right: 6px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 700;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #DEB887;
    color: #2C1810;
    border-bottom: 3px solid #CD853F;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(205, 133, 63, 0.4);
}

QTableWidget {
    background-color: rgba(255, 255, 255, 0.9);
    border: 2px solid #D2B48C;
    border-radius: 8px;
    gridline-color: #E8DCCA;
}

QTableWidget::item {
    padding: 10px;
    color: #2C1810;
}

QTableWidget::item:selected {
    background-color: rgba(222, 184, 135, 0.5);
}

QHeaderView::section {
    background-color: #DEB887;
    color: #4A2511;
    padding: 10px;
    border: none;
    font-weight: 700;
    font-size: 13px;
}

QScrollBar:vertical {
    background-color: rgba(222, 184, 135, 0.3);
    width: 14px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background-color: #CD853F;
    border-radius: 7px;
    min-height: 25px;
}

QScrollBar::handle:vertical:hover {
    background-color: #A0522D;
}

QStatusBar {
    background-color: rgba(222, 184, 135, 0.8);
    color: #4A2511;
    border-top: 2px solid #D2B48C;
    font-weight: 600;
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
            if response.status_code == 200:
                return response.json()
            # Return mock data if API fails
            return self._get_mock_agents()
        except:
            return self._get_mock_agents()

    def _get_mock_agents(self) -> List[Dict[str, Any]]:
        """Get mock agent data for display with department/original name info"""
        agents = []
        for key, info in MOB_CHARACTER_MAPPING.items():
            agents.append({
                "name": key,
                "display_name": info["name"],
                "system": info["dept"],
                "original_name": info["original"],
                "show": info["show"],
                "active": True,
                "tasks_completed": np.random.randint(50, 500),
                "success_rate": round(np.random.uniform(85, 99.9), 1)
            })
        # Add CESAR
        agents.insert(0, {
            "name": "cesar",
            "display_name": "CESAR",
            "system": "Central Executive System for Autonomous Reasoning",
            "original_name": "CESAR Orchestrator",
            "show": "Atlas Capital",
            "active": True,
            "tasks_completed": np.random.randint(1000, 5000),
            "success_rate": 99.9
        })
        return agents

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
# Financial Data Worker
# ============================================================================

class FinancialDataWorker(QThread):
    """Background thread for fetching financial data"""
    data_received = pyqtSignal(object)

    def __init__(self, ticker: str):
        super().__init__()
        self.ticker = ticker

    def run(self):
        try:
            # Fetch real data from yfinance
            stock = yf.Ticker(self.ticker)
            hist = stock.history(period="1y")
            info = stock.info

            data = {
                "ticker": self.ticker,
                "hist": hist,
                "info": info,
                "current_price": hist['Close'].iloc[-1] if not hist.empty else 0,
                "prev_close": hist['Close'].iloc[-2] if len(hist) > 1 else 0
            }
            self.data_received.emit(data)
        except Exception as e:
            self.data_received.emit({"error": str(e)})

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


class VoiceRecognitionWorker(QThread):
    """Background thread for voice recognition"""
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()

    def run(self):
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

            print("🔄 Processing speech...")
            text = self.recognizer.recognize_google(audio)
            self.text_recognized.emit(text)
        except sr.WaitTimeoutError:
            self.error_occurred.emit("Listening timed out - no speech detected")
        except sr.UnknownValueError:
            self.error_occurred.emit("Could not understand audio")
        except sr.RequestError as e:
            self.error_occurred.emit(f"Speech recognition error: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Error: {e}")


class TextToSpeechWorker(QThread):
    """Background thread for text-to-speech"""
    finished = pyqtSignal()

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 175)  # Speed
            engine.setProperty('volume', 0.9)  # Volume
            engine.say(self.text)
            engine.runAndWait()
            self.finished.emit()
        except Exception as e:
            print(f"TTS Error: {e}")
            self.finished.emit()


# ============================================================================
# Main Dashboard Window
# ============================================================================

class AtlasDashboard(QMainWindow):
    """Main dashboard window"""

    def __init__(self):
        super().__init__()
        self.client = CESARClient()
        self.chat_history = []
        self.current_ticker = "SPY"
        self.init_ui()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Atlas Capital Automations - CESAR.ai Console")
        self.setGeometry(100, 100, 1600, 1000)

        # Apply beige stylesheet
        self.setStyleSheet(BEIGE_STYLESHEET)

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
        self.tabs.addTab(self.create_financial_tab(), "📈 Financial Intelligence")
        self.tabs.addTab(self.create_agents_tab(), "🤖 Agent Systems")
        self.tabs.addTab(self.create_chat_tab(), "💬 Agent Chat")

        # Status bar
        self.statusBar().showMessage("Ready - All Systems Operational")

        # Initial data load
        self.refresh_data()
        self.load_financial_data("SPY")

    def create_header(self) -> QWidget:
        """Create header widget"""
        header = QFrame()
        header.setFrameShape(QFrame.Shape.NoFrame)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(222, 184, 135, 0.4), stop:1 rgba(205, 133, 63, 0.3));
                border-bottom: 3px solid #CD853F;
                padding: 25px;
            }
        """)
        layout = QHBoxLayout(header)

        # Left: Branding
        left_layout = QVBoxLayout()
        title = QLabel("🏛️ Atlas Capital Automations")
        title.setProperty("heading", True)
        subtitle = QLabel("a Terry Dellmonaco Co.")
        subtitle.setStyleSheet("color: #8B7355; font-size: 13px; font-style: italic; font-weight: 600;")
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
        self.time_label.setStyleSheet("color: #8B4513; font-size: 18px; font-weight: 700;")
        layout.addWidget(self.time_label)

        # Update time every second
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(lambda: self.time_label.setText(datetime.now().strftime("%H:%M:%S")))
        self.time_timer.start(1000)

        return header

    def create_metric_card(self, title: str, value_label: QLabel, delta: str = None) -> QWidget:
        """Create a metric card"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #D2B48C;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setProperty("metriclabel", True)
        layout.addWidget(title_label)

        layout.addWidget(value_label)

        if delta:
            delta_label = QLabel(delta)
            delta_color = "#228B22" if delta.startswith("+") else "#DC143C"
            delta_label.setStyleSheet(f"color: {delta_color}; font-size: 15px; font-weight: 700;")
            layout.addWidget(delta_label)

        layout.addStretch()

        return card

    def create_dashboard_tab(self) -> QWidget:
        """Create system dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Metrics row
        metrics_group = QGroupBox("System Metrics")
        metrics_layout = QGridLayout()

        self.status_label = QLabel("HEALTHY")
        self.status_label.setProperty("metric", True)
        self.status_label.setStyleSheet("color: #228B22;")
        status_container = self.create_metric_card("System Status", self.status_label)
        metrics_layout.addWidget(status_container, 0, 0)

        self.agents_label = QLabel("12")
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
        self.db_text.setMaximumHeight(250)
        db_layout = QVBoxLayout()
        db_layout.addWidget(self.db_text)
        db_group.setLayout(db_layout)
        db_cache_layout.addWidget(db_group)

        cache_group = QGroupBox("Cache Status")
        self.cache_text = QTextEdit()
        self.cache_text.setReadOnly(True)
        self.cache_text.setMaximumHeight(250)
        cache_layout = QVBoxLayout()
        cache_layout.addWidget(self.cache_text)
        cache_group.setLayout(cache_layout)
        db_cache_layout.addWidget(cache_group)

        layout.addLayout(db_cache_layout)

        layout.addStretch()

        return widget

    def create_financial_tab(self) -> QWidget:
        """Create financial intelligence tab with REAL data"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Ticker input
        input_group = QGroupBox("Stock Analysis - Paulie Walnuts (FinPsy)")
        input_layout = QHBoxLayout()

        input_layout.addWidget(QLabel("Ticker Symbol:"))
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("Enter ticker (e.g., AAPL, TSLA, NVDA)")
        self.ticker_input.setText("SPY")
        input_layout.addWidget(self.ticker_input)

        analyze_btn = QPushButton("📊 Analyze & Forecast")
        analyze_btn.clicked.connect(self.analyze_stock)
        input_layout.addWidget(analyze_btn)

        input_layout.addStretch()
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Chart display
        chart_group = QGroupBox("Price Chart, Forecast & Technical Analysis")
        chart_layout = QVBoxLayout()

        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumHeight(500)
        chart_layout.addWidget(self.chart_view)

        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)

        # Stats
        stats_group = QGroupBox("Key Metrics & Forecasting")
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        return widget

    def create_agents_tab(self) -> QWidget:
        """Create agents tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Agents table
        agents_group = QGroupBox("Active Agent Systems")
        agents_layout = QVBoxLayout()

        self.agents_table = QTableWidget()
        self.agents_table.setColumnCount(5)
        self.agents_table.setHorizontalHeaderLabels(["Agent Name", "System", "Status", "Tasks Completed", "Success Rate"])
        self.agents_table.horizontalHeader().setStretchLastSection(True)
        self.agents_table.setMinimumHeight(600)
        agents_layout.addWidget(self.agents_table)

        agents_group.setLayout(agents_layout)
        layout.addWidget(agents_group)

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
        input_layout.addWidget(self.chat_input, 1)  # Stretch factor 1

        # Voice input button
        voice_btn = QPushButton("🎤 Voice")
        voice_btn.setToolTip("Click to speak your message")
        voice_btn.clicked.connect(self.start_voice_input)
        input_layout.addWidget(voice_btn)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        return widget

    def refresh_data(self):
        """Refresh dashboard data"""
        health = self.client.health_check()

        # Update metrics
        status = health.get("status", "unknown")
        self.status_label.setText(status.upper())
        if status == "healthy":
            self.status_label.setStyleSheet("color: #228B22;")
            self.statusBar().showMessage("All Systems Operational", 3000)
        else:
            self.status_label.setStyleSheet("color: #DC143C;")
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
            display_name = agent.get("display_name", agent_name)
            system = agent.get("system", "Unknown")
            original_name = agent.get("original_name", "")
            show = agent.get("show", "")

            # Create name item with tooltip showing original name/dept
            name_item = QTableWidgetItem(display_name)
            if original_name:
                tooltip = f"{display_name}\n━━━━━━━━━━━━━━━━━━━━━━\nOriginal: {original_name}\nDepartment: {system}\nShow: {show}"
                name_item.setToolTip(tooltip)
            self.agents_table.setItem(i, 0, name_item)

            # System/Department column
            system_item = QTableWidgetItem(system)
            self.agents_table.setItem(i, 1, system_item)

            # Status
            self.agents_table.setItem(i, 2, QTableWidgetItem("✅ Active" if agent.get("active") else "⏸️ Idle"))

            # Tasks
            self.agents_table.setItem(i, 3, QTableWidgetItem(str(agent.get("tasks_completed", 0))))

            # Success rate
            self.agents_table.setItem(i, 4, QTableWidgetItem(f"{agent.get('success_rate', 0):.1f}%"))

        self.agents_label.setText(str(len(agents)))

    def load_financial_data(self, ticker: str):
        """Load financial data and create visualizations"""
        self.current_ticker = ticker
        self.statusBar().showMessage(f"Loading data for {ticker}...")

        # Start background worker
        self.fin_worker = FinancialDataWorker(ticker)
        self.fin_worker.data_received.connect(self.display_financial_data)
        self.fin_worker.start()

    def display_financial_data(self, data: Dict):
        """Display financial data with charts and forecasting"""
        if "error" in data:
            self.stats_text.setPlainText(f"Error loading data: {data['error']}")
            return

        ticker = data["ticker"]
        hist = data["hist"]
        info = data["info"]

        if hist.empty:
            self.stats_text.setPlainText("No data available for this ticker")
            return

        # Create comprehensive chart
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Price & Moving Averages', 'Volume', 'RSI (14)'),
            row_heights=[0.5, 0.25, 0.25]
        )

        # Price and moving averages
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='Price'
        ), row=1, col=1)

        # Calculate moving averages
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()

        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_20'], name='SMA 20', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], name='SMA 50', line=dict(color='blue', width=1)), row=1, col=1)

        # Simple forecast (linear regression on last 30 days)
        recent_data = hist['Close'].tail(30)
        x_vals = np.arange(len(recent_data))
        coeffs = np.polyfit(x_vals, recent_data.values, 1)
        forecast_days = 14
        future_x = np.arange(len(recent_data), len(recent_data) + forecast_days)
        forecast_y = coeffs[0] * future_x + coeffs[1]

        future_dates = pd.date_range(start=hist.index[-1] + timedelta(days=1), periods=forecast_days, freq='D')
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=forecast_y,
            name='14-Day Forecast',
            line=dict(color='red', dash='dash', width=2)
        ), row=1, col=1)

        # Volume
        colors = ['red' if row['Close'] < row['Open'] else 'green' for idx, row in hist.iterrows()]
        fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume', marker_color=colors, showlegend=False), row=2, col=1)

        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        fig.add_trace(go.Scatter(x=hist.index, y=rsi, name='RSI', line=dict(color='purple', width=2)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)

        fig.update_layout(
            title=f"{ticker} - Comprehensive Analysis with Forecast",
            xaxis_rangeslider_visible=False,
            height=800,
            template="plotly_white",
            paper_bgcolor='#FAF0E6',
            plot_bgcolor='#FFF8DC'
        )

        # Save to HTML and display
        html_str = fig.to_html(include_plotlyjs='cdn')
        self.chart_view.setHtml(html_str)

        # Display stats
        current_price = data["current_price"]
        prev_close = data["prev_close"]
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0

        forecast_end = forecast_y[-1]
        forecast_change = ((forecast_end - current_price) / current_price) * 100

        stats_text = f"""
        Paulie Walnuts says: "Lemme tell ya about {ticker}, Bobby-boy..."

        📊 CURRENT ANALYSIS:
        Current Price: ${current_price:.2f}
        Previous Close: ${prev_close:.2f}
        Change: ${change:+.2f} ({change_pct:+.2f}%)

        📈 14-DAY FORECAST:
        Predicted Price: ${forecast_end:.2f}
        Expected Change: {forecast_change:+.2f}%
        Trend: {"📈 Bullish" if forecast_change > 0 else "📉 Bearish"}

        🎯 TECHNICAL INDICATORS:
        RSI (14): {rsi.iloc[-1]:.1f} - {"Overbought ⚠️" if rsi.iloc[-1] > 70 else "Oversold 💰" if rsi.iloc[-1] < 30 else "Neutral ✅"}
        SMA 20: ${hist['SMA_20'].iloc[-1]:.2f}
        SMA 50: ${hist['SMA_50'].iloc[-1]:.2f}
        Trend: {"Above both MAs - Strong uptrend 🚀" if current_price > hist['SMA_50'].iloc[-1] else "Below MAs - Downtrend ⬇️"}

        💡 PAULIE'S TAKE:
        {self.get_trading_advice(change_pct, rsi.iloc[-1], forecast_change)}
        """

        self.stats_text.setPlainText(stats_text)
        self.statusBar().showMessage(f"Analysis complete for {ticker}", 5000)

    def get_trading_advice(self, change_pct: float, rsi: float, forecast_change: float) -> str:
        """Get Paulie Walnuts' trading advice"""
        if rsi > 70 and change_pct > 2:
            return "Fuggedaboutit! Stock's too hot right now. Maybe wait for a pullback, capisce?"
        elif rsi < 30 and forecast_change > 0:
            return "Now we're talkin'! Stock's oversold and forecast looks good. Could be a buying opportunity, Bobby-boy."
        elif forecast_change > 5:
            return "The assistant sees strong upside potential. Consider accumulating on dips."
        elif forecast_change < -5:
            return "Forecast ain't lookin' good. Might wanna take profits if you're holdin' this one."
        else:
            return "Sideways action. Nothing to get excited about. Keep an eye on it though."

    def analyze_stock(self):
        """Analyze stock when button clicked"""
        ticker = self.ticker_input.text().strip().upper()
        if ticker:
            self.load_financial_data(ticker)

    def send_message(self):
        """Send chat message"""
        message = self.chat_input.text().strip()
        if not message:
            return

        # Get selected agent
        agent_display_name = self.agent_combo.currentText()
        agent_key = AGENT_DISPLAY_NAMES.get(agent_display_name, "cesar")

        # Display user message
        self.chat_display.append(f"<div style='color: #8B4513; font-weight: 700;'>You:</div>")
        self.chat_display.append(f"<div style='margin-bottom: 15px;'>{message}</div>")

        # Clear input
        self.chat_input.clear()

        # Display thinking
        self.chat_display.append(f"<div style='color: #CD853F; font-weight: 700;'>{agent_display_name} is thinking...</div>")

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
        cursor.deletePreviousChar()

        # Display response
        self.chat_display.append(f"<div style='color: #228B22; font-weight: 700;'>{agent_name}:</div>")
        self.chat_display.append(f"<div style='margin-bottom: 20px;'>{response}</div>")
        self.chat_display.append("<hr style='border: 1px solid #D2B48C;'>")

        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # Speak response
        self.speak_response(response)

    def start_voice_input(self):
        """Start voice recognition"""
        self.statusBar().showMessage("🎤 Listening... Speak now!", 5000)

        self.voice_worker = VoiceRecognitionWorker()
        self.voice_worker.text_recognized.connect(self.on_voice_recognized)
        self.voice_worker.error_occurred.connect(self.on_voice_error)
        self.voice_worker.start()

    def on_voice_recognized(self, text: str):
        """Handle recognized speech"""
        self.chat_input.setText(text)
        self.statusBar().showMessage(f"✅ Recognized: {text}", 3000)
        # Automatically send the message
        self.send_message()

    def on_voice_error(self, error: str):
        """Handle voice recognition error"""
        self.statusBar().showMessage(f"❌ {error}", 5000)

    def speak_response(self, text: str):
        """Speak agent response using TTS"""
        # Start TTS in background
        self.tts_worker = TextToSpeechWorker(text)
        self.tts_worker.start()

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Atlas Capital - CESAR.ai V2")
    app.setOrganizationName("Atlas Capital Automations")
    app.setOrganizationDomain("atlascapital.ai")

    dashboard = AtlasDashboard()
    dashboard.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
