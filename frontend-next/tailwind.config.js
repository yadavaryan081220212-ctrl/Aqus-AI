/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'oklch(0.1593 0.0240 285.8152)',
        foreground: 'oklch(0.9702 0.0094 247.8390)',
        card: 'oklch(0.2002 0.0278 284.5989)',
        cardForeground: 'oklch(0.9791 0.0084 247.8705)',
        popover: 'oklch(0.1593 0.0240 285.8152)',
        popoverForeground: 'oklch(0.9702 0.0094 247.8390)',
        primary: 'oklch(0.8856 0.2888 334.2503)',
        primaryForeground: 'oklch(0.1593 0.0240 285.8152)',
        secondary: 'oklch(0.2795 0.0368 284.1527)',
        secondaryForeground: 'oklch(0.9498 0.0125 247.8854)',
        muted: 'oklch(0.2433 0.0247 285.8798)',
        mutedForeground: 'oklch(0.7108 0.0351 286.0665)',
        accent: 'oklch(0.3351 0.0331 284.9784)',
        accentForeground: 'oklch(0.9791 0.0084 247.8705)',
        destructive: 'oklch(0.6732 0.1866 23.8341)',
        destructiveForeground: 'oklch(0.1593 0.0240 285.8152)',
        border: 'oklch(0.2795 0.0368 284.1527)',
        input: 'oklch(0.2795 0.0368 284.1527)',
        ring: 'oklch(0.8856 0.2888 334.2503)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      borderRadius: {
        lg: '1.5rem',
        md: 'calc(1.5rem - 4px)',
        sm: 'calc(1.5rem - 8px)',
      },
    },
  },
  plugins: [],
  darkMode: 'class',
};
