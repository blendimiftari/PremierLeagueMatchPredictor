import React from 'react';
import styled from 'styled-components';

const CardContainer = styled.div`
  background-color: var(--pl-white);
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: var(--spacing-xl);
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  background-color: var(--pl-purple);
  color: var(--pl-white);
`;

const DateContainer = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
`;

const Icon = styled.span`
  font-size: 1.2rem;
`;

const DateText = styled.span`
  font-size: var(--fs-sm);
  font-weight: 600;
`;

const VenueContainer = styled.div`
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
`;

const TeamsContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: var(--spacing-xl) var(--spacing-lg);
  position: relative;
`;

const TeamInfo = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 45%;
`;

const TeamLogo = styled.img`
  height: 120px;
  width: 120px;
  object-fit: contain;
  margin-bottom: var(--spacing-md);
`;

const TeamName = styled.h2`
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--pl-black);
  margin-bottom: var(--spacing-sm);
`;

const ScoreOrTime = styled.div`
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: ${props => props.status === 'FT' ? 'var(--pl-purple)' : 'var(--pl-white)'};
  color: ${props => props.status === 'FT' ? 'var(--pl-white)' : 'var(--pl-purple)'};
  border: 2px solid var(--pl-purple);
  border-radius: 8px;
  padding: ${props => props.status === 'FT' ? 'var(--spacing-sm) var(--spacing-lg)' : 'var(--spacing-xs) var(--spacing-md)'};
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-width: 100px;
  text-align: center;
`;

const Score = styled.div`
  font-size: var(--fs-2xl);
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
`;

const ScoreSeparator = styled.span`
  margin: 0 var(--spacing-xs);
`;

const KickoffTime = styled.div`
  font-size: var(--fs-2xl);
  font-weight: 700;
`;

const TimeStatus = styled.div`
  font-size: var(--fs-xs);
  text-transform: uppercase;
  margin-top: var(--spacing-xs);
`;

const StatusLabel = styled.div`
  background-color: ${props => props.status === 'FT' ? 'var(--pl-dark-gray)' : 'var(--pl-blue)'};
  color: ${props => props.status === 'FT' ? 'var(--pl-white)' : 'var(--pl-black)'};
  border-radius: 4px;
  font-size: var(--fs-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  font-weight: 600;
  margin-top: var(--spacing-sm);
`;

const MatchCard = ({ match }) => {
  const matchDate = new Date(match.date);
  const isMatchComplete = match.home_goals !== undefined && match.away_goals !== undefined;
  const matchStatus = isMatchComplete ? 'FT' : 'Kick Off';
  
  // Format date - Tuesday 1 Apr 2025
  const formattedDate = matchDate.toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
  
  // Format time - 20:45
  const formattedTime = matchDate.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit'
  });
  
  return (
    <CardContainer>
      <CardHeader>
        <DateContainer>
          <Icon>📅</Icon>
          <DateText>{formattedDate}</DateText>
        </DateContainer>
      </CardHeader>
      
      <TeamsContainer>
        <TeamInfo>
          <TeamLogo 
            src={match.home_team.crest || `https://crests.football-data.org/${match.home_team_id}.png`} 
            alt={match.home_team_name}
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg';
            }}
          />
          <TeamName>{match.home_team_name}</TeamName>
          {isMatchComplete && (
            <StatusLabel status={matchStatus}>Home</StatusLabel>
          )}
        </TeamInfo>
        
        <ScoreOrTime status={matchStatus}>
          {isMatchComplete ? (
            <>
              <Score>
                {match.home_goals}
                <ScoreSeparator>-</ScoreSeparator>
                {match.away_goals}
              </Score>
              <TimeStatus>{matchStatus}</TimeStatus>
            </>
          ) : (
            <>
              <KickoffTime>{formattedTime}</KickoffTime>
              <TimeStatus>{matchStatus}</TimeStatus>
            </>
          )}
        </ScoreOrTime>
        
        <TeamInfo>
          <TeamLogo 
            src={match.away_team.crest || `https://crests.football-data.org/${match.away_team_id}.png`} 
            alt={match.away_team_name}
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg';
            }}
          />
          <TeamName>{match.away_team_name}</TeamName>
          {isMatchComplete && (
            <StatusLabel status={matchStatus}>Away</StatusLabel>
          )}
        </TeamInfo>
      </TeamsContainer>
    </CardContainer>
  );
};

export default MatchCard; 