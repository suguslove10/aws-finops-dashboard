'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FaAws, FaChartLine, FaHistory, FaCloudDownloadAlt, FaTimes } from 'react-icons/fa';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

export function Header() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const isActive = (path: string) => {
    return pathname === path;
  };
  
  return (
    <header className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-800 text-white shadow-md sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3 group">
            <motion.div 
              whileHover={{ rotate: 10, scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="bg-white p-2 rounded-lg shadow-md"
            >
              <FaAws className="text-2xl text-blue-700" />
            </motion.div>
            <div>
              <h1 className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-blue-100">AWS FinOps Dashboard</h1>
              <p className="text-xs text-blue-200 font-light">Cost Optimization & Resource Management</p>
            </div>
          </Link>
          
          <nav className="hidden md:block">
            <ul className="flex space-x-6">
              <li>
                <Link 
                  href="/"
                  className={`flex items-center space-x-2 py-2 px-4 rounded-full transition-all duration-300 ${
                    isActive('/') 
                      ? 'bg-white/15 text-white font-medium backdrop-blur-sm shadow-sm' 
                      : 'hover:bg-white/10 text-blue-100 hover:text-white'
                  }`}
                >
                  <FaChartLine className="text-blue-200" />
                  <span>Dashboard</span>
                </Link>
              </li>
              <li>
                <Link 
                  href="/previous-results"
                  className={`flex items-center space-x-2 py-2 px-4 rounded-full transition-all duration-300 ${
                    isActive('/previous-results') 
                      ? 'bg-white/15 text-white font-medium backdrop-blur-sm shadow-sm' 
                      : 'hover:bg-white/10 text-blue-100 hover:text-white'
                  }`}
                >
                  <FaHistory className="text-blue-200" />
                  <span>Previous Results</span>
                </Link>
              </li>
            </ul>
          </nav>
          
          <motion.button 
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
            aria-label="Toggle mobile menu"
          >
            {isMobileMenuOpen ? (
              <FaTimes className="h-6 w-6" />
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </motion.button>
        </div>
        
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.nav 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="md:hidden mt-4 pb-2"
            >
              <ul className="flex flex-col space-y-2">
                <motion.li
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.1 }}
                >
                  <Link 
                    href="/"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center space-x-3 py-3 px-4 rounded-lg ${
                      isActive('/') 
                        ? 'bg-white/15 text-white font-medium' 
                        : 'text-blue-100'
                    }`}
                  >
                    <FaChartLine className="text-lg" />
                    <span>Dashboard</span>
                  </Link>
                </motion.li>
                <motion.li
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <Link 
                    href="/previous-results"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center space-x-3 py-3 px-4 rounded-lg ${
                      isActive('/previous-results') 
                        ? 'bg-white/15 text-white font-medium' 
                        : 'text-blue-100'
                    }`}
                  >
                    <FaHistory className="text-lg" />
                    <span>Previous Results</span>
                  </Link>
                </motion.li>
              </ul>
            </motion.nav>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
} 