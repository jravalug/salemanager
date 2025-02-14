/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "selector",
  content: [
    "./app/templates/**/*.html",
    "./app/static/**/*.js",
    "./node_modules/flowbite/**/*.js",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("flowbite/plugin")],
};
