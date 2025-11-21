import React, { useEffect, useState } from "react";
import axios from "axios";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const AgentDashboard = () => {
  const [agents, setAgents] = useState([]);
  const [skills, setSkills] = useState([]);
  const [performance, setPerformance] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [agentsRes, skillsRes, perfRes] = await Promise.all([
          axios.get(`${API_URL}/api/agents`),
          axios.get(`${API_URL}/api/agent_skills`),
          axios.get(`${API_URL}/api/agents/performance`),
        ]);

        setAgents(agentsRes.data);
        setSkills(skillsRes.data);
        setPerformance(perfRes.data);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching agent data:", err);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const skillChartData = {
    labels: skills.slice(0, 10).map((s) => s.skill_name),
    datasets: [
      {
        label: "Skill Level",
        data: skills.slice(0, 10).map((s) => s.skill_level * 100),
        backgroundColor: "rgba(34, 197, 94, 0.6)",
        borderColor: "rgba(34, 197, 94, 1)",
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: "Top Agent Skills",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">Agent Dashboard</h2>

      {/* Agent Profiles */}
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Active Agents</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div key={agent.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-start mb-2">
                <h4 className="text-lg font-bold text-gray-900">{agent.agent_name}</h4>
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    agent.status === "active"
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {agent.status}
                </span>
              </div>

              <p className="text-sm text-gray-600 mb-2">{agent.agent_id}</p>
              <p className="text-sm text-gray-500 mb-4">{agent.description}</p>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Type</span>
                  <span className="font-medium text-gray-900">{agent.agent_type}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Performance</span>
                  <span className="font-medium text-gray-900">
                    {(agent.performance_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Success Rate</span>
                  <span className="font-medium text-gray-900">
                    {agent.success_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Tasks Completed</span>
                  <span className="font-medium text-gray-900">
                    {agent.total_tasks_completed}
                  </span>
                </div>
              </div>

              {agent.specialization && agent.specialization.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500 mb-2">Specializations</p>
                  <div className="flex flex-wrap gap-1">
                    {agent.specialization.map((spec, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded"
                      >
                        {spec}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Skills Chart */}
      {skills.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <Bar data={skillChartData} options={chartOptions} />
        </div>
      )}

      {/* Performance Table */}
      {performance.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Agent Performance Overview</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Agent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Skills
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Materials Studied
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reflections
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Performance
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {performance.map((perf) => (
                  <tr key={perf.agent_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {perf.agent_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {perf.agent_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {perf.skill_count} ({(perf.avg_skill_level * 100).toFixed(0)}% avg)
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {perf.materials_studied}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {perf.reflections_created}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${perf.performance_score * 100}%` }}
                          ></div>
                        </div>
                        <span>{(perf.performance_score * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentDashboard;
