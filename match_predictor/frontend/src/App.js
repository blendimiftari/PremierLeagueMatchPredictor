import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import GlobalStyles from './styles/GlobalStyles';
import FixturesPage from './pages/FixturesPage';
import MatchDetailsPage from './pages/MatchDetailsPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Router>
      <GlobalStyles />
      <div>
        <Routes>
          <Route path="/fixtures" element={<FixturesPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/match/:matchId" element={<MatchDetailsPage />} />
          <Route path="*" element={<FixturesPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
