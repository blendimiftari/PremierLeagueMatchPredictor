import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import Layout from '../components/common/Layout';
import MatchCard from '../components/matchDetails/MatchCard';
import PredictionCard from '../components/matchDetails/PredictionCard';
import { getPrediction, getMatchById } from '../api/api';

const PageContainer = styled.div`
  padding: var(--spacing-lg) 0;
`;

const BackLink = styled(Link)`
  display: inline-flex;
  align-items: center;
  color: var(--pl-dark-gray);
  margin-bottom: var(--spacing-lg);
  transition: color 0.2s ease;
  
  &:hover {
    color: var(--pl-purple);
  }
  
  svg {
    margin-right: var(--spacing-xs);
  }
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  font-size: var(--fs-lg);
  color: var(--pl-dark-gray);
`;

const ErrorContainer = styled.div`
  padding: var(--spacing-lg);
  background-color: #ffeeee;
  border-radius: 4px;
  color: #d32f2f;
  margin-bottom: var(--spacing-lg);
`;

const MatchNotFound = styled.div`
  text-align: center;
  padding: var(--spacing-xl);
  
  h2 {
    color: var(--pl-purple);
    margin-bottom: var(--spacing-md);
  }
  
  p {
    color: var(--pl-dark-gray);
    margin-bottom: var(--spacing-lg);
  }
  
  a {
    display: inline-block;
    padding: var(--spacing-sm) var(--spacing-lg);
    background-color: var(--pl-purple);
    color: var(--pl-white);
    border-radius: 4px;
    font-weight: 600;
    transition: background-color 0.2s ease;
    
    &:hover {
      background-color: #4b0054;
    }
  }
`;

const MatchDetailsPage = () => {
  const { matchId } = useParams();
  const [match, setMatch] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchMatchDetails = async () => {
      try {
        setIsLoading(true);
        
        // Get match by ID using our new API function
        const matchResult = await getMatchById(matchId);
        const matchData = matchResult.match;


        
        // Format match data for the MatchCard component
        const formattedMatch = {
          match_id: matchData.id,
          date: matchData.utcDate,
          home_team_id: matchData.homeTeam.id,
          home_team_name: matchData.homeTeam.name,
          away_team_id: matchData.awayTeam.id,
          away_team_name: matchData.awayTeam.name,
          venue: matchData.venue,
          status: matchData.status,
          home_team: {
            id: matchData.homeTeam.id,
            name: matchData.homeTeam.name,
            crest: matchData.homeTeam.crest || `https://crests.football-data.org/${matchData.home_team_id}.png`
          },
          away_team: {
            id: matchData.awayTeam.id,
            name: matchData.awayTeam.name,
            crest: matchData.awayTeam.crest || `https://crests.football-data.org/${matchData.away_team_id}.png`
          }
        };



        
        
        setMatch(formattedMatch);

    
        
        // Get prediction for the match
        const predictionData = await getPrediction(formattedMatch.home_team_id, formattedMatch.away_team_id);
        setPrediction(predictionData);
        
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching match details:', error);
        setError('Failed to load match details. Please try again later.');
        setIsLoading(false);
      }
    };
    
    if (matchId) {
      fetchMatchDetails();
    }
  }, [matchId]);

  if (isLoading) {
    return (
      <Layout>
        <LoadingContainer>Loading match details...</LoadingContainer>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
       
        <ErrorContainer>
          <p>{error}</p>
        </ErrorContainer>
      </Layout>
    );
  }

  if (!match) {
    return (
      <Layout>
        <MatchNotFound>
          <h2>Match Not Found</h2>
          <p>The match you're looking for doesn't exist or has been removed.</p>
          <Link to="/">Return to Fixtures</Link>
        </MatchNotFound>
      </Layout>
    );
  }

  return (
    <Layout>
      <PageContainer>
        <MatchCard match={match} />
        {prediction && <PredictionCard prediction={prediction} />}
      </PageContainer>
    </Layout>
  );
};

export default MatchDetailsPage; 