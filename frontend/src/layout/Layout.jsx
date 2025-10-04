// src/layout/Layout.jsx  (update your existing Layout file)
import React from "react";
import Navbar from "./Navbar";
import Footer from "./Footer";
import "../styles/layout.css";
import GameModal from "../components/Game/GameModal"; // <-- new

const Layout = ({ children }) => {
  return (
    <div className="layout-wrapper">
      <Navbar />
      <main className="layout-main">
        {children}
      </main>
      <Footer />
      <GameModal /> {/* present on every page (will only appear when a scan starts) */}
    </div>
  );
};

export default Layout;
