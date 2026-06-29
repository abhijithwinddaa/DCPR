import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Box,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Grid,
  Chip,
  Alert,
  AlertTitle,
  CircularProgress,
  Switch,
  FormControlLabel,
} from "@mui/material";
import CalculateIconRaw from "@mui/icons-material/Calculate";
import GavelIconRaw from "@mui/icons-material/Gavel";
import InfoIconRaw from "@mui/icons-material/Info";
import TaskAltIconRaw from "@mui/icons-material/TaskAlt";
import ErrorOutlineIconRaw from "@mui/icons-material/ErrorOutline";

const CalculateIcon = (CalculateIconRaw as any).default || CalculateIconRaw;
const GavelIcon = (GavelIconRaw as any).default || GavelIconRaw;
const InfoIcon = (InfoIconRaw as any).default || InfoIconRaw;
const TaskAltIcon = (TaskAltIconRaw as any).default || TaskAltIconRaw;
const ErrorOutlineIcon = (ErrorOutlineIconRaw as any).default || ErrorOutlineIconRaw;
import { useStore } from "../store/useStore";

export const CalculatorPanel: React.FC = () => {
  const {
    inputs,
    isCalculating,
    calcResult,
    setInputs,
    runCalculation,
    clearCalculation,
  } = useStore();

  const handleInputChange = (field: string, value: string) => {
    // Handle float conversion
    const numVal = parseFloat(value);
    setInputs({ [field]: isNaN(numVal) ? 0 : numVal });
  };

  const handleOverrideChange = (field: string, checked: boolean) => {
    setInputs({ [field]: checked });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await runCalculation("dcpr:scheme:33-9");
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PASS":
      case "RESOLVED":
        return <Chip label={status} color="success" size="small" variant="outlined" />;
      case "OVERRIDDEN":
        return <Chip label={status} color="warning" size="small" variant="outlined" />;
      case "FAIL":
      case "ERROR":
        return <Chip label={status} color="error" size="small" variant="outlined" />;
      default:
        return <Chip label={status} size="small" variant="outlined" />;
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {/* Parameter Form */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <CalculateIcon color="primary" /> Parameter Inputs for Scheme 33(9)
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  label="Gross Cluster Area (sq. m)"
                  type="number"
                  value={inputs.gross_cluster_area}
                  onChange={(e) => handleInputChange("gross_cluster_area", e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  label="Access Road Width (m)"
                  type="number"
                  value={inputs.access_road_width}
                  onChange={(e) => handleInputChange("access_road_width", e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  label="FSI Base Net Plot Area (sq. m)"
                  type="number"
                  value={inputs.fsi_base_area}
                  onChange={(e) => handleInputChange("fsi_base_area", e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  label="Rehab Built-Up Area (sq. m)"
                  type="number"
                  value={inputs.certified_admissible_rehabilitation_bua}
                  onChange={(e) => handleInputChange("certified_admissible_rehabilitation_bua", e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  label="ASR Land Rate (per sq. m)"
                  type="number"
                  value={inputs.weighted_land_rate}
                  onChange={(e) => handleInputChange("weighted_land_rate", e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  label="ASR Construction Cost (per sq. m)"
                  type="number"
                  value={inputs.construction_rate}
                  onChange={(e) => handleInputChange("construction_rate", e.target.value)}
                  required
                />
              </Grid>

              {/* Exception overrides toggles */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom color="text.secondary">
                  Waiver Toggles / Exception Overrides
                </Typography>
                <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={!!inputs["override_road-access-eligibility"]}
                        onChange={(e) => handleOverrideChange("override_road-access-eligibility", e.target.checked)}
                      />
                    }
                    label="Road Width Waiver"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={!!inputs["override_cluster-area-eligibility"]}
                        onChange={(e) => handleOverrideChange("override_cluster-area-eligibility", e.target.checked)}
                      />
                    }
                    label="Cluster Area Waiver"
                  />
                </Box>
              </Grid>

              <Grid item xs={12} sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}>
                <Button variant="outlined" color="inherit" onClick={clearCalculation} disabled={isCalculating}>
                  Reset
                </Button>
                <Button type="submit" variant="contained" color="primary" disabled={isCalculating} sx={{ minWidth: 150 }}>
                  {isCalculating ? <CircularProgress size={24} /> : "Run Compliance"}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>

      {/* Calculated Results */}
      {calcResult && (
        <>
          <Grid container spacing={3}>
            {/* Final Answer Cards */}
            <Grid item xs={12} md={4}>
              <Card sx={{ height: "100%", borderLeft: `6px solid ${calcResult.eligibility === "ELIGIBLE" ? "#10b981" : "#f43f5e"}` }}>
                <CardContent sx={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "space-between" }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Eligibility Result
                  </Typography>
                  <Typography variant="h4" color={calcResult.eligibility === "ELIGIBLE" ? "success.main" : "error.main"} sx={{ my: 1.5 }}>
                    {calcResult.eligibility}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Calculations evaluated deterministically by the zoning rule engine.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={4}>
              <Card sx={{ height: "100%" }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Applicable FSI
                  </Typography>
                  <Typography variant="h4" color="primary.light" sx={{ my: 1.5 }}>
                    {calcResult.applicable_fsi.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Combined rehab and incentive FSI (minimum floor: 4.00).
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={4}>
              <Card sx={{ height: "100%" }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Maximum Built-Up Area (BUA)
                  </Typography>
                  <Typography variant="h4" color="secondary.light" sx={{ my: 1.5 }}>
                    {calcResult.maximum_bua.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} sq. m
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total permissible built-up area under Regulation 33(9).
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Validation Auditing layer status */}
          <Alert severity={calcResult.validator_status === "PASS" ? "success" : "error"} icon={calcResult.validator_status === "PASS" ? <TaskAltIcon /> : <ErrorOutlineIcon />}>
            <AlertTitle sx={{ fontWeight: 700 }}>
              Independent Calculation Validation Auditing: {calcResult.validator_status}
            </AlertTitle>
            {calcResult.validator_status === "PASS" ? (
              "Independent audit checks completed successfully. Formulations, decimal rounding policies, and table lookups are verified correct."
            ) : (
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  The validation layer flagged the following warnings or boundary violations:
                </Typography>
                <Box sx={{ p: 0, m: 0 }}>
                  {calcResult.validation_warnings.map((warn, i) => (
                    <Typography key={i} variant="caption" display="block" color="error.light">
                      • {warn}
                    </Typography>
                  ))}
                </Box>
              </Box>
            )}
          </Alert>

          {/* Constraints Ledger Warnings */}
          {calcResult.constraints.length > 0 && (
            <Alert severity="warning" icon={<GavelIcon />}>
              <AlertTitle sx={{ fontWeight: 700 }}>Triggered Constraints Ledger</AlertTitle>
              <Box component="ul" sx={{ p: 0, pl: 2, m: 0 }}>
                {calcResult.constraints.map((c, i) => (
                  <li key={i}>
                    <Typography variant="body2">{c}</Typography>
                  </li>
                ))}
              </Box>
            </Alert>
          )}

          {/* Active Exceptions overrides */}
          {calcResult.exceptions.length > 0 && (
            <Alert severity="info" icon={<InfoIcon />}>
              <AlertTitle sx={{ fontWeight: 700 }}>Applied Regulatory Exception Overrides</AlertTitle>
              <Box component="ul" sx={{ p: 0, pl: 2, m: 0 }}>
                {calcResult.exceptions.map((ex, i) => (
                  <li key={i}>
                    <Typography variant="body2">{ex}</Typography>
                  </li>
                ))}
              </Box>
            </Alert>
          )}

          {/* Step-by-Step Rule Audit Trace Table */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Deterministic Rule Audit Trace Ledger
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <TableContainer component={Paper} sx={{ boxShadow: "none", border: "1px solid rgba(148, 163, 184, 0.08)" }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell width={50}>Step</TableCell>
                      <TableCell width={180}>Rule ID</TableCell>
                      <TableCell width={120}>Type</TableCell>
                      <TableCell>Expression / Operation</TableCell>
                      <TableCell width={120}>Result</TableCell>
                      <TableCell width={100}>Status</TableCell>
                      <TableCell>Audit Message</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {calcResult.rule_trace.map((trace) => (
                      <TableRow key={trace.step} hover>
                        <TableCell>{trace.step}</TableCell>
                        <TableCell>
                          <Typography variant="caption" sx={{ fontFamily: "monospace", display: "block" }}>
                            {trace.rule_id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={trace.type} size="small" variant="outlined" color="primary" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" sx={{ fontFamily: "monospace", color: "text.secondary", display: "block" }}>
                            {trace.expression}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {typeof trace.result === "number"
                              ? trace.result.toLocaleString(undefined, { maximumFractionDigits: 4 })
                              : String(trace.result)}
                          </Typography>
                        </TableCell>
                        <TableCell>{getStatusBadge(trace.status)}</TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {trace.message}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
};
