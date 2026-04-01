/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#6366f1',
        accent: '#8b5cf6',
        dark: '#0f0f0f',
        darker: '#0a0a0a'
      }
    },
  },
  plugins: [],
}
