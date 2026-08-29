import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import NavBar from "../components/NavBar";

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await api.get("/dashboard");
        setData(res.data);
      } catch (err) {
        setError(
          err.response?.data?.detail || "Failed to load dashboard data."
        );
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  const gapColor = {
    Strong: "bg-green-100 text-green-700",
    Moderate: "bg-yellow-100 text-yellow-700",
    Weak: "bg-red-100 text-red-700",
  };

  const formatDate = (value) => {
    if (!value) return "";
    const d = new Date(value);
    if (isNaN(d.getTime())) return String(value);
    return d.toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div>
      <NavBar />
      <div className="px-8 max-w-5xl mx-auto pb-16">
        <h1 className="text-2xl font-bold mb-6">
          Welcome{user?.name ? `, ${user.name}` : ""} 
        </h1>

        {loading && (
          <div className="text-gray-500">Loading dashboard...</div>
        )}

        {!loading && error && (
          <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {!loading && !error && data && (
          <>
            {/* Stat cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard label="Quizzes Taken" value={data.total_quizzes_taken} />
              <StatCard
                label="Strong Areas"
                value={data.strong_areas_count}
                color="text-green-600"
              />
              <StatCard
                label="Moderate Areas"
                value={data.moderate_areas_count}
                color="text-yellow-600"
              />
              <StatCard
                label="Weak Areas"
                value={data.weak_areas_count}
                color="text-red-600"
              />
            </div>

            {/* Competency breakdown */}
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-lg font-semibold">Competency Breakdown</h2>
              <Link
                to="/materials"
                className="text-sm text-blue-600 hover:underline"
              >
                + Take another quiz
              </Link>
            </div>

            {data.competency_breakdown.length === 0 ? (
              <EmptyState
                message="No quiz attempts yet."
                actionLabel="Add material & take a quiz"
                to="/materials"
              />
            ) : (
              <div className="overflow-x-auto mb-8 border rounded-xl">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-left">
                    <tr>
                      <th className="p-3">Competency Area</th>
                      <th className="p-3">Latest Score</th>
                      <th className="p-3">Average Score</th>
                      <th className="p-3">Gap Level</th>
                      <th className="p-3">Attempts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.competency_breakdown.map((c) => (
                      <tr key={c.competency_area} className="border-t">
                        <td className="p-3 font-medium">
                          {c.competency_area}
                        </td>
                        <td className="p-3">{c.latest_score_percent}%</td>
                        <td className="p-3">{c.average_score_percent}%</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              gapColor[c.gap_level] ||
                              "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {c.gap_level}
                          </span>
                        </td>
                        <td className="p-3">{c.attempts_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Recent attempts */}
            <h2 className="text-lg font-semibold mb-3">Recent Attempts</h2>
            {data.recent_attempts.length === 0 ? (
              <EmptyState message="No recent attempts yet." />
            ) : (
              <div className="space-y-2 mb-8">
                {data.recent_attempts.map((a, i) => {
                  const area = a.competency_area || a.material_title || "Quiz";
                  const score =
                    a.score_percent !== undefined ? `${a.score_percent}%` : null;
                  const gap = a.gap_level;
                  const date = a.attempted_at || a.created_at;

                  return (
                    <div
                      key={a._id || i}
                      className="border rounded-xl p-4 flex justify-between items-center text-sm"
                    >
                      <div>
                        <div className="font-medium">{area}</div>
                        {date && (
                          <div className="text-xs text-gray-500">
                            {formatDate(date)}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        {score && (
                          <span className="text-gray-700">{score}</span>
                        )}
                        {gap && (
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              gapColor[gap] || "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {gap}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, color = "text-gray-900" }) {
  return (
    <div className="border rounded-xl p-4 text-center shadow-sm">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}

function EmptyState({ message, actionLabel, to }) {
  return (
    <div className="border rounded-xl p-6 text-center mb-8">
      <p className="text-gray-500 mb-3">{message}</p>
      {actionLabel && to && (
        <Link
          to={to}
          className="inline-block px-4 py-2 bg-black text-white rounded-lg text-sm"
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
}