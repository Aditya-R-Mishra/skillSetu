import { createContext, useContext, useState } from "react";
import api from "../api/axios";

/**
 * AuthContext — provides login, register, logout, and current user state
 * to the entire React tree.
 *
 * HOW IT WORKS:
 *   - On login/register: calls the FastAPI backend, stores JWT + user in
 *     localStorage so the session survives page refreshes.
 *   - On mount: reads localStorage to restore the session if it exists.
 *   - On logout: clears localStorage and resets state.
 *   - On any auth failure: throws the error up to the calling page so it
 *     can display the real backend error message (e.g. "Invalid email or password").
 *
 * WHY no mock fallback?
 *   The old code silently logged in with fake credentials when the backend
 *   was offline. This masked real errors (e.g. wrong password) and would
 *   confuse judges during a live demo. All errors now surface properly.
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Restore user from localStorage on initial mount (page refresh safety)
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem("user");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  /**
   * login — calls POST /auth/login, stores token + user, updates state.
   * Throws on failure so Login.jsx can display the error.
   */
  const login = async (email, password) => {
    const res = await api.post("/auth/login", { email, password });
    const { access_token, user_id, name, email: userEmail } = res.data;
    const userData = { user_id, name, email: userEmail };
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
  };

  /**
   * register — calls POST /auth/register, stores token + user, updates state.
   * Throws on failure so Register.jsx can display the error.
   */
  const register = async (name, email, password) => {
    const res = await api.post("/auth/register", { name, email, password });
    const { access_token, user_id, name: userName, email: userEmail } = res.data;
    const userData = { user_id, name: userName, email: userEmail };
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
  };

  /**
   * logout — clears all stored auth state and resets the user to null.
   */
  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
