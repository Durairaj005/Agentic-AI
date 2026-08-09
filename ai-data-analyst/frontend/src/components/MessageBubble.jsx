import { CheckCircle, AlertCircle, Bot, User } from 'lucide-react';
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
          <span className="msg-bubble__hint">Thinking…</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`msg-row msg-row--ai animate-fade-in-up`}>
      <div className={`msg-avatar ${isError ? 'msg-avatar--error' : 'msg-avatar--ai'}`}>
        {isError ? <AlertCircle size={14} /> : <Bot size={14} />}
      </div>

      <div className={`msg-bubble ${isError ? 'msg-bubble--error' : 'msg-bubble--ai'}`}>
        {/* Chart badge OR raw result value */}
        {result && !isError && (
          <div className="msg-result">
            <CheckCircle size={13} className="msg-result__icon" />
            {isChartResult
              ? <span className="msg-result__value">📊 Chart generated — see Chart Output panel →</span>
              : <span className="msg-result__value">{result}</span>
            }
          </div>
        )}

        {/* Main explanation */}
        {cleanContent && (
          <p className="msg-bubble__text">
            {cleanContent}
          </p>
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
