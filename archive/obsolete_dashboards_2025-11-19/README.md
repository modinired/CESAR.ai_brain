# Archived Dashboard Files

**Date Archived:** 2025-11-19
**Reason:** Code consolidation - these dashboard implementations were superseded by `cesar_mcp_dashboard_fixed.py`

## Files Archived (7 total, 179KB)

1. `atlas_dashboard.py` (14KB) - Original Atlas dashboard
2. `atlas_desktop.py` (23KB) - Desktop version attempt #1
3. `atlas_desktop_v2.py` (36KB) - Desktop version attempt #2
4. `atlas_glassmorphism_dashboard.py` (25KB) - Glassmorphism experiment #1
5. `atlas_desktop_glassmorphism.py` (22KB) - Glassmorphism experiment #2
6. `cesar_mcp_dashboard_desktop.py` (28KB) - CESAR desktop attempt #1
7. `cesar_mcp_dashboard_glassmorphism.py` (31KB) - CESAR glassmorphism version

## Current Production Dashboard

**File:** `../../cesar_mcp_dashboard_fixed.py` (58KB)

**Features:**
- High-contrast accessible design (WCAG AA compliant)
- PyQt6 desktop application
- 5 tabs: Agent Chat, Workflows, Financial Intelligence, Business Health, Agent Status
- Real-time data refresh (10-second intervals)
- Enhanced financial charts with matplotlib
- CESAR chat integration with system prompt

## Historical Context

These files represent the iterative development process of the dashboard UI:
- Started with web-based Streamlit (atlas_dashboard.py)
- Evolved to PyQt6 desktop application
- Experimented with glassmorphism design patterns
- Consolidated into single production-quality implementation

## If You Need to Reference

All files are preserved in this archive for:
- Code archaeology / learning from past iterations
- Potential feature extraction
- Design pattern reference

**DO NOT USE THESE FILES IN PRODUCTION**
