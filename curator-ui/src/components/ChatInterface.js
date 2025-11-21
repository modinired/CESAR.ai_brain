import React, { useState, useRef, useEffect } from 'react';

function ChatInterface() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am CESAR, your AI agent orchestrator. Ask me to run workflows, analyze data, or delegate tasks to specialized agents.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });
      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, { role: 'assistant', content: data.response || 'Task received' }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Use API docs at http://localhost:8000/docs' }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Use API docs at http://localhost:8000/docs' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-20rem)] bg-slate-900/50 rounded-xl border border-slate-800">
      <div className="flex items-center justify-between p-4 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
            <span className="text-white font-bold">C</span>
          </div>
          <div>
            <h3 className="text-white font-semibold">CESAR Agent</h3>
            <p className="text-slate-400 text-xs">23 agents • 11 MCP systems</p>
          </div>
        </div>
        <span className="text-green-400 text-sm">● Online</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ` + (msg.role === 'user' ? 'justify-end' : 'justify-start')}>
            <div className={`max-w-[80%] rounded-lg px-4 py-2 ` + (msg.role === 'user' ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-100 border border-slate-700')}>
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2">
              <div className="flex space-x-2"><div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce"></div></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="p-4 border-t border-slate-800">
        <div className="flex space-x-2">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => { if (e.key === 'Enter') { e.preventDefault(); sendMessage(); }}}
            placeholder="Ask CESAR to run workflows, analyze data, or delegate tasks..."
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            disabled={isLoading} />
          <button onClick={sendMessage} disabled={isLoading || !input.trim()}
            className="bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700 text-white px-6 py-2 rounded-lg">Send</button>
        </div>
        <p className="text-slate-400 text-xs mt-2">Try: "Run financial analysis" or "List active agents"</p>
      </div>
    </div>
  );
}

export default ChatInterface;
