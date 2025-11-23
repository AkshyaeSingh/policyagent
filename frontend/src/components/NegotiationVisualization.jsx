import React, { useEffect, useState, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import './NegotiationVisualization.css';

export default function NegotiationVisualization({ preferences }) {
  const [graphData, setGraphData] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [agents, setAgents] = useState(new Set());
  const [currentRound, setCurrentRound] = useState(0);
  const [status, setStatus] = useState('connecting');
  const [finalProposal, setFinalProposal] = useState(null);
  const [roundSnapshots, setRoundSnapshots] = useState([]); // Store snapshot data for each round
  const [currentSnapshot, setCurrentSnapshot] = useState(null); // Current round's snapshot
  const wsRef = useRef(null);
  const conversationsEndRef = useRef(null);

  // Minecraft-style avatar colors for different agents
  const getAgentColor = (agentName) => {
    const colors = {
      'Policy_Maker': '#4A90E2', // Blue
      'Healthcare_Worker': '#E24A4A', // Red
      'Healthcare_Worker_Test': '#E24A4A', // Red
      'Business_Owner': '#4AE24A', // Green
      'default': '#E2E24A', // Yellow
    };
    return colors[agentName] || colors['default'];
  };

  const getAgentIcon = (agentName) => {
    // Enhanced Minecraft-style block representation
    const color = getAgentColor(agentName);
    const darkerColor = color + 'CC'; // Add opacity for depth
    return (
      <div className="agent-avatar" style={{ backgroundColor: color, boxShadow: `0 2px 8px ${color}40` }}>
        <div className="avatar-face" style={{ backgroundColor: color }}>
          <div className="avatar-eyes">
            <div className="eye"></div>
            <div className="eye"></div>
          </div>
          <div className="avatar-mouth"></div>
        </div>
        <div className="avatar-highlight"></div>
      </div>
    );
  };

  useEffect(() => {
    if (!preferences) return;

    const ws = new WebSocket('ws://localhost:8002/ws/negotiate');
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to negotiation server');
      setStatus('connected');
      ws.send(JSON.stringify(preferences));
    };

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      console.log('Update:', update);

      // Handle different update types
      switch (update.type) {
        case 'status':
          setStatus('negotiating');
          addConversation('system', update.message || 'Negotiation started');
          break;

        case 'round_start':
          setCurrentRound(update.round);
          addConversation('system', `Round ${update.round} started`);
          break;

        case 'score':
          // Individual agent score
          const agentName = update.agent;
          setAgents(prev => new Set([...prev, agentName]));
          
          // Update graph data with individual score
          setGraphData(prev => {
            const newData = [...prev];
            const roundNum = update.round || currentRound;
            const roundIndex = roundNum - 1;
            
            // Ensure we have data for this round
            while (newData.length < roundNum) {
              newData.push({ round: newData.length + 1 });
            }
            
            // Update the round data (preserve existing data)
            newData[roundIndex] = {
              ...newData[roundIndex],
              round: roundNum,
              [agentName]: update.score,
            };
            
            return newData;
          });

          // Add conversation message
          const scoreEmoji = update.score >= 4 ? '✅' : update.score === 3 ? '⚠️' : '❌';
          addConversation(agentName, `${scoreEmoji} Score: ${update.score}/5`, update.explanation);
          break;

        case 'round_complete':
          // Total/average score - preserve existing individual scores
          const avgScore = update.average_score;
          const roundNum = update.round;
          
          setGraphData(prev => {
            const newData = [...prev];
            const roundIndex = roundNum - 1;
            
            // Ensure we have data for this round
            while (newData.length < roundNum) {
              newData.push({ round: newData.length + 1 });
            }
            
            // Update with average score while preserving existing individual scores
            newData[roundIndex] = {
              ...newData[roundIndex],
              round: roundNum,
              average: avgScore,
            };
            
            return newData;
          });

          // Create snapshot for this round
          const snapshot = {
            round: roundNum,
            averageScore: avgScore,
            scores: update.scores || {},
            timestamp: new Date(),
          };
          
          setRoundSnapshots(prev => {
            const newSnapshots = [...prev];
            // Update or add snapshot for this round
            const existingIndex = newSnapshots.findIndex(s => s.round === roundNum);
            if (existingIndex >= 0) {
              newSnapshots[existingIndex] = snapshot;
            } else {
              newSnapshots.push(snapshot);
            }
            return newSnapshots.sort((a, b) => a.round - b.round);
          });
          
          setCurrentSnapshot(snapshot);

          // Add conversation about round completion
          const scoresText = Object.entries(update.scores || {})
            .map(([name, score]) => `${name}: ${score}/5`)
            .join(', ');
          addConversation('system', `Round ${roundNum} complete. Average: ${avgScore.toFixed(1)}/5 (${scoresText})`);
          break;

        case 'proposal':
          // New proposal created - update current snapshot with proposal data
          const proposalRound = update.round || currentRound;
          setCurrentSnapshot(prev => {
            if (prev && prev.round === proposalRound) {
              return {
                ...prev,
                modificationsCount: update.modifications_count || 0,
                totalCost: update.total_cost || 0,
                reasoning: update.reasoning,
                baseProject: update.base_project,
              };
            }
            return prev;
          });
          
          // Also update the snapshot in the history
          setRoundSnapshots(prev => prev.map(snapshot => 
            snapshot.round === proposalRound ? {
              ...snapshot,
              modificationsCount: update.modifications_count || 0,
              totalCost: update.total_cost || 0,
              reasoning: update.reasoning,
              baseProject: update.base_project,
            } : snapshot
          ));
          
          addConversation('system', `New proposal created with ${update.modifications_count || 0} modifications`, update.reasoning);
          break;

        case 'complete':
          setStatus(update.status === 'success' ? 'success' : 'pareto_optimal');
          addConversation('system', update.message || 'Negotiation complete!');
          break;

        case 'final_proposal':
          setFinalProposal(update);
          setStatus('complete');
          addConversation('system', `Final proposal: Total cost $${update.total_cost?.toLocaleString() || 0}`);
          break;

        case 'error':
          setStatus('error');
          addConversation('system', `Error: ${update.error}`, null, 'error');
          break;

        default:
          break;
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setStatus('error');
      addConversation('system', 'Connection error occurred', null, 'error');
    };

    ws.onclose = () => {
      console.log('Disconnected from negotiation server');
      setStatus('closed');
    };

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [preferences]);

  const addConversation = (agent, message, details = null, type = 'info') => {
    setConversations(prev => [...prev, {
      id: Date.now() + Math.random(),
      agent,
      message,
      details,
      type,
      timestamp: new Date(),
    }]);
    
    // Auto-scroll to bottom
    setTimeout(() => {
      conversationsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  // Prepare chart data with all agents - ensure proper ordering
  const chartData = graphData
    .filter(data => data.round !== undefined)
    .sort((a, b) => a.round - b.round)
    .map(data => {
      const chartPoint = { round: data.round };
      
      // Add average (thick line)
      if (data.average !== undefined) {
        chartPoint.average = Number(data.average.toFixed(2));
      }
      
      // Add individual agent scores (thin lines)
      Array.from(agents).forEach(agent => {
        if (data[agent] !== undefined) {
          chartPoint[agent] = Number(data[agent]);
        }
      });
      
      return chartPoint;
    });

  // Generate line components for the chart
  const agentLines = Array.from(agents).map(agent => (
    <Line
      key={agent}
      type="monotone"
      dataKey={agent}
      stroke={getAgentColor(agent)}
      strokeWidth={1.5}
      strokeOpacity={0.4}
      dot={{ r: 3, fill: getAgentColor(agent) }}
      connectNulls
    />
  ));

  return (
    <div className="negotiation-visualization">
      <div className="viz-header">
        <div className="header-title">
          <h1>Coordination Visualization</h1>
          <p className="header-subtitle">Real-time agent negotiation tracking</p>
        </div>
        <div className="status-indicator">
          <span className={`status-dot status-${status}`}></span>
          <div className="status-info">
            <span className="status-text">
              {status === 'connecting' && 'Connecting...'}
              {status === 'connected' && 'Connected'}
              {status === 'negotiating' && `Round ${currentRound}`}
              {status === 'success' && 'Success!'}
              {status === 'pareto_optimal' && 'Pareto Optimal'}
              {status === 'complete' && 'Complete'}
              {status === 'error' && 'Error'}
              {status === 'closed' && 'Disconnected'}
            </span>
            {status === 'connecting' && (
              <span className="status-hint">Establishing connection...</span>
            )}
          </div>
        </div>
      </div>

      <div className="visualizations-grid">
        {/* Left: Line Graph */}
        <div className="graph-container">
          <div className="graph-header">
            <h2>Happiness Rating Over Rounds</h2>
            {chartData.length > 0 && (
              <div className="graph-stats">
                <span className="stat-item">
                  <span className="stat-label">Current:</span>
                  <span className="stat-value">
                    {chartData[chartData.length - 1]?.average?.toFixed(1) || 'N/A'}/5
                  </span>
                </span>
              </div>
            )}
          </div>
          {chartData.length === 0 ? (
            <div className="graph-empty">
              <div className="empty-icon">📊</div>
              <p>Waiting for negotiation data...</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" opacity={0.5} />
                <XAxis 
                  dataKey="round" 
                  stroke="#666"
                  tick={{ fill: '#aaa', fontSize: 12 }}
                  label={{ value: 'Round', position: 'insideBottom', offset: -8, fill: '#fff', fontSize: 12 }}
                  tickLine={{ stroke: '#666' }}
                />
                <YAxis 
                  domain={[0, 5]}
                  stroke="#666"
                  tick={{ fill: '#aaa', fontSize: 12 }}
                  label={{ value: 'Happiness (1-5)', angle: -90, position: 'insideLeft', fill: '#fff', fontSize: 12 }}
                  tickLine={{ stroke: '#666' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1a1a1a', 
                    border: '1px solid #444', 
                    color: '#fff',
                    borderRadius: '8px',
                    padding: '10px'
                  }}
                  labelStyle={{ color: '#fff', marginBottom: '5px', fontWeight: '600' }}
                  itemStyle={{ color: '#fff', padding: '2px 0' }}
                  formatter={(value, name) => {
                    if (name === 'average') return [`${value.toFixed(2)}/5`, 'Average Happiness'];
                    return [`${value}/5`, name];
                  }}
                />
                <Legend 
                  wrapperStyle={{ color: '#fff', paddingTop: '10px' }}
                  iconType="line"
                  iconSize={12}
                  fontSize={11}
                />
                {/* Average line - thick and high opacity */}
                <Line
                  type="monotone"
                  dataKey="average"
                  stroke="#fff"
                  strokeWidth={3.5}
                  strokeOpacity={0.95}
                  dot={{ r: 6, fill: '#fff', strokeWidth: 2, stroke: '#000' }}
                  activeDot={{ r: 8, fill: '#fff', strokeWidth: 2, stroke: '#000' }}
                  name="Average Happiness"
                  connectNulls
                />
                {/* Individual agent lines - thin and low opacity */}
                {agentLines}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Right: Round Snapshot */}
        <div className="snapshot-container">
          <div className="snapshot-header">
            <h2>Round {currentRound || 0} Snapshot</h2>
            {currentSnapshot && (
              <span className="snapshot-badge">
                Avg: {currentSnapshot.averageScore?.toFixed(1) || 'N/A'}/5
              </span>
            )}
          </div>
          {!currentSnapshot || Object.keys(currentSnapshot.scores || {}).length === 0 ? (
            <div className="snapshot-empty">
              <div className="empty-icon">📈</div>
              <p>Waiting for round data...</p>
            </div>
          ) : (
            <div className="snapshot-content">
              {/* Agent Satisfaction Bar Chart */}
              <div className="snapshot-section">
                <h3>Agent Satisfaction</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart 
                    data={Object.entries(currentSnapshot.scores).map(([name, score]) => ({
                      name: name.replace(/_/g, ' '),
                      score: Number(score),
                      fullName: name,
                    }))}
                    layout="vertical"
                    margin={{ top: 5, right: 20, left: 80, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#222" opacity={0.3} />
                    <XAxis 
                      type="number"
                      domain={[0, 5]}
                      stroke="#666"
                      tick={{ fill: '#aaa', fontSize: 11 }}
                      tickLine={{ stroke: '#666' }}
                    />
                    <YAxis 
                      type="category"
                      dataKey="name"
                      stroke="#666"
                      tick={{ fill: '#aaa', fontSize: 11 }}
                      tickLine={{ stroke: '#666' }}
                      width={75}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1a1a1a', 
                        border: '1px solid #444', 
                        color: '#fff',
                        borderRadius: '8px',
                        padding: '8px'
                      }}
                      formatter={(value) => [`${value}/5`, 'Score']}
                    />
                    <Bar dataKey="score" radius={[0, 8, 8, 0]}>
                      {Object.entries(currentSnapshot.scores).map(([name], index) => (
                        <Cell key={index} fill={getAgentColor(name)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Proposal Details */}
              {currentSnapshot.modificationsCount !== undefined && (
                <div className="snapshot-section">
                  <h3>Proposal Details</h3>
                  <div className="proposal-stats-grid">
                    <div className="proposal-stat-card">
                      <span className="stat-icon">🔧</span>
                      <div>
                        <span className="stat-label">Modifications</span>
                        <span className="stat-value">{currentSnapshot.modificationsCount}</span>
                      </div>
                    </div>
                    {currentSnapshot.totalCost !== undefined && (
                      <div className="proposal-stat-card">
                        <span className="stat-icon">💰</span>
                        <div>
                          <span className="stat-label">Total Cost</span>
                          <span className="stat-value">${currentSnapshot.totalCost.toLocaleString()}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Round History */}
              {roundSnapshots.length > 0 && (
                <div className="snapshot-section">
                  <h3>Round History</h3>
                  <div className="round-history">
                    {roundSnapshots.map((snapshot) => (
                      <div 
                        key={snapshot.round} 
                        className={`history-item ${snapshot.round === currentRound ? 'active' : ''}`}
                        onClick={() => {
                          setCurrentSnapshot(snapshot);
                          setCurrentRound(snapshot.round);
                        }}
                        title={`Click to view Round ${snapshot.round} details`}
                      >
                        <span className="history-round">R{snapshot.round}</span>
                        <span className="history-score">{snapshot.averageScore?.toFixed(1) || 'N/A'}/5</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="conversations-container">
        <div className="conversations-header">
          <h2>Agent Conversations</h2>
          {conversations.length > 0 && (
            <span className="conversation-count">{conversations.length} messages</span>
          )}
        </div>
        <div className="conversations-list">
          {conversations.length === 0 ? (
            <div className="conversations-empty">
              <div className="empty-icon">💬</div>
              <p>Waiting for agent messages...</p>
            </div>
          ) : (
            conversations.map(conv => (
              <div key={conv.id} className={`conversation-item conversation-${conv.type}`}>
                <div className="conversation-avatar">
                  {conv.agent !== 'system' ? getAgentIcon(conv.agent) : (
                    <div className="agent-avatar system-avatar">⚙️</div>
                  )}
                </div>
                <div className="conversation-content">
                  <div className="conversation-header">
                    <span className="conversation-agent" style={{ color: conv.agent !== 'system' ? getAgentColor(conv.agent) : '#888' }}>
                      {conv.agent}
                    </span>
                    <span className="conversation-time">
                      {conv.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="conversation-message">{conv.message}</div>
                  {conv.details && (
                    <div className="conversation-details">{conv.details}</div>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={conversationsEndRef} />
        </div>
      </div>

      {finalProposal && (
        <div className="final-proposal">
          <div className="proposal-header">
            <h3>🎯 Final Proposal</h3>
            <span className="proposal-badge">Complete</span>
          </div>
          <div className="proposal-details">
            <div className="proposal-stat">
              <span className="stat-icon">💰</span>
              <div>
                <span className="stat-label">Total Cost</span>
                <span className="stat-value">${finalProposal.total_cost?.toLocaleString() || 0}</span>
              </div>
            </div>
            <div className="proposal-stat">
              <span className="stat-icon">🔧</span>
              <div>
                <span className="stat-label">Modifications</span>
                <span className="stat-value">{finalProposal.modifications?.length || 0}</span>
              </div>
            </div>
            {finalProposal.base_project && (
              <div className="proposal-base">
                <span className="proposal-label">Base Project:</span>
                <pre className="proposal-json">
                  {JSON.stringify(finalProposal.base_project, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

