/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./api/templates/**/*.html",
    "./api/templates/favourites.html",
    "./api/static/javascript/favourties.js",
    "./api/static/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        'oswald' : ['Oswald', 'sans-serif'],
        'roboto' : ['Roboto', 'sans-serif']
      },
      borderWidth: {
        '12':'12px'
      }
    },
  },
  plugins: [],
}