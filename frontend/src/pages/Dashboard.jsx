import React, { useState, useEffect, useRef } from 'react'
import { Bot, Send, Loader2, CheckCircle2, AlertCircle, ExternalLink, Terminal, ChevronDown, ChevronUp, History, Clock, Zap, ArrowRight, ShieldCheck, Cpu, Fingerprint, Activity } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const Dashboard = () => {
  const { user } = useAuth()
  const [formUrl, setFormUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [logs, setLogs] = useState([])
  const [showLogs, setShowLogs] = useState(true)
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const logEndRef = useRef(null)
  const logContainerRef = useRef(null)
  const isAtBottom = useRef(true)

  // Fetch History
  const fetchHistory = async () => {
    if (!user) return
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const fetchUrl = `${apiUrl}/history/${user.id}`;
      const res = await fetch(fetchUrl);
      if (!res.ok) {
        console.error(`Fetch error for ${fetchUrl}: ${res.status}`);
        return;
      }
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      console.error('History fetch error:', err)
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [user])

  useEffect(() => {
    const container = logContainerRef.current;
    if (container && isAtBottom.current) {
      container.scrollTop = container.scrollHeight;
    }
  }, [logs])

  // Polling for status
  useEffect(() => {
    let interval;
    if (loading && user) {
      interval = setInterval(async () => {
        try {
          const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
          const fetchUrl = `${apiUrl}/status/${user.id}`;
          const res = await fetch(fetchUrl);
          if (res.ok) {
            const data = await res.json()
            setLogs(data.logs || [])
            if (data.result) {
              setResult(data.result)
              setLoading(false)
              clearInterval(interval)
              fetchHistory()
            }
          }
        } catch (err) {
          console.error('Polling error:', err)
        }
      }, 1500)
    }
    return () => clearInterval(interval)
  }, [loading, user])

  const handleFillForm = async (e) => {
    e.preventDefault()
    if (!formUrl.includes('docs.google.com/forms') && !formUrl.includes('forms.gle') && !formUrl.includes('tinyurl.com') && !formUrl.includes('bit.ly')) {
      setError('Please enter a valid Google Forms URL or shortened link (tinyurl, forms.gle)')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    setLogs(['Starting Bot...'])

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const fetchUrl = `${apiUrl}/fill-form`;
      console.log(`Submitting form to: ${fetchUrl}`);
      const response = await fetch(fetchUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.id}`
        },
        body: JSON.stringify({ url: formUrl })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Server error: ${response.status}`)
      }
    } catch (err) {
      console.error('Fill form error:', err)
      setError(err.message.includes('Failed to fetch') 
        ? 'Cannot connect to backend server. Ensure uvicorn is running.' 
        : err.message)
      setLoading(false)
    }
  }

  const displayValue = result && typeof result === 'object' ? result.score : result;
  const isError = result && (
    typeof result === 'string' 
      ? result.toLowerCase().includes('error') || result.toLowerCase().includes('failed')
      : String(result.score || "").toLowerCase().includes('error') || String(result.score || "").toLowerCase().includes('failed')
  );

  // Helper to parse score from history (handles JSON strings)
  const parseScore = (score) => {
    if (!score) return 'OK';
    if (typeof score !== 'string') return String(score);
    if (!score.trim().startsWith('{')) return score;
    try {
      const parsed = JSON.parse(score);
      return parsed.score || 'OK';
    } catch (e) {
      return score;
    }
  };

  return (
    <div className="min-h-screen pt-24 pb-20 px-6 relative overflow-hidden">
      <div className="blob blob-1 opacity-20" />
      <div className="blob blob-2 opacity-20" />

      <div className="max-w-7xl mx-auto px-6 pt-16 pb-24 relative z-10">
        
        {/* HERO SECTION */}
        <section className="text-center mb-16 fade-in">
          
          <h1 className="text-6xl md:text-7xl font-black mb-6 leading-[1.1] tracking-tighter">
            Automate your <br />
            <span className="primary-gradient-text">Google Forms.</span>
          </h1>
          <p className="max-w-xl mx-auto text-gray-400 text-lg md:text-xl font-medium mb-12">
            The intelligent platform for your forms. <br />
            AutoBot reads, reasons, and fills with world-class accuracy.
          </p>
          
          {/* Main Action Area */}
          <div className="glass max-w-2xl mx-auto p-2 border-white/10 flex flex-col md:flex-row gap-2 shadow-2xl overflow-hidden group focus-within:border-primary/40 transition-all">
            <input
              type="text"
              className="flex-1 bg-transparent border-none py-4 px-6 text-lg focus:ring-0"
              placeholder="Paste Google Form URL..."
              value={formUrl}
              onChange={(e) => setFormUrl(e.target.value)}
              disabled={loading}
            />
            <button 
              onClick={handleFillForm}
              className="h-14 px-8 text-md font-black shadow-xl shrink-0 uppercase tracking-widest"
              disabled={loading || !formUrl}
            >
              {loading ? (
                <> <Loader2 className="animate-spin" size={20} /> Filling... </>
              ) : (
                <> Start Filling <ArrowRight size={20} /> </>
              )}
            </button>
          </div>
          {error && <p className="mt-4 text-red-500 text-sm font-bold flex items-center justify-center gap-2 animate-pulse"><AlertCircle size={14} /> {error}</p>}
        </section>

        {/* CONTENT GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* CORE EXECUTION TERMINAL (Left) */}
          <div className="lg:col-span-8">
            <div className={`glass overflow-hidden border-white/5 shadow-2xl transition-all duration-500 ${loading ? 'border-primary/30 ring-1 ring-primary/20 scale-[1.01]' : ''}`}>
              
              {/* Terminal Header with Live Metrics */}
                <div className="flex flex-col sm:flex-row items-center justify-between p-6 border-b border-white/5 bg-white/5 gap-4">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-2xl bg-black border border-white/10 ${loading ? 'neural-pulse border-primary/50' : ''}`}>
                    <Bot className={loading ? "text-primary text-glow" : "text-gray-700"} size={24} />
                  </div>
                  <div className="text-left">
                    <span className="block text-[10px] uppercase tracking-[0.3em] font-black text-gray-500 mb-1">Live Status</span>
                    <h3 className={`text-sm font-black uppercase tracking-widest ${isError ? 'text-amber-500' : 'text-white'}`}>
                      {loading ? 'Filling Your Form' : isError ? 'Task Interrupted' : result ? 'Task Complete' : 'System Ready'}
                    </h3>
                  </div>
                </div>

                {loading && (
                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <span className="block text-[8px] text-gray-600 font-black uppercase mb-1">Accuracy</span>
                      <div className="text-primary text-xs font-black animate-pulse">98.2%</div>
                    </div>
                    <div className="text-center border-l border-white/5 pl-6">
                      <span className="block text-[8px] text-gray-600 font-black uppercase mb-1">Speed</span>
                      <div className="text-white text-xs font-black">HIGH</div>
                    </div>
                    <div className="text-center border-l border-white/5 pl-6">
                      <span className="block text-[8px] text-gray-600 font-black uppercase mb-1">Security</span>
                      <div className="text-green-500 text-xs font-black font-mono">SECURE</div>
                    </div>
                  </div>
                )}

                {result && !isError && <span className="text-[10px] font-black text-primary flex items-center gap-1 uppercase tracking-widest bg-primary/10 px-3 py-1.5 rounded-full border border-primary/20"><ShieldCheck size={14} /> Form Filled Successfully</span>}
                {isError && <span className="text-[10px] font-black text-amber-500 flex items-center gap-1 uppercase tracking-widest bg-amber-500/10 px-3 py-1.5 rounded-full border border-amber-500/20"><AlertCircle size={14} /> Submission Needed</span>}
              </div>
              
              {/* Main Visualization Area */}
              <div className="relative relative-hidden bg-black/80 font-mono text-[11px] sm:text-xs min-h-[400px]">
                {loading && <div className="scanline" />}
                
                {!loading && !logs.length && !result ? (
                   <div className="absolute inset-0 flex flex-col items-center justify-center p-12 text-center">
                      <div className="relative mb-8">
                        <div className="w-24 h-24 rounded-full border border-white/5 flex items-center justify-center bg-white/5 animate-spin-slow">
                           <Cpu className="text-gray-800" size={40} />
                        </div>
                        <div className="absolute inset-0 bg-primary/5 rounded-full blur-xl animate-pulse" />
                      </div>
                      <h3 className="text-xl font-black mb-2 text-gray-200 uppercase tracking-tighter">Awaiting Remote Signal</h3>
                      <p className="text-gray-600 text-xs max-w-xs mx-auto uppercase tracking-widest leading-relaxed">Initate neural link by providing a valid form endpoint above.</p>
                   </div>
                ) : (
                  <div 
                    ref={logContainerRef}
                    className="p-8 space-y-2 max-h-[500px] overflow-y-auto custom-scrollbar"
                    onScroll={(e) => {
                      const el = e.target;
                      // 100px buffer to detect if user has scrolled up
                      const offset = el.scrollHeight - el.scrollTop - el.clientHeight;
                      isAtBottom.current = offset < 100;
                    }}
                  >
                    {logs.map((log, i) => (
                      <div key={i} className={`text-[11px] leading-relaxed transition-all duration-300 font-medium ${
                        log.includes('successfully') ? 'text-green-400 font-bold' :
                        log.includes('Error') || log.includes('Failed') ? 'text-red-400 font-bold' :
                        'text-gray-300'
                      }`}>
                        <span className="text-gray-600 mr-3">[{new Date().toLocaleTimeString([], { hour12: false })}]</span>
                        {log}
                      </div>
                    ))}
                    {/* Removed logEndRef div as we use scrollTop now */}
                    {loading && (
                      <div className="flex flex-col gap-2 mt-6">
                        <div className="flex items-center gap-3 text-primary/60 italic text-[10px] uppercase tracking-widest font-black animate-pulse">
                          <Activity size={14} /> Analyzing form fields...
                        </div>
                        <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                           <div className="h-full bg-primary animate-progress-indefinite" style={{ width: '40%' }} />
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {result && (
                  <div className="p-10 bg-primary/5 border-t border-white/10 animate-in fade-in zoom-in-95 duration-700 text-center relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />
                    <div className="relative z-10">
                        <div className="text-[10px] font-black text-gray-500 mb-2 uppercase tracking-[0.4em]">{isError ? 'Status Report' : 'Final Result'}</div>
                      <div className={`text-7xl font-black tracking-tighter mb-4 ${isError ? 'text-amber-500' : 'primary-gradient-text'}`}>
                        {displayValue}
                      </div>
                      <div className={`text-[8px] font-black uppercase tracking-widest flex items-center justify-center gap-2 ${isError ? 'text-amber-500/60' : 'text-primary'}`}>
                         {isError ? <AlertCircle size={12} /> : <ShieldCheck size={12} />} {isError ? 'Please check form fields' : 'Form Submitted Successfully'}
                      </div>

                      {!isError && result?.score_url && (
                        <div className="mt-10 flex justify-center">
                          <a 
                            href={result.score_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-3 px-8 py-4 bg-primary text-black rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] hover:scale-105 active:scale-95 transition-all shadow-[0_20px_40px_-10px_rgba(255,255,255,0.2)]"
                          >
                            View Your Form Score <ArrowRight size={14} />
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Submission History */}
            <div className="lg:col-span-4 flex flex-col gap-6">
              <div className="glass rounded-[2.5rem] border-white/10 overflow-hidden flex flex-col max-h-[900px]">
                <div className="p-8 border-b border-white/5 bg-white/5 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <History className="text-primary" size={18} />
                    <h2 className="text-sm font-black uppercase tracking-[0.3em]">History</h2>
                  </div>
                  <button 
                    onClick={fetchHistory}
                    className="p-2 rounded-lg hover:bg-white/5 text-gray-500 hover:text-primary transition-all"
                    title="Refresh History"
                  >
                    <Activity size={14} className={historyLoading ? "animate-spin" : ""} />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
                  {historyLoading ? (
                    <div className="py-20 flex flex-col items-center justify-center gap-4 opacity-50">
                      <Loader2 className="animate-spin text-primary" size={24} />
                      <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Syncing Records...</span>
                    </div>
                  ) : history.length === 0 ? (
                    <div className="py-20 text-center">
                      <div className="text-[10px] font-black uppercase tracking-widest text-gray-700">No neural records found.</div>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-4">
                      {history.map((item, index) => {
                        const scoreDisplay = parseScore(item.score);
                        return (
                          <div 
                            key={item.id} 
                            className="glass p-6 rounded-3xl border-white/5 hover:border-primary/40 transition-all group relative overflow-hidden flex flex-col justify-between"
                            style={{ animationDelay: `${index * 50}ms`, background: 'linear-gradient(145deg, rgba(20,20,20,0.9) 0%, rgba(10,10,10,0.8) 100%)' }}
                          >
                            <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 blur-2xl rounded-full -mr-8 -mt-8 group-hover:bg-primary/10 transition-all" />
                            
                            <div className="flex flex-col gap-4 mb-6 relative z-10 w-full">
                              <div className="flex flex-col gap-2 w-full pr-2">
                                <div className="flex items-center gap-2">
                                  <Clock size={10} className="text-gray-600 shrink-0" />
                                  <span className="text-[8px] font-black text-gray-600 uppercase tracking-widest break-words leading-tight">
                                    {new Date(item.filled_at).toLocaleDateString()} • {new Date(item.filled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                  </span>
                                </div>
                                <h4 className="text-[14px] sm:text-[15px] font-black text-white group-hover:text-primary transition-colors leading-snug break-words">
                                  {item.form_title || 'Neural Record'}
                                </h4>
                              </div>
                              <div className="flex items-center">
                                <span className={`inline-block px-3 py-1.5 rounded-xl text-[10px] sm:text-[11px] font-black border ${
                                   scoreDisplay?.includes('/') 
                                    ? 'bg-primary/20 border-primary/30 text-primary text-glow' 
                                    : 'bg-white/5 border-white/10 text-gray-400'
                                }`}>
                                  {scoreDisplay}
                                </span>
                              </div>
                            </div>
    
                            <div className="flex flex-col gap-3 relative z-10 mt-auto">
                               {item.score_url && (
                                 <a 
                                   href={item.score_url} 
                                   target="_blank" 
                                   rel="noopener noreferrer"
                                   className="w-full inline-flex items-center justify-center gap-3 px-4 py-3 sm:py-4 rounded-2xl bg-primary text-black text-[10px] sm:text-[11px] font-black uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_15px_30px_-5px_rgba(0,191,255,0.3)] group/btn"
                                 >
                                   View Form Score 
                                   <div className="p-1 rounded-md bg-white/20 group-hover/btn:bg-white/30 transition-colors">
                                     <ArrowRight size={12} />
                                   </div>
                                 </a>
                               )}
                               <div className="flex gap-2">
                                  <a 
                                    href={item.form_url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-gray-400 text-[10px] font-black uppercase tracking-widest hover:text-white hover:bg-white/10 transition-all"
                                  >
                                     {item.score_url ? <Zap size={10} fill="currentColor" /> : 'Open Form'}
                                     <span>{item.score_url ? 'Refill' : 'Source Link'}</span>
                                  </a>
                               </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

              </div>
            </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
