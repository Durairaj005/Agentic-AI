import { useEffect, useRef, useState, useCallback } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { submitQueryAsync, pollJobStatus } from '../api/client';
import MessageBubble from './MessageBubble';
import './ChatPanel.css';

const POLL_INTERVAL_MS = 1500;
const MAX_POLLS = 120; // 3 minutes max

export default function ChatPanel({ filename, onQueryComplete }) {
  const [messages, setMessages]     = useState([]);
  const [input, setInput]           = useState('');
  const [loading, setLoading]       = useState(false);
  const bottomRef                   = useRef(null);
  const inputRef                    = useRef(null);
  const pollRef                     = useRef(null);

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  const addMessage = useCallback((msg) => {
    setMessages((prev) => [...prev, { id: Date.now() + Math.random(), ...msg }]);
  }, []);

  const updateLastAI = useCallback((updater) => {
    setMessages((prev) => {
      const next = [...prev];
      for (let i = next.length - 1; i >= 0; i--) {
        if (next[i].role !== 'user') {
          next[i] = { ...next[i], ...updater(next[i]) };
          break;
        }
      }
      return next;
    });
  }, []);

  const handleSend = useCallback(async () => {
    const query = input.trim();
    if (!query || loading) return;

    setInput('');
    setLoading(true);

    // Add user message
    addMessage({ role: 'user', content: query });

    // Add AI loading placeholder
    addMessage({ role: 'ai', content: null, isLoading: true });

    try {
      // Submit async job
      const { job_id } = await submitQueryAsync(filename, query);

      // Poll until done
      let polls = 0;
      clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        polls++;
        if (polls > MAX_POLLS) {
          clearInterval(pollRef.current);
          updateLastAI(() => ({
            isLoading: false,
            role: 'error',
            content: 'Request timed out. Please try again.',
            errors: [],
          }));
          setLoading(false);
          return;
        }

        try {
          const job = await pollJobStatus(job_id);

          if (job.status === 'COMPLETED') {
            clearInterval(pollRef.current);
            const res = job.result || {};
            updateLastAI(() => ({
              isLoading: false,
              role: res.success === false ? 'error' : 'ai',
              content: res.explanation || 'Analysis complete.',
              result: res.result,
              errors: res.errors || [],
            }));
            setLoading(false);
            onQueryComplete?.(res, query);

          } else if (job.status === 'FAILED') {
            clearInterval(pollRef.current);
            updateLastAI(() => ({
              isLoading: false,
              role: 'error',
              content: job.error || 'Analysis failed.',
              errors: [],
            }));
            setLoading(false);
          }
          // RUNNING — keep polling
        } catch {
          // Transient network error — keep polling
        }
      }, POLL_INTERVAL_MS);

    } catch (e) {
      const detail = e?.response?.data?.detail || e.message || 'Request failed.';
      updateLastAI(() => ({
        isLoading: false,
        role: 'error',
        content: detail,
        errors: [],
      }));
      setLoading(false);
    }
  }, [input, loading, filename, addMessage, updateLastAI, onQueryComplete]);

  // Cleanup poll on unmount
  useEffect(() => () => clearInterval(pollRef.current), []);

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const SUGGESTIONS = [
    'Total sales',
    'Top 5 regions by profit',
    'Monthly revenue trend',
    'Correlate sales and profit',
    'Outliers in discount',
  ];

  return (
    <div className="chat-panel">
      {/* Messages area */}
      <div className="chat-messages" id="chat-messages-container">
        {messages.length === 0 ? (
          <div className="chat-empty animate-fade-in">
            <div className="chat-empty__icon animate-float">
              <Sparkles size={32} />
            </div>
            <h3 className="chat-empty__title">Ask anything about your data</h3>
            <p className="chat-empty__sub">Type a question below or try one of these:</p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className="chat-suggestion"
                  onClick={() => { setInput(s); inputRef.current?.focus(); }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-messages__list">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="chat-input-bar glass-card">
        <textarea
          ref={inputRef}
          id="chat-query-input"
          className="chat-input"
          placeholder="Ask a question about your dataset…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          disabled={loading}
        />
        <button
          id="chat-send-btn"
          className={`btn btn-primary btn-icon chat-send-btn ${loading ? 'chat-send-btn--loading' : ''}`}
          onClick={handleSend}
          disabled={loading || !input.trim()}
          aria-label="Send query"
        >
          {loading
            ? <div className="spinner spinner-sm" />
            : <Send size={15} />
          }
        </button>
      </div>

      <p className="chat-hint">
        Press <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
