import { createGlobalStyle } from 'styled-components';

const GlobalStyles = createGlobalStyle`
  :root {
    /* Premier League Colors */
    --pl-purple: #37003c;
    --pl-pink: #ff2882;
    --pl-light-pink: #ff7fa5;
    --pl-blue: #00ff87;
    --pl-light-blue: #2cc0d9;
    --pl-yellow: #feeb00;
    --pl-white: #ffffff;
    --pl-black: #231f20;
    --pl-gray: #efefef;
    --pl-medium-gray: #d0d0d0;
    --pl-dark-gray: #76766f;
    
    /* Font Sizes */
    --fs-xs: 0.75rem;
    --fs-sm: 0.875rem;
    --fs-md: 1rem;
    --fs-lg: 1.125rem;
    --fs-xl: 1.25rem;
    --fs-2xl: 1.5rem;
    --fs-3xl: 1.875rem;
    --fs-4xl: 2.25rem;
    
    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;
  }

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'PremierSans', 'Arial', sans-serif;
    background-color: var(--pl-white);
    color: var(--pl-black);
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  a {
    text-decoration: none;
    color: inherit;
  }

  button {
    cursor: pointer;
    border: none;
    outline: none;
    background: none;
    font-family: inherit;
  }

  h1, h2, h3, h4, h5, h6 {
    font-weight: 700;
  }

  /* Custom Premier League inspired font face */
  @font-face {
    font-family: 'PremierSans';
    src: url('https://www.premierleague.com/resources/prod/css/fonts/premierleague-regular-webfont.woff2') format('woff2');
    font-weight: 400;
    font-style: normal;
  }

  @font-face {
    font-family: 'PremierSans';
    src: url('https://www.premierleague.com/resources/prod/css/fonts/premierleague-bold-webfont.woff2') format('woff2');
    font-weight: 700;
    font-style: normal;
  }
`;

export default GlobalStyles; 