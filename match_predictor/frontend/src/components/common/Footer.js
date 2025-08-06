import React from 'react';
import styled from 'styled-components';

const FooterContainer = styled.footer`
  background-color: var(--pl-purple);
  color: var(--pl-white);
  padding: var(--spacing-xl) 0;
  margin-top: auto;
`;

const FooterContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 var(--spacing-xl);
`;

const FooterLogo = styled.div`
  margin-bottom: var(--spacing-lg);
  
  img {
    height: 40px;
  }
`;

const FooterLinks = styled.div`
  display: flex;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-lg);
  
  a {
    color: var(--pl-white);
    font-size: var(--fs-sm);
    font-weight: 600;
    transition: color 0.2s ease;
    
    &:hover {
      color: var(--pl-blue);
    }
  }
`;

const FooterCopyright = styled.div`
  font-size: var(--fs-xs);
  color: var(--pl-dark-gray);
`;

const Footer = () => {
  return (
    <FooterContainer>
      <FooterContent>
        <FooterLogo>
          <img 
            src="https://www.premierleague.com/resources/rebrand/v7.153.55/i/elements/pl-main-logo.png" 
            alt="Premier League Match Predictor" 
          />
        </FooterLogo>
        <FooterLinks>
          <a href="#">About</a>
          <a href="#">Terms of Service</a>
          <a href="#">Privacy Policy</a>
          <a href="#">Contact</a>
        </FooterLinks>
        <FooterCopyright>
          &copy; {new Date().getFullYear()} Premier League Match Predictor. All rights reserved.
        </FooterCopyright>
      </FooterContent>
    </FooterContainer>
  );
};

export default Footer; 