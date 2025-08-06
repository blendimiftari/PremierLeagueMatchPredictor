import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import styled from 'styled-components';

const HeaderContainer = styled.header`
  background-color: var(--pl-purple);
  color: var(--pl-white);
  padding: var(--spacing-md) var(--spacing-xl);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const HeaderContent = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  font-weight: bold;
  font-size: var(--fs-xl);

  img {
    height: 40px;
    margin-right: var(--spacing-md);
  }
`;

const NavLinks = styled.nav`
  display: flex;
  gap: var(--spacing-lg);

  a {
    color: var(--pl-white);
    font-weight: 600;
    transition: color 0.2s ease;

    &:hover {
      color: var(--pl-blue);
    }

    &.active {
      color: var(--pl-blue);
      position: relative;

      &::after {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 0;
        width: 100%;
        height: 3px;
        background-color: var(--pl-blue);
        border-radius: 3px;
      }
    }
  }
`;

const Header = () => {
  return (
    <HeaderContainer>
      <HeaderContent>
      <NavLink
          to='/'>
        <Logo>
          <img 
            src="https://www.premierleague.com/resources/rebrand/v7.153.55/i/elements/pl-main-logo.png" 
            alt="Premier League"
          />
            <span >Premier League Match Predictor</span>
        </Logo>
        </NavLink>
        <NavLinks>
          <NavLink
            to="/"
            end
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            Fixtures
          </NavLink>
          <NavLink
            to="/results"
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            Results
          </NavLink>
        </NavLinks>
      </HeaderContent>
    </HeaderContainer>
  );
};

export default Header; 