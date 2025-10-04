import React from "react";
import { Link } from "react-router-dom";
import "../../styles/home.css";

// Use icons appropriate for scanners — you can replace these with new icons later
import NetworkIcon from "../../assets/networkIcon.png";
import WebsiteIcon from "../../assets/domainIcon.png";
import WebAppIcon from "../../assets/webappIcon.png";
import APIIcon from "../../assets/apiIcon.png";
import SSLIcon from "../../assets/sslIcon.png";
import OTlogo from "/Users/darshitayar/Desktop/VaptManagement /frontend/src/assets/OTlogo.jpg";

const Home = () => {
  return (
    <div className="home-container">
      <h1 className="dashboard-title">
        Welcome to <span className="highlight">TrustGrid</span>
      </h1>
      <p className="dashboard-subtitle">Your all-in-one security scanning dashboard</p>

      <div className="tile-grid">
        {/* Leftmost */}
        <Link to="/webappscanner" className="tile tile-1">
          <img src={WebAppIcon} alt="WebApp Scanner" className="tile-icon" />
          <h3>Webapp scanning</h3>
          <p>Probe web apps for vulnerabilities, misconfigurations, and insecure workflows.</p>
        </Link>

        {/* Left-mid */}
        <Link to="/domainscanner" className="tile tile-2">  
          <img src={WebsiteIcon} alt="Website Scanner" className="tile-icon" />
          <h3>Domain scanning</h3>
          <p>Scan domains for vulnerabilities, malware, and misconfigurations.</p>
        </Link>

        {/* Center */}
        <Link to="/networkscanner" className="tile tile-3">
          <img src={NetworkIcon} alt="network Scanner" className="tile-icon" />
          <h3>Network scanning</h3>
          <p>Discover devices, open ports, and network vulnerabilities.</p>
        </Link>

        {/* Right-mid */}
        <Link to="/APIScanner" className="tile tile-4">
          <img src={APIIcon} alt="API Scanner" className="tile-icon" />
          <h3>API scanning</h3>
          <p>Check endpoints and data flows for vulnerabilities, misconfigurations, and leaks.</p>
        </Link>

        {/* Rightmost */}
        <Link to="/sslscanner" className="tile tile-5">
          <img src={SSLIcon} alt="SSL/TLS Scanner" className="tile-icon" />
          <h3>SSL/TLS scanning</h3>
          <p>Inspect secure connections for flaws or threats.</p>
        </Link>
      </div>

      <div className="author-section">
        <p>
          Crafted by <span className="author-name"><img src={OTlogo} className="hasehase" alt="Orange" /></span>
          <h2 className="hase">Orange TechnoLab Pvt. Ltd.</h2>
        </p>
      </div>
    </div>
  );
};

export default Home;
