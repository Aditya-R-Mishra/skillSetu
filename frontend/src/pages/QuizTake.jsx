import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "../api/axios";
import NavBar from "../components/NavBar";

export default function QuizTake() {
  const { quizId } = useParams();
  const navigate = useNavigate();

  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const res = await api.get(`/quizzes/${quizId}`);
        setQuiz(res.data);
        setAnswers(new Array(res.data.questions.length).fill(-1));
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load quiz.");
      } finally {
        setLoading(false);
      }
    };
    fetchQuiz();
  }, [quizId]);

  const handleSelect = (questionIndex, optionIndex) => {
    const updated = [...answers];
    updated[questionIndex] = optionIndex;
    setAnswers(updated);
  };

  const handleSubmit = async () => {
    if (answers.includes(-1)) {
      setError("Please answer all questions before submitting.");
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const res = await api.post(`/quizzes/${quizId}/submit`, { answers });
      setResult(res.data);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit quiz.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <NavBar />
      <div className="px-8 max-w-3xl mx-auto pb-16">
        {loading && <div className="text-gray-500">Loading quiz...</div>}

        {!loading && error && !quiz && (
          <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* ---- Result view ---- */}
        {!loading && quiz && result && (
          <ResultView result={result} navigate={navigate} />
        )}

        {/* ---- Quiz-taking view ---- */}
        {!loading && quiz && !result && (
          <>
            <div className="flex justify-between items-start mb-1">
              <h1 className="text-2xl font-bold">{quiz.title}</h1>
              <Link
                to="/materials"
                className="text-sm text-blue-600 hover:underline whitespace-nowrap ml-4"
              >
                ← Materials
              </Link>
            </div>
            <p className="text-sm text-gray-500 mb-6">
              {quiz.competency_area}
            </p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div className="space-y-6 mb-8">
              {quiz.questions.map((q) => (
                <div key={q.question_index} className="border rounded-xl p-4">
                  <p className="font-medium mb-3">
                    {q.question_index + 1}. {q.question}
                  </p>
                  <div className="space-y-2">
                    {q.options.map((opt, i) => (
                      <label
                        key={i}
                        className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer text-sm ${
                          answers[q.question_index] === i
                            ? "border-black bg-gray-100"
                            : "border-gray-200"
                        }`}
                      >
                        <input
                          type="radio"
                          name={`q-${q.question_index}`}
                          checked={answers[q.question_index] === i}
                          onChange={() => handleSelect(q.question_index, i)}
                        />
                        {opt}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-5 py-2.5 bg-black text-white rounded-lg text-sm disabled:opacity-50"
            >
              {submitting ? "Submitting..." : "Submit Quiz"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function ResultView({ result, navigate }) {
  const gapTextColor = {
    Strong: "text-green-600",
    Moderate: "text-yellow-600",
    Weak: "text-red-600",
  };

  return (
    <>
      <h1 className="text-2xl font-bold mb-2">Quiz Results</h1>
      <p className="mb-6 text-gray-600">
        Score:{" "}
        <span className="font-semibold">
          {result.correct_count}/{result.total_questions} (
          {result.score_percent}%)
        </span>{" "}
        — Gap Level:{" "}
        <span
          className={`font-semibold ${
            gapTextColor[result.gap_level] || ""
          }`}
        >
          {result.gap_level}
        </span>
      </p>

      <div className="space-y-4 mb-8">
        {(result.question_reviews || []).map((q) => (
          <div
            key={q.question_index}
            className={`border rounded-xl p-4 ${
              q.is_correct
                ? "border-green-300 bg-green-50"
                : "border-red-300 bg-red-50"
            }`}
          >
            <p className="font-medium mb-2">{q.question}</p>
            <div className="space-y-1 text-sm">
              {q.options.map((opt, i) => (
                <div
                  key={i}
                  className={
                    i === q.correct_index
                      ? "text-green-700 font-medium"
                      : i === q.user_answer_index
                      ? "text-red-700"
                      : "text-gray-600"
                  }
                >
                  {i === q.correct_index
                    ? "✓ "
                    : i === q.user_answer_index
                    ? "✗ "
                    : "• "}
                  {opt}
                </div>
              ))}
            </div>
            {q.explanation && (
              <p className="text-xs text-gray-500 mt-2">{q.explanation}</p>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => navigate("/dashboard")}
          className="px-4 py-2 bg-black text-white rounded-lg text-sm"
        >
          Go to Dashboard
        </button>
        <button
          onClick={() => navigate("/materials")}
          className="px-4 py-2 border rounded-lg text-sm"
        >
          Back to Materials
        </button>
      </div>
    </>
  );
}