/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        lavender: {
          50: '#faf9ff',
          100: '#f4f2ff',
          200: '#ebe6ff',
          300: '#dcd3ff',
          400: '#c3b2ff',
          500: '#a384ff',
          600: '#8453fc',
          700: '#6f36f0',
          800: '#5a27ce',
          900: '#4c22aa',
        },
        brand: {
          purple: '#6C5CE7',
          violet: '#5A46E5',
          soft: '#F3F2FD',
          lightBg: '#F8F9FE',
          card: '#FFFFFF',
          textDark: '#1E1B4B',
          textMuted: '#64748B',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 4px 20px -2px rgba(108, 92, 231, 0.08)',
        card: '0 2px 12px rgba(0, 0, 0, 0.04)',
        hover: '0 8px 24px -4px rgba(108, 92, 231, 0.14)',
      }
    },
  },
  plugins: [],
}
