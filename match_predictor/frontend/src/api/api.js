import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const getUpcomingFixtures = async (matchday = null) => {
  try {
    let url = `${API_URL}/fixtures/upcoming`;
    
    if (matchday) {
      url += `?matchday=${matchday}`;
    }
    
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    console.error('Error fetching upcoming fixtures:', error);
    throw error;
  }
};

export const getMatchById = async (matchId) => {
  try {
    const url = `${API_URL}/match/${matchId}`;
    const response = await axios.get(url);
  
    
    if (response.data) {
      return {
        match: response.data
      };
    }

    
    throw new Error('Match not found');
  } catch (error) {
    console.error(`Error fetching match with ID ${matchId}:`, error);
    throw error;
  }
};

export const getPrediction = async (homeTeamId, awayTeamId) => {
  try {
    const response = await axios.post(`${API_URL}/predict/`, {
      home_team_id: homeTeamId,
      away_team_id: awayTeamId
    });
    return response.data;
  } catch (error) {
    console.error('Error getting prediction:', error);
    throw error;
  }
};

export const getTeamElo = async (teamId) => {
  try {
    const response = await axios.get(`${API_URL}/teams/${teamId}/elo`);
    return response.data;
  } catch (error) {
    console.error('Error fetching team Elo:', error);
    throw error;
  }
};

export const getResults = async (offset = 0, limit = 20) => {
  try {
    const response = await axios.get(`${API_URL}/results?offset=${offset}&limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching results:', error);
    throw error;
  }
};



