import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Visualize UI",
  description: "Interactive data visualization surface for Claude Code sessions",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
