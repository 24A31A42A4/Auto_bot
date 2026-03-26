import React, { useState, useEffect, useRef } from "react";
import {
  Bot,
  Loader2,
  AlertCircle,
  History,
  Clock,
  Zap,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Activity,
  Trophy,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Dashboard = () => {
  const { user } = useAuth();
  const [formUrl, setFormUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState([]);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [stats, setStats] = useState({
    forms_filled: 0,
    total_points: 0,
    max_points: 0,
    accuracy: 0,
  });
  const logContainerRef = useRef(null);
  const isAtBottom = useRef(true);

  // Fetch History
  const fetchHistory = async () => {
    if (!user) return;
    try {
      const res = await fetch(`${API_URL}/history/${user.id}`);
      if (!res.ok) return;
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      console.error("History fetch error:", err);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Fetch Stats
  const fetchStats = async () => {
    if (!user) return;
    try {
      const res = await fetch(`${API_URL}/stats/${user.id}`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Stats fetch error:", err);
    }
  };

  useEffect(() => {
    fetchHistory();
    fetchStats();
  }, [user]);

  useEffect(() => {
    const container = logContainerRef.current;
    if (container && isAtBottom.current) {
      container.scrollTop = container.scrollHeight;
    }
  }, [logs]);

  // Auto-scroll to result when it appears
  useEffect(() => {
    if (result && logContainerRef.current) {
      setTimeout(() => {
        logContainerRef.current?.scrollTo({
          top: logContainerRef.current.scrollHeight,
          behavior: "smooth",
        });
      }, 100);
    }
  }, [result]);

  // Polling for status
  useEffect(() => {
    let interval;
    if (loading && user) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_URL}/status/${user.id}`);
          if (res.ok) {
            const data = await res.json();
            const newLogs = (data.logs || []).map((logText, i) => {
              if (i < logs.length && logs[i]?.text === logText) return logs[i];
              return {
                text: logText,
                time: new Date().toLocaleTimeString([], { hour12: false }),
              };
            });
            setLogs(newLogs);
            if (data.result) {
              setResult(data.result);
              setLoading(false);
              clearInterval(interval);
              fetchHistory();
              fetchStats();
            }
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 7000);
    }
    return () => clearInterval(interval);
  }, [loading, user]);

  const handleFillForm = async (e) => {
    e.preventDefault();
    if (
      !formUrl.includes("docs.google.com/forms") &&
      !formUrl.includes("forms.gle") &&
      !formUrl.includes("tinyurl.com") &&
      !formUrl.includes("bit.ly")
    ) {
      setError("Please enter a valid Google Forms URL or shortened link");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setLogs([
      {
        text: "Starting Bot...",
        time: new Date().toLocaleTimeString([], { hour12: false }),
      },
    ]);

    try {
      const response = await fetch(`${API_URL}/fill-form`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${user.id}`,
        },
        body: JSON.stringify({ url: formUrl }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }
    } catch (err) {
      setError(
        err.message.includes("Failed to fetch")
          ? "Cannot connect to backend. Ensure uvicorn is running."
          : err.message,
      );
      setLoading(false);
    }
  };

  const displayValue =
    result && typeof result === "object" ? result.score : result;
  const isError =
    result &&
    (typeof result === "string"
      ? result.toLowerCase().includes("error") ||
        result.toLowerCase().includes("failed")
      : String(result.score || "")
          .toLowerCase()
          .includes("error") ||
        String(result.score || "")
          .toLowerCase()
          .includes("failed"));

  const parseScore = (score) => {
    if (!score) return "OK";
    if (typeof score !== "string") return String(score);
    if (!score.trim().startsWith("{")) return score;
    try {
      const parsed = JSON.parse(score);
      return parsed.score || "OK";
    } catch {
      return score;
    }
  };

  const parseNumericScore = (score) => {
    const parsed = parseScore(score);
    if (typeof parsed !== "string") return Number(parsed) || null;

    if (parsed.includes("/")) {
      const [current, total] = parsed.split("/").map((v) => Number(v?.trim()));
      if (Number.isFinite(current) && Number.isFinite(total) && total > 0) {
        return Math.round((current / total) * 100);
      }
    }

    const numeric = Number(parsed);
    return Number.isFinite(numeric) ? numeric : null;
  };

  return (
    <div className="min-h-screen pt-10 pb-20 px-4 md:px-6 relative overflow-hidden">
      <div className="blob blob-1 opacity-15" />
      <div className="blob blob-2 opacity-15" />

      <div className="max-w-6xl mx-auto pt-12 pb-24 relative z-10">
        {/* HERO */}
        <section className="text-center mb-12 fade-in">
          <h1 className="text-5xl md:text-6xl font-black mb-4 leading-[1.1] tracking-tighter">
            Automate your <br />
            <span className="primary-gradient-text">Google Forms.</span>
          </h1>
          <p className="max-w-md mx-auto text-gray-500 text-sm md:text-base font-medium mb-8">
            AutoBot reads, reasons, and fills with world-class accuracy.
          </p>

          {/* URL Input */}
          <div className="glass max-w-xl mx-auto p-1.5 border-white/10 flex gap-2 shadow-2xl overflow-hidden focus-within:border-primary/40 transition-all">
            <input
              type="text"
              className="flex-1 bg-transparent border-none py-3.5 px-5 text-sm focus:ring-0 min-w-0"
              placeholder="Paste Google Form URL..."
              value={formUrl}
              onChange={(e) => setFormUrl(e.target.value)}
              disabled={loading}
            />
            <button
              onClick={handleFillForm}
              className="h-12 px-6 text-xs font-black shadow-xl shrink-0 uppercase tracking-widest whitespace-nowrap"
              disabled={loading || !formUrl}
            >
              {loading ? (
                <>
                  {" "}
                  <Loader2 className="animate-spin" size={16} /> Filling...{" "}
                </>
              ) : (
                <>
                  {" "}
                  Start <ArrowRight size={16} />{" "}
                </>
              )}
            </button>
          </div>
          {error && (
            <p className="mt-3 text-red-500 text-xs font-bold flex items-center justify-center gap-2 animate-pulse">
              <AlertCircle size={12} /> {error}
            </p>
          )}
        </section>

        {/* STATS ROW */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8 fade-in">
          <div className="glass p-4 rounded-2xl border-white/5 text-center hover:border-primary/20 transition-all">
            <div className="text-[8px] font-black text-gray-600 uppercase tracking-widest mb-1">
              Forms Filled
            </div>
            <div className="text-2xl font-black text-white">
              {stats.forms_filled || 0}
            </div>
          </div>
          <div className="glass p-4 rounded-2xl border-white/5 text-center hover:border-primary/20 transition-all">
            <div className="text-[8px] font-black text-gray-600 uppercase tracking-widest mb-1">
              Total Points
            </div>
            <div className="text-2xl font-black text-primary">
              {stats.total_points || 0}
            </div>
          </div>
          <div className="glass p-4 rounded-2xl border-white/5 text-center hover:border-primary/20 transition-all">
            <div className="text-[8px] font-black text-gray-600 uppercase tracking-widest mb-1">
              Max Points
            </div>
            <div className="text-2xl font-black text-gray-400">
              {stats.max_points || 0}
            </div>
          </div>
          <div className="glass p-4 rounded-2xl border-white/5 text-center hover:border-primary/20 transition-all">
            <div className="text-[8px] font-black text-gray-600 uppercase tracking-widest mb-1">
              Accuracy
            </div>
            <div className="text-2xl font-black text-green-500">
              {stats.accuracy || 0}%
            </div>
          </div>
        </div>

        {/* MAIN GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start fade-in">
          {/* TERMINAL PANEL (1/2 width) */}
          <div className="w-full min-h-[600px]">
            <div
              className={`glass overflow-hidden border-white/5 shadow-2xl rounded-2xl transition-all duration-500 flex flex-col h-full ${loading ? "border-primary/30 ring-1 ring-primary/20" : ""}`}
            >
              {/* Terminal Header */}
              <div className="flex items-center justify-between p-4 border-b border-white/5 bg-white/[0.03]">
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-xl bg-black border border-white/10 ${loading ? "neural-pulse border-primary/50" : ""}`}
                  >
                    <Bot
                      className={
                        loading ? "text-primary text-glow" : "text-gray-700"
                      }
                      size={18}
                    />
                  </div>
                  <div>
                    <span className="block text-[8px] uppercase tracking-[0.25em] font-black text-gray-600">
                      Live Status
                    </span>
                    <h3
                      className={`text-xs font-black uppercase tracking-wider ${isError ? "text-amber-500" : "text-white"}`}
                    >
                      {loading
                        ? "Processing..."
                        : isError
                          ? "Interrupted"
                          : result
                            ? "Complete"
                            : "System Ready"}
                    </h3>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {result && !isError && (
                    <span className="text-[8px] font-black text-primary flex items-center gap-1 uppercase tracking-widest bg-primary/10 px-2.5 py-1 rounded-full border border-primary/20">
                      <ShieldCheck size={10} /> Done
                    </span>
                  )}
                  {isError && (
                    <span className="text-[8px] font-black text-amber-500 flex items-center gap-1 uppercase tracking-widest bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
                      <AlertCircle size={10} /> Check
                    </span>
                  )}
                  {loading && (
                    <div className="flex items-center gap-3">
                      <div className="text-center">
                        <div className="text-primary text-[10px] font-black animate-pulse">
                          ACTIVE
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Terminal Body */}
              <div className="relative bg-black/80 font-mono text-[11px] h-[500px] flex flex-col">
                {loading && <div className="scanline" />}

                {!loading && !logs.length && !result ? (
                  <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                    <div className="relative mb-6">
                      <div className="w-16 h-16 rounded-full border border-white/5 flex items-center justify-center bg-white/[0.03]">
                        <Cpu className="text-gray-800" size={28} />
                      </div>
                      <div className="absolute inset-0 bg-primary/5 rounded-full blur-xl animate-pulse" />
                    </div>
                    <h3 className="text-xs font-black mb-1 text-gray-300 uppercase tracking-tight">
                      Waiting for Input...
                    </h3>
                    <p className="text-gray-700 text-[9px] max-w-xs uppercase tracking-widest leading-relaxed">
                      Paste a form URL above to begin.
                    </p>
                  </div>
                ) : (
                  <div
                    ref={logContainerRef}
                    className="flex-1 p-5 space-y-1.5 overflow-y-auto custom-scrollbar"
                    onScroll={(e) => {
                      const el = e.target;
                      const offset =
                        el.scrollHeight - el.scrollTop - el.clientHeight;
                      isAtBottom.current = offset < 100;
                    }}
                  >
                    {logs.map((log, i) => {
                      const logText = typeof log === "object" ? log.text : log;
                      const logTime =
                        typeof log === "object"
                          ? log.time
                          : new Date().toLocaleTimeString([], {
                              hour12: false,
                            });
                      return (
                        <div
                          key={i}
                          className={`text-[10px] leading-relaxed font-medium ${
                            logText.includes("successfully")
                              ? "text-green-400 font-bold"
                              : logText.includes("Error") ||
                                  logText.includes("Failed")
                                ? "text-red-400 font-bold"
                                : "text-gray-400"
                          }`}
                        >
                          <span className="text-gray-700 mr-2 font-mono">
                            [{logTime}]
                          </span>
                          {logText}
                        </div>
                      );
                    })}
                    {loading && (
                      <div className="flex flex-col gap-2 mt-4">
                        <div className="flex items-center gap-2 text-primary/60 italic text-[9px] uppercase tracking-widest font-black animate-pulse">
                          <Activity size={12} /> Analyzing form...
                        </div>
                        <div className="w-full h-0.5 bg-white/5 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary animate-progress-indefinite"
                            style={{ width: "40%" }}
                          />
                        </div>
                      </div>
                    )}
                    {result && (
                      <div className="mt-6 p-4 bg-primary/5 border border-primary/20 rounded-xl text-center relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />
                        <div className="relative z-10">
                          <div className="text-[7px] font-black text-gray-500 mb-1 uppercase tracking-[0.3em]">
                            {isError ? "Status" : "Result"}
                          </div>
                          <div
                            className={`text-xl md:text-2xl font-black tracking-tighter mb-2 ${isError ? "text-amber-500" : "primary-gradient-text"}`}
                          >
                            {displayValue}
                          </div>
                          <div
                            className={`text-[7px] font-black uppercase tracking-widest flex items-center justify-center gap-1 ${isError ? "text-amber-500/60" : "text-primary"}`}
                          >
                            {isError ? (
                              <AlertCircle size={9} />
                            ) : (
                              <ShieldCheck size={9} />
                            )}{" "}
                            {isError
                              ? "Check form fields"
                              : "Submitted Successfully"}
                          </div>

                          {!isError && result?.score_url && (
                            <div className="mt-3 flex justify-center">
                              <a
                                href={result.score_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary text-black rounded-lg text-[8px] font-black uppercase tracking-[0.15em] hover:scale-105 active:scale-95 transition-all shadow-lg"
                              >
                                View Score <ArrowRight size={10} />
                              </a>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* HISTORY PANEL (1/2 width) */}
          <div className="w-full">
            <div
              className="glass rounded-2xl border-white/5 overflow-hidden flex flex-col"
              style={{ maxHeight: "calc(100vh - 200px)" }}
            >
              <div className="p-4 border-b border-white/5 bg-white/[0.03] flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2">
                  <History className="text-primary" size={14} />
                  <h2 className="text-xs font-black uppercase tracking-[0.2em]">
                    History
                  </h2>
                  <span className="text-[8px] font-black text-gray-600 bg-white/5 px-2 py-0.5 rounded-full">
                    {history.length}
                  </span>
                </div>
                <button
                  onClick={() => {
                    setHistoryLoading(true);
                    fetchHistory();
                  }}
                  className="p-1.5 rounded-lg hover:bg-white/5 text-gray-600 hover:text-primary transition-all"
                  title="Refresh"
                >
                  <Activity
                    size={12}
                    className={historyLoading ? "animate-spin" : ""}
                  />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2">
                {historyLoading ? (
                  <div className="py-16 flex flex-col items-center justify-center gap-3 opacity-50">
                    <Loader2 className="animate-spin text-primary" size={20} />
                    <span className="text-[9px] font-black uppercase tracking-widest text-gray-600">
                      Loading...
                    </span>
                  </div>
                ) : history.length === 0 ? (
                  <div className="py-16 text-center">
                    <div className="text-[9px] font-black uppercase tracking-widest text-gray-700">
                      No records yet.
                    </div>
                  </div>
                ) : (
                  history.map((item, index) => {
                    const scoreDisplay = parseScore(item.score);
                    const hasNumericScore = scoreDisplay?.includes("/");
                    return (
                      <div
                        key={item.id}
                        className="group p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-primary/30 transition-all duration-200"
                        style={{ animationDelay: `${index * 30}ms` }}
                      >
                        {/* Date + Score Row */}
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[8px] font-bold text-gray-600 flex items-center gap-1">
                            <Clock size={8} />
                            {new Date(item.filled_at).toLocaleDateString(
                              "en-IN",
                              { day: "numeric", month: "short" },
                            )}
                            {" · "}
                            {new Date(item.filled_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                          <span
                            className={`text-[9px] font-black px-2 py-0.5 rounded-lg ${
                              hasNumericScore
                                ? "bg-primary/15 text-primary border border-primary/20"
                                : "bg-white/5 text-gray-500 border border-white/5"
                            }`}
                          >
                            {scoreDisplay}
                          </span>
                        </div>

                        {/* Title */}
                        <h4 className="text-[12px] font-bold text-gray-200 group-hover:text-white transition-colors leading-snug mb-3 line-clamp-2">
                          {item.form_title || "Untitled Form"}
                        </h4>

                        {/* Action Buttons */}
                        <div className="flex gap-2">
                          {item.score_url && (
                            <a
                              href={item.score_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-primary/10 border border-primary/20 text-primary text-[8px] font-black uppercase tracking-wider hover:bg-primary/20 transition-all"
                            >
                              <Trophy size={9} /> Score
                            </a>
                          )}
                          <a
                            href={item.form_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/5 text-gray-500 text-[8px] font-black uppercase tracking-wider hover:text-white hover:bg-white/5 transition-all"
                          >
                            <Zap size={9} />{" "}
                            {item.score_url ? "Refill" : "Open"}
                          </a>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
