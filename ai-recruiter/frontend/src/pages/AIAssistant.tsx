import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { 
  Sparkles, 
  Send, 
  Bot, 
  User, 
  Search, 
  Briefcase, 
  FileText, 
  Copy, 
  Check, 
  RefreshCw, 
  AlertCircle, 
  Database, 
  ChevronRight,
  ShieldCheck,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';
import { aiAssistantService } from '../services/aiAssistantService';
import { jobService } from '../services/jobService';
import { candidateService } from '../services/candidateService';
import { Job, Candidate, ChatMessage } from '../types';

export const AIAssistant: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `👋 **Welcome to the AI Recruiter Assistant & Local RAG Hub!**

I am your autonomous recruiting copilot powered by local vector embeddings and deterministic matching engines. 

Here are a few high-impact things you can ask me:
- **Semantic Talent Search:** *"Find candidates with strong hands-on experience in Kafka and distributed Python."*
- **Role-Tailored Interview Protocol:** Select a candidate and ask *"Generate 5 technical interview questions targeting their architecture depth."*
- **Personalized Outreach:** *"Draft an engaging outreach email for the Senior DevOps Engineer role."*
- **Evaluation Synthesis:** *"Evaluate candidate strengths and gaps for the Lead Data Engineer position."*

Select a role or candidate below to ground our conversation, or ask anything!`,
      timestamp: new Date().toISOString(),
      suggested_actions: ['Find Python Engineers', 'Draft Outreach', 'Generate Interview Questions']
    }
  ]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Context Selection
  const [jobs, setJobs] = useState<Job[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>('');

  // Vector Index Status
  const [reindexing, setReindexing] = useState(false);
  const [indexStatus, setIndexStatus] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    jobService.getJobs().then(setJobs).catch(() => {});
    candidateService.getCandidates().then(setCandidates).catch(() => {});
  }, []);

  const handleSend = async (customMessage?: string) => {
    const textToSend = customMessage || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: textToSend.trim(),
      timestamp: new Date().toISOString(),
      job_id: selectedJobId || undefined,
      candidate_id: selectedCandidateId || undefined
    };

    setMessages(prev => [...prev, userMsg]);
    if (!customMessage) setInput('');
    setLoading(true);

    try {
      // Build history
      const historyPayload = messages.slice(-6).map(m => ({
        role: m.role,
        content: m.content
      }));

      const res = await aiAssistantService.chat({
        message: userMsg.content,
        job_id: selectedJobId || undefined,
        candidate_id: selectedCandidateId || undefined,
        history: historyPayload
      });

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.reply,
        timestamp: new Date().toISOString(),
        intent: res.intent,
        results: res.results,
        suggested_actions: res.suggested_actions,
        candidate_id: res.candidate_id || undefined,
        job_id: res.job_id || undefined
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Error:** ${err?.response?.data?.detail || 'Failed to process AI consultation.'}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleReindex = async () => {
    try {
      setReindexing(true);
      const res = await aiAssistantService.reindexVectors();
      setIndexStatus(`FAISS Index: ${res.total_vectors} vectors synced (${res.dimension}-d)`);
      setTimeout(() => setIndexStatus(null), 4000);
    } catch (err: any) {
      alert('Failed to rebuild vector index');
    } finally {
      setReindexing(false);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const quickPrompts = [
    'Find candidates with 5+ years experience in distributed Python and Kubernetes',
    'Generate role-tailored technical interview questions',
    'Draft a personalized outreach email for our open role',
    'Evaluate candidate strengths and potential gaps'
  ];

  return (
    <div className="space-y-4 pb-12 animate-fade-in flex flex-col h-[calc(100vh-140px)]">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/60 border border-slate-800 p-4 rounded-2xl flex-shrink-0">
        <div>
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-brand-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              AI Recruiter Assistant & Local RAG Workspace
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Grounded in local Sentence Transformers, FAISS semantic vector indexing, and your talent database.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          {indexStatus && (
            <span className="text-2xs font-medium text-emerald-300 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
              {indexStatus}
            </span>
          )}
          <button
            onClick={handleReindex}
            disabled={reindexing}
            className="btn-secondary text-xs flex items-center space-x-1.5"
            title="Synchronize all candidate embeddings with FAISS vector store"
          >
            <Database className={`w-3.5 h-3.5 ${reindexing ? 'animate-spin text-brand-400' : 'text-slate-400'}`} />
            <span>{reindexing ? 'Re-Indexing...' : 'Sync Vector Index'}</span>
          </button>
        </div>
      </div>

      {/* Context Selection Toolbar */}
      <div className="flex flex-wrap gap-2.5 items-center bg-slate-900/40 border border-slate-800/80 p-3 rounded-xl text-xs flex-shrink-0">
        <span className="text-slate-400 font-medium">Grounded Context:</span>

        {/* Job selector */}
        <select
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="input text-xs py-1.5 w-60"
        >
          <option value="">Target Requisition: None / General</option>
          {jobs.map(j => (
            <option key={j.id} value={j.id}>{j.title} ({j.company})</option>
          ))}
        </select>

        {/* Candidate selector */}
        <select
          value={selectedCandidateId}
          onChange={(e) => setSelectedCandidateId(e.target.value)}
          className="input text-xs py-1.5 w-60"
        >
          <option value="">Specific Candidate: None / Auto-detect</option>
          {candidates.map(c => (
            <option key={c.id} value={c.id}>{c.name} &bull; {c.total_experience}y exp</option>
          ))}
        </select>

        {(selectedJobId || selectedCandidateId) && (
          <button
            onClick={() => { setSelectedJobId(''); setSelectedCandidateId(''); }}
            className="text-2xs text-slate-400 hover:text-white underline ml-auto"
          >
            Clear Context
          </button>
        )}
      </div>

      {/* Main Chat Thread */}
      <div className="flex-1 overflow-y-auto card p-4 space-y-4 custom-scrollbar bg-slate-900/30">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';

          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  isUser
                    ? 'bg-brand-600 text-white'
                    : 'bg-indigo-500/20 border border-indigo-500/30 text-indigo-400'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Content Bubble */}
              <div
                className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed space-y-3 ${
                  isUser
                    ? 'bg-brand-600 text-white shadow-md'
                    : 'bg-slate-900/90 border border-slate-800 text-slate-200 shadow-lg'
                }`}
              >
                <div className="whitespace-pre-wrap font-sans space-y-2">
                  {msg.content}
                </div>

                {/* Structured Semantic Search Candidate Cards (if returned) */}
                {msg.results && msg.results.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/80 space-y-2">
                    <span className="text-2xs uppercase tracking-wider font-semibold text-brand-400 block">
                      Retrieved Talent Matches:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {msg.results.map((res: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-white text-xs">{res.name}</span>
                            <span className="text-2xs font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                              {res.similarity_score}% Fit
                            </span>
                          </div>
                          <div className="text-[10px] text-slate-400">
                            {res.experience}y exp &bull; {res.location}
                          </div>
                          {res.skills && (
                            <div className="flex flex-wrap gap-1 pt-1">
                              {res.skills.slice(0, 3).map((s: string) => (
                                <span key={s} className="px-1 py-0.2 rounded text-[9px] bg-slate-800 text-slate-300">
                                  {s}
                                </span>
                              ))}
                            </div>
                          )}
                          {res.candidate_id && (
                            <Link
                              to={`/candidates/${res.candidate_id}`}
                              className="inline-flex items-center space-x-1 text-2xs text-brand-400 hover:text-brand-300 pt-1"
                            >
                              <span>View Profile</span>
                              <ChevronRight className="w-3 h-3" />
                            </Link>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Copy Button for drafts / protocols */}
                {!isUser && (
                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-2xs text-slate-400">
                    <span>AI Decision Support</span>
                    <button
                      onClick={() => handleCopy(msg.content, msg.id)}
                      className="flex items-center space-x-1 text-slate-400 hover:text-white transition"
                    >
                      {copiedId === msg.id ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy Response</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center">
              <Bot className="w-4 h-4 animate-pulse" />
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl px-4 py-3 text-xs text-slate-400 flex items-center space-x-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-brand-400" />
              <span>Synthesizing talent context and generating response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompt Chips */}
      <div className="flex flex-wrap gap-2 flex-shrink-0">
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            disabled={loading}
            className="text-2xs px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition flex items-center space-x-1"
          >
            <Sparkles className="w-3 h-3 text-brand-400" />
            <span>{prompt}</span>
          </button>
        ))}
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 bg-slate-900/90 border border-slate-800 rounded-2xl p-2.5 shadow-xl">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about candidates, request interview questions, or ask for email drafts..."
            className="input text-xs flex-1 bg-transparent border-none focus:ring-0"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn-primary py-2 px-4 text-xs flex items-center space-x-1.5 shadow-lg shadow-brand-500/20 disabled:opacity-40"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  );
};

export default AIAssistant;
