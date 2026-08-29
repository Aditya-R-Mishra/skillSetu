import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import NavBar from "../components/NavBar";

export default function Materials() {
  const navigate = useNavigate();
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [generatingId, setGeneratingId] = useState(null);

  const [form, setForm] = useState({
    title: "",
    competency_area: "",
    raw_text: "",
  });

  const fetchMaterials = async () => {
    setLoading(true);
    try {
      const res = await api.get("/materials");
      setMaterials(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load materials.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaterials();
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError("");
    try {
      await api.post("/materials", form);
      setForm({ title: "", competency_area: "", raw_text: "" });
      fetchMaterials();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create material.");
    } finally {
      setCreating(false);
    }
  };

  const handleGenerateQuiz = async (materialId) => {
    setGeneratingId(materialId);
    setError("");
    try {
      const res = await api.post(`/materials/${materialId}/generate-quiz`);
      navigate(`/quiz/${res.data.quiz_id}/take`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate quiz.");
    } finally {
      setGeneratingId(null);
    }
  };

  return (
    <div>
      <NavBar />
      <div className="px-8 max-w-3xl mx-auto pb-16">
        <h1 className="text-2xl font-bold mb-6">Learning Materials</h1>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Create form */}
        <form
          onSubmit={handleCreate}
          className="border rounded-xl p-5 mb-8 space-y-3"
        >
          <h2 className="font-semibold">Add New Material</h2>
          <input
            name="title"
            value={form.title}
            onChange={handleChange}
            placeholder="Title"
            required
            minLength={3}
            maxLength={150}
            className="w-full border rounded-lg p-2 text-sm"
          />
          <input
            name="competency_area"
            value={form.competency_area}
            onChange={handleChange}
            placeholder="Competency Area (e.g. Statistics, Data Visualization)"
            required
            minLength={2}
            maxLength={100}
            className="w-full border rounded-lg p-2 text-sm"
          />
          <textarea
            name="raw_text"
            value={form.raw_text}
            onChange={handleChange}
            placeholder="Paste learning material text here..."
            required
            rows={5}
            className="w-full border rounded-lg p-2 text-sm"
          />
          <button
            type="submit"
            disabled={creating}
            className="px-4 py-2 bg-black text-white rounded-lg text-sm disabled:opacity-50"
          >
            {creating ? "Adding..." : "Add Material"}
          </button>
        </form>

        {/* List */}
        <h2 className="font-semibold mb-3">Your Materials</h2>
        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : materials.length === 0 ? (
          <p className="text-gray-500">No materials yet. Add one above.</p>
        ) : (
          <div className="space-y-3">
            {materials.map((m) => (
              <div
                key={m._id}
                className="border rounded-xl p-4 flex justify-between items-center"
              >
                <div>
                  <div className="font-medium">{m.title}</div>
                  <div className="text-xs text-gray-500">
                    {m.competency_area}
                  </div>
                </div>
                <button
                  onClick={() => handleGenerateQuiz(m._id)}
                  disabled={generatingId === m._id}
                  className="px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50"
                >
                  {generatingId === m._id ? "Generating..." : "Generate Quiz"}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}