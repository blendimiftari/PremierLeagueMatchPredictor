import React from 'react';
import styled from 'styled-components';

const PredictionContainer = styled.div`
  background-color: var(--pl-white);
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  padding: var(--spacing-lg);
  max-width: 800px;
  margin: 0 auto var(--spacing-xl);
  overflow: hidden;
`;

const PredictionTitle = styled.h3`
  font-size: var(--fs-xl);
  color: var(--pl-purple);
  margin-bottom: var(--spacing-lg);
  text-align: center;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 50%;
    transform: translateX(-50%);
    width: 100px;
    height: 3px;
    background-color: var(--pl-blue);
    border-radius: 3px;
  }
`;

const PredictionResults = styled.div`
  display: flex;
  justify-content: space-around;
  margin-bottom: var(--spacing-lg);
`;

const PredictionItem = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--spacing-md);
  width: 33%;
  position: relative;
  
  ${props => props.isHighest && `
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: var(--pl-blue);
      opacity: 0.1;
      border-radius: 8px;
      z-index: 0;
    }
  `}
`;

const PredictionValue = styled.div`
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: ${props => props.isHighest ? 'var(--pl-purple)' : 'var(--pl-black)'};
  margin-bottom: var(--spacing-sm);
  position: relative;
  z-index: 1;
`;

const PredictionLabel = styled.div`
  font-size: var(--fs-sm);
  color: var(--pl-dark-gray);
  text-transform: uppercase;
  font-weight: 600;
  position: relative;
  z-index: 1;
`;

const FeaturesSectionTitle = styled.h4`
  font-size: var(--fs-lg);
  color: var(--pl-purple);
  margin: var(--spacing-lg) 0 var(--spacing-md);
`;

const FeaturesContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
`;

const FeatureItem = styled.div`
  background-color: var(--pl-gray);
  border-radius: 4px;
  padding: var(--spacing-sm) var(--spacing-md);
  flex: 1 1 calc(33% - var(--spacing-md));
  min-width: 200px;
  display: flex;
  flex-direction: column;
`;

const FeatureLabel = styled.div`
  font-size: var(--fs-xs);
  color: var(--pl-dark-gray);
  margin-bottom: var(--spacing-xs);
`;

const FeatureValue = styled.div`
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--pl-black);
`;

const PredictionCard = ({ prediction }) => {
  if (!prediction) {
    return (
      <PredictionContainer>
        <PredictionTitle>Prediction Loading...</PredictionTitle>
      </PredictionContainer>
    );
  }
  
  // Find the highest probability
  const probabilities = {
    'Home Win': prediction.home_win_probability,
    'Draw': prediction.draw_probability,
    'Away Win': prediction.away_win_probability
  };
  
  const highestProbabilityKey = Object.keys(probabilities).reduce((a, b) => 
    probabilities[a] > probabilities[b] ? a : b
  );
  
  // Format probability as percentage
  const formatProbability = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };
  
  return (
    <PredictionContainer>
      <PredictionTitle>Match Prediction</PredictionTitle>
      
      <PredictionResults>
        <PredictionItem isHighest={highestProbabilityKey === 'Home Win'}>
          {/* <PredictionValue isHighest={highestProbabilityKey === 'Home Win'}>
            {formatProbability(prediction.home_win_probability)}
          </PredictionValue> */}
          <PredictionLabel>Home Win</PredictionLabel>
        </PredictionItem>
        
        <PredictionItem isHighest={highestProbabilityKey === 'Draw'}>
          {/* <PredictionValue isHighest={highestProbabilityKey === 'Draw'}>
            {formatProbability(prediction.draw_probability)}
          </PredictionValue> */}
          <PredictionLabel>Draw</PredictionLabel>
        </PredictionItem>
        
        <PredictionItem isHighest={highestProbabilityKey === 'Away Win'}>
          {/* <PredictionValue isHighest={highestProbabilityKey === 'Away Win'}>
            {formatProbability(prediction.away_win_probability)}
          </PredictionValue> */}
          <PredictionLabel>Away Win</PredictionLabel>
        </PredictionItem>
      </PredictionResults>
      
      {/* <FeaturesSectionTitle>Prediction Factors</FeaturesSectionTitle>
      <FeaturesContainer>
        <FeatureItem>
          <FeatureLabel>Elo Difference</FeatureLabel>
          <FeatureValue>{prediction.features.Elo_Difference.toFixed(1)}</FeatureValue>
        </FeatureItem>
        
        <FeatureItem>
          <FeatureLabel>Home Team Elo</FeatureLabel>
          <FeatureValue>{prediction.features.Home_Elo.toFixed(1)}</FeatureValue>
        </FeatureItem>
        
        <FeatureItem>
          <FeatureLabel>Away Team Elo</FeatureLabel>
          <FeatureValue>{prediction.features.Away_Elo.toFixed(1)}</FeatureValue>
        </FeatureItem>
        
        <FeatureItem>
          <FeatureLabel>H2H Draws (Last 5)</FeatureLabel>
          <FeatureValue>{prediction.features.H2H_Draws_Last_5}</FeatureValue>
        </FeatureItem>
        
        <FeatureItem>
          <FeatureLabel>Home Team Draw Tendency</FeatureLabel>
          <FeatureValue>{(prediction.features.Draw_Tendency_Home * 100).toFixed(1)}%</FeatureValue>
        </FeatureItem>
        
        <FeatureItem>
          <FeatureLabel>Away Team Draw Tendency</FeatureLabel>
          <FeatureValue>{(prediction.features.Draw_Tendency_Away * 100).toFixed(1)}%</FeatureValue>
        </FeatureItem>
        
        <FeatureItem>
          <FeatureLabel>Home Team Avg Goal Diff</FeatureLabel>
          <FeatureValue>{prediction.features.Avg_Home_GD_Last_5.toFixed(2)}</FeatureValue>
        </FeatureItem>
        
        <FeatureItem>
          <FeatureLabel>Away Team Avg Goal Diff</FeatureLabel>
          <FeatureValue>{prediction.features.Avg_Away_GD_Last_5.toFixed(2)}</FeatureValue>
        </FeatureItem>
      </FeaturesContainer> */}
    </PredictionContainer>
  );
};

export default PredictionCard; 