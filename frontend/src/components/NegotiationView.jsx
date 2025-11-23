import React, { useEffect, useState } from 'react';
import styles from './NegotiationView.module.css';

export default function NegotiationView({ preferences }) {
  const [updates, setUpdates] = useState([]);
  const [currentRound, setCurrentRound] = useState(0);
  const [scores, setScores] = useState({});
  const [status, setStatus] = useState('connecting');
  const [error, setError] = useState(null);
  const [finalProposal, setFinalProposal] = useState(null);

  useEffect(() => {
    if (!preferences) return;

    const ws = new WebSocket('ws://localhost:8000/ws/negotiate');

    ws.onopen = () => {
      console.log('Connected to negotiation server');
      ws.send(JSON.stringify(preferences));
    };

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      console.log('Update:', update);

      setUpdates((prev) => [...prev, update]);

      // Handle different update types
      switch (update.type) {
        case 'round_start':
          setCurrentRound(update.round);
          setStatus('evaluating');
          break;

        case 'score':
          setScores((prev) => ({
            ...prev,
            [update.agent]: update.score,
          }));
          break;

        case 'round_complete':
          setStatus('synthesizing');
          break;

        case 'complete':
          setStatus(update.status === 'success' ? 'success' : 'pareto_optimal');
          break;

        case 'failed':
          setStatus('failed');
          setError(update.message);
          break;

        case 'final_proposal':
          setFinalProposal(update);
          break;

        default:
          break;
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('Connection error');
      setStatus('error');
    };

    ws.onclose = () => {
      console.log('Disconnected from negotiation server');
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [preferences]);

  const getStatusEmoji = () => {
    switch (status) {
      case 'connecting':
        return '🔄';
      case 'evaluating':
        return '📊';
      case 'synthesizing':
        return '🔧';
      case 'success':
        return '✅';
      case 'pareto_optimal':
        return '⚡';
      case 'failed':
        return '❌';
      default:
        return '⏳';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connecting':
        return 'Connecting...';
      case 'evaluating':
        return `Round ${currentRound}: Evaluating Proposals`;
      case 'synthesizing':
        return `Round ${currentRound}: Synthesizing New Proposal`;
      case 'success':
        return 'Success! All parties satisfied';
      case 'pareto_optimal':
        return 'Complete! Pareto optimal agreement reached';
      case 'failed':
        return 'Negotiation failed';
      default:
        return 'Status unknown';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Live Negotiation</h1>
        <div className={styles.status}>
          <span className={styles.emoji}>{getStatusEmoji()}</span>
          <p>{getStatusText()}</p>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.scores}>
        <h3>Agent Satisfaction Scores</h3>
        <div className={styles.scoresList}>
          {Object.entries(scores).map(([agent, score]) => (
            <div key={agent} className={styles.scoreItem}>
              <span className={styles.agentName}>{agent}</span>
              <div className={styles.scoreBar}>
                <div
                  className={styles.scoreFill}
                  style={{
                    width: `${(score / 5) * 100}%`,
                    backgroundColor:
                      score >= 4
                        ? '#10b981'
                        : score === 3
                          ? '#f59e0b'
                          : '#ef4444',
                  }}
                />
              </div>
              <span className={styles.scoreValue}>{score}/5</span>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.updates}>
        <h3>Negotiation Log</h3>
        <div className={styles.updatesList}>
          {updates
            .slice()
            .reverse()
            .map((update, idx) => (
              <div key={idx} className={styles.updateItem}>
                <span className={styles.type}>{update.type}</span>
                {update.round && <span className={styles.round}>Round {update.round}</span>}
                {update.message && <p className={styles.message}>{update.message}</p>}
              </div>
            ))}
        </div>
      </div>

      {finalProposal && (
        <div className={styles.proposal}>
          <h3>Final Proposal</h3>
          <div className={styles.proposalContent}>
            <p>
              <strong>Total Cost:</strong> ${finalProposal.total_cost.toLocaleString()}
            </p>
            <p>
              <strong>Modifications:</strong> {finalProposal.modifications_count}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
