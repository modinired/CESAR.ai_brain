import React, { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const MaterialList = () => {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const fetchMaterials = async () => {
      try {
        const params = filter === "all" ? {} : { processed: filter === "processed" };
        const response = await axios.get(`${API_URL}/api/materials`, { params });
        setMaterials(response.data);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching materials:", err);
        setLoading(false);
      }
    };

    fetchMaterials();
  }, [filter]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Learning Materials</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setFilter("all")}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              filter === "all"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 border border-gray-300"
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter("processed")}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              filter === "processed"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 border border-gray-300"
            }`}
          >
            Processed
          </button>
          <button
            onClick={() => setFilter("unprocessed")}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              filter === "unprocessed"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 border border-gray-300"
            }`}
          >
            Unprocessed
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {materials.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500">No materials found</p>
          </div>
        ) : (
          materials.map((material) => (
            <div key={material.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <Link
                    to={`/material/${material.id}`}
                    className="text-xl font-semibold text-blue-600 hover:text-blue-800"
                  >
                    {material.title}
                  </Link>
                  <p className="mt-2 text-gray-600">{material.description}</p>
                  <p className="mt-2 text-sm text-gray-500 line-clamp-2">{material.content}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {material.tags && material.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="ml-4 flex flex-col items-end space-y-2">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      material.processed
                        ? "bg-green-100 text-green-800"
                        : "bg-yellow-100 text-yellow-800"
                    }`}
                  >
                    {material.processed ? "Processed" : "Pending"}
                  </span>
                  <div className="text-right text-sm">
                    <div className="text-gray-500">Quality</div>
                    <div className="font-semibold text-gray-900">
                      {(material.quality_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <div className="text-gray-500">Relevance</div>
                    <div className="font-semibold text-gray-900">
                      {(material.relevance_score * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-400">
                Fetched: {new Date(material.fetched_at).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default MaterialList;
