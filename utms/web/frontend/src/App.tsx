import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout/Layout';
import { Variables } from './pages/Variables/Variables';
import { Config } from './pages/Config/Config';
import { Units } from './pages/Units/Units';
import { Anchors } from './pages/Anchors/Anchors';
import { Resolve } from './pages/Resolve/Resolve';
import { anchorsApi } from './api/anchorsApi';
import { Anchor } from './types/anchors';
import { Dashboard } from './pages/Dashboard/Dashboard';



function App() {
    const [anchorsData, setAnchorsData] = useState<Record<string, Anchor>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);


    useEffect(() => {
	loadAnchors();
    }, []);

    const loadAnchors = async () => {
	try {
	    setLoading(true);
            setError(null);
	    const data = await anchorsApi.getAnchors();
	    setAnchorsData(data);
	    setError(null);
	} catch (err) {
	    setError('Failed to load anchors data');
	    console.error('Error loading anchors:', err);
	} finally {
	    setLoading(false);
	}
    };

    if (loading) {
	return <div style={{ padding: '20px' }}>Loading...</div>;
    }

    if (error) {
	return <div style={{ padding: '20px', color: 'red' }}>{error}</div>;
    }

    return (
	<Router>
	    <Routes>
            {/* Redirect root to variables for now */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            <Route path="/dashboard" element={
		<Layout activePage="dashboard">
		    <Dashboard />
		    </Layout>
            } />
            
            <Route path="/variables" element={
		<Layout activePage="variables">
		    <Variables />
		    </Layout>
            } />
            
            <Route path="/config" element={
		<Layout activePage="config">
		    <Config />
		    </Layout>
            } />
            <Route path="/units" element={
		<Layout activePage="units">
		    <Units />
		    </Layout>
            } />
            <Route path="/anchors" element={
		<Layout activePage="anchors">
		    <Anchors />
		    </Layout>
            } />
            <Route path="/clock" element={
		<Layout activePage="clock">
		    <div>Clock Page (Coming Soon)</div>
		    </Layout>
            } />
            <Route path="/calendar" element={
		<Layout activePage="calendar">
		    <div>Calendar Page (Coming Soon)</div>
		    </Layout>
            } />
            <Route path="/resolve" element={
		<Layout activePage="resolve">
		    <Resolve anchors={anchorsData} />
		    </Layout>
            } />
            <Route path="/events" element={
		<Layout activePage="events">
		    <div>Events Page (Coming Soon)</div>
		    </Layout>
            } />
            <Route path="/analytics" element={
		<Layout activePage="analytics">
		    <div>Analytics Page (Coming Soon)</div>
		    </Layout>
            } />
	    </Routes>
	    </Router>
    );
}

export default App;
