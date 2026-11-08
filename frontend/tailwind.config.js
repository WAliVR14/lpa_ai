/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f5fa',
          100: '#e1ecf5',
          500: '#2563eb',
          600: '#1d4ed8',
          700: '#1e40af',
          800: '#002D62', // Automotive Deep Navy
          900: '#0a192f',
        },
        industrial: {
          800: '#1e293b',
          850: '#151f30',
          900: '#0f172a',
          950: '#080d1a',
        }
      }
    },
  },
  plugins: [],
}

