import React, { useEffect, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
} from "reactflow";
import type { Node, Edge } from "reactflow";
import "reactflow/dist/style.css";
import { Card, CardContent, Typography, CircularProgress, Box, Divider, Button } from "@mui/material";
import AccountTreeIconRaw from "@mui/icons-material/AccountTree";
const AccountTreeIcon = (AccountTreeIconRaw as any).default || AccountTreeIconRaw;
import { useStore } from "../store/useStore";

// Color mappings for node labels
const nodeStyles: { [key: string]: { background: string; border: string; color: string } } = {
  Scheme: { background: "#1e1b4b", border: "#6366f1", color: "#f8fafc" },
  Regulation: { background: "#1e293b", border: "#475569", color: "#f8fafc" },
  Condition: { background: "#78350f", border: "#d97706", color: "#fef3c7" },
  Formula: { background: "#064e3b", border: "#10b981", color: "#ecfdf5" },
  Table: { background: "#172554", border: "#3b82f6", color: "#eff6ff" },
  InputParameter: { background: "#3b0764", border: "#a855f7", color: "#faf5ff" },
  Fact: { background: "#27272a", border: "#71717a", color: "#f4f4f5" },
  Definition: { background: "#0f172a", border: "#334155", color: "#94a3b8" },
};

export const GraphExplorer: React.FC = () => {
  const { graphData, isLoadingGraph, fetchGraph } = useStore();

  useEffect(() => {
    // Default fetch Scheme 33(9) graph
    fetchGraph("dcpr:scheme:33-9");
  }, []);

  // Compute React Flow nodes and edges using a tiered column layout
  const { rfNodes, rfEdges } = useMemo(() => {
    if (!graphData || !graphData.nodes) {
      return { rfNodes: [], rfEdges: [] };
    }

    const { nodes, edges } = graphData;

    // Helper to bucket nodes by column index to create a clear layered layout
    const getColumnIndex = (label: string): number => {
      switch (label) {
        case "InputParameter":
        case "Fact":
          return 0;
        case "Table":
        case "Definition":
          return 1;
        case "Formula":
        case "Condition":
          return 2;
        case "Scheme":
        case "Regulation":
        case "OutputParameter":
        default:
          return 3;
      }
    };

    // Count nodes in each column to distribute vertically
    const columnCounters = [0, 0, 0, 0];
    const computedNodes: Node[] = nodes.map((node) => {
      const col = getColumnIndex(node.label);
      const rowIdx = columnCounters[col];
      columnCounters[col] += 1;

      // Positions: X column layout (260px gap), Y vertical distribute (120px gap)
      const x = col * 260 + 50;
      const y = rowIdx * 110 + 60;

      // Style matching the node type
      const style = nodeStyles[node.label] || { background: "#1e293b", border: "#475569", color: "#f8fafc" };

      return {
        id: node.id,
        position: { x, y },
        data: {
          label: (
            <Box sx={{ p: 0.5, textAlign: "left" }}>
              <Typography variant="caption" sx={{ fontWeight: 700, opacity: 0.8, display: "block" }}>
                {node.label.toUpperCase()}
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, display: "block", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", maxWidth: 200 }}>
                {node.title || node.id.split(":").pop()}
              </Typography>
              {node.citation && (
                <Typography variant="caption" sx={{ fontStyle: "italic", opacity: 0.7 }}>
                  Cit: {node.citation}
                </Typography>
              )}
            </Box>
          ),
        },
        style: {
          background: style.background,
          color: style.color,
          border: `2px solid ${style.border}`,
          borderRadius: "8px",
          width: 220,
          boxShadow: "0 4px 6px -1px rgba(0,0,0,0.2)",
        },
      };
    });

    const computedEdges: Edge[] = edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      type: "smoothstep",
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#64748b",
      },
      style: {
        strokeWidth: 2,
        stroke: "#64748b",
      },
      labelStyle: {
        fill: "#94a3b8",
        fontWeight: 600,
        fontSize: 10,
      },
      labelBgPadding: [4, 2],
      labelBgBorderRadius: 4,
      labelBgStyle: { fill: "#1e293b", fillOpacity: 0.75 },
    }));

    return { rfNodes: computedNodes, rfEdges: computedEdges };
  }, [graphData]);

  return (
    <Card sx={{ height: "100%", minHeight: 650, display: "flex", flexDirection: "column" }}>
      <CardContent sx={{ pb: 0 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Typography variant="h6" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <AccountTreeIcon color="primary" /> Interactive Regulations Graph Explorer
          </Typography>
          <Button variant="outlined" size="small" onClick={() => fetchGraph("dcpr:scheme:33-9")} disabled={isLoadingGraph}>
            Refresh Graph
          </Button>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
          Topological mapping of scheme variables, calculation tables, conditions, and formulas.
        </Typography>
      </CardContent>
      <Divider />

      <Box sx={{ height: 550, position: "relative", bgcolor: "#0f172a" }}>
        {isLoadingGraph ? (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%", width: "100%", position: "absolute", zIndex: 10 }}>
            <CircularProgress color="primary" />
          </Box>
        ) : rfNodes.length === 0 ? (
          <Box sx={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", height: "100%", width: "100%", gap: 2 }}>
            <Typography color="text.secondary">No graph data found. Upload and process a PDF document.</Typography>
          </Box>
        ) : (
          <ReactFlow nodes={rfNodes} edges={rfEdges} fitView>
            <Background color="#334155" gap={16} size={1} />
            <Controls />
          </ReactFlow>
        )}
      </Box>
    </Card>
  );
};
