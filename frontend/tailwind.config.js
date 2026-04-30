/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#d84e55',
          dark: '#b93b42',
          light: '#f47075',
        }
      }
    },
  },
  plugins: [],
}
