import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { LogOut, User, Zap, Activity, Lightbulb } from "lucide-react";
import SuggestionModal from "./SuggestionModal";

const Navbar = () => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showSuggestionModal, setShowSuggestionModal] = useState(false);

  const handleLogout = async () => {
    await signOut();
    navigate("/login");
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/5 bg-black/60 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="bg-primary/20 p-2 rounded-xl group-hover:bg-primary/30 transition-all group-hover:rotate-12 duration-300">
            <Zap className="text-primary" size={20} fill="currentColor" />
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-black tracking-tighter leading-none">
              Auto<span className="text-primary">Bot</span>
            </span>
          </div>
        </Link>

        {/* User Actions */}
        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3">
              <Link
                to="/profile"
                className={`h-10 flex items-center gap-2 px-4 rounded-xl border-2 transition-all text-[10px] font-black uppercase tracking-widest ${isActive("/profile") ? "" : "bg-transparent border-primary text-primary hover:bg-primary/10"}`}
              >
                <User size={12} /> Profile
              </Link>
              <button
                onClick={() => setShowSuggestionModal(true)}
                className="h-10 px-4 flex items-center gap-2 bg-transparent border-2 border-primary text-primary hover:bg-primary/10 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all"
                title="Suggest a feature or report a bug"
              >
                <Lightbulb size={12} /> Suggest
              </button>
              <button
                onClick={handleLogout}
                className="h-10 px-4 flex items-center gap-2 bg-transparent border-2 border-primary text-primary hover:bg-primary/10 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all"
              >
                <LogOut size={12} /> Log Out
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-6 text-[10px] font-black uppercase tracking-widest">
              <Link
                to="/login"
                className="text-gray-500 hover:text-white transition-colors"
              >
                Sign In
              </Link>
              <Link to="/register">
                <button className="h-9 px-5 text-[9px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 rounded-xl">
                  Get Started
                </button>
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Suggestion Modal */}
      <SuggestionModal
        isOpen={showSuggestionModal}
        onClose={() => setShowSuggestionModal(false)}
        userId={user?.id}
      />
    </nav>
  );
};

export default Navbar;
