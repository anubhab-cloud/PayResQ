import React, { useState, useEffect } from 'react';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { TransactionDetailPage } from './pages/TransactionDetailPage';
import { RecoveriesPage } from './pages/RecoveriesPage';
import { IntelligencePage } from './pages/IntelligencePage';
import { AuditPage } from './pages/AuditPage';
import { DemoRunResponse } from './types';

export const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>('/');
  const [selectedTxId, setSelectedTxId] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState<boolean>(true);

  // Apply dark class to document root
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const handleNavigate = (path: string) => {
    setCurrentPath(path);
    setSelectedTxId(null);
  };

  const handleSelectTransaction = (id: string) => {
    setSelectedTxId(id);
  };

  const handleDemoCompleted = (demoResult: DemoRunResponse) => {
    // Navigate to transaction detail for the demo transaction
    setSelectedTxId(demoResult.transaction_id);
    setCurrentPath('/transactions');
  };

  const renderContent = () => {
    if (selectedTxId) {
      return (
        <TransactionDetailPage
          transactionId={selectedTxId}
          onBack={() => setSelectedTxId(null)}
        />
      );
    }

    switch (currentPath) {
      case '/':
        return <DashboardPage onSelectTransaction={handleSelectTransaction} />;
      case '/transactions':
        return <TransactionsPage onSelectTransaction={handleSelectTransaction} />;
      case '/recoveries':
        return <RecoveriesPage onSelectTransaction={handleSelectTransaction} />;
      case '/intelligence':
        return <IntelligencePage />;
      case '/audit':
        return <AuditPage />;
      default:
        return <DashboardPage onSelectTransaction={handleSelectTransaction} />;
    }
  };

  return (
    <AppShell
      currentPath={currentPath}
      onNavigate={handleNavigate}
      darkMode={darkMode}
      onToggleTheme={() => setDarkMode(!darkMode)}
      onDemoCompleted={handleDemoCompleted}
    >
      {renderContent()}
    </AppShell>
  );
};

export default App;
