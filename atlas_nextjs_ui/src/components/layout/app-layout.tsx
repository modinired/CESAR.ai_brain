'use client';
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
  SidebarTrigger,
  SidebarInset,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarInput,
} from '@/components/ui/sidebar';
import {
  LayoutDashboard,
  Bot,
  GitBranch,
  MessageSquare,
  Search,
  Settings,
  Star,
  LifeBuoy,
  Plus,
  Book,
  HeartPulse,
  Briefcase,
  Database,
  Terminal,
  Cpu,
  Eye,
} from 'lucide-react';
import React from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { Logo } from '../icons/logo';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Separator } from '../ui/separator';

const navItems = [
  { href: '/', icon: <LayoutDashboard />, label: 'LAnding Page (Dashboard)' },
  { href: '/workflows', icon: <GitBranch />, label: 'Workflow Automation' },
  { href: '/agents', icon: <Bot />, label: 'AI Agent Chat' },
  { href: '/financial-reporting', icon: <Book />, label: 'Financial Reporting' },
  { href: '/business-health', icon: <HeartPulse />, label: 'Business Health' },
  { href: '/accounting', icon: <Briefcase />, label: 'Accounting Suite' },
  { href: '/bookkeeping', icon: <Book />, label: 'Bookkeeping Suite' },
  { href: '/ap', icon: <Briefcase />, label: 'AP Suite' },
  { href: '/supabase', icon: <Database />, label: 'Supabase Database' },
  { href: '/agent-forge', icon: <Cpu />, label: 'Agent Forge' },
  { href: '/optic', icon: <Eye />, label: 'Optic Nerve' },
  { href: '/singularity-console', icon: <Cpu />, label: 'Singularity Console' },
  { href: '/terminal', icon: <Terminal />, label: 'Terminal' },
];

const pinnedDashboards = [
  { href: '#', label: 'Q3 Financials' },
  { href: '#', label: 'APAC Growth' },
  { href: '#', label: 'Product Launch Metrics' },
];


export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader>
          <div className="flex items-center justify-between">
            <Logo />
            <SidebarTrigger />
          </div>
          <SidebarInput placeholder="Search..." icon={<Search className="size-4" />} />
        </SidebarHeader>

        <SidebarContent>
          <div className="p-2">
            <Button className="w-full justify-start bg-sidebar-primary text-sidebar-primary-foreground">
              <Plus className="mr-2 h-4 w-4" />
              New
            </Button>
          </div>
          <SidebarGroup>
            <SidebarGroupLabel>My Workspace</SidebarGroupLabel>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <Link href={item.href} legacyBehavior passHref>
                    <SidebarMenuButton
                      isActive={pathname === item.href}
                      icon={item.icon}
                      tooltip={item.label}
                    >
                      {item.label}
                    </SidebarMenuButton>
                  </Link>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
          <Separator />
          <SidebarGroup>
             <SidebarGroupLabel>Pinned Dashboards</SidebarGroupLabel>
             <SidebarMenu>
                {pinnedDashboards.map((item) => (
                    <SidebarMenuItem key={item.label}>
                        <Link href={item.href} legacyBehavior passHref>
                            <SidebarMenuButton
                                isActive={pathname === item.href}
                                icon={<Star className="text-yellow-500" />}
                                tooltip={item.label}
                            >
                                {item.label}
                            </SidebarMenuButton>
                        </Link>
                    </SidebarMenuItem>
                ))}
             </SidebarMenu>
          </SidebarGroup>
        </SidebarContent>

        <SidebarFooter>
          <Separator />
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton icon={<Avatar className="w-7 h-7"><AvatarImage src="https://picsum.photos/seed/10/100/100" data-ai-hint="person face" /><AvatarFallback>U</AvatarFallback></Avatar>}>
                  Atlas-Quantus
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <main>{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
