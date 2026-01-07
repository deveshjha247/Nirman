import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { walletAPI } from '../lib/api';
import Sidebar from '../components/Sidebar';

const Wallet = () => {
  const { user, refreshUser } = useAuth();
  const [wallet, setWallet] = useState({ balance: 0, transactions: [], stats: {} });
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [selectedMethod, setSelectedMethod] = useState('auto');
  const [activeTab, setActiveTab] = useState('overview');
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawForm, setWithdrawForm] = useState({
    amount: '',
    bank_account: '',
    ifsc_code: '',
    account_holder: '',
    upi_id: ''
  });
  const [withdrawals, setWithdrawals] = useState([]);

  useEffect(() => {
    fetchWallet();
    fetchPaymentMethods();
    fetchWithdrawals();
  }, []);

  const fetchWallet = async () => {
    try {
      const response = await walletAPI.getWallet();
      setWallet(response.data);
    } catch (error) {
      console.error('Failed to fetch wallet:', error);
    }
  };

  const fetchPaymentMethods = async () => {
    try {
      const response = await walletAPI.getPaymentMethods();
      setPaymentMethods(response.data.methods || []);
      setSelectedMethod(response.data.default || 'auto');
    } catch (error) {
      console.error('Failed to fetch payment methods:', error);
    }
  };

  const fetchWithdrawals = async () => {
    try {
      const response = await walletAPI.getWithdrawals();
      setWithdrawals(response.data.withdrawals || []);
    } catch (error) {
      console.error('Failed to fetch withdrawals:', error);
    }
  };

  const quickAmounts = [100, 500, 1000, 2000, 5000];

  const addMoney = async (e) => {
    e.preventDefault();
    const amountValue = parseFloat(amount);
    if (!amountValue || amountValue < 10) {
      alert('Minimum amount is ₹10');
      return;
    }
    if (amountValue > 100000) {
      alert('Maximum amount is ₹1,00,000');
      return;
    }
    
    setLoading(true);
    try {
      const response = await walletAPI.addMoney(amountValue, selectedMethod);
      
      if (response.data.status === 'success') {
        alert(`₹${amountValue} added to wallet!`);
        fetchWallet();
        refreshUser();
        setAmount('');
      } else if (response.data.status === 'order_created') {
        // Handle payment gateway redirect
        if (response.data.payment_method === 'razorpay') {
          handleRazorpayPayment(response.data);
        } else if (response.data.payment_method === 'cashfree') {
          handleCashfreePayment(response.data);
        }
      } else if (response.data.demo_mode) {
        alert('Demo Mode: Money added directly. Configure payment gateway for real payments.');
        fetchWallet();
        refreshUser();
        setAmount('');
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to add money');
    } finally {
      setLoading(false);
    }
  };

  const handleRazorpayPayment = (orderData) => {
    if (!window.Razorpay) {
      alert('Razorpay SDK not loaded. Please refresh and try again.');
      return;
    }

    const options = {
      key: orderData.key_id,
      amount: orderData.amount * 100,
      currency: orderData.currency,
      name: orderData.name,
      description: orderData.description,
      order_id: orderData.order_id,
      prefill: orderData.prefill,
      handler: async function (response) {
        try {
          await walletAPI.verifyRazorpay(
            response.razorpay_order_id,
            response.razorpay_payment_id,
            response.razorpay_signature
          );
          alert('Payment successful! Wallet credited.');
          fetchWallet();
          refreshUser();
          setAmount('');
        } catch (error) {
          alert('Payment verification failed. Contact support.');
        }
      },
      theme: {
        color: '#7c3aed'
      }
    };

    const rzp = new window.Razorpay(options);
    rzp.open();
  };

  const handleCashfreePayment = (orderData) => {
    // Cashfree checkout handling
    alert('Redirecting to Cashfree payment...');
    // In production, use Cashfree JS SDK
  };

  const requestWithdrawal = async (e) => {
    e.preventDefault();
    const withdrawAmount = parseFloat(withdrawForm.amount);
    
    if (withdrawAmount < 100) {
      alert('Minimum withdrawal is ₹100');
      return;
    }
    if (withdrawAmount > wallet.balance) {
      alert('Insufficient balance');
      return;
    }
    if (!withdrawForm.bank_account || !withdrawForm.ifsc_code || !withdrawForm.account_holder) {
      alert('Please fill all bank details');
      return;
    }

    setLoading(true);
    try {
      const response = await walletAPI.withdraw(
        withdrawAmount,
        withdrawForm.bank_account,
        withdrawForm.ifsc_code,
        withdrawForm.account_holder,
        withdrawForm.upi_id
      );
      
      alert(response.data.message || 'Withdrawal request submitted!');
      setShowWithdrawModal(false);
      setWithdrawForm({ amount: '', bank_account: '', ifsc_code: '', account_holder: '', upi_id: '' });
      fetchWallet();
      fetchWithdrawals();
      refreshUser();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to submit withdrawal request');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-400/10';
      case 'pending': return 'text-yellow-400 bg-yellow-400/10';
      case 'rejected': 
      case 'refunded': return 'text-red-400 bg-red-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 flex">
      <Sidebar active="wallet" />
      
      <main className="flex-1 p-8 overflow-auto">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <span className="text-4xl">💰</span>
              Wallet
            </h1>
            <p className="text-gray-600 mt-1">Manage your credits, payments, and withdrawals</p>
          </div>

          {/* Balance Cards */}
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            {/* Main Balance */}
            <div className="md:col-span-2 bg-gradient-to-r from-violet-600 to-purple-600 rounded-2xl p-6 text-white">
              <p className="text-white/70 mb-1">Available Balance</p>
              <h2 className="text-4xl font-bold mb-4">₹{wallet.balance?.toFixed(2) || '0.00'}</h2>
              <div className="flex gap-4">
                <button
                  onClick={() => setActiveTab('add')}
                  className="px-4 py-2 bg-white text-violet-600 rounded-xl font-medium hover:bg-white/90 transition-all"
                >
                  + Add Money
                </button>
                <button
                  onClick={() => setShowWithdrawModal(true)}
                  className="px-4 py-2 bg-white/20 text-white rounded-xl font-medium hover:bg-white/30 transition-all"
                >
                  Withdraw
                </button>
              </div>
            </div>

            {/* Stats */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6">
              <h3 className="text-sm font-medium text-gray-500 mb-4">Statistics</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Credited</span>
                  <span className="font-semibold text-green-600">₹{wallet.stats?.total_credited?.toFixed(2) || '0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Spent</span>
                  <span className="font-semibold text-red-600">₹{wallet.stats?.total_spent?.toFixed(2) || '0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Transactions</span>
                  <span className="font-semibold">{wallet.stats?.transaction_count || 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 border-b border-gray-200">
            {['overview', 'add', 'withdrawals'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 font-medium capitalize transition-all border-b-2 -mb-[2px] ${
                  activeTab === tab
                    ? 'text-violet-600 border-violet-600'
                    : 'text-gray-500 border-transparent hover:text-gray-700'
                }`}
              >
                {tab === 'add' ? 'Add Money' : tab}
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="bg-white border border-gray-200 rounded-2xl">
              <div className="p-6 border-b border-gray-100">
                <h3 className="text-lg font-semibold">Transaction History</h3>
              </div>
              <div className="divide-y divide-gray-100">
                {wallet.transactions?.length === 0 ? (
                  <div className="p-12 text-center">
                    <span className="text-5xl mb-4 block">📭</span>
                    <p className="text-gray-500">No transactions yet</p>
                    <button
                      onClick={() => setActiveTab('add')}
                      className="mt-4 px-4 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700"
                    >
                      Add Money to Get Started
                    </button>
                  </div>
                ) : (
                  wallet.transactions?.map((tx, i) => (
                    <div key={tx.id || i} className="flex items-center justify-between p-4 hover:bg-gray-50">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          tx.type === 'credit' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                        }`}>
                          {tx.type === 'credit' ? '↓' : '↑'}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{tx.description}</p>
                          <div className="flex gap-2 items-center">
                            <p className="text-sm text-gray-500">{new Date(tx.created_at).toLocaleString()}</p>
                            {tx.category && (
                              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full capitalize">
                                {tx.category}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className={`font-semibold ${tx.type === 'credit' ? 'text-green-600' : 'text-red-600'}`}>
                        {tx.type === 'credit' ? '+' : '-'}₹{tx.amount?.toFixed(2)}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Add Money Tab */}
          {activeTab === 'add' && (
            <div className="bg-white border border-gray-200 rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-6">Add Money to Wallet</h3>
              
              {/* Quick Amount Buttons */}
              <div className="mb-6">
                <label className="text-sm font-medium text-gray-700 mb-3 block">Quick Add</label>
                <div className="flex flex-wrap gap-3">
                  {quickAmounts.map(amt => (
                    <button
                      key={amt}
                      onClick={() => setAmount(amt.toString())}
                      className={`px-4 py-2 rounded-xl border-2 font-medium transition-all ${
                        amount === amt.toString()
                          ? 'border-violet-600 bg-violet-50 text-violet-600'
                          : 'border-gray-200 hover:border-gray-300 text-gray-700'
                      }`}
                    >
                      ₹{amt}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Amount */}
              <form onSubmit={addMoney} className="space-y-6">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">Enter Amount</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-xl">₹</span>
                    <input
                      type="number"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      placeholder="Enter amount"
                      min="10"
                      max="100000"
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl text-xl focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                    />
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Min ₹10 • Max ₹1,00,000</p>
                </div>

                {/* Payment Methods */}
                {paymentMethods.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-3 block">Payment Method</label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {paymentMethods.map(method => (
                        <button
                          key={method.id}
                          type="button"
                          onClick={() => setSelectedMethod(method.id)}
                          className={`p-4 rounded-xl border-2 text-left transition-all ${
                            selectedMethod === method.id
                              ? 'border-violet-600 bg-violet-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <span className="text-2xl">{method.icon}</span>
                          <p className="font-medium mt-1">{method.name}</p>
                          <p className="text-xs text-gray-500">{method.description}</p>
                          {method.recommended && (
                            <span className="inline-block mt-2 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                              Recommended
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading || !amount}
                  className="w-full py-4 bg-violet-600 text-white rounded-xl font-semibold hover:bg-violet-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <span className="animate-spin">⏳</span>
                      Processing...
                    </>
                  ) : (
                    <>Add ₹{amount || '0'} to Wallet</>
                  )}
                </button>
              </form>

              {/* Info */}
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
                <p className="text-sm text-blue-800">
                  <strong>💡 Tip:</strong> Wallet balance can be used for plan purchases, AI credits, and other services on Nirman.
                </p>
              </div>
            </div>
          )}

          {/* Withdrawals Tab */}
          {activeTab === 'withdrawals' && (
            <div className="bg-white border border-gray-200 rounded-2xl">
              <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                <h3 className="text-lg font-semibold">Withdrawal History</h3>
                <button
                  onClick={() => setShowWithdrawModal(true)}
                  className="px-4 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700"
                >
                  New Withdrawal
                </button>
              </div>
              <div className="divide-y divide-gray-100">
                {withdrawals.length === 0 ? (
                  <div className="p-12 text-center">
                    <span className="text-5xl mb-4 block">🏦</span>
                    <p className="text-gray-500">No withdrawal requests yet</p>
                  </div>
                ) : (
                  withdrawals.map((w) => (
                    <div key={w.id} className="flex items-center justify-between p-4 hover:bg-gray-50">
                      <div>
                        <p className="font-medium text-gray-900">₹{w.amount} to {w.bank_account}</p>
                        <p className="text-sm text-gray-500">{new Date(w.created_at).toLocaleString()}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${getStatusColor(w.status)}`}>
                        {w.status}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Withdraw Modal */}
      {showWithdrawModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md overflow-hidden">
            <div className="p-6 border-b border-gray-100 flex justify-between items-center">
              <h2 className="text-xl font-semibold">Withdraw to Bank</h2>
              <button
                onClick={() => setShowWithdrawModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                ✕
              </button>
            </div>
            <form onSubmit={requestWithdrawal} className="p-6 space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Amount (₹)</label>
                <input
                  type="number"
                  value={withdrawForm.amount}
                  onChange={(e) => setWithdrawForm({...withdrawForm, amount: e.target.value})}
                  placeholder="Minimum ₹100"
                  min="100"
                  max={wallet.balance}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Available: ₹{wallet.balance?.toFixed(2)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Account Holder Name</label>
                <input
                  type="text"
                  value={withdrawForm.account_holder}
                  onChange={(e) => setWithdrawForm({...withdrawForm, account_holder: e.target.value})}
                  placeholder="As per bank records"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500"
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Bank Account Number</label>
                <input
                  type="text"
                  value={withdrawForm.bank_account}
                  onChange={(e) => setWithdrawForm({...withdrawForm, bank_account: e.target.value})}
                  placeholder="Enter account number"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500"
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">IFSC Code</label>
                <input
                  type="text"
                  value={withdrawForm.ifsc_code}
                  onChange={(e) => setWithdrawForm({...withdrawForm, ifsc_code: e.target.value.toUpperCase()})}
                  placeholder="e.g., SBIN0001234"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500"
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">UPI ID (Optional)</label>
                <input
                  type="text"
                  value={withdrawForm.upi_id}
                  onChange={(e) => setWithdrawForm({...withdrawForm, upi_id: e.target.value})}
                  placeholder="yourname@upi"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500"
                />
              </div>
              
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  ⏱️ Withdrawals are processed within 3-5 business days
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-violet-600 text-white rounded-xl font-semibold hover:bg-violet-700 disabled:opacity-50"
              >
                {loading ? 'Processing...' : 'Submit Withdrawal Request'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Wallet;
