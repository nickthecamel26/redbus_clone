/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {},
    colors: {
      primary: '#D84E55', // RedBus Red
      secondary: '#3E3E52', // Deep Gray
      background: '#F0F2F5', // Dark background
    }
  },
  plugins: [require("@tailwindcss/forms")],
}
