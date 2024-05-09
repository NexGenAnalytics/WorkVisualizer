import type { Metadata } from "next";
import { inter } from '@/app/ui/fonts';
import "./globals.css";

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
      <html lang="en">
      <body className={`${inter.className} antialiased`}>{children}</body>
      </html>
  );
}
