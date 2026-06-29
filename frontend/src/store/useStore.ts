import { create } from "zustand";

export interface DocumentInfo {
  document_id: string;
  version_id: string;
  title: string;
  type: string;
  version_tag: string;
  processing_status: string;
  error_log: string | null;
  created_at: string;
}

export interface RuleTraceStep {
  step: number;
  rule_id: string;
  type: string;
  expression: string;
  result: any;
  status: string;
  message: string;
}

export interface CalculationResult {
  calculation_id: string | null;
  applicable_fsi: number;
  maximum_bua: number;
  eligibility: string;
  constraints: string[];
  exceptions: string[];
  rule_trace: RuleTraceStep[];
  validator_status: string;
  validation_warnings: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  title: string;
  citation: string | null;
  modeling_status: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SourceChunk {
  text: string;
  page: number;
  section: string;
  score: number;
  version_id?: string;
  document_id?: string;
}

export interface ProcessingProgress {
  stage: string;
  percent: number;
  pages_done: number;
  total_pages: number;
  error?: string | null;
}

interface PlatformState {
  documents: DocumentInfo[];
  currentDocumentId: string | null;
  currentVersionId: string | null;
  isUploading: boolean;
  isProcessing: boolean;
  pageRange: string;
  processingMode: "hybrid" | "rag" | "dcpr";
  processingProgress: ProcessingProgress | null;
  selectedDocId: string | null;

  // Calculator
  inputs: {
    gross_cluster_area: number;
    access_road_width: number;
    certified_admissible_rehabilitation_bua: number;
    weighted_land_rate: number;
    construction_rate: number;
    fsi_base_area: number;
    [key: string]: any;
  };
  isCalculating: boolean;
  calcResult: CalculationResult | null;

  // Graph
  graphData: GraphData | null;
  isLoadingGraph: boolean;

  // Explanation
  questionText: string;
  explanationText: string;
  isGeneratingExplanation: boolean;
  wasFallback: boolean;
  sources: SourceChunk[];

  // Actions
  fetchDocuments: () => Promise<void>;
  uploadDocument: (file: File, title: string, type: string) => Promise<any>;
  processDocument: (versionId: string, pageRange: string, mode?: "hybrid" | "rag" | "dcpr") => Promise<void>;
  setProcessingMode: (mode: "hybrid" | "rag" | "dcpr") => void;
  setSelectedDocId: (docId: string | null) => void;
  setInputs: (inputs: Partial<PlatformState["inputs"]>) => void;
  runCalculation: (schemeUri: string) => Promise<void>;
  fetchGraph: (schemeUri: string) => Promise<void>;
  askQuestion: (question: string) => Promise<void>;
  askDocumentQuestion: (question: string, documentId?: string | null) => Promise<void>;
  clearCalculation: () => void;
  deleteDocument: (docId: string) => Promise<void>;
}

const BACKEND_URL = ""; // Vite proxy routes to http://localhost:8000

export const useStore = create<PlatformState>((set, get) => ({
  documents: [],
  currentDocumentId: null,
  currentVersionId: null,
  isUploading: false,
  isProcessing: false,
  pageRange: "all",

  inputs: {
    gross_cluster_area: 8000,
    access_road_width: 18,
    certified_admissible_rehabilitation_bua: 12000,
    weighted_land_rate: 30000,
    construction_rate: 20000,
    fsi_base_area: 5000,
  },
  isCalculating: false,
  calcResult: null,

  graphData: null,
  isLoadingGraph: false,

  questionText: "",
  explanationText: "",
  isGeneratingExplanation: false,
  wasFallback: false,
  sources: [],
  processingMode: "hybrid",
  processingProgress: null,
  selectedDocId: null,

  setProcessingMode: (mode) => set({ processingMode: mode }),
  setSelectedDocId: (docId) => set({ selectedDocId: docId }),

  fetchDocuments: async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/documents`);
      if (res.ok) {
        const data = await res.json();
        set({ documents: data });
        // Auto-select the first completed version if no version is selected
        if (data.length > 0 && !get().currentVersionId) {
          const completed = data.find((d: any) => d.processing_status === "COMPLETED");
          const target = completed || data[0];
          set({
            currentDocumentId: target.document_id,
            currentVersionId: target.version_id,
          });
        }
      }
    } catch (err) {
      console.error("Failed to fetch documents", err);
    }
  },

  uploadDocument: async (file: File, title: string, type: string) => {
    set({ isUploading: true });
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title);
      formData.append("document_type", type);

      const res = await fetch(`${BACKEND_URL}/documents/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const data = await res.json();
      set({
        currentDocumentId: data.document_id,
        currentVersionId: data.version_id,
      });
      await get().fetchDocuments();
      return data;
    } catch (err) {
      console.error("Failed to upload document", err);
      throw err;
    } finally {
      set({ isUploading: false });
    }
  },

  processDocument: async (versionId: string, pageRange: string, mode: "rag" | "dcpr" = "rag") => {
    set({ isProcessing: true, pageRange, processingMode: mode, processingProgress: { stage: "Starting background processing...", percent: 0, pages_done: 0, total_pages: 0 } });
    try {
      const res = await fetch(
        `${BACKEND_URL}/documents/process?version_id=${versionId}&page_range=${pageRange}&mode=${mode}`,
        { method: "POST" }
      );

      if (!res.ok) {
        throw new Error(await res.text());
      }

      // Start polling status & granular progress
      const poll = setInterval(async () => {
        await get().fetchDocuments();
        
        // Poll granular progress
        try {
          const progRes = await fetch(`${BACKEND_URL}/documents/progress/${versionId}`);
          if (progRes.ok) {
            const progData = await progRes.json();
            set({ processingProgress: progData });
          }
        } catch (pErr) {
          console.error("Failed to poll progress", pErr);
        }

        const docs = get().documents;
        const current = docs.find((d) => d.version_id === versionId);
        if (
          current &&
          (current.processing_status === "COMPLETED" ||
            current.processing_status === "FAILED")
        ) {
          clearInterval(poll);
          set({ isProcessing: false });
          // If complete, fetch graph dynamically
          if (current.processing_status === "COMPLETED" && mode === "dcpr") {
            await get().fetchGraph("dcpr:scheme:33-9");
          }
        }
      }, 1500);
    } catch (err) {
      console.error("Failed to process document", err);
      set({ isProcessing: false, processingProgress: null });
    }
  },

  setInputs: (newInputs) => {
    set((state) => ({
      inputs: { ...state.inputs, ...newInputs },
    }));
  },

  runCalculation: async (schemeUri: string) => {
    set({ isCalculating: true, explanationText: "", wasFallback: false, sources: [] });
    try {
      const res = await fetch(`${BACKEND_URL}/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scheme_uri: schemeUri,
          inputs: get().inputs,
        }),
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const data = await res.json();
      set({ calcResult: data });
    } catch (err) {
      console.error("Failed to run calculation", err);
    } finally {
      set({ isCalculating: false });
    }
  },

  fetchGraph: async (schemeUri: string) => {
    set({ isLoadingGraph: true });
    try {
      const res = await fetch(`${BACKEND_URL}/graph/${encodeURIComponent(schemeUri)}`);
      if (res.ok) {
        const data = await res.json();
        set({ graphData: data });
      }
    } catch (err) {
      console.error("Failed to fetch graph data", err);
    } finally {
      set({ isLoadingGraph: false });
    }
  },

  askQuestion: async (question: string) => {
    const calcId = get().calcResult?.calculation_id || "";
    set({ isGeneratingExplanation: true, questionText: question, explanationText: "", sources: [] });

    try {
      const res = await fetch(`${BACKEND_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          calculation_id: calcId,
        }),
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const data = await res.json();
      set({
        explanationText: data.explanation,
        wasFallback: data.was_fallback,
      });
    } catch (err) {
      console.error("Failed to ask question", err);
      set({ explanationText: `Error communicating with explainability gateway: ${err}` });
    } finally {
      set({ isGeneratingExplanation: false });
    }
  },

  askDocumentQuestion: async (question: string, documentId?: string | null) => {
    const docIdFilter = documentId !== undefined ? documentId : get().selectedDocId;
    set({ isGeneratingExplanation: true, questionText: question, explanationText: "", sources: [] });

    try {
      const res = await fetch(`${BACKEND_URL}/ask-document`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          document_id: docIdFilter,
          top_k: 5,
        }),
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const data = await res.json();
      set({
        explanationText: data.explanation,
        wasFallback: data.was_fallback,
        sources: data.sources || [],
      });
    } catch (err) {
      console.error("Failed to execute RAG document Q&A", err);
      set({ explanationText: `Error executing RAG document intelligence query: ${err}`, sources: [] });
    } finally {
      set({ isGeneratingExplanation: false });
    }
  },

  clearCalculation: () => {
    set({ calcResult: null, explanationText: "", questionText: "" });
  },

  deleteDocument: async (docId: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/documents/${docId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      // Refresh local document list
      await get().fetchDocuments();
    } catch (err) {
      console.error("Failed to delete document", err);
      throw err;
    }
  },
}));
