/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./flaskr/templates/**/*.html'],
  theme: {
    extend: {},
  },
  plugins: [require('@tailwindcss/forms')],
};
