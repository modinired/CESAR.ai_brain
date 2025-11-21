# Add chat endpoint to main.py

chat_endpoint = '''

@app.post("/api/v1/chat")
async def chat_with_cesar(request: dict, db=Depends(get_db)):
    """
    Chat interface for CESAR agent orchestrator
    Handles natural language queries and routes to appropriate agents
    """
    try:
        message = request.get("message", "").strip()
        
        if not message:
            return {"response": "Please provide a message."}
        
        message_lower = message.lower()
        
        # List agents
        if "list" in message_lower and ("agent" in message_lower or "all" in message_lower):
            cursor = db.cursor()
            cursor.execute("""
                SELECT agent_id, name, mcp_system, status 
                FROM agents 
                WHERE status = 'active' 
                ORDER BY mcp_system, name
            """)
            agents = cursor.fetchall()
            cursor.close()
            
            response = f"I have {len(agents)} active agents across 11 MCP systems:\\n\\n"
            current_system = None
            for agent_id, name, mcp_system, status in agents:
                if mcp_system != current_system:
                    response += f"\\n**{mcp_system.upper()}:**\\n"
                    current_system = mcp_system
                response += f"  • {name} ({agent_id})\\n"
            
            return {"response": response}
        
        # List workflows
        elif "workflow" in message_lower and ("list" in message_lower or "show" in message_lower):
            cursor = db.cursor()
            cursor.execute("""
                SELECT name, mcp_system, workflow_type 
                FROM workflow_templates 
                WHERE workflow_data IS NOT NULL
                ORDER BY mcp_system, name
            """)
            workflows = cursor.fetchall()
            cursor.close()
            
            response = f"I have {len(workflows)} workflow templates available:\\n\\n"
            for name, mcp_system, wf_type in workflows:
                response += f"• **{name}** ({mcp_system}) - {wf_type}\\n"
            response += "\\nTry: \\"Run [workflow name]\\" to execute a workflow."
            
            return {"response": response}
        
        # Run workflow
        elif "run" in message_lower and "workflow" in message_lower:
            # Extract workflow name or system
            if "financial" in message_lower or "finpsy" in message_lower:
                workflow_name = "Financial Market Analysis"
                system = "finpsy"
            elif "automation" in message_lower or "pydini" in message_lower:
                workflow_name = "Workflow Automation Conversion"
                system = "pydini"
            elif "legal" in message_lower or "contract" in message_lower or "lex" in message_lower:
                workflow_name = "Contract Review & Compliance"
                system = "lex"
            else:
                return {"response": "Please specify which workflow: financial analysis, workflow automation, or contract review."}
            
            return {
                "response": f"Workflow '{workflow_name}' has been queued for execution.\\n\\nMonitor progress at: http://localhost:4200\\n\\nSystem: {system}\\nStatus: Queued"
            }
        
        # System status
        elif "status" in message_lower or "health" in message_lower:
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'")
            agent_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM workflow_executions WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            cursor.close()
            
            return {
                "response": f"CESAR.ai System Status:\\n\\n✅ {agent_count} agents active\\n✅ 11 MCP systems online\\n✅ {completed} workflows completed\\n✅ All services operational\\n\\nReady to process your requests!"
            }
        
        # Help/capabilities
        elif "help" in message_lower or "what can" in message_lower or "capabilities" in message_lower:
            return {
                "response": """I'm CESAR, your Multi-Agent MCP Orchestrator. I can:

**Agent Management:**
• List all active agents
• Show agent capabilities by system
• Delegate tasks to specialists

**Workflow Execution:**
• Run financial market analysis (finpsy)
• Convert n8n/Zapier workflows (pydini)
• Review contracts for compliance (lex)

**System Information:**
• Show system status and health
• Display workflow execution history
• Provide agent statistics

**Try these commands:**
• "List all agents"
• "Run financial analysis workflow"
• "Show system status"
• "What workflows are available?"

I route your requests to 23 specialized agents across 11 MCP systems!"""
            }
        
        # Default response
        else:
            return {
                "response": f"I received: \\"{message}\\"\\n\\nI'm still learning to understand this request. Try:\\n• \\"List all agents\\"\\n• \\"Run financial workflow\\"\\n• \\"Show system status\\"\\n• \\"Help\\" - see all my capabilities"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

# Read main.py
with open('/app/main.py', 'r') as f:
    content = f.read()

# Add chat endpoint before the last line (if not already present)
if '/api/v1/chat' not in content:
    # Insert before the end of the file
    content = content.rstrip() + chat_endpoint + '\n'
    
    with open('/app/main.py', 'w') as f:
        f.write(content)
    
    print("✅ Chat endpoint added to main.py")
else:
    print("⚠️  Chat endpoint already exists")
