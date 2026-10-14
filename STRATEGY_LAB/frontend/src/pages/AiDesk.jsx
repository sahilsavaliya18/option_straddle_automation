import { useState, useEffect } from 'react';
import { fetchTeam, sendAgentChat, runDailyAgentWorkflow, fetchAgentInsights, reviewUiComponent } from '../utils/api';
import { formatRupees } from '../utils/formatters';

export default function AiDesk() {
  const [team, setTeam] = useState([]);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [runningWorkflow, setRunningWorkflow] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState('Team Lead');

  // Chat State
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'Team Lead',
      role: 'Trading Desk Managing Director',
      text: 'Welcome to your Autonomous Options Trading Desk. My team (Data Guard, Quant Strategist, Risk Officer, Portfolio Analyst, and UI Webmaster) is online and ready. What shall we analyze today?',
      time: '09:15',
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [sendingChat, setSendingChat] = useState(false);

  // UI Reviewer Widget State
  const [reviewComp, setReviewComp] = useState('RunBacktest');
  const [uiReviewResult, setUiReviewResult] = useState(null);
  const [reviewingUi, setReviewingUi] = useState(false);

  useEffect(() => {
    Promise.all([
      fetchTeam().catch(() => ({ team: [] })),
      fetchAgentInsights().catch(() => ({ insights: [], latest: null })),
    ]).then(([teamRes, insightsRes]) => {
      setTeam(teamRes.team || []);
      setInsights(insightsRes.latest || null);
      setLoading(false);
    });
  }, []);

  const handleRunWorkflow = async () => {
    setRunningWorkflow(true);
    try {
      const res = await runDailyAgentWorkflow("27_08_2026", 500000);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'Team Lead',
          role: 'Daily Workflow Orchestrator',
          text: `Daily Autonomous Workflow Completed across 5 virtual employees!\n\nTop Performer: **${res.top_strategy || 'Short Straddle'}** (+₹${(res.top_pnl || 0).toLocaleString('en-IN')})\nTasks Executed: ${res.task_results?.length || 5}\nDuration: ${res.elapsed_seconds || 0}s.`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      // Refresh insights
      const insRes = await fetchAgentInsights();
      setInsights(insRes.latest);
    } catch (err) {
      alert(`Workflow error: ${err.message}`);
    } finally {
      setRunningWorkflow(false);
    }
  };

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!inputMessage.trim() || sendingChat) return;

    const userText = inputMessage;
    setInputMessage('');
    setChatMessages((prev) => [
      ...prev,
      {
        sender: 'You',
        role: 'Trader',
        text: userText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setSendingChat(true);

    try {
      const res = await sendAgentChat(userText, selectedAgent);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: res.agent_name,
          role: res.agent_role,
          text: res.response,
          time: res.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: selectedAgent,
          role: 'Error Handler',
          text: `Error communicating with ${selectedAgent}: ${err.message}`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setSendingChat(false);
    }
  };

  const handleUiReview = async () => {
    setReviewingUi(true);
    setUiReviewResult(null);
    try {
      const res = await reviewUiComponent(reviewComp);
      setUiReviewResult(res);
    } catch (err) {
      alert(`UI Review failed: ${err.message}`);
    } finally {
      setReviewingUi(false);
    }
  };

  if (loading) {
    return <div className="loading-state"><div className="spinner" />Loading AI Desk...</div>;
  }

  return (
    <div className="animate-in" style={{ paddingBottom: 'var(--sp-12)' }}>
      {/* Top Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: 'var(--color-accent, #6366f1)' }}>✦</span> AI Options Trading Desk
          </h1>
          <p className="page-subtitle">
            Autonomous multi-agent research & engineering team running 100% free of cost
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--sp-3)' }}>
          <button
            className="btn btn-primary"
            disabled={runningWorkflow}
            onClick={handleRunWorkflow}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              transition: 'transform 150ms ease-out',
            }}
          >
            {runningWorkflow ? (
              <><div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Running 5 Agents...</>
            ) : (
              <>▶ Run Daily AI Workflow</>
            )}
          </button>
        </div>
      </div>

      {/* Latest Executive Briefing Card */}
      {insights && (
        <div className="card mb-6" style={{
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(16, 185, 129, 0.05) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
        }}>
          <div className="card-header" style={{ borderBottom: '1px solid rgba(99, 102, 241, 0.15)' }}>
            <span className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="status-dot green" />
              Latest Executive Intelligence Briefing ({insights.analysis_date})
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              Top Strategy: <strong>{insights.top_strategy}</strong>
            </span>
          </div>
          <div className="card-body">
            <div style={{ whiteSpace: 'pre-line', lineHeight: 1.6, color: 'var(--text-primary)', fontSize: 'var(--text-sm)' }}>
              {insights.executive_summary}
            </div>
            {insights.regime_notes && (
              <div style={{ marginTop: 'var(--sp-3)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'flex', gap: '16px' }}>
                <span><strong>Market Regime:</strong> {insights.regime_notes}</span>
                <span><strong>Risk Assessment:</strong> {insights.risk_assessment}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5 Virtual Employee Cards */}
      <div style={{ marginBottom: 'var(--sp-6)' }}>
        <h3 style={{ fontSize: 'var(--text-md)', fontWeight: 600, marginBottom: 'var(--sp-3)', color: 'var(--text-secondary)' }}>
          Virtual Trading & Engineering Team
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 'var(--sp-4)',
        }}>
          {team.map((agent) => {
            const isSelected = selectedAgent === agent.name;
            return (
              <div
                key={agent.name}
                className="card"
                onClick={() => setSelectedAgent(agent.name)}
                style={{
                  cursor: 'pointer',
                  border: isSelected ? '1px solid var(--color-accent, #6366f1)' : '1px solid var(--border-color)',
                  background: isSelected ? 'rgba(99, 102, 241, 0.1)' : 'var(--card-bg)',
                  transition: 'transform 150ms ease-out, border-color 150ms ease-out',
                  padding: 'var(--sp-4)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--text-primary)' }}>
                    {agent.name}
                  </div>
                  <span className="status-dot green" />
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-accent, #818cf8)', marginBottom: '8px', fontWeight: 500 }}>
                  {agent.role}
                </div>
                <p style={{
                  fontSize: 'var(--text-xs)', color: 'var(--text-secondary)',
                  lineHeight: 1.4, margin: 0,
                  display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden'
                }}>
                  {agent.goal}
                </p>
                <div style={{ marginTop: '12px', fontSize: '10px', color: 'var(--text-tertiary)' }}>
                  Tools: {agent.tools.slice(0, 2).join(', ')}{agent.tools.length > 2 ? ` +${agent.tools.length - 2}` : ''}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Interactive Chat Console & Emil Kowalski UI Reviewer */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 'var(--sp-6)', alignItems: 'start' }}>
        
        {/* Chat Console */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '520px' }}>
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="card-title">
              Chatting with: <strong style={{ color: 'var(--color-accent, #818cf8)' }}>{selectedAgent}</strong>
            </span>
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              style={{ width: 'auto', padding: '4px 8px', fontSize: 'var(--text-xs)' }}
            >
              {team.map((a) => (
                <option key={a.name} value={a.name}>{a.name} ({a.role.split(' ')[0]})</option>
              ))}
            </select>
          </div>

          {/* Message List */}
          <div style={{
            flex: 1, overflowY: 'auto', padding: 'var(--sp-4)',
            display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)'
          }}>
            {chatMessages.map((msg, i) => {
              const isUser = msg.sender === 'You';
              return (
                <div
                  key={i}
                  style={{
                    alignSelf: isUser ? 'flex-end' : 'flex-start',
                    maxWidth: '85%',
                    background: isUser ? 'var(--color-accent, #6366f1)' : 'var(--bg-raised, #1c1f2a)',
                    color: isUser ? '#fff' : 'var(--text-primary)',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    fontSize: 'var(--text-sm)',
                    lineHeight: 1.5,
                    border: isUser ? 'none' : '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{
                    fontSize: '11px',
                    color: isUser ? 'rgba(255,255,255,0.8)' : 'var(--color-accent, #818cf8)',
                    marginBottom: '4px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: '12px'
                  }}>
                    <span><strong>{msg.sender}</strong> ({msg.role})</span>
                    <span>{msg.time}</span>
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                </div>
              );
            })}
            {sendingChat && (
              <div style={{
                alignSelf: 'flex-start', background: 'var(--bg-raised)',
                padding: '8px 12px', borderRadius: '8px', fontSize: 'var(--text-xs)',
                display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)'
              }}>
                <div className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
                {selectedAgent} is evaluating parameters & tools...
              </div>
            )}
          </div>

          {/* Quick Prompts */}
          <div style={{
            padding: '4px var(--sp-4)', background: 'var(--bg-dark, #0b0d14)',
            display: 'flex', gap: '6px', overflowX: 'auto', borderTop: '1px solid var(--border-subtle)'
          }}>
            {[
              "Why did Short Straddle perform well today?",
              "Audit margin requirement for Short Strangle with 5L capital",
              "Which strategy had the lowest transaction costs?",
            ].map((p, idx) => (
              <button
                key={idx}
                onClick={() => setInputMessage(p)}
                style={{
                  background: 'transparent', border: '1px solid var(--border-subtle)',
                  borderRadius: '12px', padding: '2px 8px', fontSize: '11px',
                  color: 'var(--text-secondary)', cursor: 'pointer', whiteSpace: 'nowrap'
                }}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <form onSubmit={handleSendMessage} style={{
            padding: 'var(--sp-3)', borderTop: '1px solid var(--border-color)',
            display: 'flex', gap: '8px', background: 'var(--card-bg)'
          }}>
            <input
              type="text"
              placeholder={`Ask ${selectedAgent}...`}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              style={{ flex: 1 }}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!inputMessage.trim() || sendingChat}
              style={{ transition: 'transform 100ms ease-out' }}
            >
              Send
            </button>
          </form>
        </div>

        {/* Emil Kowalski UI Craft Reviewer Widget */}
        <div className="card" style={{ height: '520px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
            <span className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              🎨 Emil Kowalski UI Craft Reviewer
            </span>
          </div>
          <div className="card-body" style={{ flex: 1, overflowY: 'auto' }}>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginBottom: '12px', lineHeight: 1.5 }}>
              Powered by <strong>UI Webmaster</strong> using <code>SKILLS/emil-kowalski/emil-design-eng</code>.
              Inspects components for layout shifts, ease-out curves, and <code>:active</code> press feedback.
            </p>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              <select
                value={reviewComp}
                onChange={(e) => setReviewComp(e.target.value)}
                style={{ flex: 1 }}
              >
                <option value="RunBacktest">RunBacktest.jsx</option>
                <option value="Sidebar">Sidebar.jsx</option>
                <option value="Dashboard">Dashboard.jsx</option>
                <option value="Results">Results.jsx</option>
                <option value="App">App.jsx</option>
              </select>
              <button
                className="btn btn-secondary btn-sm"
                onClick={handleUiReview}
                disabled={reviewingUi}
              >
                {reviewingUi ? 'Auditing...' : 'Review UI'}
              </button>
            </div>

            {uiReviewResult ? (
              <div className="animate-in" style={{ fontSize: 'var(--text-xs)' }}>
                <div style={{
                  padding: '8px', background: 'rgba(16, 185, 129, 0.1)',
                  borderRadius: '6px', color: 'var(--color-profit)', marginBottom: '12px'
                }}>
                  ✓ {uiReviewResult.craft_evaluation}
                </div>

                <div style={{ fontWeight: 600, marginBottom: '6px', color: 'var(--text-secondary)' }}>
                  Found {uiReviewResult.issues_found} Craft Suggestion(s):
                </div>

                <div style={{
                  background: 'var(--bg-raised)', padding: '12px',
                  borderRadius: '6px', whiteSpace: 'pre-wrap', fontFamily: 'monospace',
                  fontSize: '11px', color: 'var(--text-primary)', border: '1px solid var(--border-subtle)',
                  overflowX: 'auto'
                }}>
                  {uiReviewResult.review_table}
                </div>
              </div>
            ) : (
              <div className="empty-state" style={{ padding: 'var(--sp-8) 0' }}>
                <p>Select a component and click "Review UI" to generate an Emil Kowalski craft table.</p>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
