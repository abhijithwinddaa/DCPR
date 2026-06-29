import React, { useState, useEffect, useRef } from "react";
import {
  Typography,
  Button,
  TextField,
  Box,
  Divider,
  CircularProgress,
  Alert,
  AlertTitle,
  Paper,
  IconButton,
  Chip,
  Select,
  MenuItem,
  FormControl,
  Avatar,
} from "@mui/material";
import PsychologyIconRaw from "@mui/icons-material/Psychology";
import ChatIconRaw from "@mui/icons-material/Chat";
import SendIconRaw from "@mui/icons-material/Send";
import InfoIconRaw from "@mui/icons-material/Info";
import AccountCircleIconRaw from "@mui/icons-material/AccountCircle";
import DescriptionIconRaw from "@mui/icons-material/Description";

const PsychologyIcon = (PsychologyIconRaw as any).default || PsychologyIconRaw;
const ChatIcon = (ChatIconRaw as any).default || ChatIconRaw;
const SendIcon = (SendIconRaw as any).default || SendIconRaw;
const InfoIcon = (InfoIconRaw as any).default || InfoIconRaw;
const AccountCircleIcon = (AccountCircleIconRaw as any).default || AccountCircleIconRaw;
const DescriptionIcon = (DescriptionIconRaw as any).default || DescriptionIconRaw;
import { useStore } from "../store/useStore";
import type { SourceChunk } from "../store/useStore";

interface ChatMessage {
  sender: "user" | "qwen";
  text: string;
  isFallback?: boolean;
  msgSources?: SourceChunk[];
}

// A simple, dependency-free Markdown renderer for clean styling
const renderSimpleMarkdown = (text: string) => {
  if (!text) return null;

  const lines = text.split("\n");
  return lines.map((line, idx) => {
    let cleanLine = line.trim();
    
    // Header check
    if (cleanLine.startsWith("### ")) {
      return (
        <Typography key={idx} variant="h6" sx={{ color: "primary.light", mt: 2, mb: 1, fontWeight: 700 }}>
          {cleanLine.substring(4)}
        </Typography>
      );
    }
    if (cleanLine.startsWith("## ")) {
      return (
        <Typography key={idx} variant="subtitle1" sx={{ color: "secondary.light", mt: 2, mb: 1, fontWeight: 700 }}>
          {cleanLine.substring(3)}
        </Typography>
      );
    }

    // Bullet point check
    if (cleanLine.startsWith("- ") || cleanLine.startsWith("* ")) {
      const content = cleanLine.substring(2);
      return (
        <Box key={idx} sx={{ display: "flex", ml: 2, mb: 0.5, alignItems: "flex-start" }}>
          <Typography sx={{ mr: 1, color: "secondary.main" }}>•</Typography>
          <Typography variant="body2" color="text.primary">
            {parseBoldText(content)}
          </Typography>
        </Box>
      );
    }

    // Numbered bullet point check
    if (/^\d+\.\s/.test(cleanLine)) {
      const match = cleanLine.match(/^(\d+\.\s)(.*)/);
      if (match) {
        return (
          <Box key={idx} sx={{ display: "flex", ml: 2, mb: 0.5, alignItems: "flex-start" }}>
            <Typography sx={{ mr: 1, color: "primary.main", fontWeight: 700 }}>{match[1]}</Typography>
            <Typography variant="body2" color="text.primary">
              {parseBoldText(match[2])}
            </Typography>
          </Box>
        );
      }
    }

    // Empty line check
    if (!cleanLine) {
      return <Box key={idx} sx={{ height: 8 }} />;
    }

    // Standard paragraph with bold parsing
    return (
      <Typography key={idx} variant="body2" sx={{ mb: 1, lineHeight: 1.6 }} color="text.primary">
        {parseBoldText(cleanLine)}
      </Typography>
    );
  });
};

// Parses **bold** strings inside text
const parseBoldText = (text: string) => {
  const parts = text.split(/\*\*(.*?)\*\*/g);
  if (parts.length === 1) return text;
  
  return parts.map((part, i) => {
    if (i % 2 === 1) {
      return (
        <Box component="span" key={i} sx={{ fontWeight: 750, color: "primary.light" }}>
          {part}
        </Box>
      );
    }
    return part;
  });
};

export const AskQwenPanel: React.FC = () => {
  const {
    calcResult,
    explanationText,
    isGeneratingExplanation,
    wasFallback,
    sources,
    documents,
    selectedDocId,
    setSelectedDocId,
    askDocumentQuestion,
  } = useStore();

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat feed
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGeneratingExplanation]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isGeneratingExplanation) return;

    const userQ = question;
    setQuestion("");
    
    // Add user message immediately
    setMessages((prev) => [...prev, { sender: "user", text: userQ }]);

    try {
      // Trigger RAG API query
      await askDocumentQuestion(userQ);
    } catch (err) {
      console.error(err);
    }
  };

  // Listen for engine response and append it
  useEffect(() => {
    if (explanationText && messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.sender === "user") {
        setMessages((prev) => [
          ...prev,
          { sender: "qwen", text: explanationText, isFallback: wasFallback, msgSources: sources },
        ]);
      }
    }
  }, [explanationText, wasFallback, sources]);

  const handleQuickQuestion = async (q: string) => {
    setMessages((prev) => [...prev, { sender: "user", text: q }]);
    await askDocumentQuestion(q);
  };

  const quickQuestions = [
    { title: "Scheme 33(9) Overview", desc: "What are the applicability criteria and FSI caps for Scheme 33(9)?", query: "Tell me about Scheme 33(9) requirements and FSI limits" },
    { title: "Regulation 30 Setbacks", desc: "What setbacks and open space margins are required for cluster plots?", query: "What does Regulation 30 say about margins and setbacks?" },
    { title: "Rehabilitation BUA calculation", desc: "How is MHADA-certified rehabilitation BUA used to calculate incentive BUA?", query: "How is rehabilitation BUA used in FSI calculations?" },
    { title: "Circular Upload Guide", desc: "How do I add custom circulars and amendments to the model?", query: "Guide me on how to upload new circulars to update the knowledge base" },
  ];

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "calc(100vh - 64px)", bgcolor: "background.default", overflow: "hidden" }}>
      
      {/* Top Header Selector Bar */}
      <Box sx={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)", px: { xs: 2, md: 8, lg: 16 }, py: 1.5, bgcolor: "background.paper", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <DescriptionIcon color="primary" fontSize="small" />
          <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "text.primary" }}>Target Document Scope:</Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <Select
            value={selectedDocId || "ALL"}
            onChange={(e) => setSelectedDocId(e.target.value === "ALL" ? null : e.target.value)}
            sx={{ fontSize: "0.85rem", borderRadius: "8px" }}
          >
            <MenuItem value="ALL">🌐 All Ingested Corpus Documents</MenuItem>
            {documents.map((d) => (
              <MenuItem key={d.document_id} value={d.document_id}>
                📄 {d.title} ({d.type})
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Chat Messages Feed Area */}
      <Box sx={{ flexGrow: 1, overflowY: "auto", px: { xs: 2, md: 8, lg: 16 }, py: 4, display: "flex", flexDirection: "column", gap: 3 }}>
        
        {messages.length === 0 ? (
          /* Welcome Screen */
          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "80%", textAlign: "center", py: 4 }}>
            <Typography variant="h4" sx={{ fontFamily: "Outfit, sans-serif", fontWeight: 800, mb: 1, color: "text.primary" }}>
              How can I assist with Mumbai <span style={{ color: "#6366f1" }}>DCPR 2034</span> today?
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 6, maxWidth: 600 }}>
              The platform is loaded with RAG semantic vector intelligence and Neo4j relations. Ask any regulatory, formulaic, or dependency questions instantly.
            </Typography>

            {/* Quick Action Prompt Cards */}
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" }, gap: 2.5, width: "100%", maxWidth: 850 }}>
              {quickQuestions.map((item, idx) => (
                <Paper
                  key={idx}
                  onClick={() => handleQuickQuestion(item.query)}
                  sx={{
                    p: 2.5,
                    textAlign: "left",
                    cursor: "pointer",
                    bgcolor: "rgba(30, 41, 59, 0.4)",
                    border: "1px solid rgba(148, 163, 184, 0.08)",
                    borderRadius: "16px",
                    transition: "all 0.2s ease-in-out",
                    "&:hover": {
                      transform: "translateY(-2px)",
                      bgcolor: "rgba(99, 102, 241, 0.06)",
                      borderColor: "rgba(99, 102, 241, 0.2)",
                      boxShadow: "0 6px 20px rgba(0,0,0,0.4)"
                    }
                  }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "primary.light", mb: 0.5 }}>
                    {item.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {item.desc}
                  </Typography>
                </Paper>
              ))}
            </Box>

            {/* Upload Guidance Info Block */}
            <Paper sx={{ mt: 5, p: 2, display: "flex", gap: 1.5, alignItems: "center", bgcolor: "rgba(20, 184, 166, 0.05)", borderColor: "rgba(20, 184, 166, 0.15)", maxWidth: 850, width: "100%", borderRadius: "12px" }}>
              <InfoIcon color="secondary" />
              <Typography variant="caption" color="text.secondary" align="left">
                <strong>Custom Circulars/Amendments:</strong> Working with a newer circular? Go to the <strong>Document Ingest</strong> tab in the sidebar, upload the PDF, and select <strong>Index RAG</strong> to chunk and index all 1000+ pages!
              </Typography>
            </Paper>
          </Box>
        ) : (
          /* Active Chat Thread */
          <Box sx={{ display: "flex", flexDirection: "column", gap: 3, maxWidth: 900, width: "100%", margin: "0 auto" }}>
            {/* General Query Context Info Bar */}
            {!calcResult && (
              <Alert severity="info" sx={{ borderRadius: "12px", border: "1px solid rgba(20, 184, 166, 0.2)" }}>
                <AlertTitle sx={{ fontWeight: 700 }}>RAG Document Intelligence Gateway</AlertTitle>
                Qwen is retrieving vector chunks grounded directly in loaded DCPR regulations. You can also switch target documents using the selector at the top.
              </Alert>
            )}

            {/* Message Bubbles */}
            {messages.map((msg, idx) => (
              <Box
                key={idx}
                sx={{
                  display: "flex",
                  gap: 2,
                  justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
                  width: "100%",
                }}
              >
                {/* Avatar for AI */}
                {msg.sender === "qwen" && (
                  <Avatar sx={{ bgcolor: "primary.main", width: 36, height: 36 }}>
                    <PsychologyIcon fontSize="small" />
                  </Avatar>
                )}

                <Box
                  sx={{
                    p: 2.5,
                    borderRadius: msg.sender === "user" ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
                    bgcolor: msg.sender === "user" ? "rgba(99, 102, 241, 0.12)" : "rgba(30, 41, 59, 0.4)",
                    border: "1px solid",
                    borderColor: msg.sender === "user" ? "rgba(99, 102, 241, 0.3)" : "rgba(148, 163, 184, 0.08)",
                    maxWidth: "80%",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.25)",
                  }}
                >
                  {/* Sender Name */}
                  <Typography variant="caption" sx={{ fontWeight: 750, color: msg.sender === "user" ? "primary.light" : "secondary.light", display: "block", mb: 1 }}>
                    {msg.sender === "user" ? "Planner Request" : "Qwen RAG Regulatory Gateway"}
                  </Typography>

                  {/* Fallback Warning */}
                  {msg.isFallback && (
                    <Alert severity="warning" sx={{ mb: 2, py: 0.5, borderRadius: "8px" }}>
                      <AlertTitle sx={{ fontWeight: 700, fontSize: "0.8rem" }}>Local Chunk Fallback active</AlertTitle>
                      <span style={{ fontSize: "0.75rem" }}>Ollama LLM offline. Displaying grounded source excerpts directly from ChromaDB vector storage.</span>
                    </Alert>
                  )}

                  {/* Message Body */}
                  <Box sx={{ color: "text.primary" }}>
                    {renderSimpleMarkdown(msg.text)}
                  </Box>

                  {/* Grounded Source Citations Chips */}
                  {msg.msgSources && msg.msgSources.length > 0 && (
                    <Box sx={{ mt: 2, pt: 1.5, borderTop: "1px dashed rgba(148, 163, 184, 0.15)" }}>
                      <Typography variant="caption" sx={{ fontWeight: 700, color: "text.secondary", display: "block", mb: 1 }}>
                        📌 Grounded Source Page Citations:
                      </Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.8 }}>
                        {msg.msgSources.map((s, sIdx) => (
                          <Chip
                            key={sIdx}
                            size="small"
                            variant="outlined"
                            color="primary"
                            label={`Page ${s.page} (${s.section})`}
                            sx={{ fontSize: "0.7rem", height: 24 }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>

                {/* Avatar for User */}
                {msg.sender === "user" && (
                  <Avatar sx={{ bgcolor: "secondary.main", width: 36, height: 36 }}>
                    <AccountCircleIcon fontSize="small" />
                  </Avatar>
                )}
              </Box>
            ))}

            {/* Generating Loader */}
            {isGeneratingExplanation && (
              <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start", width: "100%" }}>
                <Avatar sx={{ bgcolor: "primary.main", width: 36, height: 36 }}>
                  <PsychologyIcon fontSize="small" />
                </Avatar>
                <Box sx={{ p: 2.5, bgcolor: "rgba(30, 41, 59, 0.4)", border: "1px solid rgba(148, 163, 184, 0.08)", borderRadius: "20px", display: "flex", alignItems: "center", gap: 2 }}>
                  <CircularProgress size={20} color="primary" />
                  <Typography variant="caption" color="text.secondary">
                    Qwen is retrieving Neo4j references and generating reasoning trace...
                  </Typography>
                </Box>
              </Box>
            )}

            <Box ref={messagesEndRef} />
          </Box>
        )}
      </Box>

      {/* Persistent Chat Input Bar at Bottom */}
      <Box sx={{ borderTop: "1px solid rgba(148, 163, 184, 0.08)", px: { xs: 2, md: 8, lg: 16 }, py: 3, bgcolor: "background.paper" }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", gap: 1.5, maxWidth: 900, margin: "0 auto", position: "relative" }}>
          <TextField
            fullWidth
            placeholder="Ask Qwen about regulations, circulars, or cross-references..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isGeneratingExplanation}
            sx={{
              "& .MuiOutlinedInput-root": {
                borderRadius: "30px",
                pr: 6,
                bgcolor: "background.default",
                "& fieldset": { borderColor: "rgba(148, 163, 184, 0.15)" },
                "&:hover fieldset": { borderColor: "rgba(99, 102, 241, 0.4)" },
                "&.Mui-focused fieldset": { borderColor: "primary.main" },
              }
            }}
          />
          <IconButton
            type="submit"
            disabled={!question.trim() || isGeneratingExplanation}
            sx={{
              position: "absolute",
              right: 8,
              top: "50%",
              transform: "translateY(-50%)",
              bgcolor: "primary.main",
              color: "white",
              "&:hover": { bgcolor: "primary.dark" },
              "&.Mui-disabled": { bgcolor: "rgba(148, 163, 184, 0.08)", color: "text.disabled" }
            }}
          >
            <SendIcon />
          </IconButton>
        </Box>
        <Typography variant="caption" color="text.disabled" align="center" display="block" sx={{ mt: 1.5, fontSize: "0.75rem" }}>
          Answers are strictly grounded in Mumbai DCPR 2034 rules retrieved from your live Neo4j Aura graph database.
        </Typography>
      </Box>

    </Box>
  );
};
