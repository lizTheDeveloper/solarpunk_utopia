import { ReactNode } from 'react';
import { Navigation } from './Navigation';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Skip to main content link for keyboard navigation */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-solarpunk-600 focus:text-white focus:rounded-lg focus:shadow-lg"
      >
        Skip to main content
      </a>
      <Navigation />
      <main id="main-content" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <footer className="bg-white border-t border-gray-200 mt-12" role="contentinfo">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs sm:text-sm text-gray-600 text-center md:text-left">
              Solarpunk Mesh Network - A gift economy for resilient communities
            </p>
            <nav className="flex items-center gap-4 sm:gap-6 text-xs sm:text-sm text-gray-600" aria-label="Footer navigation">
              <a href="#" className="hover:text-solarpunk-600 transition-colors focus:outline-none focus:ring-2 focus:ring-solarpunk-500 focus:ring-offset-2 rounded">
                About
              </a>
              <a href="#" className="hover:text-solarpunk-600 transition-colors focus:outline-none focus:ring-2 focus:ring-solarpunk-500 focus:ring-offset-2 rounded">
                Docs
              </a>
              <a href="#" className="hover:text-solarpunk-600 transition-colors focus:outline-none focus:ring-2 focus:ring-solarpunk-500 focus:ring-offset-2 rounded">
                Community
              </a>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
