import { ReactNode } from 'react';
import { Navigation } from './Navigation';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-gray-600">
              Solarpunk Mesh Network - A gift economy for resilient communities
            </p>
            <div className="flex items-center gap-6 text-sm text-gray-600">
              <a href="#" className="hover:text-solarpunk-600 transition-colors">
                About
              </a>
              <a href="#" className="hover:text-solarpunk-600 transition-colors">
                Documentation
              </a>
              <a href="#" className="hover:text-solarpunk-600 transition-colors">
                Community
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
