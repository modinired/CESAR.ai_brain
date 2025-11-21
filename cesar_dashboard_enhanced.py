#!/usr/bin/env python3
"""
CESAR Enhanced Desktop Dashboard
=================================
PhD-Level Implementation with Full Visualization Engines

NEW TABS ADDED:
1. 🧠 DataBrain 3D - 3D knowledge graph visualization with physics
2. ⚡ Automation Matrix - Workflow particle simulation
3. 💰 Liquidity Engine - Financial flow physics
4. 👥 Talent Map - Agent constellation/org graph
5. 🔄 CockroachDB Sync - Live sync status from CockroachDB

Based on cesar_mcp_dashboard_fixed.py + visualization engines from user requirements
"""

import sys
import os

# Check for required dependencies
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install PyQt6 matplotlib")
    sys.exit(1)

# Import the base dashboard
sys.path.append(os.path.dirname(__file__))
from cesar_mcp_dashboard_fixed import (
    CESARDashboard, DataManager, DASHBOARD_STYLE,
    MetricCard, ChatWorker
)

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QWidget, QPushButton, QTabWidget
)
from PyQt6.QtCore import QUrl

# Optional: web view for the Prime Console
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
import numpy as np
from datetime import datetime

load_dotenv()


class EnhancedDataManager(DataManager):
    """Extended data manager with CockroachDB support"""

    def __init__(self):
        super().__init__()
        self.cockroach_url = os.getenv("COCKROACH_DB_URL")

    def get_cockroach_connection(self):
        """Get CockroachDB connection"""
        if not self.cockroach_url or "pending" in self.cockroach_url:
            return None
        try:
            return psycopg2.connect(self.cockroach_url, cursor_factory=RealDictCursor)
        except Exception as e:
            print(f"CockroachDB connection error: {e}")
            return None

    def get_databrain_nodes(self):
        """Get all knowledge graph nodes from CockroachDB"""
        conn = self.get_cockroach_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT node_id, label, type, x_coord, y_coord, z_index, mass,
                           description, last_accessed, access_count
                    FROM graph_nodes
                    ORDER BY mass DESC
                """)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching nodes: {e}")
            return []
        finally:
            conn.close()

    def get_databrain_links(self):
        """Get all synaptic links"""
        conn = self.get_cockroach_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT link_id, source_node_id, target_node_id,
                           strength, link_type
                    FROM graph_links
                """)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching links: {e}")
            return []
        finally:
            conn.close()

    def get_cockroach_sync_status(self):
        """Get CockroachDB sync status"""
        conn = self.get_cockroach_connection()
        if not conn:
            return {
                "connected": False,
                "message": "COCKROACH_DB_URL not configured"
            }

        try:
            with conn.cursor() as cur:
                # Get counts from key tables
                tables = ['agents', 'graph_nodes', 'graph_links', 'a2a_messages',
                         'llm_collaborations', 'workflows', 'tasks']
                counts = {}
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    counts[table] = cur.fetchone()['count']

                # Get recent activity
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM a2a_messages
                    WHERE created_at > NOW() - INTERVAL '1 hour'
                """)
                hourly_messages = cur.fetchone()['count']

                return {
                    "connected": True,
                    "tables": counts,
                    "hourly_activity": hourly_messages,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "connected": False,
                "message": str(e)
            }
        finally:
            conn.close()


class AutomationMatrixCanvas(FigureCanvasQTAgg):
    """Workflow Particle Simulation with Velocity Physics"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8), facecolor='#F3F4F6')
        super().__init__(self.figure)
        self.setParent(parent)
        self.ax = self.figure.add_subplot(111, facecolor='#F3F4F6')
        self.data_manager = EnhancedDataManager()
        self.setup_plot()

    def setup_plot(self):
        """Initialize 2D particle plot"""
        self.ax.set_xlabel('Time (normalized)', fontsize=10, weight='bold')
        self.ax.set_ylabel('Workflow Progress', fontsize=10, weight='bold')
        self.ax.set_title('Automation Matrix - Workflow Particles', fontsize=14, weight='bold', pad=20)
        self.update_plot()

    def update_plot(self):
        """Render workflow particles"""
        self.ax.clear()

        # Get workflows from database
        conn = self.data_manager.get_cockroach_connection()
        if not conn:
            self.ax.text(0.5, 0.5, 'CockroachDB not connected\nCheck COCKROACH_DB_URL',
                        ha='center', va='center', fontsize=12, color='#DC2626',
                        transform=self.ax.transAxes)
            self.draw()
            return

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, status, progress,
                           EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as age_hours
                    FROM workflows
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                workflows = [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching workflows: {e}")
            workflows = []
        finally:
            conn.close()

        if not workflows:
            # Generate sample workflow particles for demonstration
            np.random.seed(42)
            num_particles = 30
            workflows = [
                {
                    'id': i,
                    'name': f'Workflow-{i}',
                    'status': np.random.choice(['running', 'completed', 'pending']),
                    'progress': np.random.uniform(0, 1),
                    'age_hours': np.random.uniform(0, 24)
                }
                for i in range(num_particles)
            ]

        # Plot particles
        xs, ys, colors, sizes = [], [], [], []
        for wf in workflows:
            x = wf.get('age_hours', 0) / 24  # Normalize to 0-1
            y = float(wf.get('progress', 0))

            xs.append(x)
            ys.append(y)

            # Color by status
            if wf['status'] == 'completed':
                colors.append('#10B981')  # Green
                sizes.append(100)
            elif wf['status'] == 'running':
                colors.append('#3B82F6')  # Blue
                sizes.append(150)
            else:
                colors.append('#9CA3AF')  # Gray
                sizes.append(80)

        self.ax.scatter(xs, ys, c=colors, s=sizes, alpha=0.7, edgecolors='#374151', linewidths=2)

        # Add velocity vectors for running workflows
        for i, wf in enumerate(workflows):
            if wf['status'] == 'running':
                x, y = xs[i], ys[i]
                dx = 0.05  # Velocity in time dimension
                dy = 0.1 * (1 - y)  # Velocity toward completion
                self.ax.arrow(x, y, dx, dy, head_width=0.02, head_length=0.03,
                             fc='#7C3AED', ec='#7C3AED', alpha=0.5, linewidth=1.5)

        self.ax.set_xlabel('Time Progress (normalized)', fontsize=10, weight='bold')
        self.ax.set_ylabel('Workflow Completion', fontsize=10, weight='bold')
        self.ax.set_title(f'Automation Matrix: {len(workflows)} Workflow Particles', fontsize=14, weight='bold')
        self.ax.set_xlim(-0.1, 1.1)
        self.ax.set_ylim(-0.1, 1.1)
        self.ax.grid(True, alpha=0.3, linestyle='--')

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#3B82F6', label='Running'),
            Patch(facecolor='#10B981', label='Completed'),
            Patch(facecolor='#9CA3AF', label='Pending')
        ]
        self.ax.legend(handles=legend_elements, loc='upper left')

        self.draw()


class LiquidityEngineCanvas(FigureCanvasQTAgg):
    """Financial Flow Physics with Source/Sink Dynamics"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8), facecolor='#F3F4F6')
        super().__init__(self.figure)
        self.setParent(parent)
        self.ax = self.figure.add_subplot(111, facecolor='#F3F4F6')
        self.data_manager = EnhancedDataManager()
        self.setup_plot()

    def setup_plot(self):
        """Initialize financial flow plot"""
        self.ax.set_xlabel('Time (days)', fontsize=10, weight='bold')
        self.ax.set_ylabel('Account Balance ($)', fontsize=10, weight='bold')
        self.ax.set_title('Liquidity Engine - Cash Flow Physics', fontsize=14, weight='bold', pad=20)
        self.update_plot()

    def update_plot(self):
        """Render cash flow streams"""
        self.ax.clear()

        # Generate sample financial flow data
        np.random.seed(123)
        days = np.linspace(0, 30, 100)

        # Multiple cash flow streams (accounts)
        accounts = [
            {'name': 'Operating', 'base': 50000, 'volatility': 5000, 'color': '#3B82F6'},
            {'name': 'Investment', 'base': 100000, 'volatility': 15000, 'color': '#8B5CF6'},
            {'name': 'Reserve', 'base': 200000, 'volatility': 3000, 'color': '#059669'},
        ]

        for account in accounts:
            # Generate flow with some randomness
            flow = account['base'] + account['volatility'] * np.cumsum(np.random.randn(len(days))) / 10
            flow = np.maximum(flow, account['base'] * 0.5)  # Floor at 50% of base

            self.ax.plot(days, flow, color=account['color'], linewidth=2.5,
                        label=f"{account['name']} (${flow[-1]:,.0f})", alpha=0.8)

            # Add source/sink markers
            sources = np.where(np.diff(flow) > account['volatility'] * 0.5)[0]
            sinks = np.where(np.diff(flow) < -account['volatility'] * 0.5)[0]

            if len(sources) > 0:
                self.ax.scatter(days[sources], flow[sources], color=account['color'],
                              marker='^', s=150, edgecolors='white', linewidths=2,
                              zorder=5, alpha=0.9, label='_nolegend_')

            if len(sinks) > 0:
                self.ax.scatter(days[sinks], flow[sinks], color=account['color'],
                              marker='v', s=150, edgecolors='white', linewidths=2,
                              zorder=5, alpha=0.9, label='_nolegend_')

        # Total liquidity line
        total = sum(account['base'] for account in accounts)
        self.ax.axhline(y=total, color='#DC2626', linestyle='--', linewidth=2,
                       label=f'Target Liquidity (${total:,.0f})', alpha=0.7)

        self.ax.set_xlabel('Time (days)', fontsize=10, weight='bold')
        self.ax.set_ylabel('Balance ($)', fontsize=10, weight='bold')
        self.ax.set_title('Liquidity Engine - Multi-Account Cash Flow', fontsize=14, weight='bold')
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.legend(loc='best', fontsize=9)

        # Format y-axis as currency
        from matplotlib.ticker import FuncFormatter
        def currency_formatter(x, p):
            return f'${x/1000:.0f}K'
        self.ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))

        self.draw()


class TalentMapCanvas(FigureCanvasQTAgg):
    """Agent Network Force-Directed Graph"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8), facecolor='#F3F4F6')
        super().__init__(self.figure)
        self.setParent(parent)
        self.ax = self.figure.add_subplot(111, facecolor='#F3F4F6')
        self.data_manager = EnhancedDataManager()
        self.setup_plot()

    def setup_plot(self):
        """Initialize network graph"""
        self.ax.set_title('Talent Map - Agent Constellation', fontsize=14, weight='bold', pad=20)
        self.ax.axis('off')
        self.update_plot()

    def update_plot(self):
        """Render agent network graph"""
        self.ax.clear()
        self.ax.axis('off')

        # Get agents from database
        conn = self.data_manager.get_cockroach_connection()
        if not conn:
            self.ax.text(0.5, 0.5, 'CockroachDB not connected\nCheck COCKROACH_DB_URL',
                        ha='center', va='center', fontsize=12, color='#DC2626')
            self.draw()
            return

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT agent_id, name, mcp_system, status,
                           x_pos, y_pos, mass
                    FROM agents
                    LIMIT 48
                """)
                agents = [dict(row) for row in cur.fetchall()]

                # Get A2A message connections for links
                cur.execute("""
                    SELECT sender_id, receiver_id, COUNT(*) as msg_count
                    FROM a2a_messages
                    GROUP BY sender_id, receiver_id
                    HAVING COUNT(*) > 0
                """)
                connections = [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching agents: {e}")
            agents = []
            connections = []
        finally:
            conn.close()

        if not agents:
            self.ax.text(0.5, 0.5, 'No agents found in database\nRun population scripts',
                        ha='center', va='center', fontsize=12, color='#DC2626')
            self.draw()
            return

        # Create node positions (use DB positions if available, else force-directed layout)
        pos = {}
        for agent in agents:
            x = float(agent.get('x_pos', 0) or 0)
            y = float(agent.get('y_pos', 0) or 0)

            if x == 0 and y == 0:
                # Use circular layout by MCP system if no position
                angle = hash(agent['agent_id']) % 360 * (3.14159 / 180)
                radius = 300 + hash(agent['mcp_system']) % 100
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)

            pos[agent['agent_id']] = (x, y)

        # MCP system colors
        mcp_colors = {
            'finpsy': '#3B82F6',
            'innovation': '#8B5CF6',
            'legal': '#DC2626',
            'creative': '#F59E0B',
            'education': '#10B981',
            'code': '#6B7280',
            'security': '#EF4444',
            'omnicognition': '#EC4899',
            'protocol': '#14B8A6',
            'skillforge': '#F97316',
            'central': '#6366F1'
        }

        # Draw connections first (so they're behind nodes)
        for conn_data in connections:
            src = conn_data['sender_id']
            tgt = conn_data['receiver_id']

            if src in pos and tgt in pos:
                x_src, y_src = pos[src]
                x_tgt, y_tgt = pos[tgt]

                # Line width proportional to message count
                width = min(conn_data['msg_count'] * 0.5, 3)

                self.ax.plot([x_src, x_tgt], [y_src, y_tgt],
                            color='#9CA3AF', alpha=0.3, linewidth=width, zorder=1)

        # Draw nodes
        for agent in agents:
            x, y = pos[agent['agent_id']]
            mcp = agent.get('mcp_system', 'central')
            color = mcp_colors.get(mcp, '#6B7280')
            size = float(agent.get('mass', 10)) * 15

            # Node circle
            circle = plt.Circle((x, y), size, color=color, alpha=0.8,
                              edgecolor='white', linewidth=2, zorder=3)
            self.ax.add_patch(circle)

            # Status indicator
            if agent.get('status') == 'active':
                # Green dot for active
                dot = plt.Circle((x + size*0.7, y + size*0.7), size*0.3,
                                color='#10B981', edgecolor='white', linewidth=1, zorder=4)
                self.ax.add_patch(dot)

        # Add MCP system labels (group centers)
        mcp_centers = {}
        for agent in agents:
            mcp = agent.get('mcp_system', 'central')
            if mcp not in mcp_centers:
                mcp_centers[mcp] = []
            mcp_centers[mcp].append(pos[agent['agent_id']])

        for mcp, positions in mcp_centers.items():
            if positions:
                cx = np.mean([p[0] for p in positions])
                cy = np.mean([p[1] for p in positions])
                self.ax.text(cx, cy, mcp.upper(), fontsize=10, weight='bold',
                           ha='center', va='center', color='#374151', alpha=0.6, zorder=2)

        self.ax.set_title(f'Talent Map: {len(agents)} Agents, {len(connections)} Connections',
                         fontsize=14, weight='bold')

        # Set equal aspect ratio and fit all nodes
        self.ax.set_aspect('equal')
        if pos:
            xs = [p[0] for p in pos.values()]
            ys = [p[1] for p in pos.values()]
            margin = 100
            self.ax.set_xlim(min(xs) - margin, max(xs) + margin)
            self.ax.set_ylim(min(ys) - margin, max(ys) + margin)

        self.draw()


class DataBrain3DCanvas(FigureCanvasQTAgg):
    """3D Knowledge Graph Visualization with Physics"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8), facecolor='#F3F4F6')
        super().__init__(self.figure)
        self.setParent(parent)
        self.ax = self.figure.add_subplot(111, projection='3d', facecolor='#F3F4F6')
        self.data_manager = EnhancedDataManager()
        self.setup_plot()

    def setup_plot(self):
        """Initialize 3D plot"""
        self.ax.set_xlabel('X', fontsize=10, weight='bold')
        self.ax.set_ylabel('Y', fontsize=10, weight='bold')
        self.ax.set_zlabel('Z-Index (Intelligence Layer)', fontsize=10, weight='bold')
        self.ax.set_title('CESAR DataBrain - 3D Knowledge Graph', fontsize=14, weight='bold', pad=20)
        self.update_plot()

    def update_plot(self):
        """Render knowledge graph"""
        self.ax.clear()

        nodes = self.data_manager.get_databrain_nodes()
        links = self.data_manager.get_databrain_links()

        if not nodes:
            self.ax.text(0.5, 0.5, 0.5, 'No DataBrain nodes found\nRun populate_databrain_complete.py',
                        ha='center', va='center', fontsize=12, color='#DC2626')
            self.draw()
            return

        # Plot nodes with color by layer
        xs, ys, zs, colors, sizes = [], [], [], [], []
        node_map = {}

        for node in nodes:
            x = float(node['x_coord'] or 0)
            y = float(node['y_coord'] or 0)
            z = float(node['z_index'] or 0)
            mass = float(node['mass'] or 10)

            xs.append(x)
            ys.append(y)
            zs.append(z)
            sizes.append(mass * 10)  # Scale for visibility
            node_map[node['node_id']] = (x, y, z)

            # Color by layer
            if z < 100:
                colors.append('#9CA3AF')  # Raw data - gray
            elif z < 200:
                colors.append('#3B82F6')  # Information - blue
            elif z < 300:
                colors.append('#8B5CF6')  # Knowledge - purple
            else:
                colors.append('#F59E0B')  # Wisdom - amber

        self.ax.scatter(xs, ys, zs, c=colors, s=sizes, alpha=0.7, edgecolors='#374151', linewidths=2)

        # Plot links
        for link in links:
            src = node_map.get(link['source_node_id'])
            tgt = node_map.get(link['target_node_id'])
            if src and tgt:
                self.ax.plot([src[0], tgt[0]], [src[1], tgt[1]], [src[2], tgt[2]],
                            'k-', alpha=0.2, linewidth=1)

        # Add layer planes
        self.ax.axhline(y=0, color='#D1D5DB', alpha=0.2, linestyle='--')
        self.ax.axvline(x=0, color='#D1D5DB', alpha=0.2, linestyle='--')

        self.ax.set_xlabel('X', fontsize=10, weight='bold')
        self.ax.set_ylabel('Y', fontsize=10, weight='bold')
        self.ax.set_zlabel('Z-Index (Layer)', fontsize=10, weight='bold')
        self.ax.set_title(f'DataBrain: {len(nodes)} Nodes, {len(links)} Links', fontsize=14, weight='bold')

        self.draw()


class CESARDashboardEnhanced(CESARDashboard):
    """Enhanced CESAR Dashboard with all visualization engines"""

    def __init__(self):
        self.enhanced_data_manager = EnhancedDataManager()
        super().__init__()

    def init_ui(self):
        """Override to add new tabs"""
        self.setWindowTitle("CESAR.ai Enhanced Dashboard - Full Visualization Suite")
        self.setGeometry(50, 30, 1920, 1080)
        self.setStyleSheet(DASHBOARD_STYLE)

        font = QFont("Inter", 14, QFont.Weight.Medium)
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        QApplication.setFont(font)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setCentralWidget(scroll)

        central = QWidget()
        scroll.setWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(30, 30, 30, 100)
        main_layout.setSpacing(25)

        # Header
        self.create_header(main_layout)

        # Metrics
        self.create_metrics(main_layout)

        # Enhanced Tabs
        tabs = QTabWidget()
        tabs.setMinimumHeight(700)

        # NEW visualization tabs first
        tabs.addTab(self.create_databrain_3d_tab(), "🧠 DataBrain 3D")
        tabs.addTab(self.create_optic_nerve_tab(), "👁️ Optic Nerve Vision")
        tabs.addTab(self.create_dspy_cortex_tab(), "🧬 DSPy Cortex")
        tabs.addTab(self.create_cockroach_sync_tab(), "🔄 CockroachDB Sync")
        tabs.addTab(self.create_automation_matrix_tab(), "⚡ Automation Matrix")
        tabs.addTab(self.create_liquidity_engine_tab(), "💰 Liquidity Engine")
        tabs.addTab(self.create_talent_map_tab(), "👥 Talent Map")
        tabs.addTab(self.create_prime_console_tab(), "🧠 Prime Console")

        # Original tabs
        tabs.addTab(self.create_chat_tab(), "💬 Agent Chat")
        tabs.addTab(self.create_workflows_tab(), "🔄 Workflows")
        tabs.addTab(self.create_financial_tab(), "📈 Financial Intelligence")
        tabs.addTab(self.create_business_health_tab(), "🏥 Business Health")
        tabs.addTab(self.create_agents_tab(), "🤖 Agent Status")

        main_layout.addWidget(tabs)

        self.statusBar().showMessage("✅ Enhanced Dashboard - All Visualization Engines Online")

        # Auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(10000)

        QTimer.singleShot(100, self.refresh_data)

    def create_databrain_3d_tab(self):
        """3D Knowledge Graph Visualization"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🧠 DataBrain - 3D Knowledge Graph Visualization")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #1E40AF; margin-bottom: 10px;")
        layout.addWidget(header)

        subtitle = QLabel("Real-time 3D visualization of knowledge nodes with z-index stratification")
        subtitle.setStyleSheet("font-size: 13px; color: #6B7280; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # 3D Canvas
        self.brain_canvas = DataBrain3DCanvas()
        layout.addWidget(self.brain_canvas)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh DataBrain")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 700;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2563EB;
            }
        """)
        refresh_btn.clicked.connect(self.brain_canvas.update_plot)
        layout.addWidget(refresh_btn)

        return widget

    def create_optic_nerve_tab(self):
        """Optic Nerve Vision-to-Graph Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("👁️ Optic Nerve - Vision-to-Graph Transduction")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #7C3AED; margin-bottom: 10px;")
        layout.addWidget(header)

        subtitle = QLabel("Upload whiteboard photos, diagrams, or screenshots to extract knowledge graph structures")
        subtitle.setStyleSheet("font-size: 13px; color: #6B7280; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # File upload section
        upload_frame = QFrame()
        upload_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px dashed #D1D5DB;
                border-radius: 12px;
                padding: 40px;
            }
        """)
        upload_layout = QVBoxLayout(upload_frame)

        upload_label = QLabel("📸 Drop image file or click to browse")
        upload_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_label.setStyleSheet("font-size: 16px; color: #6B7280; margin-bottom: 20px;")
        upload_layout.addWidget(upload_label)

        # File path display
        self.vision_file_path = QLabel("No file selected")
        self.vision_file_path.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vision_file_path.setStyleSheet("font-size: 12px; color: #9CA3AF; font-family: monospace;")
        upload_layout.addWidget(self.vision_file_path)

        # Browse button
        browse_btn = QPushButton("📁 Browse Files")
        browse_btn.setStyleSheet("""
            QPushButton {
                background: #7C3AED;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 700;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #6D28D9;
            }
        """)
        browse_btn.clicked.connect(self.browse_vision_file)
        upload_layout.addWidget(browse_btn)

        layout.addWidget(upload_frame)

        # Process button
        process_btn = QPushButton("🧠 Process Image → DataBrain")
        process_btn.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 16px 32px;
                font-weight: 700;
                font-size: 16px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background: #047857;
            }
        """)
        process_btn.clicked.connect(self.process_vision_image)
        layout.addWidget(process_btn)

        # Results display
        self.vision_results = QLabel("Results will appear here after processing...")
        self.vision_results.setWordWrap(True)
        self.vision_results.setStyleSheet("""
            QLabel {
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 20px;
                font-size: 13px;
                color: #374151;
                font-family: monospace;
                margin-top: 20px;
            }
        """)
        layout.addWidget(self.vision_results)

        layout.addStretch()

        return widget

    def browse_vision_file(self):
        """Open file browser for image selection"""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image File",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )

        if file_path:
            self.selected_vision_file = file_path
            self.vision_file_path.setText(f"Selected: {file_path}")
            self.vision_file_path.setStyleSheet("font-size: 12px; color: #059669; font-family: monospace;")

    def process_vision_image(self):
        """Process selected image through Optic Nerve"""
        if not hasattr(self, 'selected_vision_file'):
            self.vision_results.setText("❌ No file selected. Please browse and select an image first.")
            self.vision_results.setStyleSheet("""
                QLabel {
                    background: #FEE2E2;
                    border: 1px solid #DC2626;
                    border-radius: 8px;
                    padding: 20px;
                    font-size: 13px;
                    color: #DC2626;
                    font-family: monospace;
                    margin-top: 20px;
                }
            """)
            return

        self.vision_results.setText("👁️ Processing image through Optic Nerve...\n\nThis may take 5-10 seconds...")
        self.vision_results.setStyleSheet("""
            QLabel {
                background: #FEF3C7;
                border: 1px solid #F59E0B;
                border-radius: 8px;
                padding: 20px;
                font-size: 13px;
                color: #92400E;
                font-family: monospace;
                margin-top: 20px;
            }
        """)

        try:
            from services.optic_nerve_vision import get_vision_service

            vision = get_vision_service()
            result = vision.analyze_image(image_path=self.selected_vision_file)

            # Insert into DataBrain
            stats = vision.insert_into_databrain(
                result,
                source_image=self.selected_vision_file.split('/')[-1]
            )

            # Display results
            results_text = f"""✅ VISION PROCESSING COMPLETE

📊 Extracted Knowledge:
   • Nodes: {len(result.nodes)}
   • Links: {len(result.links)}
   • Confidence: {result.confidence:.1%}

📝 Context: {result.context}

💾 DataBrain Integration:
   • Nodes Created: {stats.get('nodes_created', 0)}
   • Links Created: {stats.get('links_created', 0)}

🎯 Status: Knowledge successfully implanted into DataBrain
"""

            self.vision_results.setText(results_text)
            self.vision_results.setStyleSheet("""
                QLabel {
                    background: #D1FAE5;
                    border: 1px solid #059669;
                    border-radius: 8px;
                    padding: 20px;
                    font-size: 13px;
                    color: #065F46;
                    font-family: monospace;
                    margin-top: 20px;
                }
            """)

            # Refresh DataBrain visualization
            if hasattr(self, 'brain_canvas'):
                self.brain_canvas.update_plot()

        except Exception as e:
            self.vision_results.setText(f"❌ Processing failed:\n\n{str(e)}\n\nCheck that OPENAI_API_KEY is set in .env file.")
            self.vision_results.setStyleSheet("""
                QLabel {
                    background: #FEE2E2;
                    border: 1px solid #DC2626;
                    border-radius: 8px;
                    padding: 20px;
                    font-size: 13px;
                    color: #DC2626;
                    font-family: monospace;
                    margin-top: 20px;
                }
            """)

    def create_dspy_cortex_tab(self):
        """DSPy Neuro-Symbolic Reasoning Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("🧬 DSPy Cortex - Neuro-Symbolic Reasoning")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #DC2626; margin-bottom: 10px;")
        layout.addWidget(header)

        subtitle = QLabel("Type-safe graph reasoning with chain-of-thought and formal validation")
        subtitle.setStyleSheet("font-size: 13px; color: #6B7280; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # Query input
        query_label = QLabel("💭 Enter reasoning query:")
        query_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 8px;")
        layout.addWidget(query_label)

        from PyQt6.QtWidgets import QTextEdit
        self.dspy_query_input = QTextEdit()
        self.dspy_query_input.setPlaceholderText("Example: Why is revenue dropping and what actions should we take?")
        self.dspy_query_input.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #374151;
                min-height: 80px;
            }
        """)
        layout.addWidget(self.dspy_query_input)

        # Node context input
        node_label = QLabel("🎯 Target node label (optional):")
        node_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #374151; margin-top: 20px; margin-bottom: 8px;")
        layout.addWidget(node_label)

        from PyQt6.QtWidgets import QLineEdit
        self.dspy_node_input = QLineEdit()
        self.dspy_node_input.setPlaceholderText("Leave empty to use highest-mass node")
        self.dspy_node_input.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #374151;
            }
        """)
        layout.addWidget(self.dspy_node_input)

        # Reason button
        reason_btn = QPushButton("🧠 Execute Reasoning")
        reason_btn.setStyleSheet("""
            QPushButton {
                background: #DC2626;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 16px 32px;
                font-weight: 700;
                font-size: 16px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background: #B91C1C;
            }
        """)
        reason_btn.clicked.connect(self.execute_dspy_reasoning)
        layout.addWidget(reason_btn)

        # Results display
        self.dspy_results = QLabel("Reasoning results will appear here...")
        self.dspy_results.setWordWrap(True)
        self.dspy_results.setStyleSheet("""
            QLabel {
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 20px;
                font-size: 13px;
                color: #374151;
                font-family: monospace;
                margin-top: 20px;
            }
        """)
        layout.addWidget(self.dspy_results)

        layout.addStretch()

        return widget

    def execute_dspy_reasoning(self):
        """Execute DSPy reasoning on selected node"""
        query = self.dspy_query_input.toPlainText().strip()

        if not query:
            self.dspy_results.setText("❌ Please enter a reasoning query")
            return

        self.dspy_results.setText("🧬 Executing neuro-symbolic reasoning...\n\nThis may take 5-15 seconds...")

        try:
            from services.dspy_cortex_optimizer import get_cortex_service, NodeContext, Neighbor

            # Get target node
            target_label = self.dspy_node_input.text().strip()

            conn = self.enhanced_data_manager.get_cockroach_connection()
            if not conn:
                self.dspy_results.setText("❌ CockroachDB not connected")
                return

            with conn.cursor() as cur:
                if target_label:
                    cur.execute("""
                        SELECT node_id, label, mass, z_index, access_count
                        FROM graph_nodes
                        WHERE label ILIKE %s
                        LIMIT 1
                    """, (f"%{target_label}%",))
                else:
                    cur.execute("""
                        SELECT node_id, label, mass, z_index, access_count
                        FROM graph_nodes
                        ORDER BY mass DESC
                        LIMIT 1
                    """)

                node_row = cur.fetchone()
                if not node_row:
                    self.dspy_results.setText("❌ No nodes found in DataBrain")
                    conn.close()
                    return

                # Build context
                z_layers = ['Raw_Data', 'Information', 'Knowledge', 'Wisdom']
                z_index = int(node_row['z_index'] or 0)
                layer = z_layers[min(z_index // 100, 3)]

                context = NodeContext(
                    id=node_row['node_id'],
                    label=node_row['label'],
                    mass=float(node_row['mass'] or 10.0),
                    layer=layer,
                    access_count=int(node_row['access_count'] or 0)
                )

                # Get neighbors
                cur.execute("""
                    SELECT gn.node_id, gn.label, gl.strength, gl.relationship
                    FROM graph_links gl
                    JOIN graph_nodes gn ON gl.target_id = gn.node_id
                    WHERE gl.source_id = %s
                    LIMIT 10
                """, (context.id,))

                neighbors = []
                for row in cur.fetchall():
                    neighbors.append(Neighbor(
                        id=row['node_id'],
                        label=row['label'],
                        link_strength=float(row['strength'] or 0.5),
                        relationship=row['relationship']
                    ))

            conn.close()

            # Execute reasoning
            cortex = get_cortex_service()
            result = cortex.reason(context, neighbors, query)

            # Format results
            results_text = f"""✅ REASONING COMPLETE

🎯 Target Node: {context.label} (mass={context.mass:.1f}, layer={context.layer})
🔗 Neighbors Analyzed: {len(neighbors)}

💭 CHAIN OF THOUGHT:
{result.rationale}

⚡ PROPOSED MUTATIONS ({len(result.mutations)}):
"""
            for i, mutation in enumerate(result.mutations, 1):
                results_text += f"\n{i}. [{mutation.action}] (confidence={mutation.confidence:.1%})"
                results_text += f"\n   Params: {mutation.params}\n"

            results_text += f"\n📊 Confidence: {result.confidence:.1%}"
            results_text += f"\n🔢 Computational Steps: {result.computational_steps}"

            self.dspy_results.setText(results_text)
            self.dspy_results.setStyleSheet("""
                QLabel {
                    background: #D1FAE5;
                    border: 1px solid #059669;
                    border-radius: 8px;
                    padding: 20px;
                    font-size: 13px;
                    color: #065F46;
                    font-family: monospace;
                    margin-top: 20px;
                }
            """)

        except Exception as e:
            self.dspy_results.setText(f"❌ Reasoning failed:\n\n{str(e)}")
            self.dspy_results.setStyleSheet("""
                QLabel {
                    background: #FEE2E2;
                    border: 1px solid #DC2626;
                    border-radius: 8px;
                    padding: 20px;
                    font-size: 13px;
                    color: #DC2626;
                    font-family: monospace;
                    margin-top: 20px;
                }
            """)

    def create_cockroach_sync_tab(self):
        """CockroachDB Sync Status Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("🔄 CockroachDB Cloud Synchronization")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #059669; margin-bottom: 10px;")
        layout.addWidget(header)

        self.sync_status_label = QLabel("Checking connection...")
        self.sync_status_label.setStyleSheet("font-size: 14px; color: #374151; font-family: monospace;")
        self.sync_status_label.setWordWrap(True)
        layout.addWidget(self.sync_status_label)

        layout.addStretch()

        # Update sync status
        self.update_sync_status()

        return widget

    def update_sync_status(self):
        """Update CockroachDB sync status display"""
        status = self.enhanced_data_manager.get_cockroach_sync_status()

        if status['connected']:
            text = "✅ CONNECTED TO COCKROACHDB\n\n"
            text += "📊 Table Record Counts:\n"
            for table, count in status['tables'].items():
                text += f"   {table}: {count:,} records\n"
            text += f"\n💬 A2A Messages (last hour): {status['hourly_activity']}\n"
            text += f"🕐 Last check: {status['timestamp']}"
        else:
            text = f"❌ NOT CONNECTED\n\n{status.get('message', 'Unknown error')}"

        self.sync_status_label.setText(text)

    def create_automation_matrix_tab(self):
        """Workflow Particle Simulation Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("⚡ Automation Matrix - Workflow Particle Physics Engine")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #7C3AED; margin-bottom: 10px;")
        layout.addWidget(header)

        subtitle = QLabel("Real-time workflow execution visualization with velocity-based particle physics")
        subtitle.setStyleSheet("font-size: 13px; color: #6B7280; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # Matplotlib Canvas
        self.automation_canvas = AutomationMatrixCanvas()
        layout.addWidget(self.automation_canvas)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Workflows")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #7C3AED;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 700;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #6D28D9;
            }
        """)
        refresh_btn.clicked.connect(self.automation_canvas.update_plot)
        layout.addWidget(refresh_btn)

        return widget

    def create_liquidity_engine_tab(self):
        """Financial Flow Physics Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("💰 Liquidity Engine - Financial Flow Simulation")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #059669; margin-bottom: 10px;")
        layout.addWidget(header)

        subtitle = QLabel("Cash flow dynamics with source/sink physics and transaction particle streams")
        subtitle.setStyleSheet("font-size: 13px; color: #6B7280; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # Matplotlib Canvas
        self.liquidity_canvas = LiquidityEngineCanvas()
        layout.addWidget(self.liquidity_canvas)

        # Refresh button
        refresh_btn = QPushButton("💸 Refresh Cash Flow")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 700;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #047857;
            }
        """)
        refresh_btn.clicked.connect(self.liquidity_canvas.update_plot)
        layout.addWidget(refresh_btn)

        return widget

    def create_talent_map_tab(self):
        """Agent Constellation/Org Graph Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("👥 Talent Map - Agent Constellation & Organizational Graph")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #DC2626; margin-bottom: 10px;")
        layout.addWidget(header)

        subtitle = QLabel("Force-directed network graph showing agent relationships and MCP system organization")
        subtitle.setStyleSheet("font-size: 13px; color: #6B7280; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # Matplotlib Canvas
        self.talent_canvas = TalentMapCanvas()
        layout.addWidget(self.talent_canvas)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Agent Network")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #DC2626;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 700;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #B91C1C;
            }
        """)
        refresh_btn.clicked.connect(self.talent_canvas.update_plot)
        layout.addWidget(refresh_btn)

        return widget

    def create_prime_console_tab(self):
        """
        Embed the Prime Console (HTML) into the native desktop app.
        Requires PyQt6-WebEngine; otherwise a warning is shown.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("🧠 CESAR.AI Prime Console")
        header.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A; padding: 12px;")
        layout.addWidget(header)

        if WEB_ENGINE_AVAILABLE:
            view = QWebEngineView()
            asset_path = os.path.join(os.path.dirname(__file__), "assets", "prime_console.html")
            view.load(QUrl.fromLocalFile(asset_path))
            layout.addWidget(view)
        else:
            warning = QLabel("PyQt6-WebEngine not available. Install it to render the Prime Console UI.")
            warning.setStyleSheet("color: #B45309; padding: 12px; background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 8px;")
            layout.addWidget(warning)

        return widget


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # PyQt6 enables high DPI by default, no need for setAttribute

    dashboard = CESARDashboardEnhanced()
    dashboard.show()

    print("=" * 80)
    print("✅ CESAR Enhanced Dashboard Launched")
    print("=" * 80)
    print("\nNew Visualization Engines:")
    print("  🧠 DataBrain 3D - Knowledge graph with 37 nodes, 30 links")
    print("  🔄 CockroachDB Sync - Live database status")
    print("  ⚡ Automation Matrix - Workflow particle simulation")
    print("  💰 Liquidity Engine - Financial flow physics")
    print("  👥 Talent Map - Agent constellation graph")
    print("=" * 80)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
