import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import Layout from '../components/common/Layout';
import { getResults } from '../api/api';

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: var(--fs-lg);
  color: var(--pl-dark-gray);
`;

const ErrorContainer = styled.div`
  max-width: 1200px;
  margin: 20px auto;
  padding: 16px;
  background-color: #ffeeee;
  border-radius: 4px;
  color: #d32f2f;
`;

const RefreshButton = styled.button`
  display: flex;
  align-items: center;
  gap: 2px;
  background-color: var(--pl-purple);
  color: var(--pl-white);
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease;
  margin: 20px auto;
  
  &:hover {
    background-color: var(--pl-pink);
  }
  
  &:disabled {
    background-color: var(--pl-gray);
    cursor: not-allowed;
  }
  
  svg {
    width: 20px;
    height: 20px;
    animation: ${props => props.isRefreshing ? 'spin 1s linear infinite' : 'none'};
  }
  
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
`;

const MatchList = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const MatchCard = styled.div`
  background: var(--pl-white);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  @media (min-width: 768px) {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
`;

const MatchInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: center;

  @media (min-width: 768px) {
    flex: 1;
    text-align: left;
  }
`;

const MatchTeams = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--pl-dark-gray);

  @media (min-width: 768px) {
    flex: 2;
    justify-content: center;
  }
`;

const TeamName = styled.span`
  flex: 1;
  text-align: right;

  @media (min-width: 768px) {
    flex: none;
    width: 150px;
  }
`;

const Score = styled.span`
  font-size: var(--fs-lg);
  font-weight: 700;
  color: var(--pl-purple);
  min-width: 60px;
  text-align: center;
`;

const PredictionBadge = styled.div`
  background: var(--pl-light-gray);
  color: var(--pl-dark-gray);
  padding: 8px 12px;
  border-radius: 4px;
  font-size: var(--fs-sm);
  font-weight: 500;
  text-align: center;
  display: flex;
  align-items: center;
  gap: 4px;

  b {
    color: var(--pl-purple);
  }

  .details {
    color: #888;
    display: none;
  }

  &:hover .details {
    display: inline;
  }

  @media (min-width: 768px) {
    flex: 1;
    text-align: right;
  }
`;

const DateVenue = styled.div`
  font-size: var(--fs-sm);
  color: var(--pl-black);
  text-align: center;

  @media (min-width: 768px) {
    text-align: left;
  }
`;

const LoadMoreButton = styled.button`
  margin: 24px auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 32px;
  background: var(--pl-purple);
  color: var(--pl-white);
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease;
  
  &:hover {
    background: var(--pl-pink);
  }
  
  &:disabled {
    background: var(--pl-gray);
    cursor: not-allowed;
  }
`;

// Helper function to determine the actual outcome
const getActualOutcome = (home_goals, away_goals) => {
  if (home_goals > away_goals) return 'Home';
  if (home_goals < away_goals) return 'Away';
  return 'Draw';
};

const PredictionCell = ({ prediction, home_goals, away_goals }) => {
  if (!prediction) return <span style={{ color: '#aaa' }}>N/A</span>;
  
  const { home_win_probability, draw_probability, away_win_probability } = prediction;
  const actualOutcome = getActualOutcome(home_goals, away_goals);
  
  // Determine predicted outcome based on highest probability
  const max = Math.max(home_win_probability, draw_probability, away_win_probability);
  let predictedLabel = '';
  if (max === home_win_probability) predictedLabel = 'Home';
  else if (max === draw_probability) predictedLabel = 'Draw';
  else predictedLabel = 'Away';
  
  // Apply color logic
  let color;
  if (actualOutcome === 'Draw') {
    color = 'orange';
  } else if (predictedLabel === actualOutcome) {
    color = 'green';
  } else {
    color = 'red';
  }
  
  return (
    <span>
      <b style={{ color }}>{predictedLabel}</b> <span className="details">
        (H: {home_win_probability.toFixed(2)}, D: {draw_probability.toFixed(2)}, A: {away_win_probability.toFixed(2)})
      </span>
    </span>
  );
};

const ResultsPage = () => {
  const [results, setResults] = useState([]);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const limit = 20;

  const fetchResults = async (append = false) => {
    setIsLoading(!append);
    try {
      setError(null);
      const data = await getResults(offset, limit);
      setTotal(data.total);
      setResults(append ? [...results, ...data.results] : data.results);
    } catch (e) {
      setError('Failed to load results. Please try again later.');
      console.error('Error fetching results:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!isRefreshing) {
      setIsRefreshing(true);
      setOffset(0);
      await fetchResults();
      setIsRefreshing(false);
    }
  };

  const handleLoadMore = () => {
    setOffset(prev => prev + limit);
  };

  useEffect(() => {
    fetchResults();
  }, []);

  useEffect(() => {
    if (offset === 0) return;
    fetchResults(true);
  }, [offset]);

  return (
    <Layout>
      {isLoading ? (
        <LoadingContainer>Loading results...</LoadingContainer>
      ) : error ? (
        <ErrorContainer>{error}</ErrorContainer>
      ) : results.length === 0 ? (
        <LoadingContainer>No results available.</LoadingContainer>
      ) : (
        <MatchList>
          <h2>Results</h2>
          
          {results.map(match => (
            <MatchCard key={match.match_id}>
              <MatchInfo>
                <DateVenue>{new Date(match.date).toLocaleDateString()}</DateVenue>
              </MatchInfo>
              <MatchTeams>
                <TeamName>{match.home_team}</TeamName>
                <Score>{match.home_goals} - {match.away_goals}</Score>
                <TeamName style={{ textAlign: 'left' }}>{match.away_team}</TeamName>
              </MatchTeams>
              <PredictionBadge>
                <PredictionCell 
                  prediction={match.prediction} 
                  home_goals={match.home_goals} 
                  away_goals={match.away_goals} 
                />
              </PredictionBadge>
            </MatchCard>
          ))}
          {results.length < total && (
            <LoadMoreButton onClick={handleLoadMore} disabled={isLoading}>
              {isLoading ? 'Loading...' : 'Load More'}
            </LoadMoreButton>
          )}
        </MatchList>
      )}
    </Layout>
  );
};

export default ResultsPage;