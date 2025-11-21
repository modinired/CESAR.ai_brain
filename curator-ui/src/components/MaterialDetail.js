import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const MaterialDetail = () => {
  const { id } = useParams();
  const [material, setMaterial] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [materialRes, similarRes] = await Promise.all([
          axios.get(`${API_URL}/api/materials/${id}`),
          axios.get(`${API_URL}/api/materials/${id}/similar`).catch(() => ({ data: [] }))
        ]);

        setMaterial(materialRes.data);
        setSimilar(similarRes.data);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching material:", err);
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!material) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Material not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/materials" className="text-blue-600 hover:text-blue-800 text-sm">
          ← Back to Materials
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex justify-between items-start">
          <h2 className="text-3xl font-bold text-gray-900">{material.title}</h2>
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              material.processed
                ? "bg-green-100 text-green-800"
                : "bg-yellow-100 text-yellow-800"
            }`}
          >
            {material.processed ? "Processed" : "Pending"}
          </span>
        </div>

        {material.description && (
          <p className="mt-4 text-lg text-gray-600">{material.description}</p>
        )}

        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-500">Quality Score</div>
            <div className="text-2xl font-bold text-gray-900">
              {(material.quality_score * 100).toFixed(0)}%
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-500">Relevance Score</div>
            <div className="text-2xl font-bold text-gray-900">
              {(material.relevance_score * 100).toFixed(0)}%
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-500">Fetched</div>
            <div className="text-lg font-semibold text-gray-900">
              {new Date(material.fetched_at).toLocaleDateString()}
            </div>
          </div>
        </div>

        {material.tags && material.tags.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {material.tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Content</h3>
          <div className="prose max-w-none">
            <p className="text-gray-700 whitespace-pre-wrap">{material.content}</p>
          </div>
        </div>
      </div>

      {similar && similar.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Similar Materials</h3>
          <div className="space-y-3">
            {similar.map((item) => (
              <Link
                key={item.id}
                to={`/material/${item.id}`}
                className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">{item.title}</h4>
                    {item.description && (
                      <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                    )}
                  </div>
                  <div className="ml-4 text-sm font-semibold text-blue-600">
                    {(item.similarity_score * 100).toFixed(0)}% match
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MaterialDetail;
