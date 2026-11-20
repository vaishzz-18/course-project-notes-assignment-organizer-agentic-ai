/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f4ff',
          100: '#e0e8ff',
          600: '#2d4a8a',
          700: '#1e3a7a',
          800: '#152d6b',
          900: '#0d1f5c',
        },
      },
    },
  },
  plugins: [],
}
