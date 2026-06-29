import React, { useState } from "react";
import {
  ThemeProvider,
  CssBaseline,
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
} from "@mui/material";
import CalculateIconRaw from "@mui/icons-material/Calculate";
import AccountTreeIconRaw from "@mui/icons-material/AccountTree";
import BusinessIconRaw from "@mui/icons-material/Business";
import ChatIconRaw from "@mui/icons-material/Chat";
import CloudUploadIconRaw from "@mui/icons-material/CloudUpload";

const CalculateIcon = (CalculateIconRaw as any).default || CalculateIconRaw;
const AccountTreeIcon = (AccountTreeIconRaw as any).default || AccountTreeIconRaw;
const BusinessIcon = (BusinessIconRaw as any).default || BusinessIconRaw;
const ChatIcon = (ChatIconRaw as any).default || ChatIconRaw;
const CloudUploadIcon = (CloudUploadIconRaw as any).default || CloudUploadIconRaw;

import { theme } from "./theme";
import { FileUploadZone } from "./components/FileUploadZone";
import { CalculatorPanel } from "./components/CalculatorPanel";
import { GraphExplorer } from "./components/GraphExplorer";
import { AskQwenPanel } from "./components/AskQwenPanel";
import { useStore } from "./store/useStore";
import { CircularProgress } from "@mui/material";

function App() {
  const [activeTab, setActiveTab] = useState(0); // 0: Chat, 1: Calculator, 2: Graph, 3: Ingest
  const { isProcessing } = useStore();

  const menuItems = [
    { label: "Regulatory AI Chat", icon: <ChatIcon /> },
    { label: "FSI Calculator", icon: <CalculateIcon /> },
    { label: "Knowledge Graph", icon: <AccountTreeIcon /> },
    { label: "Document Ingest", icon: <CloudUploadIcon /> },
  ];

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: "flex", height: "100vh", width: "100vw", overflow: "hidden", bgcolor: "background.default" }}>
        
        {/* Left Sidebar */}
        <Box
          sx={{
            width: 280,
            flexShrink: 0,
            bgcolor: "rgba(15, 23, 42, 0.95)",
            borderRight: "1px solid rgba(148, 163, 184, 0.08)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            zIndex: 1100,
          }}
        >
          <Box>
            {/* Sidebar Logo Header */}
            <Box sx={{ p: 3, display: "flex", alignItems: "center", gap: 1.5 }}>
              <BusinessIcon color="primary" sx={{ fontSize: 28 }} />
              <Typography
                variant="h6"
                sx={{
                  fontFamily: "Outfit, sans-serif",
                  fontWeight: 800,
                  letterSpacing: "-0.02em",
                  color: "text.primary",
                }}
              >
                DCPR <span style={{ color: "#6366f1" }}>Base</span>
              </Typography>
            </Box>
            <Divider sx={{ borderColor: "rgba(148, 163, 184, 0.08)" }} />

            {/* Navigation Menu */}
            <List sx={{ px: 1.5, py: 2 }}>
              {menuItems.map((item, idx) => (
                <ListItem key={item.label} disablePadding sx={{ mb: 1 }}>
                  <ListItemButton
                    selected={activeTab === idx}
                    onClick={() => setActiveTab(idx)}
                    sx={{
                      borderRadius: "10px",
                      py: 1.25,
                      px: 2,
                      color: activeTab === idx ? "primary.light" : "text.secondary",
                      bgcolor: activeTab === idx ? "rgba(99, 102, 241, 0.08)" : "transparent",
                      "&.Mui-selected": {
                        bgcolor: "rgba(99, 102, 241, 0.12)",
                        color: "primary.light",
                        "& .MuiListItemIcon-root": {
                          color: "primary.light",
                        },
                      },
                      "&:hover": {
                        bgcolor: "rgba(148, 163, 184, 0.04)",
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 40,
                        color: activeTab === idx ? "primary.light" : "text.secondary",
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{
                        fontWeight: activeTab === idx ? 700 : 500,
                        fontSize: "0.95rem",
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Box>

          {/* Sidebar Footer */}
          <Box sx={{ p: 3, borderTop: "1px solid rgba(148, 163, 184, 0.08)" }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5, fontWeight: 500 }}>
              Mumbai DCPR 2034 Platform
            </Typography>
            <Typography variant="caption" color="text.disabled" sx={{ fontSize: "0.7rem" }}>
              Pre-loaded with CKM Regulations 30-32 & Scheme 33(9).
            </Typography>
          </Box>
        </Box>

        {/* Main Work Area */}
        <Box sx={{ flexGrow: 1, height: "100%", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          
          {/* Top Navbar */}
          <Box
            sx={{
              height: 64,
              borderBottom: "1px solid rgba(148, 163, 184, 0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              px: 4,
              bgcolor: "background.paper",
            }}
          >
            <Typography variant="subtitle1" sx={{ fontWeight: 700, fontFamily: "Outfit, sans-serif" }}>
              {menuItems[activeTab].label}
            </Typography>
            <Typography variant="caption" sx={{ bgcolor: "rgba(99, 102, 241, 0.1)", color: "primary.light", px: 2, py: 0.5, borderRadius: "20px", fontWeight: 650 }}>
              Sandbox Mode (Live Neo4j Connect)
            </Typography>
          </Box>

          {/* Content Pane */}
          <Box sx={{ flexGrow: 1, overflow: "auto", position: "relative" }}>
            {activeTab === 0 && <AskQwenPanel />}
            {activeTab === 1 && <Box sx={{ p: 4 }}><CalculatorPanel /></Box>}
            {activeTab === 2 && <GraphExplorer />}
            {activeTab === 3 && <Box sx={{ p: 4, maxWidth: 800, margin: "0 auto" }}><FileUploadZone /></Box>}
          </Box>
        </Box>

        {/* Persistent Ingestion Spinner Alert */}
        {isProcessing && (
          <Box
            sx={{
              position: "fixed",
              bottom: 24,
              right: 24,
              zIndex: 2000,
              display: "flex",
              alignItems: "center",
              gap: 2,
              bgcolor: "rgba(30, 41, 59, 0.9)",
              backdropFilter: "blur(12px)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              borderRadius: "16px",
              boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
              p: 2.5,
              maxWidth: 400,
              animation: "slideIn 0.3s ease-out",
              "@keyframes slideIn": {
                "0%": { transform: "translateY(50px)", opacity: 0 },
                "100%": { transform: "translateY(0)", opacity: 1 },
              },
            }}
          >
            <CircularProgress size={28} color="secondary" />
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "secondary.light" }}>
                Ingesting Regulatory Corpus
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                Parsing page layouts, running OCR tables, and building the Neo4j knowledge graph in the background...
              </Typography>
            </Box>
          </Box>
        )}

      </Box>
    </ThemeProvider>
  );
}

export default App;
