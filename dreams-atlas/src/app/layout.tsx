import type { Metadata } from 'next';
import './globals.css';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export const metadata: Metadata = {
  title: 'DREAMS Atlas | Spectral Adhesive Classification',
  description:
    'Dual-modality Recognition and Evaluation of Adhesive Materials via Spectroscopy. IR + Raman spectral classification for adhesive identification by K-Dense Science Lab.',
  icons: {
    icon: '/favicon.svg',
  },
  openGraph: {
    title: 'DREAMS Atlas | Spectral Adhesive Classification',
    description:
      'Combining IR and Raman spectroscopy with deep learning to classify 7 adhesive families across 43 compounds.',
    siteName: 'DREAMS Atlas',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Navbar />
        <main className="pt-16">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
