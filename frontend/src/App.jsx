import React, { useState, useEffect, useRef, useMemo } from 'react';
import axios from 'axios';
import { 
  FileText, Mic, History, Trash2, Languages, 
  Search, Upload, CheckCircle, AlertCircle, 
  Printer, Barcode, Box, MapPin, User,
  Maximize2, X, HelpCircle, Square, Cloud, Moon, Sun, Download, BarChart2, MessageSquare, Send
} from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:5000/api';
const STATIC_BASE = 'http://localhost:5000';

function App() {
  const [results, setResults] = useState([]);
  const [history, setHistory] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [voiceResult, setVoiceResult] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [fullScreenPages, setFullScreenPages] = useState(null);
  
  // Advanced Features State
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [historyFilter, setHistoryFilter] = useState("all");
  const [activeTab, setActiveTab] = useState("dashboard");
  const [translatingIdx, setTranslatingIdx] = useState(null);
  
  // Chat State
  const [chatInputs, setChatInputs] = useState({});
  const [chatHistory, setChatHistory] = useState({}); 

  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);
  const recordTimeout = useRef(null);

  useEffect(() => {
    fetchHistory();
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
      document.body.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    document.body.classList.toggle('dark', newMode);
    localStorage.setItem('theme', newMode ? 'dark' : 'light');
  };

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/history`);
      const data = Array.isArray(res.data) ? res.data : [];
      setHistory(data.reverse());
    } catch (err) { 
      console.error("History fetch failed", err); 
      setHistory([]);
    }
  };

  const handleFiles = async (files) => {
    if (!files || !files.length) return;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) formData.append('pdfFile', files[i]);

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/upload`, formData);
      if (res.data && res.data.results && res.data.results.length > 0) {
        setResults(res.data.results);
        setActiveTab("dashboard");
      } else { 
        alert("No logistics data detected in file."); 
      }
      fetchHistory();
    } catch (err) { 
      alert(`Upload failed: ${err.message}`); 
    } finally { 
      setLoading(false); 
    }
  };

  const handleFileUpload = (e) => handleFiles(e.target.files);

  const clearHistory = async () => {
    if (!window.confirm("Clear all records?")) return;
    try {
      await axios.post(`${API_BASE}/history/clear`);
      setHistory([]);
      setResults([]);
    } catch (err) { console.error(err); }
  };

  // --- Voice & Speech ---
  const toggleRecording = () => isRecording ? stopRecording() : startRecording();
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];
      mediaRecorder.current.ondataavailable = (e) => audioChunks.current.push(e.data);
      mediaRecorder.current.onstop = sendVoiceData;
      mediaRecorder.current.start();
      setIsRecording(true);
      setVoiceResult(null);
      recordTimeout.current = setTimeout(() => stopRecording(), 10000);
    } catch (err) { alert("Mic access denied."); }
  };
  const stopRecording = () => {
    if (recordTimeout.current) clearTimeout(recordTimeout.current);
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      if (mediaRecorder.current.stream) {
        mediaRecorder.current.stream.getTracks().forEach(t => t.stop());
      }
    }
  };
  const sendVoiceData = async () => {
    if (audioChunks.current.length === 0) return;
    const formData = new FormData();
    formData.append('audio', new Blob(audioChunks.current, { type: 'audio/webm' }));
    try {
      const res = await axios.post(`${API_BASE}/voice`, formData);
      setVoiceResult(res.data);
      if (res.data && res.data.text) fetchHistory();
    } catch (err) { console.error("Voice failed", err); }
  };

  // --- Gemini Chat Logic ---
  const handleChat = async (resultId, docText) => {
    const question = chatInputs[resultId];
    if (!question || !resultId) return;

    const newChatHistory = { ...chatHistory };
    if (!newChatHistory[resultId]) newChatHistory[resultId] = [];
    newChatHistory[resultId].push({ role: 'user', text: question });
    setChatHistory(newChatHistory);
    setChatInputs({ ...chatInputs, [resultId]: "" });

    try {
      const res = await axios.post(`${API_BASE}/chat`, { document_text: docText, question });
      newChatHistory[resultId].push({ role: 'ai', text: res.data?.answer || "No response from AI." });
      setChatHistory({ ...newChatHistory });
    } catch (err) {
      newChatHistory[resultId].push({ role: 'ai', text: "Gemini API Error. Check backend configuration." });
      setChatHistory({ ...newChatHistory });
    }
  };

  // --- Analytics Donut Chart Component ---
  const DonutChart = ({ data }) => {
    if (!data || data.length === 0) return null;
    let cumulativePercent = 0;
    const radius = 70;
    const circumference = 2 * Math.PI * radius;
    const colors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

    return (
      <svg width="200" height="200" viewBox="0 0 200 200" style={{transform: 'rotate(-90deg)'}}>
        {data.map((item, i) => {
          const strokeDasharray = `${(item.percent / 100) * circumference} ${circumference}`;
          const strokeDashoffset = -(cumulativePercent / 100) * circumference;
          cumulativePercent += item.percent;
          return (
            <circle
              key={i}
              cx="100" cy="100" r={radius}
              fill="transparent"
              stroke={colors[i % colors.length]}
              strokeWidth="30"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
            />
          );
        })}
        <circle cx="100" cy="100" r="55" fill="var(--card-bg)" style={{transform: 'rotate(90deg)'}} />
      </svg>
    );
  };

  const analyticsData = useMemo(() => {
    const uploads = (history || []).filter(h => h.type === 'upload' && h.data);
    const docTypes = {};
    uploads.forEach(u => {
      const rawType = u.data?.doc_type || "Unknown";
      const type = typeof rawType === 'string' ? rawType.split(' (')[0] : "Unknown";
      docTypes[type] = (docTypes[type] || 0) + 1;
    });
    return {
      total: uploads.length,
      docTypes: Object.entries(docTypes).map(([type, count]) => ({
        type, count, percent: uploads.length > 0 ? Math.round((count/uploads.length)*100) : 0
      }))
    };
  }, [history]);

  return (
    <div className="app-container">
      <header>
        <div className="logo"><Box size={32} /> LogiVoice 2.0</div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={toggleDarkMode} title="Toggle Theme">
            {isDarkMode ? <Sun size={18}/> : <Moon size={18}/>}
          </button>
          <button className="btn btn-secondary" onClick={() => setShowHelp(true)} title="Help"><HelpCircle size={18}/></button>
          <button className="btn btn-secondary" onClick={clearHistory} title="Clear Records"><Trash2 size={18}/></button>
        </div>
      </header>

      <main className="dashboard-grid">
        <div className="main-content">
          <div className="tabs">
            <button className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>Dashboard</button>
            <button className={`tab ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => setActiveTab('analytics')}>Analytics</button>
          </div>

          {activeTab === 'dashboard' && (
            <div className="card">
              <label className={`upload-zone ${isDragging ? 'dragging' : ''}`}
                onDragOver={e => {e.preventDefault(); setIsDragging(true)}}
                onDragLeave={() => setIsDragging(false)}
                onDrop={e => {e.preventDefault(); setIsDragging(false); handleFiles(e.dataTransfer.files)}}>
                <input type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.txt" onChange={handleFileUpload} hidden />
                <Upload size={48} color="#94a3b8" />
                <p><b>Drag & Drop</b> or Click to Upload Documents</p>
              </label>

              {loading && (
                <div style={{textAlign: 'center', padding: '2rem'}}>
                  <div className="spinner"></div>
                  <p>Processing with AI...</p>
                </div>
              )}

              <div className="results-list">
                {(results || []).map((res, i) => (
                  <div key={res.id || i} className="result-item-wrapper" style={{marginBottom: '2rem'}}>
                    <div className="result-item">
                      <div className="preview-container" onClick={() => setFullScreenPages(res.all_pages || (res.img_url ? [res.img_url] : []))}>
                        {res.img_url ? (
                          <img src={`${STATIC_BASE}${res.img_url}`} className="preview-img" alt="Preview"/>
                        ) : (
                          <div style={{height: '100%', display: 'flex', alignItems:'center', justifyContent:'center', background: 'var(--bg)'}}>No Preview</div>
                        )}
                        <button className="preview-overlay-btn"><Maximize2 size={16}/></button>
                      </div>
                      <div className="data-container">
                        <div className="badge success" style={{marginBottom:'1rem'}}>{res.doc_type || "Logistics Doc"}</div>
                        <div className="data-field"><b>INV NO:</b> {res.invoice_number || "N/A"}</div>
                        <div className="data-field"><b>CUSTOMER:</b> {res.customer_name || "N/A"}</div>
                        <div className="data-field"><b>ADDRESS:</b> {res.delivery_address || "N/A"}</div>
                        <div style={{marginTop: 'auto'}}>
                          <button className="btn btn-secondary print-keep" onClick={() => window.print()}><Printer size={16}/> Print</button>
                        </div>
                      </div>
                    </div>

                    {/* Gemini Chat UI */}
                    <div className="chat-box" style={{marginTop: '1rem', background: 'var(--bg)', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--border)'}}>
                      <div style={{display:'flex', alignItems:'center', gap:'0.5rem', marginBottom:'1rem', color:'var(--primary)'}}>
                        <MessageSquare size={18}/> <b>Chat with this Document (AI)</b>
                      </div>
                      <div className="chat-messages" style={{maxHeight: '150px', overflowY: 'auto', marginBottom: '1rem'}}>
                        {(chatHistory[res.id || i] || []).map((msg, mid) => (
                          <div key={mid} style={{marginBottom:'0.5rem', textAlign: msg.role === 'user' ? 'right' : 'left'}}>
                            <span style={{
                              display:'inline-block', padding:'0.5rem', borderRadius:'0.5rem',
                              background: msg.role === 'user' ? 'var(--primary)' : 'var(--card-bg)',
                              color: msg.role === 'user' ? 'white' : 'var(--text)',
                              fontSize: '0.875rem', border: '1px solid var(--border)'
                            }}>
                              {msg.text}
                            </span>
                          </div>
                        ))}
                      </div>
                      <div style={{display:'flex', gap:'0.5rem'}}>
                        <input type="text" placeholder="Ask AI anything about this doc..." className="search-input" style={{margin:0}}
                          value={chatInputs[res.id || i] || ""} onChange={e => setChatInputs({...chatInputs, [res.id || i]: e.target.value})}
                          onKeyPress={e => e.key === 'Enter' && handleChat(res.id || i, res.full_text)} />
                        <button className="btn btn-primary" onClick={() => handleChat(res.id || i, res.full_text)}><Send size={16}/></button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="card">
              <h2 style={{marginTop: 0}}>Analytics Overview</h2>
              {analyticsData.total === 0 ? (
                <p>No documents processed yet.</p>
              ) : (
                <div style={{display: 'flex', gap: '3rem', alignItems: 'center', flexWrap: 'wrap'}}>
                  <div style={{textAlign:'center'}}>
                    <DonutChart data={analyticsData.docTypes} />
                    <h3 style={{marginTop:'1rem'}}>Total: {analyticsData.total} Docs</h3>
                  </div>
                  <div style={{flex: 1, minWidth: '250px'}}>
                    {analyticsData.docTypes.map((dt, i) => (
                      <div key={i} style={{marginBottom:'1rem'}}>
                        <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.875rem'}}>
                          <span>{dt.type}</span> <b>{dt.count} ({dt.percent}%)</b>
                        </div>
                        <div style={{height:'8px', background:'var(--border)', borderRadius:'4px', marginTop:'0.25rem'}}>
                          <div style={{height:'100%', background:['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][i%5], width:`${dt.percent}%`, borderRadius:'4px'}} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="sidebar">
          <div className="card">
            <h3><History size={20}/> History</h3>
            <input type="text" placeholder="Search history..." className="search-input" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
            <div className="history-list">
              {history.length === 0 && <p style={{color: 'var(--text-muted)', fontSize: '0.875rem'}}>No records found.</p>}
              {(history || []).map((h, i) => (
                <div key={i} className="history-item">
                  <b>{h.type === 'upload' ? (h.data?.filename || "Unknown File") : `Voice: "${h.text || "..."}"`}</b>
                  <div style={{fontSize:'0.7rem', color:'var(--text-muted)'}}>{h.timestamp ? new Date(h.timestamp).toLocaleString() : "Date Unknown"}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <div className={`voice-btn ${isRecording ? 'recording' : ''}`} onClick={toggleRecording} title="Voice Command">
        {isRecording ? <Square size={28} fill="white" /> : <Mic size={28} />}
      </div>

      {fullScreenPages && fullScreenPages.length > 0 && (
        <div className="modal-overlay" onClick={() => setFullScreenPages(null)}>
          <div className="modal-content" style={{background:'none', maxWidth:'90vw', overflowY:'auto', maxHeight: '100vh'}}>
            {fullScreenPages.map((url, i) => (
              <img key={i} src={`${STATIC_BASE}${url}`} style={{width:'100%', marginBottom:'2rem', borderRadius:'1rem', background: 'white'}} alt={`Page ${i+1}`} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
