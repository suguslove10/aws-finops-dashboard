'use client';

import { Card, Title, Text } from '@tremor/react';
import { FaMoneyBillWave, FaCheckCircle } from 'react-icons/fa';
import { fetchCurrencies } from '@/lib/api';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface CurrencySelectorProps {
  selectedCurrency: string;
  onSelectCurrency: (currency: string) => void;
}

export function CurrencySelector({ selectedCurrency, onSelectCurrency }: CurrencySelectorProps) {
  const [currencies, setCurrencies] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [currencySymbols, setCurrencySymbols] = useState<Record<string, string>>({});

  useEffect(() => {
    const loadCurrencies = async () => {
      try {
        const data = await fetchCurrencies();
        setCurrencies(data.map(currency => currency.code));
        
        // Create a map of currency codes to symbols
        const symbolMap: Record<string, string> = {};
        data.forEach(currency => {
          symbolMap[currency.code] = currency.symbol;
        });
        setCurrencySymbols(symbolMap);
      } catch (error) {
        console.error('Failed to load currencies:', error);
      } finally {
        setLoading(false);
      }
    };

    loadCurrencies();
  }, []);

  return (
    <Card className="shadow-md border border-gray-200 dark:border-gray-700 transition-all duration-300 hover:shadow-lg">
      <div className="px-1 py-2">
        <div className="flex items-center mb-2">
          <div className="bg-gradient-to-br from-green-500/20 to-emerald-600/10 p-2 rounded-lg mr-3">
            <FaMoneyBillWave className="text-green-600 dark:text-green-400 text-xl" />
          </div>
          <div>
            <Title className="text-xl font-bold text-gray-900 dark:text-white">Currency</Title>
            {selectedCurrency && (
              <Text className="text-sm text-green-600 dark:text-green-400 font-medium">
                Selected: {selectedCurrency} {currencySymbols[selectedCurrency] || ''}
              </Text>
            )}
          </div>
        </div>
        <Text className="mt-2 mb-4 text-gray-600 dark:text-gray-300">
          Select the currency for cost data display
        </Text>
        
        {loading ? (
          <div className="animate-pulse h-10 bg-gray-200 dark:bg-gray-700 rounded-lg w-full"></div>
        ) : (
          <div className="grid grid-cols-4 gap-2">
            {currencies.map((currency) => (
              <div key={currency} className="relative">
                <button
                  onClick={() => onSelectCurrency(currency)}
                  className={`w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                    selectedCurrency === currency
                      ? 'bg-green-600 text-white dark:bg-green-700 border border-green-700 dark:border-green-600 shadow-md'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-green-50 dark:hover:bg-green-900/10'
                  }`}
                >
                  <div className="flex items-center justify-center">
                    {selectedCurrency === currency && (
                      <FaCheckCircle className="mr-1 text-white" />
                    )}
                    <span>{currency}</span>
                    {currencySymbols[currency] && (
                      <span className="ml-1 opacity-75">{currencySymbols[currency]}</span>
                    )}
                  </div>
                </button>
                
                {selectedCurrency === currency && (
                  <motion.div
                    layoutId="currencyHighlight"
                    style={{
                      position: 'absolute',
                      inset: 0,
                      borderRadius: '0.5rem',
                      border: '2px solid',
                      borderColor: 'rgb(34 197 94)',
                      pointerEvents: 'none'
                    }}
                    initial={false}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
} 