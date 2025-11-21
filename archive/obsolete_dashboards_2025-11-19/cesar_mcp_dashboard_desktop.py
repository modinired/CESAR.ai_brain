#!/usr/bin/env python3
"""
CESAR Multi-Agent MCP Dashboard - Local Desktop Edition
Native PyQt6 Terminal-Style Interface with Glassmorphism Design
NO WEB UI - Pure Desktop Application

a Terry Dellmonaco Co.
Atlas Capital Automations - CESAR.ai Ecosystem
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QTableWidget, QTableWidgetItem,
    QGraphicsDropShadowEffect, QGridLayout, QFrame, QScrollArea, QTabWidget,
    QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont, QTextCursor
import numpy as np

# ============================================================================
# GLASSMORPHISM + TERMINAL HYBRID STYLESHEET
# ============================================================================

CESAR_TERMINAL_STYLE = """
/* GLOBAL BACKGROUND - DEEP MESH GRADIENT */
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #1e293b,
        stop:0.4 #0f172a,
        stop:1 #020617
    );
}

QWidget {
    background: transparent;
    color: #e2e8f0;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 13px;
}

/* GLASS PANE - FROSTED BLUR EFFECT */
.glass-pane {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(51, 65, 85, 0.5);
    border-radius: 12px;
    padding: 16px;
}

/* TERMINAL WINDOW - PURE BLACK WITH GREEN TEXT */
QTextEdit#terminal {
    background-color: #000000;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px;
    color: #10b981;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 13px;
    selection-background-color: #1e3a5f;
}

QLineEdit#terminalInput {
    background-color: #0a0a0a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #10b981;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 13px;
}

QLineEdit#terminalInput:focus {
    border: 1px solid #10b981;
}

/* SECTION HEADERS */
QLabel#paneHeader {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #94a3b8;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 5px;
}

/* METRIC CARDS */
QFrame#metricCard {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(59, 130, 246, 0.1),
        stop:1 rgba(139, 92, 246, 0.1)
    );
    border: 1px solid rgba(147, 197, 253, 0.2);
    border-radius: 12px;
    padding: 15px;
}

/* BUTTONS */
QPushButton {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6,
        stop:1 #8b5cf6
    );
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 13px;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #2563eb,
        stop:1 #7c3aed
    );
}

QPushButton:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #1d4ed8,
        stop:1 #6d28d9
    );
}

/* TABLE STYLING */
QTableWidget {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: #e2e8f0;
    gridline-color: rgba(255, 255, 255, 0.05);
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background: rgba(96, 165, 250, 0.2);
}

QHeaderView::section {
    background: rgba(255, 255, 255, 0.05);
    color: #94a3b8;
    padding: 8px;
    border: none;
    font-weight: 600;
}

/* TABS */
QTabWidget::pane {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 15px;
}

QTabBar::tab {
    background: transparent;
    color: #94a3b8;
    padding: 12px 24px;
    border-radius: 8px;
    margin-right: 8px;
    font-weight: 500;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

QTabBar::tab:selected {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(59, 130, 246, 0.2),
        stop:1 rgba(139, 92, 246, 0.2)
    );
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

QTabBar::tab:hover:!selected {
    background: rgba(96, 165, 250, 0.1);
    color: #60a5fa;
}

/* PROGRESS BAR */
QProgressBar {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    text-align: center;
    color: #e2e8f0;
}

QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6,
        stop:1 #10b981
    );
    border-radius: 6px;
}

/* SCROLLBAR */
QScrollBar:vertical {
    background: rgba(255, 255, 255, 0.05);
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: rgba(96, 165, 250, 0.3);
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(96, 165, 250, 0.5);
}

QScrollBar:horizontal {
    background: rgba(255, 255, 255, 0.05);
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background: rgba(96, 165, 250, 0.3);
    border-radius: 5px;
}
"""

# ============================================================================
# LIBRARY DATA - FROM cesar_terminal.py
# ============================================================================

LIBRARY_DATA = [
    {"category": "OSINT Tools", "cmd": "osint", "desc": "Launch OSINT investigation menu", "date": "2024-10-01"},
    {"category": "OSINT Tools", "cmd": "osint-web", "desc": "Open OSINT web dashboard", "date": "2024-10-05"},
    {"category": "OSINT Tools", "cmd": "shodan", "desc": "Shodan CLI (device search)", "date": "2024-09-12"},
    {"category": "Agent Systems", "cmd": "spedines", "desc": "Spedines agent TUI", "date": "2025-01-15"},
    {"category": "Agent Systems", "cmd": "jim-verbose", "desc": "Jim with verbose output", "date": "2025-02-01"},
    {"category": "Agent Systems", "cmd": "job-search", "desc": "Recurring job search agent", "date": "2025-02-10"},
    {"category": "Dashboards", "cmd": "workflow_dashboard", "desc": "Main workflow dashboard", "date": "2024-11-20"},
    {"category": "Dashboards", "cmd": "dashbrew", "desc": "Dashbrew terminal UI", "date": "2024-12-01"},
    {"category": "Quick Commands", "cmd": "library-update", "desc": "Update all tools", "date": "2025-02-18"},
]

# ============================================================================
# API CLIENT
# ============================================================================

class CESARAPIClient:
    """Client for CESAR.ai MCP API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.json() if response.status_code == 200 else {"status": "error"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def get_agents(self) -> List[Dict[str, Any]]:
        """Get all MCP agents"""
        try:
            response = self.session.get(f"{self.base_url}/api/agents", timeout=5)
            if response.status_code == 200:
                return response.json()
            return self._get_mock_agents()
        except:
            return self._get_mock_agents()

    def _get_mock_agents(self) -> List[Dict[str, Any]]:
        """Mock agent data for offline mode"""
        agents = [
            {"name": "CESAR", "status": "active", "tasks": 1247, "success_rate": 99.9},
            {"name": "FinPsy", "status": "active", "tasks": 847, "success_rate": 98.7},
            {"name": "Pydini", "status": "active", "tasks": 623, "success_rate": 97.2},
            {"name": "Lex", "status": "idle", "tasks": 412, "success_rate": 99.1},
            {"name": "Inno", "status": "active", "tasks": 389, "success_rate": 96.8},
            {"name": "Edu", "status": "active", "tasks": 278, "success_rate": 98.3},
        ]
        return agents

    def execute_command(self, command: str, agent: str = "cesar") -> str:
        """Execute command via MCP"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/chat",
                json={"message": command, "agent": agent},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "No response")
            return f"Error: HTTP {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

# ============================================================================
# COMMAND WORKER THREAD
# ============================================================================

class CommandWorker(QThread):
    """Background thread for command execution"""
    response_received = pyqtSignal(str)

    def __init__(self, client: CESARAPIClient, command: str, agent: str = "cesar"):
        super().__init__()
        self.client = client
        self.command = command
        self.agent = agent

    def run(self):
        response = self.client.execute_command(self.command, self.agent)
        self.response_received.emit(response)

# ============================================================================
# TERMINAL WIDGET
# ============================================================================

class TerminalWidget(QWidget):
    """Terminal-style output widget with input"""

    def __init__(self, title: str, shell_type: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.shell_type = shell_type
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QLabel(f"{self.title}  [{self.shell_type}]")
        header.setObjectName("paneHeader")
        header.setStyleSheet("""
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #94a3b8;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding: 8px;
        """)
        layout.addWidget(header)

        # Terminal output
        self.output = QTextEdit()
        self.output.setObjectName("terminal")
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(300)
        layout.addWidget(self.output)

        # Input
        self.input_field = QLineEdit()
        self.input_field.setObjectName("terminalInput")
        self.input_field.setPlaceholderText(f"root@{self.title.lower()}: >")
        layout.addWidget(self.input_field)

    def append_log(self, message: str, color: str = "#10b981"):
        """Append log message with timestamp and color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        self.output.append(html)
        self.output.moveCursor(QTextCursor.MoveOperation.End)

    def clear_output(self):
        """Clear terminal output"""
        self.output.clear()

# ============================================================================
# METRIC CARD
# ============================================================================

class MetricCard(QFrame):
    """Glassmorphism metric card"""

    def __init__(self, title: str, value: str, delta: str = None, color: str = "#60a5fa"):
        super().__init__()
        self.setObjectName("metricCard")
        self.init_ui(title, value, delta, color)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def init_ui(self, title: str, value: str, delta: Optional[str], color: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #94a3b8; font-size: 11px; text-transform: uppercase;")
        layout.addWidget(title_label)

        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 800;")
        layout.addWidget(value_label)

        # Delta
        if delta:
            delta_label = QLabel(delta)
            delta_color = "#34d399" if "▲" in delta or "+" in delta else "#ef4444"
            delta_label.setStyleSheet(f"color: {delta_color}; font-size: 11px; font-weight: 600;")
            layout.addWidget(delta_label)

        layout.addStretch()
        self.setFixedHeight(120)

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

class CESARMCPDashboard(QMainWindow):
    """CESAR Multi-Agent MCP Dashboard - Desktop Edition"""

    def __init__(self):
        super().__init__()
        self.client = CESARAPIClient()
        self.command_history = []
        self.init_ui()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

        # Initial load
        self.refresh_data()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("CESAR.ai // TERMINAL ACCESS - Multi-Agent MCP Dashboard")
        self.setGeometry(100, 50, 1800, 1000)
        self.setStyleSheet(CESAR_TERMINAL_STYLE)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        self.create_header(main_layout)

        # Status bar
        self.create_status_bar_widget(main_layout)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_terminal_tab(), "🖥️ Dual CLI")
        tabs.addTab(self.create_workflows_tab(), "🔄 Workflows")
        tabs.addTab(self.create_library_tab(), "📚 Tool Library")
        tabs.addTab(self.create_agents_tab(), "🤖 Agents")
        main_layout.addWidget(tabs)

        # Status bar
        self.statusBar().showMessage("Ready - All Systems Operational")

    def create_header(self, parent_layout):
        """Create glassmorphism header"""
        header = QFrame()
        header.setStyleSheet("""
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: 25px;
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 8)
        header.setGraphicsEffect(shadow)

        layout = QHBoxLayout(header)

        # Left: Title
        left_layout = QVBoxLayout()
        title = QLabel("🏛️ CESAR.ai // TERMINAL ACCESS")
        title.setStyleSheet("color: #60a5fa; font-size: 36px; font-weight: 800; font-family: 'Inter', sans-serif;")
        subtitle = QLabel("Tri-Modal Interface: Human | Agent-A | Agent-B")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px; font-style: italic; font-family: 'Inter', sans-serif;")
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        layout.addLayout(left_layout)

        layout.addStretch()

        # Right: Status
        self.system_status_label = QLabel("● SYSTEM ONLINE")
        self.system_status_label.setStyleSheet("""
            background: rgba(30, 41, 59, 0.8);
            padding: 10px 20px;
            border-radius: 8px;
            color: #10b981;
            border: 1px solid #10b981;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        """)
        layout.addWidget(self.system_status_label)

        parent_layout.addWidget(header)

    def create_status_bar_widget(self, parent_layout):
        """Create metrics status bar"""
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(15)

        self.metric_connectivity = MetricCard("System Connectivity", "100%", "All Systems Operational", "#60a5fa")
        metrics_layout.addWidget(self.metric_connectivity, 0, 0)

        self.metric_agents = MetricCard("Active Agents", "6", "+2 from baseline", "#34d399")
        metrics_layout.addWidget(self.metric_agents, 0, 1)

        self.metric_tasks = MetricCard("Tasks Completed", "2,847", "+12% this hour", "#a78bfa")
        metrics_layout.addWidget(self.metric_tasks, 0, 2)

        self.metric_success = MetricCard("Success Rate", "98.7%", "Above target (95%)", "#60a5fa")
        metrics_layout.addWidget(self.metric_success, 0, 3)

        parent_layout.addLayout(metrics_layout)

    def create_terminal_tab(self) -> QWidget:
        """Create dual CLI terminal tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Dual terminal layout
        terminals_layout = QHBoxLayout()

        # Terminal 1
        self.terminal1 = TerminalWidget("CLI-01 [Primary]", "BASH")
        self.terminal1.input_field.returnPressed.connect(lambda: self.execute_terminal_command(self.terminal1, "cesar"))
        terminals_layout.addWidget(self.terminal1)

        # Terminal 2
        self.terminal2 = TerminalWidget("CLI-02 [Agent Stream]", "PYTHON KERNEL")
        self.terminal2.input_field.returnPressed.connect(lambda: self.execute_terminal_command(self.terminal2, "pydini"))
        terminals_layout.addWidget(self.terminal2)

        layout.addLayout(terminals_layout)

        # Initialize terminal logs
        self.terminal1.append_log("Initializing CESAR core...")
        self.terminal1.append_log("Connecting to PostgresDB... OK", "#10b981")
        self.terminal1.append_log("Loading Agent 'Pydini'...", "#3b82f6")
        self.terminal1.append_log("Ready for command input.", "#10b981")

        self.terminal2.append_log(">>> import cesar_agent as ca", "#3b82f6")
        self.terminal2.append_log(">>> agent = ca.load('FinPsy')", "#3b82f6")
        self.terminal2.append_log("[FinPsy] Agent loaded successfully", "#10b981")
        self.terminal2.append_log(">>> Awaiting next instruction...", "#94a3b8")

        return widget

    def create_workflows_tab(self) -> QWidget:
        """Create workflows tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Workflows table
        self.workflows_table = QTableWidget()
        self.workflows_table.setColumnCount(4)
        self.workflows_table.setHorizontalHeaderLabels(["Workflow ID", "Agent", "Status", "Last Active"])
        self.workflows_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.workflows_table)

        # Progress bar
        progress_label = QLabel("Global Task Completion Rate")
        progress_label.setStyleSheet("color: #94a3b8; font-size: 12px; margin-top: 10px;")
        layout.addWidget(progress_label)

        self.workflow_progress = QProgressBar()
        self.workflow_progress.setValue(45)
        self.workflow_progress.setTextVisible(True)
        self.workflow_progress.setFormat("%p% Complete")
        layout.addWidget(self.workflow_progress)

        # Populate table
        workflows = [
            ("WF-1024", "FinPsy", "RUNNING", "Now"),
            ("WF-1025", "Pydini", "IDLE", "2m ago"),
            ("WF-1026", "Lex", "FAILED", "1h ago"),
            ("WF-1027", "Inno", "QUEUED", "5m ago"),
        ]

        self.workflows_table.setRowCount(len(workflows))
        for row, (wf_id, agent, status, last_active) in enumerate(workflows):
            self.workflows_table.setItem(row, 0, QTableWidgetItem(wf_id))
            self.workflows_table.setItem(row, 1, QTableWidgetItem(agent))

            # Color code status
            status_item = QTableWidgetItem(status)
            if status == "RUNNING":
                status_item.setForeground(QColor("#10b981"))
            elif status == "FAILED":
                status_item.setForeground(QColor("#ef4444"))
            else:
                status_item.setForeground(QColor("#94a3b8"))
            self.workflows_table.setItem(row, 2, status_item)

            self.workflows_table.setItem(row, 3, QTableWidgetItem(last_active))

        return widget

    def create_library_tab(self) -> QWidget:
        """Create tool library tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Library:")
        search_label.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif;")
        search_layout.addWidget(search_label)

        self.library_search = QLineEdit()
        self.library_search.setPlaceholderText("Type to filter (e.g., 'osint')")
        self.library_search.textChanged.connect(self.filter_library)
        search_layout.addWidget(self.library_search)
        layout.addLayout(search_layout)

        # Library table
        self.library_table = QTableWidget()
        self.library_table.setColumnCount(4)
        self.library_table.setHorizontalHeaderLabels(["Command", "Description", "Category", "Date"])
        self.library_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.library_table)

        # Buttons
        button_layout = QHBoxLayout()
        launch_btn = QPushButton("🚀 Launch Selected")
        launch_btn.clicked.connect(self.launch_library_tool)
        button_layout.addWidget(launch_btn)

        add_btn = QPushButton("📝 Add New Script")
        button_layout.addWidget(add_btn)
        layout.addLayout(button_layout)

        # Populate library
        self.populate_library()

        return widget

    def create_agents_tab(self) -> QWidget:
        """Create agents tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Agents table
        self.agents_table = QTableWidget()
        self.agents_table.setColumnCount(4)
        self.agents_table.setHorizontalHeaderLabels(["Agent Name", "Status", "Tasks Completed", "Success Rate"])
        self.agents_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.agents_table)

        return widget

    def populate_library(self):
        """Populate library table"""
        self.library_table.setRowCount(len(LIBRARY_DATA))
        for row, item in enumerate(LIBRARY_DATA):
            self.library_table.setItem(row, 0, QTableWidgetItem(item["cmd"]))
            self.library_table.setItem(row, 1, QTableWidgetItem(item["desc"]))
            self.library_table.setItem(row, 2, QTableWidgetItem(item["category"]))
            self.library_table.setItem(row, 3, QTableWidgetItem(item["date"]))

    def filter_library(self, text: str):
        """Filter library table by search text"""
        for row in range(self.library_table.rowCount()):
            match = False
            for col in range(self.library_table.columnCount()):
                item = self.library_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.library_table.setRowHidden(row, not match)

    def launch_library_tool(self):
        """Launch selected library tool"""
        selected = self.library_table.currentRow()
        if selected >= 0:
            cmd = self.library_table.item(selected, 0).text()
            self.terminal1.append_log(f"Launching tool: {cmd}", "#3b82f6")
            self.statusBar().showMessage(f"🚀 Launching {cmd}...", 3000)

    def execute_terminal_command(self, terminal: TerminalWidget, agent: str):
        """Execute command from terminal input"""
        command = terminal.input_field.text().strip()
        if not command:
            return

        # Display command
        terminal.append_log(f"$ {command}", "#60a5fa")
        terminal.input_field.clear()

        # Execute via worker thread
        self.command_worker = CommandWorker(self.client, command, agent)
        self.command_worker.response_received.connect(lambda resp: self.display_command_response(terminal, resp))
        self.command_worker.start()

        # Show thinking
        terminal.append_log("Processing...", "#94a3b8")

    def display_command_response(self, terminal: TerminalWidget, response: str):
        """Display command response"""
        terminal.append_log(response, "#10b981")

    def refresh_data(self):
        """Refresh all data"""
        # Health check
        health = self.client.health_check()
        status = health.get("status", "unknown")

        if status == "healthy":
            self.system_status_label.setText("● SYSTEM ONLINE")
            self.system_status_label.setStyleSheet("""
                background: rgba(30, 41, 59, 0.8);
                padding: 10px 20px;
                border-radius: 8px;
                color: #10b981;
                border: 1px solid #10b981;
                font-weight: 700;
                font-family: 'JetBrains Mono', monospace;
            """)
        else:
            self.system_status_label.setText("● SYSTEM OFFLINE")
            self.system_status_label.setStyleSheet("""
                background: rgba(30, 41, 59, 0.8);
                padding: 10px 20px;
                border-radius: 8px;
                color: #ef4444;
                border: 1px solid #ef4444;
                font-weight: 700;
                font-family: 'JetBrains Mono', monospace;
            """)

        # Update agents table
        agents = self.client.get_agents()
        self.agents_table.setRowCount(len(agents))

        for row, agent in enumerate(agents):
            name_item = QTableWidgetItem(agent.get("name", "Unknown"))
            self.agents_table.setItem(row, 0, name_item)

            status_text = agent.get("status", "unknown").upper()
            status_item = QTableWidgetItem(f"✅ {status_text}" if status_text == "ACTIVE" else f"⏸️ {status_text}")
            if status_text == "ACTIVE":
                status_item.setForeground(QColor("#10b981"))
            else:
                status_item.setForeground(QColor("#94a3b8"))
            self.agents_table.setItem(row, 1, status_item)

            self.agents_table.setItem(row, 2, QTableWidgetItem(str(agent.get("tasks", 0))))
            self.agents_table.setItem(row, 3, QTableWidgetItem(f"{agent.get('success_rate', 0):.1f}%"))

        # Update metrics
        active_agents = sum(1 for a in agents if a.get("status") == "active")
        self.metric_agents.findChild(QLabel).setText(str(active_agents))

        self.statusBar().showMessage(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}", 3000)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Launch CESAR MCP Dashboard"""
    print("=" * 80)
    print("CESAR.ai Multi-Agent MCP Dashboard - Desktop Edition")
    print("a Terry Dellmonaco Co.")
    print("Atlas Capital Automations")
    print("=" * 80)
    print()
    print("Starting desktop application...")
    print()

    app = QApplication(sys.argv)
    app.setApplicationName("CESAR MCP Dashboard")
    app.setOrganizationName("Atlas Capital Automations")

    # Set app-wide font
    font = QFont("Inter", 10)
    app.setFont(font)

    dashboard = CESARMCPDashboard()
    dashboard.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
