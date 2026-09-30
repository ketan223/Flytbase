import React, { useState, useEffect, useRef } from 'react';
import {
  Shield, AlertTriangle, Search, MessageSquare, FileText,
  Play, Pause, SkipBack, SkipForward, Radio, BatteryCharging,
  Compass, MapPin, Gauge, Eye, Clock, Crosshair, Terminal,
  ExternalLink, CheckCircle, Volume2, Sun, Sparkles, Send
} from 'lucide-react';

export default function App() {
  const [frames, setFrames] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [status, setStatus] = useState(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTab, setActiveTab] = useState('alerts'); // 'alerts', 'search', 'chat', 'summary'
  const [selectedMission, setSelectedMission] = useState('ALL');

  // Search state
  const [searchQuery, setSearchQuery] = useState('show all truck events');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  // Chat state
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Security Command Online. I am your autonomous Drone Security Analyst Agent. How can I assist you with current airspace patrols?'
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [summaryData, setSummaryData] = useState(null);
  const [actionNotice, setActionNotice] = useState(null);

  // Fetch initial data
  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(data => setStatus(data))
      .catch(err => console.error("Status fetch err", err));

    fetch('/api/frames')
      .then(res => res.json())
      .then(data => {
        setFrames(data);
        if (data.length > 0) setCurrentIdx(0);
      })
      .catch(err => console.error("Frames fetch err", err));

    fetch('/api/alerts')
      .then(res => res.json())
      .then(data => setAlerts(data))
      .catch(err => console.error("Alerts fetch err", err));

    fetch('/api/summary')
      .then(res => res.json())
      .then(data => setSummaryData(data))
      .catch(err => console.error("Summary fetch err", err));

    // Initial search
    executeSearch('show all truck events');
  }, []);

  // Filtered frames
  const displayFrames = selectedMission === 'ALL'
    ? frames
    : frames.filter(f => f.mission_id === selectedMission);

  const currentFrame = displayFrames[currentIdx] || frames[0] || null;

  // Auto-play timer
  useEffect(() => {
    let interval = null;
    if (isPlaying && displayFrames.length > 0) {
      interval = setInterval(() => {
        setCurrentIdx(prev => (prev + 1) % displayFrames.length);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, displayFrames.length]);

  const executeSearch = async (queryText) => {
    if (!queryText.trim()) return;
    setIsSearching(true);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(queryText)}`);
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSendChat = async (question) => {
    const q = question || chatInput;
    if (!q.trim()) return;

    setMessages(prev => [...prev, { role: 'user', text: q }]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', text: data.answer }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: "Error communicating with LangChain security agent." }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const dispatchAction = async (alertId, actionType) => {
    try {
      const res = await fetch('/api/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId, action_type: actionType })
      });
      const data = await res.json();
      setActionNotice(data.message);
      setTimeout(() => setActionNotice(null), 4000);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-200 flex flex-col font-sans">
      {/* Action Notification Toast */}
      {actionNotice && (
        <div className="fixed top-4 right-4 z-50 bg-cyan-950 border border-cyan-500 text-cyan-200 px-4 py-3 rounded-lg shadow-2xl flex items-center gap-3 animate-bounce">
          <Radio className="w-5 h-5 text-cyan-400 animate-pulse" />
          <span className="text-sm font-mono">{actionNotice}</span>
        </div>
      )}

      {/* TOP TACTICAL NAVIGATION BAR */}
      <header className="border-b border-slate-800/80 bg-[#0b1120]/90 backdrop-blur px-6 py-3 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center pulse-radar">
            <Shield className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white tracking-wider font-mono">FLYTBASE AERO-DEFENSE</h1>
              <span className="text-[10px] bg-cyan-900/60 text-cyan-300 font-mono px-2 py-0.5 rounded border border-cyan-700/50">
                DIAZ-01 // v2.4
              </span>
            </div>
            <p className="text-xs text-slate-400">Docked Autonomous Drone Security Analyst Agent</p>
          </div>
        </div>

        {/* Center Mission Selector */}
        <div className="flex items-center gap-2 bg-[#070b14] border border-slate-800 rounded-lg px-3 py-1.5">
          <span className="text-xs text-slate-400 font-mono">MISSION:</span>
          <select
            value={selectedMission}
            onChange={(e) => {
              setSelectedMission(e.target.value);
              setCurrentIdx(0);
            }}
            className="bg-transparent text-xs font-mono text-cyan-400 focus:outline-none cursor-pointer"
          >
            <option value="ALL" className="bg-slate-900 text-slate-200">ALL MISSIONS (DAY + NIGHT)</option>
            <option value="PATROL_DAY_1200" className="bg-slate-900 text-slate-200">DAY PATROL (12:00 PM)</option>
            <option value="PATROL_NIGHT_0001" className="bg-slate-900 text-slate-200">NIGHT CURFEW PATROL (00:01 AM)</option>
          </select>
        </div>

        {/* Right Status Indicators */}
        <div className="flex items-center gap-5 text-xs font-mono">
          <div className="flex items-center gap-2 bg-emerald-950/40 border border-emerald-500/30 px-2.5 py-1 rounded">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-emerald-300 font-medium">DOCK: ARMED & LOCKED</span>
          </div>

          <div className="flex items-center gap-2 text-slate-300">
            <BatteryCharging className="w-4 h-4 text-emerald-400" />
            <span>96% [CHARGING]</span>
          </div>

          <div className="flex items-center gap-2 text-amber-300 bg-amber-950/30 border border-amber-600/30 px-2.5 py-1 rounded">
            <Clock className="w-3.5 h-3.5" />
            <span>CURFEW: 22:00 - 06:00</span>
          </div>
        </div>
      </header>

      {/* METRICS STRIP */}
      <section className="grid grid-cols-4 gap-4 px-6 py-3 border-b border-slate-800/60 bg-[#090e1a]">
        <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-3 flex items-center justify-between">
          <div>
            <div className="text-[11px] text-slate-400 font-mono uppercase">Frames Ingested</div>
            <div className="text-2xl font-bold font-mono text-white mt-0.5">{frames.length}</div>
          </div>
          <Eye className="w-6 h-6 text-cyan-400/60" />
        </div>

        <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-3 flex items-center justify-between">
          <div>
            <div className="text-[11px] text-slate-400 font-mono uppercase">Security Incidents</div>
            <div className="text-2xl font-bold font-mono text-crimson-400 text-red-400 mt-0.5 flex items-center gap-2">
              {alerts.length}
              <span className="text-[10px] bg-red-950 text-red-300 px-1.5 py-0.5 rounded border border-red-800">
                2 CRITICAL
              </span>
            </div>
          </div>
          <AlertTriangle className="w-6 h-6 text-red-400/60" />
        </div>

        <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-3 flex items-center justify-between">
          <div>
            <div className="text-[11px] text-slate-400 font-mono uppercase">Tracked Entities</div>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-0.5">
              {status ? status.tracked_entities : 3}
            </div>
          </div>
          <Crosshair className="w-6 h-6 text-cyan-400/60" />
        </div>

        <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-3 flex items-center justify-between">
          <div>
            <div className="text-[11px] text-slate-400 font-mono uppercase">Active Zones Monitored</div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-0.5">4 SECTORS</div>
          </div>
          <MapPin className="w-6 h-6 text-emerald-400/60" />
        </div>
      </section>

      {/* MAIN TWO-COLUMN WORKSPACE */}
      <main className="flex-1 grid grid-cols-12 gap-6 p-6">
        {/* LEFT COLUMN: DRONE GIMBAL VIDEO FEED & TELEMETRY HUD (7 COLS) */}
        <section className="col-span-7 flex flex-col gap-4">
          {/* Tactical Video Canvas Card */}
          <div className="bg-[#0f172a] border border-slate-800 rounded-xl overflow-hidden shadow-2xl relative flex flex-col">
            {/* Gimbal Header Banner */}
            <div className="bg-[#131d31] px-4 py-2 border-b border-slate-800 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="text-cyan-300 font-semibold">GIMBAL CAM 01 // 4K EO/IR FEED</span>
              </div>
              <div className="text-slate-400">
                {currentFrame ? currentFrame.timestamp : 'SYNCHRONIZING...'}
              </div>
            </div>

            {/* Video Canvas Container */}
            <div className="relative aspect-[16/10] bg-black overflow-hidden flex items-center justify-center">
              {currentFrame ? (
                <img
                  src={currentFrame.image_url}
                  alt={currentFrame.frame_id}
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-slate-500 font-mono text-sm animate-pulse">STREAMING DRONE VIDEO FEED...</div>
              )}

              {/* Tactical HUD Reticles on Corners */}
              <div className="absolute top-4 left-4 w-6 h-6 border-t-2 border-l-2 border-cyan-400/80 pointer-events-none" />
              <div className="absolute top-4 right-4 w-6 h-6 border-t-2 border-r-2 border-cyan-400/80 pointer-events-none" />
              <div className="absolute bottom-4 left-4 w-6 h-6 border-b-2 border-l-2 border-cyan-400/80 pointer-events-none" />
              <div className="absolute bottom-4 right-4 w-6 h-6 border-b-2 border-r-2 border-cyan-400/80 pointer-events-none" />

              {/* Central Target Crosshair */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40">
                <div className="w-10 h-10 border border-cyan-400 rounded-full flex items-center justify-center">
                  <div className="w-1 h-1 bg-cyan-400" />
                </div>
              </div>

              {/* Top Tactical Status Badge */}
              <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur border border-slate-700/60 px-3 py-1 rounded text-[11px] font-mono flex items-center gap-2 text-cyan-300">
                <span>SECTOR: {currentFrame?.telemetry?.zone_name || 'MAIN GATE'}</span>
                <span>|</span>
                <span>MODE: AUTO-SORTIE</span>
              </div>

              {/* Frame Alert Warning Overlay */}
              {currentFrame?.is_alert && (
                <div className="absolute top-12 left-0 right-0 bg-red-600/90 text-white px-4 py-1.5 text-xs font-mono font-bold flex items-center justify-between shadow-lg">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 animate-bounce" />
                    <span>INCIDENT DETECTED ON FRAME {currentFrame.frame_id}</span>
                  </div>
                  <span className="text-[10px] bg-black/40 px-2 py-0.5 rounded">POLICY TRIGGERED</span>
                </div>
              )}
            </div>

            {/* Video Playback & Timeline Controls */}
            <div className="bg-[#0b1120] p-4 border-t border-slate-800 flex flex-col gap-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">
                  FRAME: <strong className="text-white">{currentIdx + 1}</strong> OF <strong className="text-white">{displayFrames.length}</strong> ({currentFrame?.frame_id})
                </span>
                <span className="text-cyan-400 font-mono">
                  {currentFrame ? currentFrame.timestamp : ''}
                </span>
              </div>

              {/* Range Slider */}
              <input
                type="range"
                min="0"
                max={Math.max(0, displayFrames.length - 1)}
                value={currentIdx}
                onChange={(e) => setCurrentIdx(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
              />

              {/* Playback Buttons */}
              <div className="flex items-center justify-between pt-1">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentIdx(prev => Math.max(0, prev - 1))}
                    className="p-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300"
                    title="Previous Frame"
                  >
                    <SkipBack className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className={`px-3 py-1.5 rounded text-xs font-mono flex items-center gap-1.5 transition ${
                      isPlaying
                        ? 'bg-amber-600 text-white hover:bg-amber-500'
                        : 'bg-cyan-600 text-white hover:bg-cyan-500'
                    }`}
                  >
                    {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                    <span>{isPlaying ? 'PAUSE PATROL' : 'RUN FLIGHT SIM'}</span>
                  </button>

                  <button
                    onClick={() => setCurrentIdx(prev => Math.min(displayFrames.length - 1, prev + 1))}
                    className="p-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300"
                    title="Next Frame"
                  >
                    <SkipForward className="w-4 h-4" />
                  </button>
                </div>

                <div className="text-xs text-slate-400 font-mono">
                  MISSION: <span className="text-slate-200">{currentFrame?.mission_id || 'PATROL'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* TELEMETRY HUD & VLM INFERENCE BOX */}
          <div className="grid grid-cols-2 gap-4">
            {/* Live Flight Telemetry Gauge Box */}
            <div className="bg-[#0f172a] border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                <div className="text-xs font-mono font-bold text-slate-300 flex items-center gap-2">
                  <Gauge className="w-4 h-4 text-cyan-400" />
                  <span>FLIGHT TELEMETRY HUD</span>
                </div>
                <span className="text-[10px] font-mono text-emerald-400">TELEMETRY SYNCED</span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="bg-[#090d16] p-2.5 rounded border border-slate-800/80">
                  <span className="text-[10px] text-slate-400">ALTITUDE (AGL)</span>
                  <div className="text-lg font-bold text-white mt-0.5">
                    {currentFrame?.telemetry?.altitude_m?.toFixed(1) || '16.5'} m
                  </div>
                </div>

                <div className="bg-[#090d16] p-2.5 rounded border border-slate-800/80">
                  <span className="text-[10px] text-slate-400">AIR SPEED</span>
                  <div className="text-lg font-bold text-white mt-0.5">
                    {currentFrame?.telemetry?.speed_mps?.toFixed(1) || '4.2'} m/s
                  </div>
                </div>

                <div className="bg-[#090d16] p-2.5 rounded border border-slate-800/80">
                  <span className="text-[10px] text-slate-400">HEADING ANGLE</span>
                  <div className="text-lg font-bold text-white mt-0.5">
                    {currentFrame?.telemetry?.heading_deg?.toFixed(0) || '045'}°
                  </div>
                </div>

                <div className="bg-[#090d16] p-2.5 rounded border border-slate-800/80">
                  <span className="text-[10px] text-slate-400">BATTERY STATE</span>
                  <div className="text-lg font-bold text-emerald-400 mt-0.5">
                    {currentFrame?.telemetry?.battery_pct?.toFixed(0) || '98'}%
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-800/60 text-[11px] font-mono text-slate-400 flex items-center justify-between">
                <span>GPS LAT: {currentFrame?.telemetry?.latitude?.toFixed(6) || '37.774929'}</span>
                <span>LON: {currentFrame?.telemetry?.longitude?.toFixed(6) || '-122.419416'}</span>
              </div>
            </div>

            {/* VLM Analysis Box */}
            <div className="bg-[#0f172a] border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                <div className="text-xs font-mono font-bold text-slate-300 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  <span>VLM & CONTEXT INFERENCE</span>
                </div>
                <span className="text-[10px] font-mono bg-cyan-950 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-800">
                  BLIP/CLIP
                </span>
              </div>

              <div className="text-xs space-y-2.5 flex-1">
                <div>
                  <span className="text-[10px] font-mono text-slate-400">NATURAL LANGUAGE CAPTION:</span>
                  <p className="text-slate-200 mt-0.5 font-medium leading-relaxed">
                    "{currentFrame?.caption || 'Scanning area...'}"
                  </p>
                </div>

                <div>
                  <span className="text-[10px] font-mono text-slate-400">CONTEXTUAL ACTIVITY:</span>
                  <p className="text-slate-300 mt-0.5 text-[11px] leading-relaxed">
                    {currentFrame?.activity_summary || 'Standard patrol monitoring.'}
                  </p>
                </div>

                {currentFrame?.detected_objects && currentFrame.detected_objects.length > 0 && (
                  <div>
                    <span className="text-[10px] font-mono text-slate-400">DETECTED ENTITIES:</span>
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {currentFrame.detected_objects.map((obj, i) => (
                        <span key={i} className="text-[10px] font-mono bg-slate-800 text-cyan-300 px-2 py-0.5 rounded border border-slate-700">
                          {obj.description} ({obj.label}) — {(obj.confidence * 100).toFixed(0)}%
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN: TABBED INTELLIGENCE & CONTROL PANELS (5 COLS) */}
        <section className="col-span-5 bg-[#0f172a] border border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-2xl">
          {/* TAB HEADER BAR */}
          <div className="bg-[#131d31] p-1.5 border-b border-slate-800 grid grid-cols-4 gap-1 text-xs font-mono">
            <button
              onClick={() => setActiveTab('alerts')}
              className={`py-2 px-2 rounded-lg font-medium flex items-center justify-center gap-1.5 transition ${
                activeTab === 'alerts'
                  ? 'bg-red-950/80 text-red-300 border border-red-700/60 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>ALERTS ({alerts.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('search')}
              className={`py-2 px-2 rounded-lg font-medium flex items-center justify-center gap-1.5 transition ${
                activeTab === 'search'
                  ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-700/60 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>SEARCH</span>
            </button>

            <button
              onClick={() => setActiveTab('chat')}
              className={`py-2 px-2 rounded-lg font-medium flex items-center justify-center gap-1.5 transition ${
                activeTab === 'chat'
                  ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-700/60 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>AI CHAT</span>
            </button>

            <button
              onClick={() => setActiveTab('summary')}
              className={`py-2 px-2 rounded-lg font-medium flex items-center justify-center gap-1.5 transition ${
                activeTab === 'summary'
                  ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-700/60 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>DEBRIEF</span>
            </button>
          </div>

          {/* TAB CONTENT PANELS */}
          <div className="flex-1 p-4 overflow-y-auto max-h-[calc(100vh-230px)]">
            {/* TAB 1: ALERTS STREAM */}
            {activeTab === 'alerts' && (
              <div className="space-y-3.5">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-xs font-mono">
                  <span className="text-slate-400">REAL-TIME INCIDENT STREAM</span>
                  <span className="text-red-400">{alerts.length} ALERTS TRIGGERED</span>
                </div>

                {alerts.map((a, i) => {
                  const isCrit = a.severity === 'CRITICAL';
                  return (
                    <div
                      key={i}
                      className={`p-3.5 rounded-lg border text-xs flex flex-col gap-2 transition ${
                        isCrit
                          ? 'bg-red-950/20 border-red-800/80 alert-pulse'
                          : 'bg-amber-950/20 border-amber-800/60'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className={`w-4 h-4 ${isCrit ? 'text-red-400' : 'text-amber-400'}`} />
                          <span className={`font-mono font-bold ${isCrit ? 'text-red-300' : 'text-amber-300'}`}>
                            [{a.severity}] {a.description}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-400">{a.timestamp}</span>
                      </div>

                      <div className="text-[11px] text-slate-300">
                        <strong>Reason:</strong> {a.context_reason}
                      </div>

                      <div className="text-[11px] text-cyan-300 font-mono">
                        <strong>Suggested Action:</strong> {a.suggested_action}
                      </div>

                      {/* Tactical Response Action Buttons */}
                      <div className="pt-2 border-t border-slate-800/60 flex items-center gap-2">
                        <button
                          onClick={() => dispatchAction(a.alert_id, 'spotlight')}
                          className="px-2.5 py-1 bg-cyan-950 hover:bg-cyan-900 border border-cyan-700/60 text-cyan-300 rounded text-[10px] font-mono flex items-center gap-1"
                        >
                          <Sun className="w-3 h-3" />
                          <span>DRONE SPOTLIGHT</span>
                        </button>

                        <button
                          onClick={() => dispatchAction(a.alert_id, 'loudspeaker')}
                          className="px-2.5 py-1 bg-amber-950 hover:bg-amber-900 border border-amber-700/60 text-amber-300 rounded text-[10px] font-mono flex items-center gap-1"
                        >
                          <Volume2 className="w-3 h-3" />
                          <span>LOUDSPEAKER WARNING</span>
                        </button>

                        <button
                          onClick={() => dispatchAction(a.alert_id, 'acknowledge')}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px] font-mono flex items-center gap-1 ml-auto"
                        >
                          <CheckCircle className="w-3 h-3 text-emerald-400" />
                          <span>ACK</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* TAB 2: SEMANTIC CROSS-DOMAIN SEARCH */}
            {activeTab === 'search' && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="text-xs font-mono text-slate-400">CHROMA VECTOR SEARCH ENGINE</div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && executeSearch(searchQuery)}
                      placeholder="e.g., show all truck events..."
                      className="flex-1 bg-[#090d16] border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                    />
                    <button
                      onClick={() => executeSearch(searchQuery)}
                      disabled={isSearching}
                      className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition"
                    >
                      <Search className="w-3.5 h-3.5" />
                      <span>{isSearching ? 'SEARCHING...' : 'QUERY'}</span>
                    </button>
                  </div>

                  {/* Quick Suggested Queries */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {['show all truck events', 'person loitering at midnight', 'delivery vehicles', 'garage bay staging'].map((chip, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setSearchQuery(chip);
                          executeSearch(chip);
                        }}
                        className="text-[10px] font-mono bg-slate-800/80 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-700"
                      >
                        {chip}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Search Results Grid */}
                <div className="space-y-3 pt-2 border-t border-slate-800">
                  <div className="text-xs font-mono text-slate-400 flex items-center justify-between">
                    <span>INDEXED MATCHES ({searchResults.length})</span>
                    <span className="text-cyan-400">APPROX NEAREST NEIGHBOR</span>
                  </div>

                  {searchResults.map((r, i) => (
                    <div
                      key={i}
                      className="bg-[#090d16] border border-slate-800 hover:border-cyan-500/50 rounded-lg p-3 flex gap-3 transition"
                    >
                      {r.image_url && (
                        <img
                          src={r.image_url}
                          alt={r.frame_id}
                          className="w-24 h-16 object-cover rounded bg-black border border-slate-800 shrink-0"
                        />
                      )}
                      <div className="flex-1 min-w-0 text-xs">
                        <div className="flex items-center justify-between font-mono">
                          <span className="font-bold text-cyan-300">{r.frame_id}</span>
                          <span className="text-[10px] bg-cyan-950 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-800">
                            MATCH: {r.score}%
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                          🕒 {r.timestamp} | 📍 {r.zone_name}
                        </div>
                        <p className="text-[11px] text-slate-300 mt-1 line-clamp-2">
                          {r.document}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 3: LANGCHAIN SECURITY ANALYST CHAT */}
            {activeTab === 'chat' && (
              <div className="flex flex-col h-[520px]">
                {/* Chat Stream */}
                <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                  {messages.map((m, idx) => (
                    <div
                      key={idx}
                      className={`flex flex-col text-xs ${
                        m.role === 'user' ? 'items-end' : 'items-start'
                      }`}
                    >
                      <div className="text-[10px] font-mono text-slate-500 mb-1">
                        {m.role === 'user' ? 'SECURITY OPERATOR' : 'AI SECURITY ANALYST AGENT'}
                      </div>
                      <div
                        className={`p-3 rounded-xl max-w-[88%] leading-relaxed ${
                          m.role === 'user'
                            ? 'bg-cyan-600 text-white rounded-br-none'
                            : 'bg-[#090d16] border border-slate-800 text-slate-200 rounded-bl-none shadow-md font-sans whitespace-pre-line'
                        }`}
                      >
                        {m.text}
                      </div>
                    </div>
                  ))}
                  {isChatLoading && (
                    <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 animate-pulse">
                      <Terminal className="w-3.5 h-3.5" />
                      <span>Agent reasoning over patrol vector store...</span>
                    </div>
                  )}
                </div>

                {/* Quick Query Chips */}
                <div className="pt-2 flex flex-wrap gap-1 border-t border-slate-800 mb-2">
                  {[
                    "What objects were in the video?",
                    "Did the blue Ford F150 enter twice today?",
                    "What alerts triggered at midnight?"
                  ].map((chip, i) => (
                    <button
                      key={i}
                      onClick={() => handleSendChat(chip)}
                      className="text-[10px] font-mono bg-slate-800/80 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-700"
                    >
                      {chip}
                    </button>
                  ))}
                </div>

                {/* Chat Input Box */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                    placeholder="Ask about detected vehicles, loitering, or zone history..."
                    className="flex-1 bg-[#090d16] border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    onClick={() => handleSendChat()}
                    disabled={isChatLoading}
                    className="px-3 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs flex items-center justify-center transition"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* TAB 4: POST-PATROL DEBRIEF & SUMMARY */}
            {activeTab === 'summary' && (
              <div className="space-y-4 text-xs font-sans">
                {/* 1-Sentence Executive Summary */}
                <div className="bg-cyan-950/30 border border-cyan-800/60 rounded-lg p-3.5">
                  <div className="text-[10px] font-mono text-cyan-400 font-bold uppercase mb-1">
                    📌 1-Sentence Executive Summary (Bonus 1)
                  </div>
                  <p className="text-slate-100 font-medium leading-relaxed">
                    {summaryData?.one_sentence_summary || "Patrol mission completed across 3 sectors."}
                  </p>
                </div>

                {/* Full Executive Briefing */}
                <div className="bg-[#090d16] border border-slate-800 rounded-lg p-3.5">
                  <div className="text-[10px] font-mono text-slate-400 font-bold uppercase mb-2">
                    Operational Debriefing
                  </div>
                  <pre className="text-[11px] font-mono text-slate-300 whitespace-pre-wrap leading-relaxed">
                    {summaryData?.executive_summary}
                  </pre>
                </div>

                {/* Chronological Key Events */}
                <div className="space-y-2">
                  <div className="text-[10px] font-mono text-slate-400 font-bold uppercase">
                    Chronological Incident Milestones
                  </div>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto">
                    {summaryData?.key_events?.map((ev, i) => (
                      <div key={i} className="text-[11px] text-slate-300 font-mono bg-[#090d16] p-2 rounded border border-slate-800/80">
                        {ev}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Embedded Video Walkthrough with Controls */}
                <div className="bg-[#090d16] border border-cyan-700/60 rounded-lg p-3 space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono font-bold text-cyan-400">
                    <div className="flex items-center gap-1.5">
                      <Play className="w-3.5 h-3.5 text-cyan-400" />
                      <span>CANDIDATE DEMO WALKTHROUGH VIDEO</span>
                    </div>
                    <span className="text-[10px] bg-cyan-950 px-1.5 py-0.5 rounded border border-cyan-800 text-cyan-300">
                      WITH VOICEOVER
                    </span>
                  </div>
                  <video
                    controls
                    className="w-full rounded-md border border-slate-800 aspect-video bg-black"
                    src="/data/walkthrough_demo.mp4"
                    poster="/data/react_dashboard_live.png"
                  >
                    Your browser does not support HTML5 video.
                  </video>
                  <a
                    href="https://drive.google.com/file/d/1npOgKsi35nmpjYtcANqZdjWedgEEL4sb/view?usp=sharing"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] font-mono text-cyan-400 hover:underline flex items-center gap-1 justify-center pt-1"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>Open Alternative Google Drive Stream</span>
                  </a>
                </div>

                {/* PDF Download Button */}
                <div className="pt-2 border-t border-slate-800">
                  <a
                    href="/data/FlytBase_AI_Engineer_Assignment_Report.pdf"
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-mono font-bold flex items-center justify-center gap-2 border border-slate-700 transition"
                  >
                    <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
                    <span>VIEW OFFICIAL PDF ASSIGNMENT REPORT</span>
                  </a>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
