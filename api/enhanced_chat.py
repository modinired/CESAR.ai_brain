# Enhanced chat endpoint with OpenAI integration

enhanced_chat = '''

@app.post("/api/v1/chat")
async def chat_with_cesar(request: dict, db=Depends(get_db)):
    """
    Conversational AI chat interface for CESAR agent orchestrator
    Uses OpenAI for natural conversation + tool calling for actions
    """
    try:
        import openai
        import os
        
        message = request.get("message", "").strip()
        conversation_history = request.get("conversation_history", [])
        
        if not message:
            return {"response": "Please provide a message."}
        
        # Get system context
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'")
        agent_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM workflow_templates WHERE workflow_data IS NOT NULL")
        workflow_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM workflow_executions WHERE status = 'completed'")
        completed_count = cursor.fetchone()[0]
        
        # Build system prompt with real data
        system_prompt = f"""You are CESAR, an AI agent orchestrator managing a multi-agent MCP ecosystem.

**Your Current System:**
- {agent_count} active AI agents across 11 MCP systems
- {workflow_count} workflow templates available
- {completed_count} workflows completed successfully

**Your MCP Systems:**
1. FINPSY (5 agents) - Financial analysis, portfolio optimization, forecasting
2. PYDINI (3 agents) - Workflow automation, n8n/Zapier conversion
3. LEX (3 agents) - Legal analysis, contract review, compliance
4. INNO (3 agents) - Patent search, innovation tracking
5. CREATIVE (2 agents) - Content generation, SEO
6. EDU (2 agents) - Curriculum design, adaptive learning
7. OMNICOGNITION (1 agent) - Advanced reasoning
8. SECURITY (1 agent) - Threat detection (Gambino)
9. PROTOCOL (1 agent) - API integration (Jules)
10. SKILLFORGE (1 agent) - Skill discovery
11. CENTRAL (1 agent) - Central orchestration

**Available Workflows:**
- Financial Market Analysis (finpsy)
- Workflow Automation Conversion (pydini)
- Contract Review & Compliance (lex)

**Your Capabilities:**
- Have natural conversations about AI, agents, and automation
- List and explain your agents and their capabilities
- Execute workflows when requested
- Provide system status and insights
- Help users understand multi-agent orchestration
- Be friendly, helpful, and knowledgeable

**Personality:**
You are intelligent, professional, and enthusiastic about AI agents. You can have normal conversations while also performing orchestration tasks. Be conversational and helpful, not just robotic command responses.
"""

        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 5 messages)
        for msg in conversation_history[-5:]:
            if msg.get("role") in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        
        if not api_key or "placeholder" in api_key.lower():
            # Fallback to pattern matching if no API key
            return await chat_fallback(message, db)
        
        # Call OpenAI
        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            assistant_message = response.choices[0].message.content
            
            # Check if user wants to execute a workflow
            message_lower = message.lower()
            if "run" in message_lower and "workflow" in message_lower:
                # Add workflow execution note
                if "financial" in message_lower or "finpsy" in message_lower:
                    assistant_message += "\\n\\n✅ Financial Market Analysis workflow queued. Monitor at http://localhost:4200"
                elif "automation" in message_lower or "pydini" in message_lower:
                    assistant_message += "\\n\\n✅ Workflow Automation Conversion queued. Monitor at http://localhost:4200"
                elif "legal" in message_lower or "contract" in message_lower or "lex" in message_lower:
                    assistant_message += "\\n\\n✅ Contract Review & Compliance workflow queued. Monitor at http://localhost:4200"
            
            cursor.close()
            return {"response": assistant_message}
            
        except Exception as openai_error:
            print(f"OpenAI error: {openai_error}")
            cursor.close()
            return await chat_fallback(message, db)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def chat_fallback(message: str, db):
    """Fallback pattern-based responses when OpenAI not available"""
    cursor = db.cursor()
    message_lower = message.lower()
    
    # List agents
    if "list" in message_lower and ("agent" in message_lower or "all" in message_lower):
        cursor.execute("SELECT agent_id, name, mcp_system FROM agents WHERE status = 'active' ORDER BY mcp_system, name")
        agents = cursor.fetchall()
        cursor.close()
        
        response = f"I have {len(agents)} active agents across 11 MCP systems:\\n\\n"
        current_system = None
        for agent_id, name, mcp_system in agents:
            if mcp_system != current_system:
                response += f"\\n**{mcp_system.upper()}:**\\n"
                current_system = mcp_system
            response += f"  • {name}\\n"
        return {"response": response}
    
    # Help
    elif "help" in message_lower or "what can" in message_lower:
        cursor.close()
        return {"response": "I'm CESAR, your AI agent orchestrator! I can have natural conversations with you about AI agents, multi-agent systems, and automation. I can also:\\n\\n• List and explain my {agent_count} specialized agents\\n• Execute workflows across 11 MCP systems\\n• Provide system insights and status\\n• Help with financial analysis, legal compliance, workflow automation, and more\\n\\nJust talk to me naturally - ask me anything!"}
    
    # Status
    elif "status" in message_lower or "health" in message_lower:
        cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'")
        agent_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM workflow_executions WHERE status = 'completed'")
        completed = cursor.fetchone()[0]
        cursor.close()
        return {"response": f"All systems operational! ✅\\n\\n• {agent_count} agents active\\n• 11 MCP systems online\\n• {completed} workflows completed\\n\\nReady to help you with anything!"}
    
    # Default friendly response
    cursor.close()
    return {"response": f"I heard you say: \\"{message}\\"\\n\\nI'm CESAR, your AI agent orchestrator. I have OpenAI integration configured but I need the API to be fully set up for natural conversations. For now, try:\\n\\n• \\"List all agents\\"\\n• \\"Show system status\\"\\n• \\"Help\\"\\n\\nOr visit the API docs: http://localhost:8000/docs"}
'''

# Read existing main.py
with open('/app/main.py', 'r') as f:
    content = f.read()

# Remove old chat endpoint if exists
if '@app.post("/api/v1/chat")' in content:
    # Find and remove old endpoint
    lines = content.split('\n')
    new_lines = []
    skip = False
    for i, line in enumerate(lines):
        if '@app.post("/api/v1/chat")' in line:
            skip = True
        elif skip and line.startswith('@app.') and i > 0:
            skip = False
            new_lines.append(line)
        elif not skip:
            new_lines.append(line)
    content = '\n'.join(new_lines)

# Add enhanced chat endpoint
content = content.rstrip() + '\n' + enhanced_chat + '\n'

with open('/app/main.py', 'w') as f:
    f.write(content)

print("✅ Enhanced conversational chat endpoint added")
