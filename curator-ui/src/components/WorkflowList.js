import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const WorkflowList = () => {
  const [workflows, setWorkflows] = useState([]);
  const [status, setStatus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [workflowsRes, statusRes] = await Promise.all([
        axios.get(`${API_URL}/api/workflows`),
        axios.get(`${API_URL}/api/workflows/status`),
      ]);

      setWorkflows(workflowsRes.data);
      setStatus(statusRes.data);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching workflows:", err);
      setLoading(false);
    }
  };

  const triggerWorkflow = async () => {
    setTriggering(true);
    try {
      await axios.post(`${API_URL}/api/workflows/trigger`, null, {
        params: { workflow_name: "daily_recursive_learning_full" },
      });
      alert("Workflow triggered successfully!");
      // Refresh data after a short delay
      setTimeout(fetchData, 2000);
    } catch (err) {
      console.error("Error triggering workflow:", err);
      alert("Failed to trigger workflow");
    } finally {
      setTriggering(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "running":
        return "bg-blue-100 text-blue-800";
      case "failed":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Workflows</h2>
        <button
          onClick={triggerWorkflow}
          disabled={triggering}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {triggering ? "Triggering..." : "Trigger Learning Flow"}
        </button>
      </div>

      {/* Workflow Status Summary */}
      {status.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Summary</h3>
          <div className="space-y-3">
            {status.map((ws, idx) => (
              <div key={idx} className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="font-semibold text-gray-900">{ws.workflow_name}</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    {ws.total_runs} total runs • {ws.successful_runs} successful • {ws.failed_runs}{" "}
                    failed
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Avg Duration</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {ws.avg_duration_seconds ? `${ws.avg_duration_seconds.toFixed(0)}s` : "N/A"}
                  </div>
                  {ws.last_run_time && (
                    <div className="text-xs text-gray-400 mt-1">
                      Last: {new Date(ws.last_run_time).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Workflow Executions */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Executions</h3>
        <div className="space-y-3">
          {workflows.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-500">No workflow executions found</p>
            </div>
          ) : (
            workflows.map((workflow) => (
              <div key={workflow.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">{workflow.workflow_name}</h4>
                    {workflow.workflow_run_id && (
                      <p className="text-sm text-gray-500 mt-1">Run ID: {workflow.workflow_run_id}</p>
                    )}
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(workflow.status)}`}>
                    {workflow.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-gray-500">Tasks Total</div>
                    <div className="text-lg font-semibold text-gray-900">{workflow.tasks_total}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Completed</div>
                    <div className="text-lg font-semibold text-green-600">{workflow.tasks_completed}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Failed</div>
                    <div className="text-lg font-semibold text-red-600">{workflow.tasks_failed}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Duration</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {workflow.duration_seconds ? `${workflow.duration_seconds}s` : "N/A"}
                    </div>
                  </div>
                </div>

                {workflow.tasks_total > 0 && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{
                        width: `${(workflow.tasks_completed / workflow.tasks_total) * 100}%`,
                      }}
                    ></div>
                  </div>
                )}

                <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between text-xs text-gray-400">
                  <span>Started: {new Date(workflow.start_time).toLocaleString()}</span>
                  {workflow.end_time && <span>Ended: {new Date(workflow.end_time).toLocaleString()}</span>}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkflowList;
