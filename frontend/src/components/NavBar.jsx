import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function NavBar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const linkClass = (path) =>
    `text-sm px-3 py-1.5 rounded-lg transition ${
      location.pathname.startsWith(path)
        ? "bg-black text-white"
        : "hover:bg-gray-100 text-gray-700"
    }`;

  return (
    <div className="border-b mb-6">
      <div className="max-w-5xl mx-auto px-8 py-3 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="font-bold text-lg mr-4">SkillSetu</span>
          <Link to="/dashboard" className={linkClass("/dashboard")}>
            Dashboard
          </Link>
          <Link to="/materials" className={linkClass("/materials")}>
            Materials
          </Link>
          <Link to="/recommendations" className={linkClass("/recommendations")}>
            Recommendations
          </Link>
        </div>
        <div className="flex items-center gap-3">
          {user?.name && (
            <span className="text-sm text-gray-500 hidden sm:inline">
              {user.name}
            </span>
          )}
          <button
            onClick={logout}
            className="text-sm px-3 py-1.5 border rounded-lg hover:bg-gray-100"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}