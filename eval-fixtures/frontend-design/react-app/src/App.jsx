// Orbit dashboard shell. The header's project switcher is still a placeholder.
export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <span className="logo">Orbit</span>
        {/* TODO: project switcher (button that opens a menu of projects) */}
      </header>
      <main className="app-main">
        <h1>Overview</h1>
        <p>Pick a project to see its deploys.</p>
      </main>
    </div>
  );
}
