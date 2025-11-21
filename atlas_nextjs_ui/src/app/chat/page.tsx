import AppLayout from '@/components/layout/app-layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Paperclip, ScreenShare, Send, Bot, User } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';

const messages = [
    { from: 'bot', text: 'Hello! I am the CESAR.AI assistant. How can I help you with your data analysis today?' },
    { from: 'user', text: 'Can you give me a summary of the latest anomaly report?' },
    { from: 'bot', text: 'Certainly. The latest report highlights a significant spike in operational costs for the APAC region, up 15% month-over-month. This is considered a high-priority anomaly. Would you like me to generate a detailed breakdown?' },
];

export default function ChatPage() {
  return (
    <AppLayout>
      <div className="flex h-[calc(100vh-60px)]">
        <div className="flex-1 flex flex-col p-4">
          <Card className="flex-1 flex flex-col">
            <CardHeader>
              <CardTitle>Chat with AI Assistant</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
                <ScrollArea className="flex-1 mb-4 pr-4">
                    <div className="space-y-6">
                        {messages.map((msg, index) => (
                            <div key={index} className={`flex items-start gap-3 ${msg.from === 'user' ? 'justify-end' : ''}`}>
                                {msg.from === 'bot' && (
                                    <Avatar>
                                        <AvatarFallback><Bot className="text-primary"/></AvatarFallback>
                                    </Avatar>
                                )}
                                <div className={`rounded-lg p-3 max-w-md ${msg.from === 'bot' ? 'bg-muted' : 'bg-primary text-primary-foreground'}`}>
                                    <p className="text-sm">{msg.text}</p>
                                </div>
                                {msg.from === 'user' && (
                                    <Avatar>
                                        <AvatarFallback><User /></AvatarFallback>
                                    </Avatar>
                                )}
                            </div>
                        ))}
                    </div>
                </ScrollArea>
                <div className="relative">
                    <Input placeholder="Type your message..." className="pr-32" />
                    <div className="absolute inset-y-0 right-0 flex items-center">
                        <Button variant="ghost" size="icon"><Paperclip className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="icon"><ScreenShare className="w-4 h-4" /></Button>
                        <Button size="icon" className="mr-2"><Send className="w-4 h-4" /></Button>
                    </div>
                </div>
            </CardContent>
          </Card>
        </div>

        <div className="w-1/3 border-l bg-card flex flex-col p-4">
            <Card className="flex-1 flex flex-col bg-gray-900 text-gray-200 font-mono border-gray-700">
                <CardHeader className="border-b border-gray-700">
                    <CardTitle className="text-gray-200">CLI Terminal</CardTitle>
                </CardHeader>
                <CardContent className="flex-1 p-4 text-sm">
                    <p><span className="text-green-400">user@cesar-ai</span>:<span className="text-blue-400">~</span>$ run forecast --scenario=recession</p>
                    <p>Initializing forecasting agent...</p>
                    <p>Loading historical data model...</p>
                    <p>Generating forecast for 'recession' scenario... <span className="animate-pulse">|</span></p>
                    <br/>
                    <p className="text-green-400">Forecast complete.</p>
                    <p>Results saved to /forecasts/recession_q3_2024.json</p>
                    <br/>
                    <p><span className="text-green-400">user@cesar-ai</span>:<span className="text-blue-400">~</span>$ <span className="animate-pulse">_</span></p>
                </CardContent>
            </Card>
        </div>
      </div>
    </AppLayout>
  );
}
