import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DB Quality Inspector',
  description: 'Automated data quality checks for DuckDB databases',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
