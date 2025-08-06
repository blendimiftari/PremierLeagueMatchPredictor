import React from 'react';
import styled from 'styled-components';
import { format, parseISO } from 'date-fns';
import { Link, useNavigate } from 'react-router-dom';

const FixturesContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'PremierSans', Arial, sans-serif;
`;

const DateHeader = styled.div` 
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  margin-bottom: 8px;
`;

const DateText = styled.h2`
  color: var(--pl-purple);
  font-size: 18px;
  font-weight: 600;
  margin: 0;
`;

const PLLogo = styled.img`
  height: 32px;
  width: auto;
`;

const TeamName = styled.span`
  font-weight: 700;
  color: #37003C;
  font-size: 15px;
  transition: color 0.2s ease;
`;

const MatchTime = styled.div`
  font-size: 16px;
  font-weight: 500;
  color: #37003C;
  text-align: center;
  padding: 2px;
  border-radius: 3px;
  transition: all 0.2s ease;
  border: 1px solid rgb(236, 236, 236);
`;

const QuickViewButton = styled(Link)`
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--pl-purple);
  font-weight: 500;
  font-size: 14px;
  text-decoration: none;
  padding: 8px 16px;
  margin-left: auto;
  transition: color 0.2s ease;
`;

const QuickViewText = styled.span`
  font-size: 14px;
  font-weight: 500;
  color: #37003C;
  margin-right: 4px;
  padding: 4px 16px;
  border: 1px solid rgb(236, 236, 236);
  border-radius: 3px;
`;

const Arrow = styled.span`
  font-size: 16px;
  margin-left: 8px;
`;

const MatchRow = styled.div`
  display: grid;
  grid-template-columns: 2fr 80px 2fr auto;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s ease;
  cursor: pointer;
  
  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background-color: rgb(44, 136, 217);
  }

  &:hover ${TeamName} {
    color: #ffffff;
  }

  &:hover ${MatchTime} {
    background-color: transparent;
    color: #ffffff;
    border: 1px solid  #ffffff;
  }

  &:hover ${QuickViewText} {
   background-color: #ffffff;
   color: #37003C;
  }

  &:hover ${Arrow} {
    color: #ffffff;
    animation: 1s ease-in-out;
    transform: translateX(4px);
  }
`;

const HomeTeamInfo = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding-right: 12px;
`;

const AwayTeamInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 12px;
`;

const TeamCrest = styled.img`
  width: 25px;
  height: 25px;
  object-fit: contain;
`;

const groupMatchesByDate = (matches) => {
  return matches.reduce((groups, match) => {
    const date = format(parseISO(match.date), 'yyyy-MM-dd');
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(match);
    return groups;
  }, {});
};

const UpcomingFixtures = ({ matches }) => { 
  const groupedMatches = groupMatchesByDate(matches);
  const navigate = useNavigate();

  const handleMatchClick = (matchId) => {
    navigate(`/match/${matchId}`);
  };

  return (
    <FixturesContainer>
      {Object.entries(groupedMatches).map(([date, dayMatches]) => (
        <div key={date}>
          <DateHeader>
            <DateText>
              {format(parseISO(date), 'EEEE d MMMM yyyy')}
            </DateText>
            <PLLogo 
              src="https://www.premierleague.com/resources/prod/v6.122.5-4671/i/elements/pl-main-logo.png"
              alt="Premier League"
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = 'https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg';
              }}
            />
          </DateHeader>
          
          {dayMatches.map((match) => (
            <MatchRow 
              key={match.match_id} 
              onClick={() => handleMatchClick(match.match_id)}
            >
              <HomeTeamInfo>
                <TeamName>{match.home_team_name}</TeamName>
                <TeamCrest 
                  src={`https://crests.football-data.org/${match.home_team_id}.png`}
                  alt={match.home_team_name}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg';
                  }}
                />
              </HomeTeamInfo>
              
              <MatchTime>
                {format(parseISO(match.date), 'HH:mm')}
              </MatchTime>
              
              <AwayTeamInfo>
                <TeamCrest 
                  src={`https://crests.football-data.org/${match.away_team_id}.png`}
                  alt={match.away_team_name}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg';
                  }}
                />
                <TeamName>{match.away_team_name}</TeamName>
              </AwayTeamInfo>
              
              <QuickViewButton to={`/match/${match.match_id}`} onClick={(e) => e.stopPropagation()}>
                <QuickViewText>Predict</QuickViewText>
                <Arrow>→</Arrow>
              </QuickViewButton>
            </MatchRow>
          ))}
        </div>
      ))}
    </FixturesContainer>
  );
};

export default UpcomingFixtures; 