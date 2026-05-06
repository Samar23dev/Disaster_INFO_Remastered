/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        surface: 'var(--surface)',
        surfaceBorder: 'var(--surface-border)',
        textMain: 'var(--text-main)',
        textMuted: 'var(--text-muted)',
        primary: 'var(--primary)',
        primaryHover: 'var(--primary-hover)',
        danger: 'var(--danger)',
        warning: 'var(--warning)',
        success: 'var(--success)',
      }
    },
  },
  plugins: [],
}
