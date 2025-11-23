import React, { useEffect, useState, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './NegotiationVisualization.css';

export default function NegotiationVisualization({ preferences }) {
  const [graphData, setGraphData] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [agents, setAgents] = useState(new Set());
  const [currentRound, setCurrentRound] = useState(0);
  const [status, setStatus] = useState('connecting');
  const [finalProposal, setFinalProposal] = useState(null);
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
    // Simple Minecraft-style block representation
    const color = getAgentColor(agentName);
    return (
      <div className="agent-avatar" style={{ backgroundColor: color }}>
        <div className="avatar-face" style={{ backgroundColor: color }}>
          <div className="avatar-eyes">
            <div className="eye"></div>
            <div className="eye"></div>
          </div>
          <div className="avatar-mouth"></div>
        </div>
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
          // Total/average score
          const avgScore = update.average_score;
          const roundNum = update.round;
          
          setGraphData(prev => {
            const newData = [...prev];
            const roundIndex = roundNum - 1;
            
            // Ensure we have data for this round
            while (newData.length < roundNum) {
              newData.push({ round: newData.length + 1 });
            }
            
            // Update with average score
            newData[roundIndex] = {
              ...newData[roundIndex],
              round: roundNum,
              average: avgScore,
            };
            
            return newData;
          });

          // Add conversation about round completion
          const scoresText = Object.entries(update.scores || {})
            .map(([name, score]) => `${name}: ${score}/5`)
            .join(', ');
          addConversation('system', `Round ${roundNum} complete. Average: ${avgScore.toFixed(1)}/5 (${scoresText})`);
          break;

        case 'proposal':
          // New proposal created
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

  // Prepare chart data with all agents
  const chartData = graphData.map(data => {
    const chartPoint = { round: data.round };
    
    // Add average (thick line)
    if (data.average !== undefined) {
      chartPoint.average = data.average;
    }
    
    // Add individual agent scores (thin lines)
    Array.from(agents).forEach(agent => {
      if (data[agent] !== undefined) {
        chartPoint[agent] = data[agent];
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
        <h1>Coordination Visualization</h1>
        <div className="status-indicator">
          <span className={`status-dot status-${status}`}></span>
          <span className="status-text">
            {status === 'connecting' && 'Connecting...'}
            {status === 'connected' && 'Connected'}
            {status === 'negotiating' && `Round ${currentRound}`}
            {status === 'success' && 'Success!'}
            {status === 'pareto_optimal' && 'Pareto Optimal'}
            {status === 'complete' && 'Complete'}
            {status === 'error' && 'Error'}
          </span>
        </div>
      </div>

      <div className="graph-container">
        <h2>Happiness Rating Over Rounds</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="round" 
              stroke="#888"
              tick={{ fill: '#fff' }}
              label={{ value: 'Round', position: 'insideBottom', offset: -5, fill: '#fff' }}
            />
            <YAxis 
              domain={[0, 5]}
              stroke="#888"
              tick={{ fill: '#fff' }}
              label={{ value: 'Happiness (1-5)', angle: -90, position: 'insideLeft', fill: '#fff' }}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', color: '#fff' }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend 
              wrapperStyle={{ color: '#fff' }}
              iconType="line"
            />
            {/* Average line - thick and high opacity */}
            <Line
              type="monotone"
              dataKey="average"
              stroke="#fff"
              strokeWidth={3}
              strokeOpacity={0.9}
              dot={{ r: 5, fill: '#fff' }}
              name="Average Happiness"
              connectNulls
            />
            {/* Individual agent lines - thin and low opacity */}
            {agentLines}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="conversations-container">
        <h2>Agent Conversations</h2>
        <div className="conversations-list">
          {conversations.map(conv => (
            <div key={conv.id} className={`conversation-item conversation-${conv.type}`}>
              <div className="conversation-avatar">
                {conv.agent !== 'system' ? getAgentIcon(conv.agent) : (
                  <div className="agent-avatar system-avatar">⚙️</div>
                )}
              </div>
              <div className="conversation-content">
                <div className="conversation-header">
                  <span className="conversation-agent">{conv.agent}</span>
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
          ))}
          <div ref={conversationsEndRef} />
        </div>
      </div>

      {finalProposal && (
        <div className="final-proposal">
          <h3>Final Proposal</h3>
          <div className="proposal-details">
            <p><strong>Total Cost:</strong> ${finalProposal.total_cost?.toLocaleString() || 0}</p>
            <p><strong>Modifications:</strong> {finalProposal.modifications?.length || 0}</p>
          </div>
        </div>
      )}
    </div>
  );
}

