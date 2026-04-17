/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // shadcn / CSS-var bridge
        border:      'hsl(var(--border))',
        input:       'hsl(var(--input))',
        ring:        'hsl(var(--ring))',
        background:  'hsl(var(--background))',
        foreground:  'hsl(var(--foreground))',
        destructive: {
          DEFAULT:      'hsl(var(--destructive))',
          foreground:   'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT:    'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT:    'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT:    'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT:    'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        // Institutional blue (IESTP RFA — formal, trust, engineering heritage)
        primary: {
          DEFAULT:    'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#2563eb',
          600: '#1d4ed8',
          700: '#1e40af',
          800: '#1e3a8a',
          900: '#172554',
          950: '#0b1845',
        },
        secondary: {
          DEFAULT:    'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        // Deep institutional navy (headers, hero)
        institutional: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          500: '#1e3a8a',
          600: '#1e293b',
          700: '#172554',
          900: '#0f172a',
        },
        // Heritage gold (academic honor + German flag reference)
        heritage: {
          50:  '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          400: '#facc15',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        // Peruvian red (accent, shared with destructive)
        peru: {
          50:  '#fef2f2',
          500: '#dc2626',
          600: '#b91c1c',
          700: '#991b1b',
        },
        module: {
          locked:    '#9ca3af',
          progress:  '#2563eb',
          completed: '#16a34a',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      boxShadow: {
        'brand-sm': '0 1px 2px 0 rgba(23, 37, 84, 0.08)',
        'brand-md': '0 4px 12px -2px rgba(23, 37, 84, 0.12), 0 2px 4px -1px rgba(23, 37, 84, 0.06)',
        'brand-lg': '0 20px 40px -12px rgba(23, 37, 84, 0.25)',
      },
      backgroundImage: {
        'brand-hero':      'linear-gradient(135deg, #172554 0%, #1e3a8a 50%, #1e40af 100%)',
        'heritage-accent': 'linear-gradient(90deg, #f59e0b 0%, #facc15 50%, #f59e0b 100%)',
      },
      keyframes: {
        'fade-in-up': {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in-up': 'fade-in-up 220ms ease-out',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
