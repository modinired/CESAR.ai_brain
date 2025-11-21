import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const SystemOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/stats/overview`);
        setStats(response.data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading system stats: {error}</p>
      </div>
    );
  }

  const statCards = [
    { label: "Total Sources", value: stats?.total_sources || 0, color: "blue" },
    { label: "Total Materials", value: stats?.total_materials || 0, color: "green" },
    { label: "Processed Materials", value: stats?.processed_materials || 0, color: "purple" },
    { label: "Total Reflections", value: stats?.total_reflections || 0, color: "orange" },
    { label: "Active Agents", value: stats?.active_agents || 0, color: "red" },
    { label: "Completed Workflows", value: stats?.completed_workflows || 0, color: "indigo" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">System Overview</h2>
        <p className="mt-2 text-gray-600">
          Real-time metrics and performance indicators for the multi-agent learning ecosystem
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat, index) => (
          <div
            key={index}
            className={`bg-white rounded-lg shadow-md p-6 border-l-4 border-${stat.color}-500`}
          >
            <p className="text-sm font-medium text-gray-600">{stat.label}</p>
            <p className="mt-2 text-3xl font-bold text-gray-900">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Quality Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quality Metrics</h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Avg Material Quality</span>
                <span className="font-semibold text-gray-900">
                  {(stats?.avg_material_quality * 100 || 0).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${(stats?.avg_material_quality * 100 || 0)}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Avg Agent Performance</span>
                <span className="font-semibold text-gray-900">
                  {(stats?.avg_agent_performance * 100 || 0).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${(stats?.avg_agent_performance * 100 || 0)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Database</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                Healthy
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">API Server</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                Online
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Prefect Workflows</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                Running
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemOverview;
