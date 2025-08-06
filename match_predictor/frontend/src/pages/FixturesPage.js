import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import Layout from '../components/common/Layout';
import UpcomingFixtures from '../components/fixtures/UpcomingFixtures';
import { getUpcomingFixtures } from '../api/api';

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
  gap: 8px;
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

const FixturesPage = () => {
  const [matches, setMatches] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchFixtures = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getUpcomingFixtures();
      setMatches(data.data.fixtures);
    } catch (err) {
      setError('Failed to load fixtures. Please try again later.');
      console.error('Error fetching fixtures:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!isRefreshing) {
      setIsRefreshing(true);
      await fetchFixtures();
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFixtures();
  }, []);

  return (
    <Layout>
      {isLoading ? (
        <LoadingContainer>Loading fixtures...</LoadingContainer>
      ) : error ? (
        <ErrorContainer>{error}</ErrorContainer>
      ) : matches.length === 0 ? (
        <LoadingContainer>No matches coming up soon.</LoadingContainer>
      ) : (
        <>
          <UpcomingFixtures matches={matches} />
        </>
      )}
    </Layout>
  );
};

export default FixturesPage; 