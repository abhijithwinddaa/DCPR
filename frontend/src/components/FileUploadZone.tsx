import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Box,
  Divider,
  LinearProgress,
  IconButton,
} from "@mui/material";
import CloudUploadIconRaw from "@mui/icons-material/CloudUpload";
import AutoStoriesIconRaw from "@mui/icons-material/AutoStories";
import CheckCircleIconRaw from "@mui/icons-material/CheckCircle";
import ErrorIconRaw from "@mui/icons-material/Error";
import PlayArrowIconRaw from "@mui/icons-material/PlayArrow";
import DeleteIconRaw from "@mui/icons-material/Delete";

const CloudUploadIcon = (CloudUploadIconRaw as any).default || CloudUploadIconRaw;
const AutoStoriesIcon = (AutoStoriesIconRaw as any).default || AutoStoriesIconRaw;
const CheckCircleIcon = (CheckCircleIconRaw as any).default || CheckCircleIconRaw;
const ErrorIcon = (ErrorIconRaw as any).default || ErrorIconRaw;
const PlayArrowIcon = (PlayArrowIconRaw as any).default || PlayArrowIconRaw;
const DeleteIcon = (DeleteIconRaw as any).default || DeleteIconRaw;

import { useStore } from "../store/useStore";

export const FileUploadZone: React.FC = () => {
  const {
    documents,
    isUploading,
    processingMode,
    processingProgress,
    setProcessingMode,
    fetchDocuments,
    uploadDocument,
    processDocument,
    deleteDocument,
  } = useStore();

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("Mumbai DCPR 2034");
  const [docType, setDocType] = useState("DCPR");
  const [pagesInput, setPagesInput] = useState("all");

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    try {
      await uploadDocument(file, title, docType);
      setFile(null);
    } catch (err: any) {
      alert(`Upload failed: ${err.message || err}`);
    }
  };

  const handleProcessSubmit = async (versionId: string) => {
    try {
      await processDocument(versionId, pagesInput, processingMode);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (window.confirm("Are you sure you want to delete this document and clear its parsing metadata and vector chunks?")) {
      try {
        await deleteDocument(docId);
      } catch (err: any) {
        alert(`Failed to delete document: ${err.message || err}`);
      }
    }
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return <Chip icon={<CheckCircleIcon />} label="Completed" color="success" size="small" variant="outlined" />;
      case "PROCESSING":
        return <Chip icon={<CircularProgress size={16} color="inherit" />} label="Processing" color="secondary" size="small" />;
      case "FAILED":
        return <Chip icon={<ErrorIcon />} label="Failed" color="error" size="small" variant="outlined" />;
      default:
        return <Chip label="Pending" color="default" size="small" variant="outlined" />;
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {/* Upload Document Card */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <CloudUploadIcon color="primary" /> Ingest Regulatory PDF Source
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Box component="form" onSubmit={handleUploadSubmit} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <TextField
                label="Document Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                size="small"
                sx={{ flexGrow: 1 }}
              />
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Type</InputLabel>
                <Select value={docType} label="Type" onChange={(e) => setDocType(e.target.value)}>
                  <MenuItem value="DCPR">DCPR (Regulations)</MenuItem>
                  <MenuItem value="AMENDMENT">Amendment</MenuItem>
                  <MenuItem value="CIRCULAR">Circular</MenuItem>
                  <MenuItem value="NOTIFICATION">Notification</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <Button
                variant="outlined"
                component="label"
                sx={{ flexGrow: 1, py: 1.5, borderStyle: "dashed" }}
              >
                {file ? file.name : "Select DCPR PDF File"}
                <input type="file" hidden accept=".pdf" onChange={handleFileChange} />
              </Button>

              <Button
                type="submit"
                variant="contained"
                disabled={!file || isUploading}
                sx={{ px: 4, py: 1.5 }}
              >
                {isUploading ? <CircularProgress size={24} /> : "Upload"}
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Document Lineage List Card */}
      <Card>
        <CardContent>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5, flexWrap: "wrap", gap: 1 }}>
            <Typography variant="h6" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <AutoStoriesIcon color="secondary" /> Corpus Ingestion Lineage
            </Typography>

            {/* Mode selector */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, bgcolor: "action.hover", p: 0.5, borderRadius: 2 }}>
              <Typography variant="caption" sx={{ px: 1, fontWeight: 600, color: "text.secondary" }}>Pipeline Mode:</Typography>
              <Button
                size="small"
                variant={processingMode === "hybrid" ? "contained" : "text"}
                color="success"
                onClick={() => setProcessingMode("hybrid")}
                sx={{ textTransform: "none", fontSize: "0.75rem", fontWeight: 700 }}
              >
                ✨ Unified Hybrid (RAG + Neo4j)
              </Button>
              <Button
                size="small"
                variant={processingMode === "rag" ? "contained" : "text"}
                color="primary"
                onClick={() => setProcessingMode("rag")}
                sx={{ textTransform: "none", fontSize: "0.75rem" }}
              >
                RAG Vector Only
              </Button>
              <Button
                size="small"
                variant={processingMode === "dcpr" ? "contained" : "text"}
                color="secondary"
                onClick={() => setProcessingMode("dcpr")}
                sx={{ textTransform: "none", fontSize: "0.75rem" }}
              >
                Graph Only
              </Button>
            </Box>
          </Box>
          <Divider sx={{ mb: 2 }} />

          {documents.length === 0 ? (
            <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 3 }}>
              No documents uploaded yet. Start by uploading Mumbai-DCPR.pdf or equivalent.
            </Typography>
          ) : (
            <List sx={{ width: "100%", bgcolor: "background.paper", borderRadius: 2 }}>
              {documents.map((doc, idx) => (
                <React.Fragment key={doc.version_id}>
                  {idx > 0 && <Divider component="li" />}
                  <ListItem
                    secondaryAction={
                      <Box sx={{ display: "flex", gap: 1.5, alignItems: "center" }}>
                        {doc.processing_status !== "PROCESSING" && doc.processing_status !== "COMPLETED" ? (
                          <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                            {(processingMode === "dcpr" || processingMode === "hybrid") && (
                              <TextField
                                label="Graph Pages"
                                size="small"
                                value={pagesInput}
                                onChange={(e) => setPagesInput(e.target.value)}
                                sx={{ width: 105 }}
                              />
                            )}
                            <Button
                              variant="contained"
                              color={processingMode === "hybrid" ? "success" : processingMode === "rag" ? "primary" : "secondary"}
                              size="small"
                              onClick={() => handleProcessSubmit(doc.version_id)}
                              startIcon={<PlayArrowIcon />}
                            >
                              {processingMode === "hybrid" ? "Process Document (Hybrid)" : processingMode === "rag" ? "Index RAG" : "Compile Graph"}
                            </Button>
                          </Box>
                        ) : (
                          getStatusChip(doc.processing_status)
                        )}
                        
                        {/* Delete Button */}
                        <IconButton
                          edge="end"
                          aria-label="delete"
                          color="error"
                          onClick={() => handleDeleteDocument(doc.document_id)}
                          disabled={doc.processing_status === "PROCESSING"}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    }
                  >
                    <ListItemText
                      primary={doc.title}
                      secondary={
                        <>
                          <Typography variant="caption" color="text.secondary" component="span" display="block">
                            Type: {doc.type} | Version Tag: {doc.version_tag}
                          </Typography>
                          {doc.error_log && (
                            <Typography variant="caption" color="error" component="span" display="block" sx={{ mt: 0.5, fontStyle: "italic" }}>
                              Error: {doc.error_log.split("\n")[0]}
                            </Typography>
                          )}
                        </>
                      }
                    />
                  </ListItem>
                  {doc.processing_status === "PROCESSING" && (
                    <Box sx={{ width: "100%", px: 2, pb: 2, pt: 1, bgcolor: "action.hover", borderRadius: 1, my: 1 }}>
                      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5, alignItems: "center" }}>
                        <Typography variant="caption" sx={{ fontWeight: 600, color: "primary.main" }}>
                          {processingProgress?.stage || "Processing background task..."}
                        </Typography>
                        <Typography variant="caption" sx={{ fontWeight: 700, color: "text.primary" }}>
                          {processingProgress?.percent ?? 0}%
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant={processingProgress ? "determinate" : "indeterminate"}
                        value={processingProgress?.percent ?? 0} 
                        color={processingMode === "rag" ? "primary" : "secondary"} 
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                      {processingProgress && processingProgress.total_pages > 0 && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
                          Pages extracted: {processingProgress.pages_done} / {processingProgress.total_pages}
                        </Typography>
                      )}
                    </Box>
                  )}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};
