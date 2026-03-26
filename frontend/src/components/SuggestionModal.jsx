import React, { useState } from "react";
import {
  X,
  Send,
  AlertCircle,
  CheckCircle,
  Lightbulb,
  Bug,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const SuggestionModal = ({ isOpen, onClose, userId }) => {
  const [suggestType, setSuggestType] = useState("feature");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null); // "success", "error", or null
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (!title.trim()) {
      setStatus("error");
      setMessage("Please enter a title");
      return;
    }

    if (!description.trim()) {
      setStatus("error");
      setMessage("Please enter a description");
      return;
    }

    if (!userId) {
      setStatus("error");
      setMessage("User ID not found. Please log in again.");
      return;
    }

    setLoading(true);
    setStatus(null);
    setMessage("");

    try {
      const response = await fetch(`${API_URL}/suggest`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${userId}`,
        },
        body: JSON.stringify({
          suggestion_type: suggestType,
          title: title.trim(),
          description: description.trim(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail ||
            `Failed to submit suggestion (${response.status})`,
        );
      }

      const data = await response.json();
      setStatus("success");
      setMessage(data.message || "Your suggestion has been saved!");

      // Clear form and close after 2 seconds
      setTimeout(() => {
        setTitle("");
        setDescription("");
        setSuggestType("feature");
        setStatus(null);
        onClose();
      }, 2000);
    } catch (err) {
      console.error("Submission error:", err);
      setStatus("error");
      setMessage(err.message || "Error submitting suggestion");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-16 z-50 h-screen pointer-events-none">
      {/* Modal - Right Side Compact */}
      <div className="pointer-events-auto relative right-4 top-4 w-80 max-h-[calc(100vh-100px)] bg-black border border-white/20 rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300">
        {/* Close Button - Positioned at top right outside header */}
        <div className="absolute top-0 right-0 p-2 z-50">
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/20 text-gray-400 hover:text-white transition-all"
          >
            <X size={20} />
          </button>
        </div>

        <div className="h-full p-5 pt-12 flex flex-col overflow-y-auto custom-scrollbar">
          {/* Header */}
          <h2 className="text-xl font-black text-white mb-1">
            Share Your Idea
          </h2>
          <p className="text-xs text-gray-400 mb-5">
            Help us improve AutoBot by reporting bugs or suggesting features
          </p>

          {/* Success/Error Messages */}
          {status === "success" && (
            <div className="mb-3 p-2 rounded-lg bg-green-500/10 border border-green-500/20 flex items-start gap-2">
              <CheckCircle
                className="text-green-500 shrink-0 mt-0.5"
                size={16}
              />
              <p className="text-xs text-green-200">{message}</p>
            </div>
          )}

          {status === "error" && (
            <div className="mb-3 p-2 rounded-lg bg-red-500/10 border border-red-500/20 flex items-start gap-2">
              <AlertCircle className="text-red-500 shrink-0 mt-0.5" size={16} />
              <p className="text-xs text-red-200">{message}</p>
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            className="space-y-3 flex-1 flex flex-col"
          >
            {/* Type Selection */}
            <div>
              <label className="block text-[10px] font-black text-gray-300 uppercase tracking-wider mb-2">
                Type
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSuggestType("feature")}
                  className={`p-2 rounded-lg border-2 transition-all flex items-center justify-center gap-1 text-[11px] cursor-pointer ${
                    suggestType === "feature"
                      ? "bg-primary/20 border-primary text-primary"
                      : "bg-white/5 border-white/10 text-gray-400 hover:border-white/20"
                  }`}
                >
                  <Lightbulb size={13} />
                  <span className="font-bold">Feature</span>
                </button>
                <button
                  type="button"
                  onClick={() => setSuggestType("bug")}
                  className={`p-2 rounded-lg border-2 transition-all flex items-center justify-center gap-1 text-[11px] cursor-pointer ${
                    suggestType === "bug"
                      ? "bg-red-500/20 border-red-500 text-red-400"
                      : "bg-white/5 border-white/10 text-gray-400 hover:border-white/20"
                  }`}
                >
                  <Bug size={13} />
                  <span className="font-bold">Bug</span>
                </button>
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-[10px] font-black text-gray-300 uppercase tracking-wider mb-1">
                Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Add batch form filling"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
                disabled={loading}
                maxLength="100"
              />
              <p className="text-[9px] text-gray-600 mt-0.5">
                {title.length}/100
              </p>
            </div>

            {/* Description */}
            <div>
              <label className="block text-[10px] font-black text-gray-300 uppercase tracking-wider mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your idea or bug..."
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all resize-none"
                rows="3"
                disabled={loading}
                maxLength="500"
              />
              <p className="text-[9px] text-gray-600 mt-0.5">
                {description.length}/500
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-3 rounded-lg bg-primary text-black font-black uppercase tracking-widest text-xs flex items-center justify-center gap-2 hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer mt-auto"
            >
              {loading ? (
                <>
                  <div className="w-3 h-3 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send size={13} />
                  Submit
                </>
              )}
            </button>
          </form>

          {/* Suggested Features Info */}
          <div className="mt-4 p-3 rounded-lg bg-white/5 border border-white/10">
            <p className="text-[9px] font-bold text-gray-300 mb-2 uppercase tracking-wider">
              💡 Suggested:
            </p>
            <ul className="text-[8px] text-gray-400 space-y-0.5">
              <li>• Batch form filling</li>
              <li>• Save form templates</li>
              <li>• AI preferences</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SuggestionModal;
