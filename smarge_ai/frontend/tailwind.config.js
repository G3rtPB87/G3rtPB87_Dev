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
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))",
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))",
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))",
                },
            },
            lg: "var(--radius)",
            md: "calc(var(--radius) - 2px)",
            sm: "calc(var(--radius) - 4px)",
        },
        fontFamily: {
            sans: ['"Inter"', 'sans-serif'],
            mono: ['"Inconsolata"', 'monospace'],
        },
        keyframes: {
            'slide-up': {
                '0%': { transform: 'translateY(10px)', opacity: 0 },
                '100%': { transform: 'translateY(0)', opacity: 1 },
            },
            'fade-in': {
                '0%': { opacity: 0 },
                '100%': { opacity: 1 },
            }
        },
        animation: {
            'slide-up': 'slide-up 0.3s ease-out',
            'fade-in': 'fade-in 0.2s ease-out',
        }
    },
},
plugins: [],
}
