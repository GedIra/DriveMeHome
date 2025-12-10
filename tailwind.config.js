module.exports = {
  content: [
    './templates/**/*.html',
    './users/templates/**/*.html',
    './**/*.html',
    './static/src/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1a237e',
        secondary: '#ffc107',
        gret: '#9ca3af',
      },
    },
  },
  plugins: [tailwindcss()],
}
