import {nextui} from '@nextui-org/theme';
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  darkMode: "class",
 plugins: [nextui({
   themes: {
     dark: {
       colors: {
         background: "#000000",
         foreground: "#ECEDEE",
         primary: {
           foreground: "#FFFFFF",
           DEFAULT: "#006FEE",
         },
         // ... rest of the colors
       },
     },
     light: {
       colors: {
         background: "#FFFFFF",
         foreground: "#11181C",
         primary: {
           foreground: "#FFFFFF",
           DEFAULT: "#006FEE",
         },
         // ... rest of the colors
       },
     },
     // ... custom themes
   },
 }),],
};
export default config;
