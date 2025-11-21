import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const ReflectionList = () => {
  const [reflections, setReflections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReflections = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/reflections`);
        setReflections(response.data);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching reflections:", err);
        setLoading(false);
      }
    };

    fetchReflections();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">Learning Reflections</h2>

      <div className="grid grid-cols-1 gap-6">
        {reflections.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500">No reflections found</p>
          </div>
        ) : (
          reflections.map((reflection) => (
            <div key={reflection.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className="inline-block px-3 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded-full">
                    {reflection.reflection_type}
                  </span>
                  <span className="ml-2 text-sm text-gray-500">
                    by <strong>{reflection.agent_id}</strong>
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Score</div>
                  <div className="text-lg font-bold text-gray-900">
                    {(reflection.reflection_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap">{reflection.reflection_text}</p>
              </div>

              {reflection.key_insights && reflection.key_insights.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Insights</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {reflection.key_insights.map((insight, idx) => (
                      <li key={idx} className="text-sm text-gray-600">
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-400">
                  {new Date(reflection.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ReflectionList;
