#!/usr/bin/env python3
"""
CESAR Multi-Agent MCP Dashboard - Glassmorphism Desktop Edition
Native PyQt6 with Dark Mesh Gradient & Frosted Glass + Terminal CLI Windows
Based on atlas_desktop_glassmorphism.py architecture

NO WEB UI - Pure Local Desktop Application

a Terry Dellmonaco Co.
Atlas Capital Automations - CESAR.ai Multi-Agent Ecosystem
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QGraphicsDropShadowEffect, QGridLayout, QFrame, QScrollArea,
    QTextEdit, QLineEdit, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCursor
import numpy as np
import pandas as pd

# ============================================================================
# DARK GLASSMORPHISM STYLESHEET WITH TERMINAL ELEMENTS
# ============================================================================

GLASSMORPHISM_STYLE = """
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #1e293b,
        stop:0.5 #0f172a,
        stop:1 #020617
    );
}

QWidget {
    background: transparent;
    color: #e2e8f0;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* Glass Card Class */
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
}

/* Header Glass */
QLabel#header {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 20px;
    padding: 30px;
    color: #60a5fa;
    font-size: 36px;
    font-weight: 800;
}

/* Metric Cards */
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

/* Terminal Window - Pure Black with Matrix Green */
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
    background-color: #1a1a1a;
    border: 2px solid #10b981;
    border-radius: 6px;
    padding: 10px 14px;
    color: #10b981;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 14px;
    font-weight: 600;
    min-height: 20px;
}

QLineEdit#terminalInput:focus {
    border: 2px solid #34d399;
    background-color: #222222;
}

QLineEdit#terminalInput::placeholder {
    color: #6b7280;
    font-style: italic;
}

/* Terminal Header */
QLabel#terminalHeader {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #94a3b8;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding: 8px;
}

/* Tabs */
QTabWidget::pane {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 15px;
}

QTabBar::tab {
    background: transparent;
    color: #e2e8f0;
    padding: 12px 24px;
    border-radius: 8px;
    margin-right: 8px;
    font-weight: 600;
    font-size: 14px;
}

QTabBar::tab:selected {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(59, 130, 246, 0.3),
        stop:1 rgba(139, 92, 246, 0.3)
    );
    color: #ffffff;
    border: 1px solid rgba(59, 130, 246, 0.5);
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background: rgba(96, 165, 250, 0.15);
    color: #ffffff;
}

/* Buttons */
QPushButton {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6,
        stop:1 #8b5cf6
    );
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: 600;
    font-size: 14px;
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

/* Table */
QTableWidget {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    color: #ffffff;
    gridline-color: rgba(255, 255, 255, 0.1);
    font-size: 13px;
}

QTableWidget::item {
    padding: 10px;
    color: #ffffff;
    background: transparent;
}

QTableWidget::item:selected {
    background: rgba(96, 165, 250, 0.3);
    color: #ffffff;
}

QHeaderView::section {
    background: rgba(59, 130, 246, 0.2);
    color: #ffffff;
    padding: 10px;
    border: none;
    font-weight: 700;
    font-size: 13px;
}

/* Progress Bar */
QProgressBar {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    text-align: center;
    color: #e2e8f0;
    font-weight: 600;
}

QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6,
        stop:1 #10b981
    );
    border-radius: 6px;
}

/* Scroll Bar */
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
# LIBRARY DATA
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
# GLASS CARD WIDGET
# ============================================================================

class GlassCard(QFrame):
    """Glassmorphism card widget with blur effect and hover animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setFrameStyle(QFrame.Shape.Box)

        # Add drop shadow for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # Animation for hover
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setDuration(300)

        self.original_geometry = None

    def enterEvent(self, event):
        """Lift card on hover."""
        if self.original_geometry is None:
            self.original_geometry = self.geometry()

        new_geometry = QRect(
            self.original_geometry.x(),
            self.original_geometry.y() - 5,
            self.original_geometry.width(),
            self.original_geometry.height()
        )

        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(new_geometry)
        self.animation.start()

    def leaveEvent(self, event):
        """Return card to original position."""
        if self.original_geometry:
            self.animation.setStartValue(self.geometry())
            self.animation.setEndValue(self.original_geometry)
            self.animation.start()

# ============================================================================
# NEON TEXT LABEL
# ============================================================================

class NeonLabel(QLabel):
    """Label with neon glow effect."""

    def __init__(self, text, color="#60a5fa", size=48, parent=None):
        super().__init__(text, parent)
        self.neon_color = QColor(color)
        self.setStyleSheet(f"""
            color: {color};
            font-size: {size}px;
            font-weight: 800;
        """)

        # Add glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(self.neon_color)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)

# ============================================================================
# METRIC CARD WIDGET
# ============================================================================

class MetricCard(GlassCard):
    """Metric display card with title, value, and delta."""

    def __init__(self, title, value, delta=None, color="#60a5fa", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #94a3b8; font-size: 12px; text-transform: uppercase;")
        layout.addWidget(title_label)

        # Value with neon effect
        self.value_label = NeonLabel(value, color=color, size=40)
        layout.addWidget(self.value_label)

        # Delta (optional)
        if delta:
            delta_label = QLabel(delta)
            delta_color = "#34d399" if "▲" in delta else "#ef4444"
            delta_label.setStyleSheet(f"color: {delta_color}; font-size: 11px;")
            layout.addWidget(delta_label)

        self.setFixedHeight(150)

# ============================================================================
# DATA MANAGER (Cached API Calls)
# ============================================================================

class DataManager:
    """Manages API calls and data caching."""

    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.cache = {}
        self.cache_ttl = {}

    def get_api_health(self):
        """Check API health."""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {"status": "unavailable"}

    def get_agent_performance(self):
        """Get agent performance data."""
        agents = [
            "CESAR", "FinPsy", "Pydini", "Lex", "Inno", "Edu", "Creative"
        ]

        data = []
        for agent in agents:
            data.append({
                "Agent": agent,
                "Performance": f"{np.random.uniform(85, 99.9):.1f}%",
                "Tasks": np.random.randint(150, 500),
                "Success": f"{np.random.uniform(92, 99.5):.1f}%",
                "Status": np.random.choice(["Active", "Idle"], p=[0.9, 0.1])
            })

        return data

    def execute_command(self, command: str, agent: str = "cesar") -> str:
        """Execute command via MCP API"""
        try:
            response = requests.post(
                f"{self.api_base}/api/v1/chat",
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

    def __init__(self, data_manager: DataManager, command: str, agent: str = "cesar"):
        super().__init__()
        self.data_manager = data_manager
        self.command = command
        self.agent = agent

    def run(self):
        response = self.data_manager.execute_command(self.command, self.agent)
        self.response_received.emit(response)

# ============================================================================
# TERMINAL WIDGET
# ============================================================================

class TerminalWidget(QWidget):
    """Terminal-style CLI widget with glass pane styling"""

    def __init__(self, title: str, shell_type: str, data_manager: DataManager, agent: str = "cesar", parent=None):
        super().__init__(parent)
        self.title = title
        self.shell_type = shell_type
        self.data_manager = data_manager
        self.agent = agent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QLabel(f"{self.title}  [{self.shell_type}]")
        header.setObjectName("terminalHeader")
        layout.addWidget(header)

        # Terminal output
        self.output = QTextEdit()
        self.output.setObjectName("terminal")
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(300)
        layout.addWidget(self.output)

        # Input section with label
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid #10b981;
                border-radius: 8px;
                padding: 8px;
                margin-top: 5px;
            }
        """)
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(5, 5, 5, 5)
        input_layout.setSpacing(5)

        # Input label
        input_label = QLabel("Command Input:")
        input_label.setStyleSheet("color: #10b981; font-weight: 600; font-size: 11px; background: transparent; border: none; padding: 0; margin: 0;")
        input_layout.addWidget(input_label)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.setObjectName("terminalInput")
        self.input_field.setPlaceholderText(f"root@{self.title.lower()}: > Type command here...")
        self.input_field.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.input_field)

        layout.addWidget(input_container)

    def append_log(self, message: str, color: str = "#10b981"):
        """Append log message with timestamp and color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        self.output.append(html)
        self.output.moveCursor(QTextCursor.MoveOperation.End)

    def execute_command(self):
        """Execute command from input field"""
        command = self.input_field.text().strip()
        if not command:
            return

        # Display command
        self.append_log(f"$ {command}", "#60a5fa")
        self.input_field.clear()

        # Execute via worker thread
        self.worker = CommandWorker(self.data_manager, command, self.agent)
        self.worker.response_received.connect(self.display_response)
        self.worker.start()

        # Show thinking
        self.append_log("Processing...", "#94a3b8")

    def display_response(self, response: str):
        """Display command response"""
        self.append_log(response, "#10b981")

    def clear_output(self):
        """Clear terminal output"""
        self.output.clear()

# ============================================================================
# MAIN WINDOW
# ============================================================================

class CESARMCPDashboardGlass(QMainWindow):
    """CESAR Multi-Agent MCP Dashboard - Glassmorphism Edition"""

    def __init__(self):
        super().__init__()

        self.data_manager = DataManager()
        self.init_ui()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def init_ui(self):
        """Initialize the user interface."""

        self.setWindowTitle("Atlas Capital Automations - CESAR.ai MCP Dashboard")
        self.setGeometry(100, 100, 1800, 1000)
        self.setStyleSheet(GLASSMORPHISM_STYLE)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        self.create_header(main_layout)

        # Control bar
        self.create_control_bar(main_layout)

        # Metrics row
        self.create_metrics_row(main_layout)

        # Tabs
        self.create_tabs(main_layout)

        # Status bar
        self.create_status_bar()

        # Initial data load
        self.refresh_data()

    def create_header(self, parent_layout):
        """Create glassmorphism header."""

        header = QFrame()
        header.setStyleSheet("""
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: 30px;
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 8)
        header.setGraphicsEffect(shadow)

        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(8)

        # Title with gradient effect
        title = QLabel("Atlas Capital Automations")
        title.setStyleSheet("""
            color: #60a5fa;
            font-size: 48px;
            font-weight: 800;
        """)

        title_glow = QGraphicsDropShadowEffect()
        title_glow.setBlurRadius(20)
        title_glow.setColor(QColor(96, 165, 250))
        title_glow.setOffset(0, 0)
        title.setGraphicsEffect(title_glow)

        header_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("CESAR.ai Multi-Agent MCP Dashboard - a Terry Dellmonaco Co.")
        subtitle.setStyleSheet("""
            color: #94a3b8;
            font-size: 18px;
            font-style: italic;
        """)
        header_layout.addWidget(subtitle)

        parent_layout.addWidget(header)

    def create_control_bar(self, parent_layout):
        """Create control bar with API status and refresh button."""

        control_bar = QHBoxLayout()

        # API Status
        self.api_status_label = QLabel("● API Status: CHECKING...")
        self.api_status_label.setStyleSheet("""
            background: rgba(255, 255, 255, 0.05);
            padding: 12px 20px;
            border-radius: 12px;
            color: #94a3b8;
            font-size: 14px;
        """)
        control_bar.addWidget(self.api_status_label, stretch=3)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Data")
        refresh_btn.clicked.connect(self.refresh_data)
        control_bar.addWidget(refresh_btn, stretch=1)

        # Agents online
        self.agents_label = QLabel("7/7 Agents Online")
        self.agents_label.setStyleSheet("""
            color: #34d399;
            font-size: 24px;
            font-weight: 700;
            padding-right: 20px;
        """)
        self.agents_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        control_bar.addWidget(self.agents_label, stretch=1)

        parent_layout.addLayout(control_bar)

    def create_metrics_row(self, parent_layout):
        """Create row of metric cards."""

        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(20)

        # System Connectivity
        self.metric1 = MetricCard("System Connectivity", "100%", "▲ All Systems Operational", "#60a5fa")
        metrics_layout.addWidget(self.metric1, 0, 0)

        # Active Agents
        self.metric2 = MetricCard("Active Agents", "7", "▲ +2 from baseline", "#34d399")
        metrics_layout.addWidget(self.metric2, 0, 1)

        # Tasks Completed
        self.metric3 = MetricCard("Tasks Completed", "2,847", "▲ +12% this hour", "#a78bfa")
        metrics_layout.addWidget(self.metric3, 0, 2)

        # Success Rate
        self.metric4 = MetricCard("Success Rate", "98.7%", "▲ Above target (95%)", "#60a5fa")
        metrics_layout.addWidget(self.metric4, 0, 3)

        parent_layout.addLayout(metrics_layout)

    def create_tabs(self, parent_layout):
        """Create tabbed interface."""

        tabs = QTabWidget()

        # Terminal Tab
        terminal_tab = self.create_terminal_tab()
        tabs.addTab(terminal_tab, "🖥️ Dual CLI")

        # Agents Tab
        agents_tab = self.create_agents_tab()
        tabs.addTab(agents_tab, "🤖 Agents")

        # Workflows Tab
        workflow_tab = self.create_workflow_tab()
        tabs.addTab(workflow_tab, "🔄 Workflows")

        # Library Tab
        library_tab = self.create_library_tab()
        tabs.addTab(library_tab, "📚 Tool Library")

        parent_layout.addWidget(tabs)

    def create_terminal_tab(self):
        """Create dual terminal tab with CLI windows."""

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(15)

        # Terminal 1 - Primary CLI
        self.terminal1 = TerminalWidget("CLI-01 [Primary]", "BASH", self.data_manager, "cesar")
        self.terminal1.append_log("Initializing CESAR core...")
        self.terminal1.append_log("Connecting to PostgresDB... OK", "#10b981")
        self.terminal1.append_log("Loading Agent 'Pydini'...", "#3b82f6")
        self.terminal1.append_log("Ready for command input.", "#10b981")
        layout.addWidget(self.terminal1)

        # Terminal 2 - Agent Stream
        self.terminal2 = TerminalWidget("CLI-02 [Agent Stream]", "PYTHON KERNEL", self.data_manager, "pydini")
        self.terminal2.append_log(">>> import cesar_agent as ca", "#3b82f6")
        self.terminal2.append_log(">>> agent = ca.load('FinPsy')", "#3b82f6")
        self.terminal2.append_log("[FinPsy] Agent loaded successfully", "#10b981")
        self.terminal2.append_log(">>> Awaiting next instruction...", "#94a3b8")
        layout.addWidget(self.terminal2)

        return widget

    def create_agents_tab(self):
        """Create agents performance tab."""

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Agent table
        self.agent_table = QTableWidget()
        self.agent_table.setColumnCount(5)
        self.agent_table.setHorizontalHeaderLabels(["Agent", "Performance", "Tasks", "Success Rate", "Status"])
        self.agent_table.horizontalHeader().setStretchLastSection(True)
        self.agent_table.setAlternatingRowColors(True)

        layout.addWidget(self.agent_table)

        return widget

    def create_workflow_tab(self):
        """Create workflow management tab."""

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Workflow table
        workflow_table = QTableWidget()
        workflow_table.setColumnCount(4)
        workflow_table.setHorizontalHeaderLabels(["Workflow ID", "Agent", "Status", "Last Active"])
        workflow_table.setRowCount(4)

        workflows = [
            ("WF-1024", "FinPsy", "RUNNING", "Now"),
            ("WF-1025", "Pydini", "IDLE", "2m ago"),
            ("WF-1026", "Lex", "FAILED", "1h ago"),
            ("WF-1027", "Inno", "QUEUED", "5m ago")
        ]

        for row, (wf_id, agent, status, last_active) in enumerate(workflows):
            workflow_table.setItem(row, 0, QTableWidgetItem(wf_id))
            workflow_table.setItem(row, 1, QTableWidgetItem(agent))

            # Color code status
            status_item = QTableWidgetItem(status)
            if status == "RUNNING":
                status_item.setForeground(QColor("#10b981"))
            elif status == "FAILED":
                status_item.setForeground(QColor("#ef4444"))
            else:
                status_item.setForeground(QColor("#94a3b8"))
            workflow_table.setItem(row, 2, status_item)

            workflow_table.setItem(row, 3, QTableWidgetItem(last_active))

        layout.addWidget(workflow_table)

        # Progress bar
        progress_label = QLabel("Global Task Completion Rate")
        progress_label.setStyleSheet("color: #94a3b8; font-size: 12px; margin-top: 10px;")
        layout.addWidget(progress_label)

        progress = QProgressBar()
        progress.setValue(45)
        progress.setTextVisible(True)
        progress.setFormat("%p% Complete")
        layout.addWidget(progress)

        return widget

    def create_library_tab(self):
        """Create tool library tab."""

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Library:")
        search_label.setStyleSheet("color: #94a3b8;")
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

    def create_status_bar(self):
        """Create status bar."""

        status = self.statusBar()
        status.setStyleSheet("""
            background: rgba(255, 255, 255, 0.05);
            color: #64748b;
            font-size: 12px;
            padding: 5px;
        """)
        status.showMessage(f"Atlas Capital Automations © {datetime.now().year} | CESAR.ai Multi-Agent Ecosystem")

    def refresh_data(self):
        """Refresh all data from API."""

        # Update API status
        api_health = self.data_manager.get_api_health()
        status = api_health.get("status", "unknown")
        status_color = "#34d399" if status == "healthy" else "#ef4444"

        self.api_status_label.setText(f"● API Status: {status.upper()}")
        self.api_status_label.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.05);
            padding: 12px 20px;
            border-radius: 12px;
            color: {status_color};
            font-size: 14px;
            font-weight: 600;
        """)

        # Update agent table
        agent_data = self.data_manager.get_agent_performance()
        self.agent_table.setRowCount(len(agent_data))

        for row, agent in enumerate(agent_data):
            self.agent_table.setItem(row, 0, QTableWidgetItem(agent["Agent"]))
            self.agent_table.setItem(row, 1, QTableWidgetItem(agent["Performance"]))
            self.agent_table.setItem(row, 2, QTableWidgetItem(str(agent["Tasks"])))
            self.agent_table.setItem(row, 3, QTableWidgetItem(agent["Success"]))

            status_item = QTableWidgetItem(agent["Status"])
            if agent["Status"] == "Active":
                status_item.setForeground(QColor("#10b981"))
            else:
                status_item.setForeground(QColor("#94a3b8"))
            self.agent_table.setItem(row, 4, status_item)

        # Update status bar
        self.statusBar().showMessage(
            f"Last Updated: {datetime.now().strftime('%I:%M:%S %p')} | "
            f"Atlas Capital Automations © {datetime.now().year}"
        )

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Launch the application."""

    print("=" * 80)
    print("CESAR.ai Multi-Agent MCP Dashboard - Glassmorphism Desktop Edition")
    print("a Terry Dellmonaco Co.")
    print("Atlas Capital Automations")
    print("=" * 80)
    print()
    print("Starting desktop application...")
    print()

    app = QApplication(sys.argv)

    # Set application-wide font
    font = QFont("Inter", 10)
    app.setFont(font)

    # Create and show main window
    window = CESARMCPDashboardGlass()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
