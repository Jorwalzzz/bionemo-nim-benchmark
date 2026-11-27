/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./cockpit.html",
    "./js/**/*.js"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter Tight', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
        heading: ['Space Grotesk', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif']
      },
      colors: {
        nvidia: { green: '#76b900', bright: '#a3e635' },
        cyber: { cyan: '#00f1fd', purple: '#a855f7', blue: '#3b82f6' },
        surface: {
          base: 'var(--color-canvas, #0B0E14)',
          card: 'var(--color-surface, #111622)',
          elevated: 'var(--color-surface-elevated, #171E2E)',
          border: 'var(--border-hairline, rgba(255,255,255,0.1))'
        }
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'slide-in': 'slideIn 0.4s ease-out',
        'fade-up': 'fadeUp 0.5s ease-out',
        'scan-line': 'scanLine 3s linear infinite',
        'float': 'float 3s ease-in-out infinite',
        'agent-run': 'agentRun 1.5s ease-in-out infinite'
      },
      keyframes: {
        pulseGlow: { '0%,100%': { opacity: '0.6' }, '50%': { opacity: '1' } },
        slideIn: { from: { opacity: '0', transform: 'translateX(-20px)' }, to: { opacity: '1', transform: 'translateX(0)' } },
        fadeUp: { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        scanLine: { '0%': { top: '0%' }, '100%': { top: '100%' } },
        float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-6px)' } },
        agentRun: { '0%,100%': { boxShadow: '0 0 5px rgba(118,185,0,0.3)' }, '50%': { boxShadow: '0 0 20px rgba(118,185,0,0.8), 0 0 40px rgba(118,185,0,0.3)' } }
      }
    }
  },
  plugins: []
}
