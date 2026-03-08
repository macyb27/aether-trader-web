import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Petrol/Dark theme
        primary: {
          50: '#f0f9fb',
          100: '#e0f2f7',
          200: '#c1e5ef',
          300: '#a2d8e7',
          400: '#83cbdf',
          500: '#0a7ea4', // Primary petrol
          600: '#086a8a',
          700: '#065670',
          800: '#043e56',
          900: '#022a3c',
        },
        dark: {
          50: '#f8f9fa',
          100: '#f1f3f5',
          200: '#e9ecef',
          300: '#dee2e6',
          400: '#ced4da',
          500: '#adb5bd',
          600: '#868e96',
          700: '#495057',
          800: '#343a40',
          900: '#212529',
        },
      },
      backgroundImage: {
        'gradient-dark': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        'gradient-petrol': 'linear-gradient(135deg, #0a7ea4 0%, #065670 100%)',
      },
    },
  },
  plugins: [],
}
export default config
