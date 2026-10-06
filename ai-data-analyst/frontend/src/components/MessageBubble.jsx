import { CheckCircle, AlertCircle, Bot, User, Code2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './MessageBubble.css';

export default function MessageBubble({ message }) {
  const { role, content, result, errors, isLoading } = message;
  const isUser  = role === 'user';
  const isError = role === 'error' || (errors && errors.length > 0 && !result);

  // Detect if result is a chart file path — show a badge instead of raw path
  const isChartResult = result && (result.includes('.png') || result.includes('.jpg')) &&
                        (result.includes('exports') || result.includes('charts'));

  // Detect raw <function=...> text leaking from LLM — suppress it
  const cleanContent = content?.replace(/<function=[\s\S]*?<\/function>/g, '').trim() || content;

  if (isUser) {
    return (
      <div className="msg-row msg-row--user animate-fade-in-up">
        <div className="msg-bubble msg-bubble--user">
          <p className="msg-bubble__text">{content}</p>
        </div>
        <div className="msg-avatar msg-avatar--user">
          <User size={14} />
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="msg-row msg-row--ai animate-fade-in">
        <div className="msg-avatar msg-avatar--ai">
          <Bot size={14} />
        </div>
        <div className="msg-bubble msg-bubble--loading">
          <div className="msg-typing">
            <span className="msg-typing__dot" />
            <span className="msg-typing__dot" />
            <span className="msg-typing__dot" />
          </div>
          <span className="msg-bubble__hint">Analyzing data…</span>
        </div>
      </div>
    );
  }

  // Format raw result for optional debug inspection
  const formattedRawResult = typeof result === 'object' 
    ? JSON.stringify(result, null, 2) 
    : String(result || '');

  return (
    <div className={`msg-row msg-row--ai animate-fade-in-up`}>
      <div className={`msg-avatar ${isError ? 'msg-avatar--error' : 'msg-avatar--ai'}`}>
        {isError ? <AlertCircle size={14} /> : <Bot size={14} />}
      </div>

      <div className={`msg-bubble ${isError ? 'msg-bubble--error' : 'msg-bubble--ai'}`}>
        {/* Chart badge if chart generated */}
        {isChartResult && !isError && (
          <div className="msg-result msg-result--chart">
            <CheckCircle size={13} className="msg-result__icon" />
            <span className="msg-result__value">📊 Chart generated — see Chart Output panel →</span>
          </div>
        )}

        {/* Clean Natural Markdown Explanation */}
        {cleanContent && (
          <div className="msg-markdown">
            <ReactMarkdown>{cleanContent}</ReactMarkdown>
          </div>
        )}

        {/* Optional Collapsed Raw Query Result (only if non-chart and technical data exists) */}
        {result && !isChartResult && !isError && formattedRawResult.trim() !== '' && (
          <details className="msg-raw-details">
            <summary className="msg-raw-summary">
              <Code2 size={12} />
              <span>Raw dataset output</span>
            </summary>
            <pre className="msg-raw-pre">{formattedRawResult}</pre>
          </details>
        )}

        {/* Errors */}
        {errors && errors.length > 0 && (
          <div className="msg-errors">
            {errors.map((e, i) => (
              <p key={i} className="msg-errors__item">⚠ {e}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
