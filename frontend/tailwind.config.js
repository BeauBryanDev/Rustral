/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core Rustral Palette
        'space-gray': '#0B0E14',
        'rust-orange': '#FF5F00',
        'neon-cyan': '#00F2FF',
        'industrial-gray': '#666666',
        
        // UI Surface Colors
        'surface-dark': '#11141A',
        'surface-light': '#1A1D24',
      },
      boxShadow: {
        // Cyberpunk Glow Effects
        'glow-cyan': '0 0 10px rgba(0, 242, 255, 0.4), 0 0 20px rgba(0, 242, 255, 0.2)',
        'glow-rust': '0 0 10px rgba(255, 95, 0, 0.4), 0 0 20px rgba(255, 95, 0, 0.2)',
      },
      fontFamily: {
        // Industry-standard tech fonts
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}