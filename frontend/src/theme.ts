import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#6366f1", // Sleek Indigo
      light: "#818cf8",
      dark: "#4f46e5",
      contrastText: "#ffffff",
    },
    secondary: {
      main: "#14b8a6", // Vibrant Teal
      light: "#2dd4bf",
      dark: "#0f766e",
      contrastText: "#ffffff",
    },
    background: {
      default: "#0f172a", // Deep slate background
      paper: "#1e293b",   // Elevated card background
    },
    text: {
      primary: "#f8fafc",
      secondary: "#94a3b8",
    },
    error: {
      main: "#f43f5e", // Smooth Rose
    },
    warning: {
      main: "#f59e0b", // Warm Amber
    },
    success: {
      main: "#10b981", // Emerald Green
    },
  },
  typography: {
    fontFamily: [
      "Outfit",
      "Inter",
      "-apple-system",
      "BlinkMacSystemFont",
      '"Segoe UI"',
      "Roboto",
      '"Helvetica Neue"',
      "Arial",
      "sans-serif",
    ].join(","),
    h1: {
      fontWeight: 800,
      letterSpacing: "-0.025em",
    },
    h4: {
      fontWeight: 700,
      letterSpacing: "-0.015em",
    },
    h6: {
      fontWeight: 600,
    },
    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: "8px",
          padding: "8px 16px",
          transition: "all 0.2s ease-in-out",
          "&:hover": {
            transform: "translateY(-1px)",
            boxShadow: "0 4px 12px rgba(99, 102, 241, 0.25)",
          },
        },
        containedSecondary: {
          "&:hover": {
            boxShadow: "0 4px 12px rgba(20, 184, 166, 0.25)",
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          border: "1px solid rgba(148, 163, 184, 0.08)",
          boxShadow: "0 4px 20px 0 rgba(0, 0, 0, 0.3)",
          backdropFilter: "blur(8px)",
          borderRadius: "16px",
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: "1px solid rgba(148, 163, 184, 0.08)",
        },
        head: {
          fontWeight: 600,
          backgroundColor: "rgba(15, 23, 42, 0.4)",
        },
      },
    },
  },
});
