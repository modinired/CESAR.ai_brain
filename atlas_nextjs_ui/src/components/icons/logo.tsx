import { Bot } from 'lucide-react';

export function Logo() {
  return (
    <div className="flex items-center gap-2 font-bold text-lg text-sidebar-foreground">
      <div className="bg-sidebar-accent rounded-lg p-1.5">
        <Bot className="h-6 w-6 text-sidebar-foreground" />
      </div>
      <span className="font-headline">CESAR.AI</span>
    </div>
  );
}
