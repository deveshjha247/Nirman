import React, { useState, useEffect } from 'react';

const CookieConsent = () => {
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('nirman-cookie-consent');
    if (!consent) {
      // Show banner after 1 second
      setTimeout(() => setShowBanner(true), 1000);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('nirman-cookie-consent', 'accepted');
    setShowBanner(false);
  };

  const handleDecline = () => {
    localStorage.setItem('nirman-cookie-consent', 'declined');
    setShowBanner(false);
  };

  if (!showBanner) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[100] p-4 md:p-6 animate-slide-up">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white/95 backdrop-blur-2xl border border-purple-100 rounded-3xl shadow-2xl shadow-purple-200/30 p-6 md:p-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-3xl">🍪</span>
                <h3 className="text-xl font-bold text-gray-900">We Value Your Privacy</h3>
              </div>
              <p className="text-gray-600 leading-relaxed">
                We use cookies to enhance your experience, analyze site traffic, and personalize content. 
                By clicking &quot;Accept All&quot;, you consent to our use of cookies. 
                <a href="/privacy" className="text-purple-600 hover:text-purple-700 font-medium ml-1 underline">
                  Learn more
                </a>
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={handleDecline}
                className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-all duration-200"
              >
                Decline
              </button>
              <button
                onClick={handleAccept}
                className="px-8 py-3 bg-gradient-to-r from-purple-600 to-violet-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-violet-700 transition-all duration-200 shadow-lg shadow-purple-300/50 hover:shadow-xl hover:scale-105"
              >
                Accept All
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CookieConsent;
