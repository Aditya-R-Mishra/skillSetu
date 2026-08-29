import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { uploadPDF } from "../api/axios";
import NavBar from "../components/NavBar";

/**
 * Materials page — two upload modes:
 *   1. Text Paste  → POST /materials         (JSON body)
 *   2. PDF Upload  → POST /materials/upload-pdf (multipart/form-data)
 *
 * After uploading, user can click "Generate Quiz" on any material to trigger
 * Gemini AI quiz generation and navigate directly to the quiz taking page.
 */
export default function Materials() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [generatingId, setGeneratingId] = useState(null);
  const [uploadMode, setUploadMode] = useState("text"); // "text" | "pdf"

  const [form, setForm] = useState({
    title: "",
    competency_area: "",
    raw_text: "",
  });
  const [pdfForm, setPdfForm] = useState({
    title: "",
    competency_area: "",
    file: null,
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

  const handlePdfFormChange = (e) => {
    setPdfForm({ ...pdfForm, [e.target.name]: e.target.value });
  };

  // ── Text paste upload ──────────────────────────────────────────────────────
  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError("");
    try {
      await api.post("/materials", form);
      setForm({ title: "", competency_area: "", raw_text: "" });
      fetchMaterials();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map((d) => d.msg).join(", ")
          : detail || "Failed to create material."
      );
    } finally {
      setCreating(false);
    }
  };

  // ── PDF upload ─────────────────────────────────────────────────────────────
  const handlePdfUpload = async (e) => {
    e.preventDefault();
    if (!pdfForm.file) {
      setError("Please select a PDF file.");
      return;
    }
    setCreating(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("title", pdfForm.title);
      formData.append("competency_area", pdfForm.competency_area);
      formData.append("file", pdfForm.file);
      await uploadPDF(formData);
      setPdfForm({ title: "", competency_area: "", file: null });
      if (fileInputRef.current) fileInputRef.current.value = "";
      fetchMaterials();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map((d) => d.msg).join(", ")
          : detail || "Failed to upload PDF."
      );
    } finally {
      setCreating(false);
    }
  };

  // ── Generate quiz from a material ─────────────────────────────────────────
  const handleGenerateQuiz = async (materialId) => {
    setGeneratingId(materialId);
    setError("");
    try {
      const res = await api.post(`/materials/${materialId}/generate-quiz`);
      navigate(`/quiz/${res.data.quiz_id}/take`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map((d) => d.msg).join(", ")
          : detail || "Failed to generate quiz."
      );
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

        {/* ── Mode toggle ── */}
        <div className="flex gap-2 mb-4">
          <button
            type="button"
            onClick={() => { setUploadMode("text"); setError(""); }}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
              uploadMode === "text"
                ? "bg-black text-white"
                : "border hover:bg-gray-100 text-gray-700"
            }`}
          >
            📝 Paste Text
          </button>
          <button
            type="button"
            onClick={() => { setUploadMode("pdf"); setError(""); }}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
              uploadMode === "pdf"
                ? "bg-black text-white"
                : "border hover:bg-gray-100 text-gray-700"
            }`}
          >
            📄 Upload PDF
          </button>
        </div>

        {/* ── Text paste form ── */}
        {uploadMode === "text" && (
          <form
            onSubmit={handleCreate}
            className="border rounded-xl p-5 mb-8 space-y-3"
          >
            <h2 className="font-semibold">Add Material — Paste Text</h2>
            <input
              name="title"
              value={form.title}
              onChange={handleChange}
              placeholder="Title (e.g. Introduction to Survey Design)"
              required
              minLength={3}
              maxLength={150}
              className="w-full border rounded-lg p-2 text-sm"
            />
            <input
              name="competency_area"
              value={form.competency_area}
              onChange={handleChange}
              placeholder="Competency Area (e.g. Survey Design, Data Analysis)"
              required
              minLength={2}
              maxLength={100}
              className="w-full border rounded-lg p-2 text-sm"
            />
            <textarea
              name="raw_text"
              value={form.raw_text}
              onChange={handleChange}
              placeholder="Paste learning material text here (minimum 50 words required)..."
              required
              rows={6}
              className="w-full border rounded-lg p-2 text-sm"
            />
            <p className="text-xs text-gray-400">
              Word count: {form.raw_text.trim() ? form.raw_text.trim().split(/\s+/).length : 0} / 50 minimum
            </p>
            <button
              type="submit"
              disabled={creating}
              className="px-4 py-2 bg-black text-white rounded-lg text-sm disabled:opacity-50"
            >
              {creating ? "Adding..." : "Add Material"}
            </button>
          </form>
        )}

        {/* ── PDF upload form ── */}
        {uploadMode === "pdf" && (
          <form
            onSubmit={handlePdfUpload}
            className="border rounded-xl p-5 mb-8 space-y-3"
          >
            <h2 className="font-semibold">Add Material — Upload PDF</h2>
            <input
              name="title"
              value={pdfForm.title}
              onChange={handlePdfFormChange}
              placeholder="Title (e.g. Survey Methodology Notes)"
              required
              minLength={3}
              maxLength={150}
              className="w-full border rounded-lg p-2 text-sm"
            />
            <input
              name="competency_area"
              value={pdfForm.competency_area}
              onChange={handlePdfFormChange}
              placeholder="Competency Area (e.g. Field Methodology)"
              required
              minLength={2}
              maxLength={100}
              className="w-full border rounded-lg p-2 text-sm"
            />
            <div className="border-2 border-dashed rounded-lg p-4 text-center">
              <p className="text-sm text-gray-500 mb-2">
                PDF only · Max 10 MB · Min 50 words of extractable text
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                required
                onChange={(e) =>
                  setPdfForm({ ...pdfForm, file: e.target.files[0] || null })
                }
                className="text-sm"
              />
              {pdfForm.file && (
                <p className="text-xs text-green-600 mt-1">
                  ✓ {pdfForm.file.name} ({(pdfForm.file.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>
            <button
              type="submit"
              disabled={creating || !pdfForm.file}
              className="px-4 py-2 bg-black text-white rounded-lg text-sm disabled:opacity-50"
            >
              {creating ? "Uploading & Extracting..." : "Upload PDF"}
            </button>
          </form>
        )}

        {/* ── Materials list ── */}
        <h2 className="font-semibold mb-3">Your Materials</h2>
        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : materials.length === 0 ? (
          <p className="text-gray-500">No materials yet. Add one above.</p>
        ) : (
          <div className="space-y-3">
            {materials.map((m) => (
              <div
                key={m._id || m.id}
                className="border rounded-xl p-4 flex justify-between items-center"
              >
                <div>
                  <div className="font-medium">{m.title}</div>
                  <div className="text-xs text-gray-500">
                    {m.competency_area}
                    {m.file_type === "pdf" && (
                      <span className="ml-2 px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">
                        PDF
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleGenerateQuiz(m._id || m.id)}
                  disabled={generatingId === (m._id || m.id)}
                  className="px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-100 disabled:opacity-50 whitespace-nowrap"
                >
                  {generatingId === (m._id || m.id)
                    ? "Generating AI Quiz..."
                    : "Generate Quiz →"}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}