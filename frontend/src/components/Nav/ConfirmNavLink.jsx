// src/components/Nav/ConfirmNavLink.jsx
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useScan } from "../../context/ScanContext";

export default function ConfirmNavLink({ to, children, ...rest }) {
  const { scanRunning } = useScan();
  const navigate = useNavigate();

  const handleClick = (e) => {
    if (scanRunning) {
      e.preventDefault();
      const ok = window.confirm("A scan is running. If you leave the page the scan may be interrupted. Continue?");
      if (ok) navigate(to);
    }
    // otherwise default Link behavior will navigate
  };

  return (
    <Link to={to} onClick={handleClick} {...rest}>
      {children}
    </Link>
  );
}
