'use client';
import {
  Users,
  BookOpen,
  BrainCircuit,
  Zap,
  Activity,
  X,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

function KpiCard({
  title,
  value,
  gradientClass,
}: {
  title: string;
  value: string;
  gradientClass: string;
}) {
  return (
    <Card className="glass-card">
      <CardContent className="p-4 text-center">
        <div className={`text-5xl font-bold ${gradientClass}`}>{value}</div>
        <p className="text-sm text-muted-foreground mt-2">{title}</p>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [isBannerVisible, setIsBannerVisible] = React.useState(true);

  return (
    <div className="flex flex-col min-h-screen bg-deep-mesh-gradient">
      {isBannerVisible && (
        <div className="bg-primary/80 text-white p-2 text-center text-sm relative">
          <span>
            Unified access to Dell Bocca Boys, Knowledge Base, Learning System,
            and Connectivity Status.
          </span>
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-1/2 right-2 -translate-y-1/2 h-6 w-6 text-white hover:bg-primary/90"
            onClick={() => setIsBannerVisible(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-white">
              Atlas Capital Automations{' '}
              <em className="text-xl font-light text-gray-400 not-italic">
                - a Terry Dellmonaco Co.
              </em>
            </h2>
          </div>
          <Badge className="bg-blue-500 text-white border-blue-400">
            6/6 Connected
          </Badge>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            title="System Connectivity"
            value="100%"
            gradientClass="text-gradient-cyan-blue"
          />
          <KpiCard
            title="Active Agents"
            value="7"
            gradientClass="bg-gradient-to-r from-green-400 to-teal-400 text-transparent bg-clip-text"
          />
          <KpiCard
            title="Knowledge Entries"
            value="17"
            gradientClass="bg-gradient-to-r from-purple-400 to-pink-500 text-transparent bg-clip-text"
          />
          <KpiCard
            title="Success Rate"
            value="1%"
            gradientClass="bg-gradient-to-r from-amber-400 to-orange-500 text-transparent bg-clip-text"
          />
        </div>

        <Card className="glass-card">
          <div className="flex items-center justify-between p-4">
            <div>
              <h3 className="font-semibold text-white">
                CESAR Multi-Agent Ecosystem
              </h3>
              <p className="text-xs text-gray-400 mt-1">
                Last updated: 7:02:49 AM
              </p>
            </div>
            <Button className="glossy-button shadow-lg shadow-blue-500/50 hover:shadow-blue-500/80">
              <Activity className="mr-2 h-4 w-4" />
              Refresh Dashboard
            </Button>
          </div>
        </Card>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="bg-white/10 border border-white/20 text-gray-300">
            <TabsTrigger value="overview" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">Overview</TabsTrigger>
            <TabsTrigger value="dellBoccaBoys" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">CESAR Agent Ecosystem</TabsTrigger>
            <TabsTrigger value="knowledgeBase" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">Knowledge Base</TabsTrigger>
            <TabsTrigger value="learningSystem" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">Learning System</TabsTrigger>
            <TabsTrigger value="connectivity" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">Connectivity</TabsTrigger>
            <TabsTrigger value="cesarLearning" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">CESAR Learning</TabsTrigger>
            <TabsTrigger value="unifiedWorkflows" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">Unified Workflows</TabsTrigger>
            <TabsTrigger value="automationMatrix" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">Automation Matrix</TabsTrigger>
            <TabsTrigger value="aiSkillsEnhancer" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">AI Skills Enhancer</TabsTrigger>
            <TabsTrigger value="systemIntegration" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">
              System Integration
            </TabsTrigger>
            <TabsTrigger value="atlasQuantus" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">Atlas-Quantus</TabsTrigger>
            <TabsTrigger value="recurringWorkflows" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">
              Recurring Workflows
            </TabsTrigger>
            <TabsTrigger value="systemStatus" className="data-[state=active]:bg-primary/80 data-[state=active]:text-white">System Status</TabsTrigger>
          </TabsList>
          <TabsContent value="overview">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2 pt-4">
              <Card className="glass-card">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base font-medium text-white">
                    CESAR Agent Ecosystem Status
                  </CardTitle>
                  <Users className="h-5 w-5 text-gray-400" />
                </CardHeader>
                <CardContent className="space-y-2">
                  <div>
                    <div className="flex justify-between text-sm mb-1 text-gray-300">
                      <span>Active Agents</span>
                      <span>7/6</span>
                    </div>
                    <Progress value={(7 / 6) * 100} className="h-2 bg-white/20 [&>div]:bg-blue-400" />
                  </div>
                  <p className="text-sm text-gray-400 pt-2">
                    Chicky Camarrano, Arthur Bucco, Little Jim Soprano,
                    Collogero Anello, Gerry Torciano, Vito Spatafore,
                    Atlas-Quantus
                  </p>
                </CardContent>
              </Card>
              <Card className="glass-card">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base font-medium text-white">
                    Knowledge Ecosystem
                  </CardTitle>
                  <BookOpen className="h-5 w-5 text-gray-400" />
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">Total Entries</span>
                    <Badge
                      variant="secondary"
                      className="bg-purple-500/20 text-purple-300 border border-purple-500/30"
                    >
                      17
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">Categories</span>
                    <Badge variant="secondary" className="bg-white/10 text-gray-300 border-white/20">9</Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">Avg Confidence</span>
                    <span className="font-bold text-white">95%</span>
                  </div>
                </CardContent>
              </Card>
              <Card className="glass-card">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base font-medium text-white">
                    Learning & Adaptation
                  </CardTitle>
                  <BrainCircuit className="h-5 w-5 text-gray-400" />
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">Learning Patterns</span>
                    <Badge
                      variant="secondary"
                      className="bg-blue-500/20 text-blue-300 border border-blue-500/30"
                    >
                      0
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">Adaptations</span>
                    <span className="text-white">0</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">
                      Collaboration Effectiveness
                    </span>
                    <span className="font-bold text-white">85%</span>
                  </div>
                </CardContent>
              </Card>
              <Card className="glass-card">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base font-medium text-white">
                    System Performance
                  </CardTitle>
                  <Zap className="h-5 w-5 text-gray-400" />
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">Active Workflows</span>
                    <Badge
                      variant="secondary"
                      className="bg-blue-500/20 text-blue-300 border border-blue-500/30"
                    >
                      1
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">Success Rate</span>
                    <span className="text-white">1%</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-400">Total Conversations</span>
                    <span className="text-white">0</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
