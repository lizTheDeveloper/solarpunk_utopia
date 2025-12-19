/**
 * Decoy Calculator - Appears as a normal calculator
 *
 * Secret gesture (e.g., "31337=") reveals real app.
 * This provides plausible deniability during phone inspection.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function DecoyCalculatorPage() {
  const navigate = useNavigate();
  const [display, setDisplay] = useState('0');
  const [secretGesture, setSecretGesture] = useState('31337=');
  const [inputBuffer, setInputBuffer] = useState('');

  useEffect(() => {
    // Fetch secret gesture from config
    fetchSecretGesture();
  }, []);

  const fetchSecretGesture = async () => {
    try {
      const res = await fetch('/api/panic/decoy-mode/config');
      if (res.ok) {
        const data = await res.json();
        if (data.secret_gesture) {
          setSecretGesture(data.secret_gesture);
        }
      }
    } catch (err) {
      // Fail silently - use default
    }
  };

  const handleButtonClick = (value: string) => {
    // Track input for secret gesture detection
    const newBuffer = inputBuffer + value;
    setInputBuffer(newBuffer);

    // Check if secret gesture was entered
    if (newBuffer.endsWith(secretGesture)) {
      // Reveal real app
      navigate('/');
      return;
    }

    // Keep buffer limited to prevent memory issues
    if (newBuffer.length > 20) {
      setInputBuffer(newBuffer.slice(-20));
    }

    // Normal calculator logic
    if (value === 'C') {
      setDisplay('0');
      setInputBuffer('');
    } else if (value === '=') {
      try {
        // Safe eval: only allow numbers and basic operators
        const sanitized = display.replace(/[^0-9+\-*/().]/g, '');
        const result = eval(sanitized);
        setDisplay(String(result));
      } catch {
        setDisplay('Error');
      }
    } else if (value === '←') {
      setDisplay(display.length > 1 ? display.slice(0, -1) : '0');
    } else {
      setDisplay(display === '0' ? value : display + value);
    }
  };

  const buttons = [
    ['7', '8', '9', '/'],
    ['4', '5', '6', '*'],
    ['1', '2', '3', '-'],
    ['C', '0', '=', '+'],
    ['(', ')', '.', '←']
  ];

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-sm">
        {/* Calculator Display */}
        <div className="bg-gray-800 text-white text-right p-4 rounded mb-4 text-3xl font-mono">
          {display}
        </div>

        {/* Calculator Buttons */}
        <div className="grid gap-2">
          {buttons.map((row, i) => (
            <div key={i} className="grid grid-cols-4 gap-2">
              {row.map((btn) => (
                <button
                  key={btn}
                  onClick={() => handleButtonClick(btn)}
                  className={`
                    p-4 rounded font-semibold text-lg
                    ${btn === '=' ? 'bg-blue-500 text-white hover:bg-blue-600' :
                      btn === 'C' ? 'bg-red-500 text-white hover:bg-red-600' :
                      'bg-gray-200 text-gray-800 hover:bg-gray-300'}
                    active:scale-95 transition-transform
                  `}
                >
                  {btn}
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* Hidden hint - only visible in source */}
        {/* Secret gesture: Type ${secretGesture} to reveal app */}
      </div>
    </div>
  );
}
