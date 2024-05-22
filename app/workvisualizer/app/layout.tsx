import type { Metadata } from "next";
import { inter } from '@/app/ui/fonts';
import { Inter as FontSans } from "next/font/google"
import { ThemeProvider } from "next-themes";
import "./globals.css";


import { cn } from "@/lib/utils"

const fontSans = FontSans({
    subsets: ["latin"],
    variable: "--font-sans",
})

export const metadata: Metadata = {
  title: "Work Visualizer",
  description: "A Work Visualizer for visualizing visualization",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
      <html suppressHydrationWarning lang="en">
      <body className={cn(
          "min-h-screen bg-background font-sans antialiased",
          fontSans.variable
      )}
      >
        <ThemeProvider>{children}</ThemeProvider>
      </body>
      </html>
  );
}
