import { useEffect, useState } from "react";
import api from "../api/axios";
import NavBar from "../components/NavBar";

/**
 * Recommendations page — shows personalized course recommendations for
 * competency areas where the learner scored Weak or Moderate.
 *
 * Backend endpoints used:
 *   GET  /recommendations                        → list of weak/moderate areas + courses
 *   POST /recommendations/{competency_area}/sync-igot  → simulated iGOT enrollment
 */
export default function Recommendations() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [syncingArea, setSyncingArea] = useState(null); // area currently syncing
  const [syncResults, setSyncResults] = useState({}); // { area: igot_response }

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const res = await api.get("/recommendations");
        setRecommendations(res.data);
      } catch (err) {
        setError(
          err.response?.data?.detail || "Failed to load recommendations."
        );
      } finally {
        setLoading(false);
      }
    };
    fetchRecommendations();
  }, []);

  const handleSyncIGOT = async (competencyArea) => {
    setSyncingArea(competencyArea);
    try {
      const res = await api.post(
        `/recommendations/${encodeURIComponent(competencyArea)}/sync-igot`
      );
      setSyncResults((prev) => ({ ...prev, [competencyArea]: res.data }));
    } catch (err) {
      setSyncResults((prev) => ({
        ...prev,
        [competencyArea]: {
          error: err.response?.data?.detail || "Sync failed. Try again.",
        },
      }));
    } finally {
      setSyncingArea(null);
    }
  };

  const gapBadge = {
    Weak: "bg-red-100 text-red-700",
    Moderate: "bg-yellow-100 text-yellow-700",
    Strong: "bg-green-100 text-green-700",
  };

  return (
    <div>
      <NavBar />
      <div className="px-8 max-w-3xl mx-auto pb-16">
        <h1 className="text-2xl font-bold mb-2">Personalized Recommendations</h1>
        <p className="text-sm text-gray-500 mb-6">
          Targeted course modules for your weak and moderate competency areas.
        </p>

        {loading && <p className="text-gray-500">Loading recommendations...</p>}

        {!loading && error && (
          <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {!loading && !error && recommendations.length === 0 && (
          <div className="border rounded-xl p-6 text-center text-gray-500">
            <p className="mb-2">No recommendations yet.</p>
            <p className="text-sm">
              Take a quiz first — if you score below 75%, a course recommendation
              will appear here.
            </p>
          </div>
        )}

        {!loading && !error && recommendations.length > 0 && (
          <div className="space-y-4">
            {recommendations.map((rec) => {
              const synced = syncResults[rec.competency_area];
              return (
                <div
                  key={rec.competency_area}
                  className="border rounded-xl p-5 space-y-3"
                >
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="font-semibold text-base">
                        {rec.competency_area}
                      </h2>
                      <p className="text-xs text-gray-500">
                        Latest score: {rec.latest_score_percent}%
                      </p>
                    </div>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        gapBadge[rec.gap_level] || "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {rec.gap_level}
                    </span>
                  </div>

                  {/* Recommended course card */}
                  {rec.recommended_course && (
                    <div className="bg-slate-50 rounded-lg p-4 text-sm space-y-1">
                      <div className="font-medium text-slate-800">
                        {rec.recommended_course.course_title}
                      </div>
                      <div className="text-xs text-slate-500">
                        Course Code:{" "}
                        <span className="font-mono font-semibold text-indigo-600">
                          {rec.recommended_course.igot_course_code}
                        </span>
                      </div>
                      {rec.recommended_course.description && (
                        <p className="text-gray-600 text-xs pt-1">
                          {rec.recommended_course.description}
                        </p>
                      )}
                      <div className="flex gap-3 text-xs text-gray-500 pt-1">
                        {rec.recommended_course.duration && (
                          <span>⏱ {rec.recommended_course.duration}</span>
                        )}
                        {rec.recommended_course.difficulty && (
                          <span>📊 {rec.recommended_course.difficulty}</span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* iGOT Sync button / result */}
                  {synced ? (
                    synced.error ? (
                      <p className="text-xs text-red-600">⚠ {synced.error}</p>
                    ) : (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm">
                        <p className="text-green-700 font-medium">
                          ✓ Synced with iGOT Karmayogi
                        </p>
                        <p className="text-green-600 text-xs mt-1">
                          {synced.message}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          iGOT Course Code:{" "}
                          <span className="font-mono font-semibold">
                            {synced.igot_course_code}
                          </span>
                        </p>
                      </div>
                    )
                  ) : (
                    <button
                      onClick={() => handleSyncIGOT(rec.competency_area)}
                      disabled={syncingArea === rec.competency_area}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50 transition"
                    >
                      {syncingArea === rec.competency_area
                        ? "Syncing..."
                        : "🔗 Sync with iGOT Karmayogi"}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
