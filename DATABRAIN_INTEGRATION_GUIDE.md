# DataBrain Integration Guide for CESAR Agents
**PhD-Level Living Knowledge Graph Integration**

## Overview

All 48 MCP agents now have access to the **DataBrain** - a living 3D knowledge graph with 37 semantic nodes representing:
- Wisdom Layer (300+ z-index): Strategic architecture concepts
- Knowledge Layer (200-300): MCP system domains, protocols
- Information Layer (100-200): Agent specializations
- Raw Data Layer (0-100): Unprocessed information

**Key Innovation**: Agents don't just process queries in isolation - they tap into collective memory, learn from each other's experiences, and contribute back to the shared knowledge base.

---

## Integration Architecture

```
┌─────────────────┐
│   MCP Agent     │
│  (FinPsy/Lex)   │
└────────┬────────┘
         │
         │ get_brain_context("portfolio optimization")
         ▼
┌─────────────────┐         ┌──────────────────────────┐
│  BaseMCPAgent   │────────►│  DataBrain (CockroachDB)  │
│  (with brain)   │         │  37 nodes, 30 links      │
└─────────────────┘         └──────────────────────────┘
         │
         │ GRAPH_STATE injected
         ▼
┌─────────────────┐
│  process()      │
│  with context   │
└────────┬────────┘
         │
         │ mutate_brain(UPDATE_MASS)
         ▼
┌──────────────────────────┐
│  Brain learns & grows    │
└──────────────────────────┘
```

---

## Usage for Agent Developers

### Method 1: Automatic Integration (Recommended)

Use `process_with_brain()` for automatic context injection and brain updates:

```python
from mcp_agents.base_agent import BaseMCPAgent

class MyFinancialAgent(BaseMCPAgent):
    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        # Check if brain context is available
        graph_state = task_input.get("GRAPH_STATE")

        if graph_state and graph_state.get("current_node_context"):
            # Use brain context in decision-making
            context_node = graph_state["current_node_context"]
            print(f"Using knowledge from: {context_node['label']}")
            print(f"Layer: {context_node['z_layer']}, Mass: {context_node['mass']}")

            # Access connected concepts
            for neighbor in graph_state.get("connected_neighbors", []):
                print(f"  Related: {neighbor['label']} (link: {neighbor['link_strength']})")

        # Your processing logic here
        return {"status": "completed", "result": "..."}

# Usage:
agent = MyFinancialAgent(agent_id="fin_agent_01", mcp_system="finpsy")

# This automatically gets context, processes, and updates brain
result = agent.process_with_brain(
    query="portfolio optimization",
    task_input={"action": "analyze", "data": {...}}
)
```

### Method 2: Manual Integration (Fine-grained Control)

For custom workflows where you need explicit control:

```python
class CustomAgent(BaseMCPAgent):
    def execute_complex_task(self, query: str, data: Dict) -> Dict:
        # Step 1: Get brain context
        context = self.get_brain_context(query, max_neighbors=10)

        # Step 2: Use context in your logic
        if context.get("current_node_context"):
            # Make decisions based on collective knowledge
            wisdom = context["current_node_context"]
            # ...

        # Step 3: Process your task
        result = self.my_custom_processing(data, context)

        # Step 4: Update brain based on results
        if result["quality_score"] > 0.85:
            # Create new knowledge node
            self.mutate_brain([
                {
                    "action": "CREATE_NODE",
                    "params": {
                        "label": f"Insight: {result['key_finding']}",
                        "type": "knowledge",
                        "initial_mass": 25,
                        "description": result["explanation"]
                    }
                }
            ])

        return result
```

---

## Neuroplasticity Protocol

### Supported Mutations

1. **CREATE_NODE** - Add new knowledge to the brain
```python
{
    "action": "CREATE_NODE",
    "params": {
        "label": "Q3 Revenue Forecasting Model",
        "type": "knowledge",  # raw_data, information, knowledge, wisdom
        "initial_mass": 30,
        "description": "Advanced time-series model achieving 94% accuracy",
        "metadata": {"accuracy": 0.94, "training_samples": 10000}
    }
}
```

2. **CREATE_LINK** - Connect related concepts
```python
{
    "action": "CREATE_LINK",
    "params": {
        "source_id": "portfolio_optimization_spec",
        "target_label": "Q3 Revenue Forecasting Model",
        "weight": 0.88
    }
}
```

3. **UPDATE_MASS** - Boost importance of frequently used knowledge
```python
{
    "action": "UPDATE_MASS",
    "params": {
        "target_id": "finpsy_domain",
        "delta": 5.0  # Increase mass by 5 (max 100)
    }
}
```

4. **DECAY_NODE** - Reduce importance of stale knowledge
```python
{
    "action": "DECAY_NODE",
    "params": {
        "target_id": "outdated_model_2023",
        "reason": "replaced_by_newer_version"
    }
}
```

---

## Best Practices

### 1. Query Strategy
- **Specific queries** work best: "portfolio optimization" > "finance"
- Use domain terminology that matches knowledge node labels
- Query for concepts, not specific data values

### 2. Mass Management
- UPDATE_MASS when knowledge proves useful (+2-5)
- DECAY_NODE when knowledge becomes obsolete (×0.8)
- CREATE_NODE with initial_mass based on confidence:
  - High confidence: 30-40
  - Medium confidence: 20-25
  - Exploratory: 10-15

### 3. Link Strength
- 0.9-1.0: Core dependencies (e.g., agent → specialization)
- 0.7-0.9: Strong collaboration (cross-domain synergy)
- 0.5-0.7: Loose relationships (occasional interaction)

### 4. When to Create Nodes
✅ **DO** create nodes for:
- Validated insights (quality_score > 0.85)
- Reusable patterns or strategies
- Cross-domain knowledge synthesis
- Successful agent collaborations

❌ **DON'T** create nodes for:
- One-time task results
- Agent-specific ephemeral data
- Unvalidated hypotheses

---

## Configuration

Enable/disable DataBrain per agent:

```python
# Enable (default)
agent = MyAgent(agent_id="...", mcp_system="...", enable_databrain=True)

# Disable if not needed
agent = MyAgent(agent_id="...", mcp_system="...", enable_databrain=False)
```

Environment variable (applies to all agents):
```bash
# .env
ENABLE_DATABRAIN=true  # default
COCKROACH_DB_URL=postgresql://...  # required for brain access
```

---

## Real-World Example: Financial Agent

```python
from mcp_agents.base_agent import BaseMCPAgent
from typing import Dict, Any

class PortfolioOptimizerAgent(BaseMCPAgent):
    """
    Financial agent that uses DataBrain for portfolio optimization
    with historical context and market sentiment awareness.
    """

    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """Process portfolio optimization with brain context"""

        # Extract brain context if available
        graph_state = task_input.get("GRAPH_STATE", {})
        portfolio_data = task_input.get("portfolio")

        optimization_strategy = "modern_portfolio_theory"  # default

        # Use brain context to enhance strategy
        if graph_state.get("current_node_context"):
            context_node = graph_state["current_node_context"]

            # Check if we have sentiment analysis context
            neighbors = {n["label"]: n for n in graph_state.get("connected_neighbors", [])}

            if "Market Sentiment Analysis" in neighbors:
                # Adjust strategy based on sentiment
                self.logger.info("✨ Using sentiment-aware optimization")
                optimization_strategy = "sentiment_adjusted_mpt"

        # Run optimization
        result = self.run_optimization(portfolio_data, optimization_strategy)

        # If optimization performed exceptionally well, teach the brain
        if result["sharpe_ratio"] > 1.8:
            self.mutate_brain([
                {
                    "action": "CREATE_NODE",
                    "params": {
                        "label": f"High-Performance Portfolio Config {result['timestamp']}",
                        "type": "knowledge",
                        "initial_mass": 28,
                        "description": f"Sharpe ratio: {result['sharpe_ratio']}, "
                                     f"Strategy: {optimization_strategy}"
                    }
                }
            ])

        return result

    def run_optimization(self, portfolio, strategy):
        # Your actual optimization logic here
        return {"status": "completed", "sharpe_ratio": 1.9, "timestamp": "..."}

# Usage
agent = PortfolioOptimizerAgent(
    agent_id="portfolio_optimizer_01",
    mcp_system="finpsy"
)

# This queries brain for "portfolio" knowledge, injects context, and processes
result = agent.process_with_brain(
    query="portfolio optimization",
    task_input={"portfolio": {...}}
)
```

---

## Monitoring Brain Health

Check DataBrain status in the dashboard:
```bash
python3 cesar_dashboard_enhanced.py
```

Navigate to **🧠 DataBrain 3D** tab to visualize:
- 37 knowledge nodes colored by layer
- 30 synaptic links showing relationships
- Real-time node mass (importance)
- Z-index stratification

Or query via API:
```bash
curl http://localhost:8000/sync/brain/stats
```

---

## Troubleshooting

### Brain Integration Not Working

**Symptom**: `agent.databrain` is `None`

**Solution**:
1. Check `COCKROACH_DB_URL` is configured in `.env`
2. Verify CockroachDB is accessible: `psql $COCKROACH_DB_URL`
3. Ensure brain is populated: `python3 populate_databrain_complete.py`

### No Context Returned

**Symptom**: `get_brain_context()` returns empty context

**Solution**:
- Query may not match any node labels (try broader terms)
- Brain may need more nodes (check node count in dashboard)
- Check logs for connection errors

### Mutations Failing

**Symptom**: `mutate_brain()` returns errors

**Solution**:
- Verify node IDs exist before UPDATE_MASS or DECAY_NODE
- Check link target exists before CREATE_LINK
- Ensure params are well-formed (see examples above)

---

## Advanced Topics

### Hippocampal Replay for Model Training

High-quality interactions (quality_score ≥ 0.85) are automatically collected by `services/hourly_data_ingestion.py` for LoRA fine-tuning. No agent changes needed.

### Cross-Agent Learning

When Agent A creates a knowledge node, all agents instantly have access via `get_brain_context()`. This enables emergent collaboration patterns:

```python
# Agent A (in FinPsy system) discovers a pattern
agent_a.mutate_brain([{
    "action": "CREATE_NODE",
    "params": {
        "label": "Crypto Market Volatility Pattern Q4",
        "type": "knowledge",
        ...
    }
}])

# Agent B (in Legal system) automatically sees it
context_b = agent_b.get_brain_context("volatility")
# Returns the node Agent A created, enabling legal risk assessment
```

### Semantic Search

Brain uses trigram-based similarity matching. For better results:
- Use full terms: "portfolio optimization" not "port opt"
- Match domain vocabulary from `populate_databrain_complete.py`
- Nodes are indexed by label, description, and semantic_vector

---

## Summary

🎯 **Key Takeaway**: Every agent inheriting from `BaseMCPAgent` now has three superpowers:

1. **`get_brain_context(query)`** - Tap into collective intelligence
2. **`mutate_brain(actions)`** - Contribute learnings back
3. **`process_with_brain(query, input)`** - Automatic integration

The DataBrain grows smarter with every interaction, creating a self-improving ecosystem where agents learn from each other's experiences.

---

**Test Your Integration**:
```bash
python3 test_brain_integration.py
```

**View Brain State**:
```bash
python3 cesar_dashboard_enhanced.py
```

Happy coding! 🧠✨
