import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './components/Home';
import OratorChat from './pages/OratorChat';
import Meetings from './pages/Meetings';
import Settings from './pages/Settings';
import Transcribe from './pages/Transcribe';

function App() {
  return (
    <Router>
      <Layout>
        <Switch>
          <Route exact path="/" component={Home} />
          <Route path="/orator-chat" component={OratorChat} />
          <Route path="/meetings" component={Meetings} />
          <Route path="/settings" component={Settings} />
          <Route path="/transcribe" component={Transcribe} />
        </Switch>
      </Layout>
    </Router>
  );
}

export default App;
