'use client';

import { Card, Title, Text } from '@tremor/react';
import { FaMoneyBillWave } from 'react-icons/fa';
import { fetchCurrencies } from '@/lib/api';
import { useEffect, useState } from 'react';

interface CurrencySelectorProps {
  selectedCurrency: string;
  onSelectCurrency: (currency: string) => void;
}

export function CurrencySelector({ selectedCurrency, onSelectCurrency }: CurrencySelectorProps) {
  const [currencies, setCurrencies] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCurrencies = async () => {
      try {
        const data = await fetchCurrencies();
        setCurrencies(data.map(currency => currency.code));
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
          <Title className="text-xl font-bold text-gray-900 dark:text-white">Currency</Title>
        </div>
        <Text className="mt-2 mb-4 text-gray-600 dark:text-gray-300">
          Select the currency for cost data display
        </Text>
        
        {loading ? (
          <div className="animate-pulse h-10 bg-gray-200 dark:bg-gray-700 rounded-lg w-full"></div>
        ) : (
          <div className="grid grid-cols-4 gap-2">
            {currencies.map((currency) => (
              <button
                key={currency}
                onClick={() => onSelectCurrency(currency)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                  selectedCurrency === currency
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border border-green-200 dark:border-green-800/50'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-green-50 dark:hover:bg-green-900/10'
                }`}
              >
                {currency}
              </button>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
} 