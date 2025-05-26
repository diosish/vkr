// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import EventsPage from './pages/EventsPage';
import EventDetailsPage from './pages/EventDetailsPage';
import MyRegistrationsPage from './pages/MyRegistrationsPage';
import ManageEventsPage from './pages/ManageEventsPage';
import CreateEventPage from './pages/CreateEventPage';
import AdminPanelPage from './pages/AdminPanelPage';
import RegisterPage from './pages/RegisterPage';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/events/:id" element={<EventDetailsPage />} />
            <Route path="/my-registrations" element={<MyRegistrationsPage />} />
            <Route path="/manage-events" element={<ManageEventsPage />} />
            <Route path="/create-event" element={<CreateEventPage />} />
            <Route path="/admin" element={<AdminPanelPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Routes>
        </Layout>
      </AuthProvider>
    </Router>
  );
}

export default App;