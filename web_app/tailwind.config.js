/** @type {import('tailwindcss').Config} */
module.exports = {
// Add this line
  darkMode: 'class',
  content: [
    './templates/**/*.html', // Scan all .html files in the templates folder
    './static/js/**/*.js',   // Scan JS files if you add classes with JS
  ],
  // ADD THIS SAFELIST BLOCK
  safelist: [
    // ✅ Text colors
    { pattern: /^text-(red|orange|yellow|green|blue|indigo|purple|pink|gray|black|white)(-\d{1,3})?$/ },

    // ✅ Background colors
    { pattern: /^bg-(red|orange|yellow|green|blue|indigo|purple|pink|gray|black|white)(-\d{1,3})?$/ },

    // ✅ Hover background colors
    {
      pattern: /^bg-(red|orange|yellow|green|blue|indigo|purple|pink|gray)(-\d{1,3})?$/,
      variants: ['hover']
    },

    // ✅ Dark mode hover backgrounds
    {
      pattern: /^bg-(red|orange|yellow|green|blue|indigo|purple|pink|gray)(-\d{1,3})?$/,
      variants: ['dark', 'hover']
    },

    // ✅ Border colors
    {
      pattern: /^border-(red|orange|yellow|green|blue|indigo|purple|pink|gray)(-\d{1,3})?$/,
      variants: ['hover']
    },

    // ✅ Ring colors
    {
      pattern: /^ring-(red|orange|yellow|green|blue|indigo|purple|pink|gray)(-\d{1,3})?$/,
      variants: ['focus']
    },
  ],

  theme: {
    extend: {
      animation: {
        // adjust speed according to your need
        marquee: 'marquee 40s linear infinite',
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(-200%)' },
        }
      }
    }
  },
  variants: {
    extend: {
      animation: ['hover', 'focus'],
    }
  },
  plugins: [],
}

