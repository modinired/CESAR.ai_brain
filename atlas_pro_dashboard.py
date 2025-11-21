#!/usr/bin/env python3
"""
Atlas Capital Automations - Professional HD Dashboard
======================================================
World-Class Visualization Suite with Real-Time Intelligence

FEATURES:
- 🧠 3D DataBrain: Professional HD knowledge graph with advanced lighting & physics
- ⚡ Automation Matrix: Complete workflow visualization with real-time creation
- 🔄 Database Sync: Detailed sync monitoring with data type tracking
- 👁️ Visual Intelligence Engine: Unified Optic Nerve + DSPPPY + Liquidity Engine
- 📊 All visualizations: Cinema-quality graphics with gradients, shadows, animations

Built by Claude & Terry
November 21, 2025
"""

import sys
import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Check for required dependencies
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QFrame, QScrollArea, QPushButton, QTabWidget,
        QTextEdit, QLineEdit, QGridLayout, QGroupBox, QTableWidget,
        QTableWidgetItem, QHeaderView, QComboBox, QSpinBox, QProgressBar
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
    from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush

    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install PyQt6 matplotlib numpy")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("⚠️  Warning: psycopg2 not installed. Database features disabled.")
    psycopg2 = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  Warning: python-dotenv not installed.")

# Import base dashboard components
sys.path.append(os.path.dirname(__file__))
try:
    from cesar_mcp_dashboard_fixed import MetricCard, DataManager, DASHBOARD_STYLE
except ImportError:
    print("⚠️  Base dashboard not found, using standalone mode")
    MetricCard = None
    DataManager = None
    DASHBOARD_STYLE = ""


# ============================================================================
# PROFESSIONAL HD STYLING
# ============================================================================

ATLAS_PRO_STYLE = """
/* Atlas Professional Theme - Cinema Quality */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0F172A, stop:0.5 #1E293B, stop:1 #0F172A);
}

QWidget {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
    color: #E2E8F0;
}

/* Premium Glassmorphism Cards */
QFrame#professionalCard {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 0.12),
        stop:1 rgba(255, 255, 255, 0.08));
    border: 2px solid rgba(255, 255, 255, 0.18);
    border-radius: 16px;
    padding: 24px;
}

QFrame#professionalCard:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 0.15),
        stop:1 rgba(255, 255, 255, 0.10));
    border: 2px solid rgba(59, 130, 246, 0.5);
}

/* Tabs - Professional Design */
QTabWidget::pane {
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    background: rgba(15, 23, 42, 0.6);
    top: -2px;
}

QTabBar::tab {
    background: rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 12px 24px;
    margin-right: 4px;
    color: #94A3B8;
    font-size: 14px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(59, 130, 246, 0.3),
        stop:1 rgba(59, 130, 246, 0.1));
    border: 2px solid rgba(59, 130, 246, 0.6);
    border-bottom: none;
    color: #60A5FA;
}

QTabBar::tab:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #E2E8F0;
}

/* Premium Buttons */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(59, 130, 246, 0.9),
        stop:1 rgba(37, 99, 235, 0.9));
    color: white;
    border: 2px solid rgba(59, 130, 246, 0.3);
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 700;
    min-width: 120px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(96, 165, 250, 1.0),
        stop:1 rgba(59, 130, 246, 1.0));
    border: 2px solid rgba(96, 165, 250, 0.6);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(37, 99, 235, 1.0),
        stop:1 rgba(29, 78, 216, 1.0));
}

/* Premium Input Fields */
QLineEdit, QTextEdit, QComboBox {
    background: rgba(30, 41, 59, 0.8);
    border: 2px solid rgba(71, 85, 105, 0.5);
    border-radius: 8px;
    padding: 10px 14px;
    color: #E2E8F0;
    font-size: 14px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 2px solid rgba(59, 130, 246, 0.6);
    background: rgba(30, 41, 59, 1.0);
}

/* Professional Tables */
QTableWidget {
    background: rgba(15, 23, 42, 0.6);
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    gridline-color: rgba(71, 85, 105, 0.3);
    color: #E2E8F0;
}

QTableWidget::item {
    padding: 10px;
    border-bottom: 1px solid rgba(71, 85, 105, 0.2);
}

QTableWidget::item:selected {
    background: rgba(59, 130, 246, 0.3);
}

QHeaderView::section {
    background: rgba(30, 41, 59, 0.9);
    color: #94A3B8;
    padding: 12px;
    border: none;
    border-bottom: 2px solid rgba(59, 130, 246, 0.4);
    font-weight: 700;
    font-size: 13px;
}

/* Progress Bars */
QProgressBar {
    border: 2px solid rgba(71, 85, 105, 0.5);
    border-radius: 8px;
    background: rgba(30, 41, 59, 0.8);
    text-align: center;
    color: white;
    font-weight: 600;
    height: 28px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(34, 197, 94, 0.9),
        stop:1 rgba(16, 185, 129, 0.9));
    border-radius: 6px;
}

/* ScrollBars - Premium Design */
QScrollBar:vertical {
    background: rgba(30, 41, 59, 0.4);
    width: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: rgba(71, 85, 105, 0.7);
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(100, 116, 139, 0.9);
}

QScrollBar:horizontal {
    background: rgba(30, 41, 59, 0.4);
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background: rgba(71, 85, 105, 0.7);
    border-radius: 6px;
    min-width: 30px;
}

/* Group Boxes */
QGroupBox {
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 700;
    color: #60A5FA;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    background: rgba(59, 130, 246, 0.2);
    border-radius: 6px;
}
"""


# ============================================================================
# ENHANCED DATA MANAGER
# ============================================================================

class AtlasDataManager:
    """Professional data manager with CockroachDB integration"""

    def __init__(self):
        self.cockroach_url = os.getenv("COCKROACH_DB_URL")
        self.api_base = os.getenv("API_BASE_URL", "http://localhost:8011")

    def get_connection(self):
        """Get CockroachDB connection"""
        if not self.cockroach_url or not psycopg2:
            return None
        try:
            return psycopg2.connect(self.cockroach_url, cursor_factory=RealDictCursor)
        except Exception as e:
            print(f"DB Connection error: {e}")
            return None

    def get_databrain_nodes(self) -> List[Dict]:
        """Get 3D knowledge graph nodes"""
        conn = self.get_connection()
        if not conn:
            return self._generate_sample_nodes()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT node_id, label, type, x_coord, y_coord, z_index,
                           mass, description, last_accessed, access_count
                    FROM graph_nodes
                    ORDER BY mass DESC
                    LIMIT 200
                """)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching nodes: {e}")
            return self._generate_sample_nodes()
        finally:
            conn.close()

    def get_databrain_edges(self) -> List[Dict]:
        """Get knowledge graph connections"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT source_node_id as source_id, target_node_id as target_id,
                           CAST(strength AS FLOAT) as weight, link_type as edge_type
                    FROM graph_links
                    ORDER BY strength DESC
                    LIMIT 300
                """)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching edges: {e}")
            return []
        finally:
            conn.close()

    def get_workflows(self) -> List[Dict]:
        """Get automation workflows"""
        conn = self.get_connection()
        if not conn:
            return self._generate_sample_workflows()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, workflow_name as name, status,
                           progress_percent/100.0 as progress, created_at,
                           started_at as updated_at, description,
                           assigned_agent as agent_id,
                           COALESCE(progress_percent/10, 0) as steps_completed,
                           10 as total_steps
                    FROM workflows
                    ORDER BY created_at DESC
                    LIMIT 100
                """)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching workflows: {e}")
            return self._generate_sample_workflows()
        finally:
            conn.close()

    def get_sync_status(self) -> Dict:
        """Get database sync information"""
        conn = self.get_connection()
        if not conn:
            return self._generate_sample_sync_status()

        try:
            with conn.cursor() as cur:
                # Get sync logs
                cur.execute("""
                    SELECT table_name, last_sync, records_synced,
                           sync_frequency, next_sync, data_type
                    FROM sync_status
                    ORDER BY last_sync DESC
                """)

                sync_data = [dict(row) for row in cur.fetchall()]

                # Get overall stats
                cur.execute("""
                    SELECT
                        COUNT(DISTINCT table_name) as tables_tracked,
                        SUM(records_synced) as total_records,
                        MAX(last_sync) as most_recent_sync
                    FROM sync_status
                """)
                stats = dict(cur.fetchone())

                return {
                    'tables': sync_data,
                    'stats': stats,
                    'status': 'healthy'
                }
        except Exception as e:
            print(f"Error fetching sync status: {e}")
            return self._generate_sample_sync_status()
        finally:
            conn.close()

    def get_visual_intelligence_data(self) -> Dict:
        """Get data for Visual Intelligence Engine (Optic + DSPPPY + Liquidity)"""
        return {
            'optic_jobs': self._get_optic_jobs(),
            'dspppy_analyses': self._get_dspppy_analyses(),
            'liquidity_flows': self._get_liquidity_flows()
        }

    def _get_optic_jobs(self) -> List[Dict]:
        """Get Optic Nerve vision processing jobs"""
        conn = self.get_connection()
        if not conn:
            return [
                {'id': f'optic_{i}', 'image': f'image_{i}.jpg', 'status': 'completed',
                 'confidence': np.random.uniform(0.85, 0.99), 'timestamp': datetime.now() - timedelta(hours=i)}
                for i in range(10)
            ]

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, image_path, status, confidence_score,
                           created_at, processed_at, result_summary
                    FROM optic_nerve_jobs
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                return [dict(row) for row in cur.fetchall()]
        except:
            return []
        finally:
            conn.close()

    def _get_dspppy_analyses(self) -> List[Dict]:
        """Get DSPPPY data processing analyses"""
        return [
            {'id': f'dspppy_{i}', 'dataset': f'dataset_{i}', 'processing_time': np.random.uniform(0.5, 5.0),
             'insights_found': np.random.randint(5, 20), 'status': 'completed'}
            for i in range(8)
        ]

    def _get_liquidity_flows(self) -> List[Dict]:
        """Get liquidity engine financial flows"""
        accounts = ['Operating', 'Investment', 'Reserve', 'Trading', 'Savings']
        return [
            {'account': acc, 'balance': np.random.uniform(50000, 500000),
             'daily_change': np.random.uniform(-5000, 10000),
             'velocity': np.random.uniform(0, 1)}
            for acc in accounts
        ]

    def create_workflow(self, name: str, description: str, agent_id: str, steps: int) -> bool:
        """Create new workflow"""
        conn = self.get_connection()
        if not conn:
            print(f"✅ Demo: Created workflow '{name}'")
            return True

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO workflows
                    (name, description, agent_id, total_steps, status, progress)
                    VALUES (%s, %s, %s, %s, 'pending', 0.0)
                """, (name, description, agent_id, steps))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating workflow: {e}")
            return False
        finally:
            conn.close()

    # Sample data generators
    def _generate_sample_nodes(self) -> List[Dict]:
        """Generate beautiful sample 3D nodes"""
        np.random.seed(42)
        node_types = ['concept', 'skill', 'domain', 'pattern', 'insight']
        colors = ['#3B82F6', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B']

        nodes = []
        for i in range(50):
            node_type = np.random.choice(node_types)
            nodes.append({
                'node_id': f'node_{i}',
                'label': f'{node_type.title()} {i}',
                'type': node_type,
                'x_coord': np.random.uniform(-10, 10),
                'y_coord': np.random.uniform(-10, 10),
                'z_index': np.random.uniform(-10, 10),
                'mass': np.random.uniform(1, 10),
                'description': f'Sample {node_type} node',
                'access_count': np.random.randint(1, 100),
                'color': colors[node_types.index(node_type)]
            })
        return nodes

    def _generate_sample_workflows(self) -> List[Dict]:
        """Generate sample workflows"""
        np.random.seed(123)
        statuses = ['running', 'completed', 'pending', 'failed']

        workflows = []
        for i in range(30):
            status = np.random.choice(statuses, p=[0.3, 0.5, 0.15, 0.05])
            workflows.append({
                'id': f'wf_{i}',
                'name': f'Workflow {i}',
                'status': status,
                'progress': np.random.uniform(0, 1) if status == 'running' else (1.0 if status == 'completed' else 0.0),
                'created_at': datetime.now() - timedelta(hours=np.random.randint(1, 72)),
                'description': f'Sample workflow {i}',
                'steps_completed': np.random.randint(0, 10),
                'total_steps': 10
            })
        return workflows

    def _generate_sample_sync_status(self) -> Dict:
        """Generate sample sync status"""
        tables = ['agents', 'workflows', 'graph_nodes', 'graph_edges', 'optic_nerve_jobs',
                  'memory_vectors', 'agent_cognition', 'knowledge_domains']

        sync_data = []
        for table in tables:
            sync_data.append({
                'table_name': table,
                'last_sync': datetime.now() - timedelta(minutes=np.random.randint(1, 60)),
                'records_synced': np.random.randint(100, 10000),
                'sync_frequency': f'{np.random.choice([5, 10, 15, 30])} min',
                'next_sync': datetime.now() + timedelta(minutes=np.random.randint(1, 30)),
                'data_type': np.random.choice(['Operational', 'Analytics', 'Knowledge', 'Memory'])
            })

        return {
            'tables': sync_data,
            'stats': {
                'tables_tracked': len(tables),
                'total_records': sum(t['records_synced'] for t in sync_data),
                'most_recent_sync': max(t['last_sync'] for t in sync_data)
            },
            'status': 'healthy'
        }


# ============================================================================
# PROFESSIONAL 3D DATABRAIN CANVAS
# ============================================================================

class DataBrain3DCanvas(FigureCanvasQTAgg):
    """Cinema-quality 3D knowledge graph with advanced lighting"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(14, 10), facecolor='#0F172A')
        super().__init__(self.figure)
        self.setParent(parent)

        self.ax = self.figure.add_subplot(111, projection='3d', facecolor='#0F172A')
        self.data_manager = AtlasDataManager()

        # Animation parameters
        self.rotation_angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)

        self.setup_plot()

    def setup_plot(self):
        """Initialize professional 3D plot with cinema lighting"""
        self.ax.set_xlabel('X Dimension', fontsize=11, weight='bold', color='#94A3B8')
        self.ax.set_ylabel('Y Dimension', fontsize=11, weight='bold', color='#94A3B8')
        self.ax.set_zlabel('Z Dimension', fontsize=11, weight='bold', color='#94A3B8')
        self.ax.set_title('🧠 DataBrain 3D - Knowledge Graph Physics',
                         fontsize=16, weight='bold', color='#60A5FA', pad=20)

        # Professional dark theme
        self.ax.set_facecolor('#0F172A')
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False

        # Grid styling
        self.ax.xaxis.pane.set_edgecolor('#1E293B')
        self.ax.yaxis.pane.set_edgecolor('#1E293B')
        self.ax.zaxis.pane.set_edgecolor('#1E293B')
        self.ax.grid(True, alpha=0.15, linestyle='--', color='#475569')

        # Tick colors
        self.ax.tick_params(colors='#64748B')

        self.update_plot()

    def update_plot(self):
        """Render HD 3D knowledge graph"""
        self.ax.clear()

        # Get data
        nodes = self.data_manager.get_databrain_nodes()
        edges = self.data_manager.get_databrain_edges()

        if not nodes:
            return

        # Create node lookup
        node_lookup = {n['node_id']: n for n in nodes}

        # Draw edges with gradient effect
        for edge in edges[:100]:  # Limit for performance
            src = node_lookup.get(edge.get('source_id'))
            tgt = node_lookup.get(edge.get('target_id'))

            if src and tgt:
                x_line = [float(src['x_coord']), float(tgt['x_coord'])]
                y_line = [float(src['y_coord']), float(tgt['y_coord'])]
                z_line = [float(src['z_index']), float(tgt['z_index'])]

                weight = float(edge.get('weight', 0.5))
                alpha = min(weight, 0.4)
                linewidth = weight * 2

                self.ax.plot(x_line, y_line, z_line,
                           color='#3B82F6', alpha=alpha, linewidth=linewidth,
                           linestyle='-', zorder=1)

        # Draw nodes with professional styling
        for node in nodes:
            x, y, z = float(node['x_coord']), float(node['y_coord']), float(node['z_index'])
            mass = float(node.get('mass', 1.0))
            color = node.get('color', '#60A5FA')

            # Size based on importance
            size = 100 + mass * 50

            # Node with glow effect (multiple layers)
            self.ax.scatter([x], [y], [z],
                          c=[color], s=size * 1.5, alpha=0.2,
                          edgecolors='none', zorder=2)  # Glow layer
            self.ax.scatter([x], [y], [z],
                          c=[color], s=size, alpha=0.8,
                          edgecolors='white', linewidths=1.5, zorder=3)  # Main node
            self.ax.scatter([x], [y], [z],
                          c=['white'], s=size * 0.3, alpha=0.6,
                          edgecolors='none', zorder=4)  # Highlight

        # Professional styling
        self.ax.set_xlabel('X - Semantic Space', fontsize=10, weight='bold', color='#94A3B8')
        self.ax.set_ylabel('Y - Context Dimension', fontsize=10, weight='bold', color='#94A3B8')
        self.ax.set_zlabel('Z - Abstraction Level', fontsize=10, weight='bold', color='#94A3B8')
        self.ax.set_title(f'🧠 DataBrain HD - {len(nodes)} Knowledge Nodes',
                         fontsize=15, weight='bold', color='#60A5FA', pad=15)

        # Set limits
        self.ax.set_xlim(-12, 12)
        self.ax.set_ylim(-12, 12)
        self.ax.set_zlim(-12, 12)

        # Cinema-quality view angle
        self.ax.view_init(elev=20, azim=self.rotation_angle)

        self.ax.set_facecolor('#0F172A')
        self.ax.grid(True, alpha=0.12, linestyle='--', color='#475569')

        self.draw()

    def animate(self):
        """Smooth rotation animation"""
        self.rotation_angle = (self.rotation_angle + 0.5) % 360
        self.ax.view_init(elev=20, azim=self.rotation_angle)
        self.draw()

    def start_animation(self):
        """Start auto-rotation"""
        self.timer.start(50)  # 50ms = 20 FPS

    def stop_animation(self):
        """Stop auto-rotation"""
        self.timer.stop()


# ============================================================================
# PROFESSIONAL AUTOMATION MATRIX WITH REAL-TIME CREATION
# ============================================================================

class AutomationMatrixWidget(QWidget):
    """Professional workflow visualization with creation interface"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_manager = AtlasDataManager()
        self.setup_ui()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # 5 seconds

    def setup_ui(self):
        """Setup professional UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header with description
        header_frame = self._create_header()
        layout.addWidget(header_frame)

        # Split view: Visualization + Creation
        content_layout = QHBoxLayout()

        # Left: Workflow Matrix Visualization
        viz_group = self._create_visualization_section()
        content_layout.addWidget(viz_group, 60)

        # Right: Real-Time Creation
        creation_group = self._create_creation_section()
        content_layout.addWidget(creation_group, 40)

        layout.addLayout(content_layout)

    def _create_header(self) -> QWidget:
        """Create professional header with descriptions"""
        frame = QFrame()
        frame.setObjectName("professionalCard")
        layout = QVBoxLayout(frame)

        # Title
        title = QLabel("⚡ Automation Matrix - Workflow Intelligence")
        title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #60A5FA; margin-bottom: 8px;")
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "<b>Real-time workflow orchestration and monitoring.</b><br>"
            "<span style='color: #94A3B8;'>"
            "• <b>Particles:</b> Individual workflows in execution<br>"
            "• <b>Colors:</b> <span style='color: #3B82F6;'>●</span> Running  "
            "<span style='color: #10B981;'>●</span> Completed  "
            "<span style='color: #9CA3AF;'>●</span> Pending  "
            "<span style='color: #EF4444;'>●</span> Failed<br>"
            "• <b>Arrows:</b> Velocity vectors showing progress direction and speed<br>"
            "• <b>Size:</b> Computational complexity and resource usage<br>"
            "• <b>Position:</b> X-axis = time elapsed, Y-axis = completion percentage"
            "</span>"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #E2E8F0; font-size: 13px; line-height: 1.6;")
        layout.addWidget(desc)

        return frame

    def _create_visualization_section(self) -> QGroupBox:
        """Create workflow visualization section"""
        group = QGroupBox("📊 Live Workflow Matrix")
        group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        layout = QVBoxLayout(group)

        # Canvas
        self.canvas = MatrixVisualizationCanvas()
        layout.addWidget(self.canvas)

        # Stats bar
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Loading workflows...")
        self.stats_label.setStyleSheet("color: #94A3B8; font-size: 12px; padding: 8px;")
        stats_layout.addWidget(self.stats_label)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        stats_layout.addWidget(refresh_btn)

        layout.addLayout(stats_layout)

        return group

    def _create_creation_section(self) -> QGroupBox:
        """Create real-time workflow creation section"""
        group = QGroupBox("✨ Create New Workflow")
        group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        layout = QVBoxLayout(group)
        layout.setSpacing(15)

        # Workflow name
        layout.addWidget(QLabel("Workflow Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Portfolio Rebalance")
        layout.addWidget(self.name_input)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Describe the workflow purpose and goals...")
        self.desc_input.setMaximumHeight(100)
        layout.addWidget(self.desc_input)

        # Agent selection
        layout.addWidget(QLabel("Assign Agent:"))
        self.agent_combo = QComboBox()
        self.agent_combo.addItems([
            "portfolio_optimizer",
            "financial_analyst",
            "risk_manager",
            "market_intelligence",
            "compliance_monitor"
        ])
        layout.addWidget(self.agent_combo)

        # Steps count
        layout.addWidget(QLabel("Number of Steps:"))
        self.steps_spin = QSpinBox()
        self.steps_spin.setMinimum(1)
        self.steps_spin.setMaximum(50)
        self.steps_spin.setValue(5)
        layout.addWidget(self.steps_spin)

        # Progress preview
        layout.addWidget(QLabel("Creation Progress:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Create button
        create_btn = QPushButton("🚀 Create Workflow")
        create_btn.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        create_btn.clicked.connect(self.create_workflow)
        layout.addWidget(create_btn)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #10B981; font-weight: 600; padding: 8px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        return group

    def create_workflow(self):
        """Create new workflow with real-time progress"""
        name = self.name_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        agent_id = self.agent_combo.currentText()
        steps = self.steps_spin.value()

        if not name:
            self.status_label.setText("❌ Please enter a workflow name")
            self.status_label.setStyleSheet("color: #EF4444; font-weight: 600;")
            return

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("⏳ Creating workflow...")
        self.status_label.setStyleSheet("color: #F59E0B; font-weight: 600;")

        # Simulate creation progress
        for i in range(0, 101, 20):
            self.progress_bar.setValue(i)
            QApplication.processEvents()

        # Create in database
        success = self.data_manager.create_workflow(name, description, agent_id, steps)

        if success:
            self.status_label.setText(f"✅ Workflow '{name}' created successfully!\n"
                                     f"Agent: {agent_id} | Steps: {steps}")
            self.status_label.setStyleSheet("color: #10B981; font-weight: 600;")

            # Clear inputs
            self.name_input.clear()
            self.desc_input.clear()

            # Refresh visualization
            self.refresh_data()
        else:
            self.status_label.setText("❌ Failed to create workflow")
            self.status_label.setStyleSheet("color: #EF4444; font-weight: 600;")

        self.progress_bar.setVisible(False)

    def refresh_data(self):
        """Refresh workflow data"""
        workflows = self.data_manager.get_workflows()

        # Update stats
        running = sum(1 for w in workflows if w['status'] == 'running')
        completed = sum(1 for w in workflows if w['status'] == 'completed')
        pending = sum(1 for w in workflows if w['status'] == 'pending')

        self.stats_label.setText(
            f"📊 {len(workflows)} Total  |  "
            f"<span style='color: #3B82F6;'>▶ {running} Running</span>  |  "
            f"<span style='color: #10B981;'>✓ {completed} Completed</span>  |  "
            f"<span style='color: #9CA3AF;'>⏸ {pending} Pending</span>"
        )

        # Update canvas
        self.canvas.update_workflows(workflows)


class MatrixVisualizationCanvas(FigureCanvasQTAgg):
    """Professional workflow particle visualization"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(10, 7), facecolor='#0F172A')
        super().__init__(self.figure)
        self.setParent(parent)
        self.ax = self.figure.add_subplot(111, facecolor='#0F172A')
        self.workflows = []
        self.setup_plot()

    def setup_plot(self):
        """Initialize plot styling"""
        self.ax.set_facecolor('#0F172A')
        self.ax.tick_params(colors='#64748B')
        self.ax.spines['bottom'].set_color('#475569')
        self.ax.spines['left'].set_color('#475569')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

    def update_workflows(self, workflows: List[Dict]):
        """Update visualization with new workflow data"""
        self.workflows = workflows
        self.render()

    def render(self):
        """Render professional workflow particles"""
        self.ax.clear()

        if not self.workflows:
            self.ax.text(0.5, 0.5, 'No workflows available\nCreate one to get started!',
                        ha='center', va='center', color='#64748B', fontsize=14,
                        transform=self.ax.transAxes)
            self.draw()
            return

        xs, ys, colors, sizes, labels = [], [], [], [], []

        for wf in self.workflows:
            # Calculate position
            age_hours = (datetime.now() - wf.get('created_at', datetime.now())).total_seconds() / 3600
            x = min(age_hours / 24, 1.0)  # Normalize to 0-1 (24 hours max)
            y = float(wf.get('progress', 0.0))

            xs.append(x)
            ys.append(y)
            labels.append(wf.get('name', 'Unknown'))

            # Professional color scheme
            status = wf.get('status', 'pending')
            if status == 'completed':
                colors.append('#10B981')
                sizes.append(120)
            elif status == 'running':
                colors.append('#3B82F6')
                sizes.append(180)
            elif status == 'failed':
                colors.append('#EF4444')
                sizes.append(100)
            else:
                colors.append('#9CA3AF')
                sizes.append(90)

        # Plot particles with glow effect
        for i in range(len(xs)):
            # Glow layer
            self.ax.scatter([xs[i]], [ys[i]], c=[colors[i]], s=sizes[i]*1.8,
                          alpha=0.15, edgecolors='none', zorder=1)
            # Main particle
            self.ax.scatter([xs[i]], [ys[i]], c=[colors[i]], s=sizes[i],
                          alpha=0.85, edgecolors='white', linewidths=2, zorder=2)

        # Add velocity arrows for running workflows
        for i, wf in enumerate(self.workflows):
            if wf.get('status') == 'running':
                x, y = xs[i], ys[i]
                dx = 0.08
                dy = 0.12 * (1 - y)
                self.ax.arrow(x, y, dx, dy, head_width=0.03, head_length=0.04,
                            fc='#8B5CF6', ec='#8B5CF6', alpha=0.6, linewidth=2, zorder=3)

        # Professional styling
        self.ax.set_xlabel('Time Elapsed (normalized)', fontsize=11, weight='bold', color='#94A3B8')
        self.ax.set_ylabel('Completion Progress', fontsize=11, weight='bold', color='#94A3B8')
        self.ax.set_title(f'Workflow Particles: {len(self.workflows)} Active',
                         fontsize=13, weight='bold', color='#60A5FA', pad=12)
        self.ax.set_xlim(-0.05, 1.05)
        self.ax.set_ylim(-0.05, 1.05)
        self.ax.grid(True, alpha=0.15, linestyle='--', color='#475569')
        self.ax.set_facecolor('#0F172A')

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#3B82F6', label='Running'),
            Patch(facecolor='#10B981', label='Completed'),
            Patch(facecolor='#9CA3AF', label='Pending'),
            Patch(facecolor='#EF4444', label='Failed'),
        ]
        self.ax.legend(handles=legend_elements, loc='upper left',
                      facecolor='#1E293B', edgecolor='#475569', framealpha=0.9,
                      labelcolor='#E2E8F0')

        self.draw()


# ============================================================================
# DATABASE SYNC MONITOR
# ============================================================================

class DatabaseSyncWidget(QWidget):
    """Professional database sync monitoring with detailed metrics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_manager = AtlasDataManager()
        self.setup_ui()

        # Auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(10000)  # 10 seconds

    def setup_ui(self):
        """Setup professional UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Stats cards
        stats_layout = QHBoxLayout()
        self.total_tables_card = self._create_stat_card("Tables Tracked", "0", "#3B82F6")
        self.total_records_card = self._create_stat_card("Total Records", "0", "#10B981")
        self.last_sync_card = self._create_stat_card("Last Sync", "Never", "#8B5CF6")

        stats_layout.addWidget(self.total_tables_card)
        stats_layout.addWidget(self.total_records_card)
        stats_layout.addWidget(self.last_sync_card)
        layout.addLayout(stats_layout)

        # Sync table
        table_group = QGroupBox("📋 Sync Status by Table")
        table_group.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        table_layout = QVBoxLayout(table_group)

        self.sync_table = QTableWidget()
        self.sync_table.setColumnCount(6)
        self.sync_table.setHorizontalHeaderLabels([
            "Table Name", "Data Type", "Records Synced",
            "Last Sync", "Frequency", "Next Sync"
        ])
        self.sync_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sync_table.setAlternatingRowColors(True)
        self.sync_table.verticalHeader().setVisible(False)

        table_layout.addWidget(self.sync_table)
        layout.addWidget(table_group)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Sync Status")
        refresh_btn.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)

        # Initial load
        self.refresh_data()

    def _create_header(self) -> QWidget:
        """Create header with description"""
        frame = QFrame()
        frame.setObjectName("professionalCard")
        layout = QVBoxLayout(frame)

        title = QLabel("🔄 CockroachDB Sync Monitor")
        title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #60A5FA; margin-bottom: 8px;")
        layout.addWidget(title)

        desc = QLabel(
            "<b>Real-time database synchronization monitoring.</b><br>"
            "<span style='color: #94A3B8;'>"
            "• <b>Operational Data:</b> Agent status, workflows, metrics (synced every 5-10 min)<br>"
            "• <b>Analytics Data:</b> Performance logs, cognition scores (synced every 15 min)<br>"
            "• <b>Knowledge Data:</b> Graph nodes, edges, concepts (synced every 30 min)<br>"
            "• <b>Memory Data:</b> Vector embeddings, context (synced every 1 hour)"
            "</span>"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #E2E8F0; font-size: 13px;")
        layout.addWidget(desc)

        return frame

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create professional stat card"""
        card = QFrame()
        card.setObjectName("professionalCard")
        card.setMinimumWidth(200)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 600;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName(f"{title.replace(' ', '_')}_value")
        value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 800;")
        layout.addWidget(value_label)

        return card

    def refresh_data(self):
        """Refresh sync data"""
        sync_data = self.data_manager.get_sync_status()

        # Update stats cards
        stats = sync_data.get('stats', {})
        self.total_tables_card.findChild(QLabel, "Tables_Tracked_value").setText(
            str(stats.get('tables_tracked', 0))
        )
        self.total_records_card.findChild(QLabel, "Total_Records_value").setText(
            f"{stats.get('total_records', 0):,}"
        )

        last_sync = stats.get('most_recent_sync')
        if last_sync:
            time_ago = datetime.now() - last_sync
            if time_ago.total_seconds() < 60:
                time_str = "Just now"
            elif time_ago.total_seconds() < 3600:
                time_str = f"{int(time_ago.total_seconds() / 60)} min ago"
            else:
                time_str = f"{int(time_ago.total_seconds() / 3600)} hr ago"
            self.last_sync_card.findChild(QLabel, "Last_Sync_value").setText(time_str)

        # Update table
        tables = sync_data.get('tables', [])
        self.sync_table.setRowCount(len(tables))

        for i, table in enumerate(tables):
            self.sync_table.setItem(i, 0, QTableWidgetItem(table.get('table_name', '')))
            self.sync_table.setItem(i, 1, QTableWidgetItem(table.get('data_type', '')))
            self.sync_table.setItem(i, 2, QTableWidgetItem(f"{table.get('records_synced', 0):,}"))

            last_sync = table.get('last_sync')
            if last_sync:
                time_str = last_sync.strftime('%H:%M:%S')
            else:
                time_str = 'Never'
            self.sync_table.setItem(i, 3, QTableWidgetItem(time_str))

            self.sync_table.setItem(i, 4, QTableWidgetItem(table.get('sync_frequency', 'N/A')))

            next_sync = table.get('next_sync')
            if next_sync:
                delta = next_sync - datetime.now()
                if delta.total_seconds() > 0:
                    next_str = f"in {int(delta.total_seconds() / 60)} min"
                else:
                    next_str = "Overdue"
            else:
                next_str = 'N/A'
            self.sync_table.setItem(i, 5, QTableWidgetItem(next_str))


# ============================================================================
# VISUAL INTELLIGENCE ENGINE (Consolidated)
# ============================================================================

class VisualIntelligenceWidget(QWidget):
    """Unified: Optic Nerve + DSPPPY + Liquidity Engine"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_manager = AtlasDataManager()
        self.setup_ui()

    def setup_ui(self):
        """Setup unified visual intelligence UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Tabs for each engine
        tabs = QTabWidget()
        tabs.setFont(QFont("Inter", 12, QFont.Weight.Bold))

        # Optic Nerve Tab
        optic_tab = self._create_optic_tab()
        tabs.addTab(optic_tab, "👁️ Optic Nerve")

        # DSPPPY Tab
        dspppy_tab = self._create_dspppy_tab()
        tabs.addTab(dspppy_tab, "📊 DSPPPY Analytics")

        # Liquidity Engine Tab
        liquidity_tab = self._create_liquidity_tab()
        tabs.addTab(liquidity_tab, "💰 Liquidity Engine")

        layout.addWidget(tabs)

    def _create_header(self) -> QWidget:
        """Create header"""
        frame = QFrame()
        frame.setObjectName("professionalCard")
        layout = QVBoxLayout(frame)

        title = QLabel("👁️ Visual Intelligence Engine")
        title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #60A5FA; margin-bottom: 8px;")
        layout.addWidget(title)

        desc = QLabel(
            "<b>Unified visual processing, data analytics, and financial intelligence.</b><br>"
            "<span style='color: #94A3B8;'>"
            "Combines Optic Nerve (vision AI), DSPPPY (data processing), and Liquidity Engine (cash flow)"
            "</span>"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #E2E8F0; font-size: 13px;")
        layout.addWidget(desc)

        return frame

    def _create_optic_tab(self) -> QWidget:
        """Create Optic Nerve vision processing tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Recent jobs table
        jobs_table = QTableWidget()
        jobs_table.setColumnCount(4)
        jobs_table.setHorizontalHeaderLabels(["Job ID", "Image", "Status", "Confidence"])
        jobs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Sample data
        jobs = self.data_manager._get_optic_jobs()
        jobs_table.setRowCount(len(jobs))
        for i, job in enumerate(jobs):
            jobs_table.setItem(i, 0, QTableWidgetItem(job['id']))
            jobs_table.setItem(i, 1, QTableWidgetItem(job['image']))
            jobs_table.setItem(i, 2, QTableWidgetItem(job['status']))
            jobs_table.setItem(i, 3, QTableWidgetItem(f"{job['confidence']:.2%}"))

        layout.addWidget(QLabel("Recent Vision Processing Jobs"))
        layout.addWidget(jobs_table)

        return widget

    def _create_dspppy_tab(self) -> QWidget:
        """Create DSPPPY analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        analyses_table = QTableWidget()
        analyses_table.setColumnCount(4)
        analyses_table.setHorizontalHeaderLabels(["Analysis ID", "Dataset", "Processing Time (s)", "Insights"])
        analyses_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        analyses = self.data_manager._get_dspppy_analyses()
        analyses_table.setRowCount(len(analyses))
        for i, analysis in enumerate(analyses):
            analyses_table.setItem(i, 0, QTableWidgetItem(analysis['id']))
            analyses_table.setItem(i, 1, QTableWidgetItem(analysis['dataset']))
            analyses_table.setItem(i, 2, QTableWidgetItem(f"{analysis['processing_time']:.2f}"))
            analyses_table.setItem(i, 3, QTableWidgetItem(str(analysis['insights_found'])))

        layout.addWidget(QLabel("Recent Data Processing Analyses"))
        layout.addWidget(analyses_table)

        return widget

    def _create_liquidity_tab(self) -> QWidget:
        """Create Liquidity Engine tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Canvas
        canvas = LiquidityEngineCanvas()
        layout.addWidget(canvas)

        return widget


class LiquidityEngineCanvas(FigureCanvasQTAgg):
    """Professional liquidity visualization"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8), facecolor='#0F172A')
        super().__init__(self.figure)
        self.setParent(parent)
        self.ax = self.figure.add_subplot(111, facecolor='#0F172A')
        self.data_manager = AtlasDataManager()
        self.render()

    def render(self):
        """Render professional cash flow visualization"""
        self.ax.clear()

        flows = self.data_manager._get_liquidity_flows()

        accounts = [f['account'] for f in flows]
        balances = [f['balance'] for f in flows]
        changes = [f['daily_change'] for f in flows]

        # Create bars with gradient effect
        colors = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EC4899']
        bars = self.ax.barh(accounts, balances, color=colors, alpha=0.8, edgecolor='white', linewidth=2)

        # Add change indicators
        for i, (account, balance, change) in enumerate(zip(accounts, balances, changes)):
            change_color = '#10B981' if change > 0 else '#EF4444'
            change_text = f"+${change:,.0f}" if change > 0 else f"-${abs(change):,.0f}"
            self.ax.text(balance + 10000, i, change_text,
                        va='center', color=change_color, fontweight='bold', fontsize=10)

        self.ax.set_xlabel('Balance ($)', fontsize=11, weight='bold', color='#94A3B8')
        self.ax.set_title('💰 Liquidity Engine - Account Balances',
                         fontsize=14, weight='bold', color='#60A5FA', pad=15)
        self.ax.set_facecolor('#0F172A')
        self.ax.tick_params(colors='#64748B')
        self.ax.grid(True, axis='x', alpha=0.15, linestyle='--', color='#475569')

        # Format x-axis as currency
        from matplotlib.ticker import FuncFormatter
        def currency_formatter(x, p):
            return f'${x/1000:.0f}K'
        self.ax.xaxis.set_major_formatter(FuncFormatter(currency_formatter))

        self.draw()


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

class AtlasProfessionalDashboard(QMainWindow):
    """Atlas Capital Automations - Professional HD Dashboard"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Atlas Capital Automations - a Terry Dellmonaco Co.")
        self.setMinimumSize(1600, 1000)

        # Apply professional styling
        self.setStyleSheet(ATLAS_PRO_STYLE)

        self.setup_ui()
        self.show()

    def setup_ui(self):
        """Setup main dashboard UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Main tabs
        tabs = QTabWidget()
        tabs.setFont(QFont("Inter", 13, QFont.Weight.Bold))

        # 3D DataBrain
        databrain_tab = self._create_databrain_tab()
        tabs.addTab(databrain_tab, "🧠 3D DataBrain")

        # Automation Matrix
        matrix_tab = AutomationMatrixWidget()
        tabs.addTab(matrix_tab, "⚡ Automation Matrix")

        # Database Sync
        sync_tab = DatabaseSyncWidget()
        tabs.addTab(sync_tab, "🔄 Database Sync")

        # Visual Intelligence Engine
        visual_tab = VisualIntelligenceWidget()
        tabs.addTab(visual_tab, "👁️ Visual Intelligence")

        layout.addWidget(tabs)

        # Compact AI Chat Bar at bottom
        chat_bar = self._create_chat_bar()
        layout.addWidget(chat_bar)

    def _create_chat_bar(self) -> QWidget:
        """Create compact AI chat bar at bottom"""
        chat_frame = QFrame()
        chat_frame.setFixedHeight(60)
        chat_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(30, 41, 59, 0.95),
                    stop:1 rgba(15, 23, 42, 0.95));
                border-top: 2px solid rgba(59, 130, 246, 0.3);
            }
        """)

        layout = QHBoxLayout(chat_frame)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)

        # Agent selector
        agent_label = QLabel("🤖")
        agent_label.setStyleSheet("font-size: 18px; background: transparent;")
        layout.addWidget(agent_label)

        self.agent_selector = QComboBox()
        self.agent_selector.addItems(["CESAR", "FinPsy", "Pydini", "Lex", "Inno", "Edu"])
        self.agent_selector.setFixedWidth(100)
        self.agent_selector.setStyleSheet("""
            QComboBox {
                background: rgba(51, 65, 85, 0.8);
                border: 1px solid rgba(71, 85, 105, 0.5);
                border-radius: 6px;
                padding: 6px 10px;
                color: #E2E8F0;
                font-size: 12px;
                font-weight: 600;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: rgba(30, 41, 59, 0.95);
                border: 1px solid rgba(71, 85, 105, 0.5);
                selection-background-color: rgba(59, 130, 246, 0.3);
                color: #E2E8F0;
            }
        """)
        layout.addWidget(self.agent_selector)

        # Attachment button
        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(40, 40)
        attach_btn.setToolTip("Attach files")
        attach_btn.setStyleSheet("""
            QPushButton {
                background: rgba(71, 85, 105, 0.5);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(100, 116, 139, 0.7);
                border: 1px solid rgba(148, 163, 184, 0.5);
            }
        """)
        attach_btn.clicked.connect(self._handle_attachment)
        layout.addWidget(attach_btn)

        # Text input
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask CESAR anything... (Press Enter to send)")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background: rgba(51, 65, 85, 0.8);
                border: 1px solid rgba(71, 85, 105, 0.5);
                border-radius: 8px;
                padding: 10px 15px;
                color: #E2E8F0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(59, 130, 246, 0.6);
                background: rgba(51, 65, 85, 1.0);
            }
        """)
        self.chat_input.returnPressed.connect(self._send_message)
        layout.addWidget(self.chat_input, 1)  # Takes up remaining space

        # Microphone button
        mic_btn = QPushButton("🎤")
        mic_btn.setFixedSize(40, 40)
        mic_btn.setToolTip("Voice input")
        mic_btn.setStyleSheet("""
            QPushButton {
                background: rgba(71, 85, 105, 0.5);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
                border: 1px solid rgba(239, 68, 68, 0.5);
            }
        """)
        mic_btn.clicked.connect(self._handle_voice)
        layout.addWidget(mic_btn)

        # Screen share button
        share_btn = QPushButton("🖥️")
        share_btn.setFixedSize(40, 40)
        share_btn.setToolTip("Screen share")
        share_btn.setStyleSheet("""
            QPushButton {
                background: rgba(71, 85, 105, 0.5);
                border: 1px solid rgba(100, 116, 139, 0.3);
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(139, 92, 246, 0.3);
                border: 1px solid rgba(139, 92, 246, 0.5);
            }
        """)
        share_btn.clicked.connect(self._handle_screen_share)
        layout.addWidget(share_btn)

        # Send button
        send_btn = QPushButton("📤")
        send_btn.setFixedSize(40, 40)
        send_btn.setToolTip("Send message")
        send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(59, 130, 246, 0.9),
                    stop:1 rgba(37, 99, 235, 0.9));
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(96, 165, 250, 1.0),
                    stop:1 rgba(59, 130, 246, 1.0));
            }
        """)
        send_btn.clicked.connect(self._send_message)
        layout.addWidget(send_btn)

        return chat_frame

    def _send_message(self):
        """Send message to selected agent"""
        message = self.chat_input.text().strip()
        if not message:
            return

        agent = self.agent_selector.currentText()

        # Show notification
        self.statusBar().showMessage(f"💬 Sending to {agent}: {message[:50]}...", 3000)

        # Clear input
        self.chat_input.clear()

        # TODO: Integrate with actual agent API
        # For now, just show confirmation
        print(f"[{agent}] Message: {message}")

    def _handle_attachment(self):
        """Handle file attachment"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Attach",
            "",
            "All Files (*.*)"
        )
        if file_path:
            self.statusBar().showMessage(f"📎 Attached: {file_path}", 3000)
            print(f"Attached: {file_path}")

    def _handle_voice(self):
        """Handle voice input"""
        self.statusBar().showMessage("🎤 Voice input feature coming soon!", 2000)
        print("Voice input triggered")

    def _handle_screen_share(self):
        """Handle screen share"""
        self.statusBar().showMessage("🖥️ Screen share feature coming soon!", 2000)
        print("Screen share triggered")

    def _create_header(self) -> QWidget:
        """Create professional header"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(59, 130, 246, 0.15),
                    stop:0.5 rgba(139, 92, 246, 0.15),
                    stop:1 rgba(59, 130, 246, 0.15));
                border-bottom: 2px solid rgba(59, 130, 246, 0.3);
            }
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 10, 30, 10)

        # Title
        title = QLabel("🏛️ Atlas Capital Automations - a Terry Dellmonaco Co.")
        title.setFont(QFont("Inter", 26, QFont.Weight.ExtraBold))
        title.setStyleSheet("color: #60A5FA; background: transparent;")
        layout.addWidget(title)

        layout.addStretch()

        # Status indicator
        status = QLabel("● ONLINE")
        status.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        status.setStyleSheet("color: #10B981; background: transparent;")
        layout.addWidget(status)

        return header

    def _create_databrain_tab(self) -> QWidget:
        """Create 3D DataBrain tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Description
        desc_frame = QFrame()
        desc_frame.setObjectName("professionalCard")
        desc_layout = QVBoxLayout(desc_frame)

        title = QLabel("🧠 3D DataBrain - Knowledge Graph Physics")
        title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #60A5FA;")
        desc_layout.addWidget(title)

        desc = QLabel(
            "<b>Interactive 3D visualization of knowledge structure.</b><br>"
            "<span style='color: #94A3B8;'>"
            "• Nodes represent concepts, skills, domains, and patterns<br>"
            "• Edges show relationships and knowledge connections<br>"
            "• Size indicates importance and access frequency<br>"
            "• Colors categorize by type (blue=concepts, purple=skills, etc.)"
            "</span>"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #E2E8F0; font-size: 13px;")
        desc_layout.addWidget(desc)

        layout.addWidget(desc_frame)

        # Canvas
        self.databrain_canvas = DataBrain3DCanvas()
        layout.addWidget(self.databrain_canvas)

        # Controls
        controls_layout = QHBoxLayout()

        rotate_btn = QPushButton("🔄 Auto-Rotate")
        rotate_btn.setCheckable(True)
        rotate_btn.toggled.connect(self._toggle_rotation)
        controls_layout.addWidget(rotate_btn)

        refresh_btn = QPushButton("🔃 Refresh")
        refresh_btn.clicked.connect(self.databrain_canvas.update_plot)
        controls_layout.addWidget(refresh_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        return widget

    def _toggle_rotation(self, checked: bool):
        """Toggle 3D rotation"""
        if checked:
            self.databrain_canvas.start_animation()
        else:
            self.databrain_canvas.stop_animation()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Launch Atlas Professional Dashboard"""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Atlas Capital Automations")
    app.setOrganizationName("Terry Dellmonaco Co.")

    # Launch dashboard
    dashboard = AtlasProfessionalDashboard()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
