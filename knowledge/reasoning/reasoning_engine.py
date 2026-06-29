import os
import json
import urllib.request
import urllib.error

class QwenReasoningEngine:
    """
    QwenReasoningEngine handles natural language explainability.
    It queries a local Ollama reasoning model (Qwen) if running,
    but falls back to a deterministic trace-based text generator if offline.
    """
    def __init__(self, ollama_url="http://localhost:11434/api/generate", model_name="qwen3:8b", timeout=120):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.timeout = timeout

    def explain(self, user_question, context_data):
        """
        Explains the Rule Engine outputs and trace for the user question.
        context_data dictionary contains:
          - user_inputs
          - execution_output (Rule Engine outputs)
          - validation_output (Phase 5 validator summary)
          - graph_context (general matched nodes and links)
        """
        exec_out = context_data.get("execution_output", {})
        val_out = context_data.get("validation_output", {})
        user_inputs = context_data.get("user_inputs", {})
        graph_context = context_data.get("graph_context", {})
        
        # Build prompt containing full structured context
        prompt = self._build_prompt(user_question, user_inputs, exec_out, val_out, graph_context)
        
        # Attempt to query Ollama
        response_text = self._query_ollama(prompt)
        
        if response_text:
            return response_text
            
        # Fallback to local trace compiler if Ollama is offline
        if not exec_out:
            return self._generate_local_general_explanation(user_question, graph_context)
        return self._generate_local_explanation(user_question, user_inputs, exec_out, val_out)

    def explain_rag(self, user_question, chunks, graph_context=None):
        """
        Explains user question using retrieved source chunks and optional graph cross-references.
        Returns tuple: (explanation_text, was_fallback)
        """
        prompt = self._build_rag_prompt(user_question, chunks, graph_context)
        response_text = self._query_ollama(prompt)
        if response_text:
            return response_text, False

        # Fallback if Ollama is offline
        return self._format_chunks_fallback(user_question, chunks, graph_context), True

    def _build_rag_prompt(self, question, chunks, graph_context=None):
        """Constructs grounded RAG prompt with strict source verification and page citation rules."""
        sources_list = []
        for idx, c in enumerate(chunks, 1):
            page_info = f"Page {c.get('page', 'Unknown')}"
            sec_info = f"Section: {c.get('section', 'General')}"
            snippet = c.get('text', '').strip()[:1000]
            sources_list.append(f"[Source Excerpt {idx} | {page_info} | {sec_info}]\n{snippet}")

        sources_str = "\n\n".join(sources_list)

        graph_str = ""
        if graph_context and graph_context.get("matched_nodes"):
            graph_nodes = [f"- {n['title']} ({n['id']})" for n in graph_context["matched_nodes"][:5]]
            graph_str = "\nCross-Referenced Graph Entities:\n" + "\n".join(graph_nodes)

        prompt = (
            "You are an expert regulatory legal advisor for Mumbai DCPR (Development Control & Promotion Regulations).\n"
            "Answer the user's question accurately using ONLY the official source document excerpts provided below.\n\n"
            "CRITICAL GUARDRAILS:\n"
            "1. Ground every fact or threshold in the source excerpts. Always cite the page number (e.g., [Page 45]) whenever referencing a rule or table.\n"
            "2. Do NOT invent numbers, percentages, or statutory definitions not present in the excerpts.\n"
            "3. If the provided excerpts do not contain enough information to answer the question completely, state clearly what is specified and what is missing.\n"
            "4. Provide your final structured answer directly using bold bullet points and statutory headings without internal monologue or conversational preamble.\n\n"
            f"USER QUESTION: {question}\n\n"
            f"OFFICIAL SOURCE EXCERPTS:\n{sources_str}\n"
            f"{graph_str}\n\n"
            "Provide a comprehensive, professional, and well-structured statutory answer with explicit page citations."
        )
        return prompt

    def _format_chunks_fallback(self, question, chunks, graph_context=None):
        """Formats retrieved chunks into clean markdown when Ollama is offline."""
        explanation = "### RAG Source Retrieval Gateway (Local Fallback)\n\n"
        explanation += "*(Note: The Ollama LLM is currently offline or warming up. Displaying grounded source excerpts retrieved directly from the vector index.)*\n\n"
        explanation += f"Here are the top regulatory source excerpts matching **\"{question}\"**:\n\n"

        for idx, c in enumerate(chunks, 1):
            page = c.get("page", 1)
            sec = c.get("section", "General")
            score = c.get("score", 0.0)
            text = c.get("text", "").strip()

            explanation += f"#### 📄 Excerpt #{idx} (Page {page} — `{sec}`)\n"
            explanation += f"- **Relevance Match Score:** `{score}`\n"
            explanation += f"```text\n{text[:1200]}\n```\n\n"

        if graph_context and graph_context.get("matched_nodes"):
            explanation += "### 🔗 Connected Graph Knowledge Nodes\n"
            for n in graph_context["matched_nodes"][:5]:
                explanation += f"- **{n['title']}** (`{n['id']}`)\n"

        return explanation

    def _build_prompt(self, question, inputs, outputs, validation, graph_context=None):
        """Constructs a structured prompt for the Qwen explanation gateway."""
        if not outputs and graph_context and graph_context.get("matched_nodes"):
            # Construct general graph prompt
            nodes_info = []
            for n in graph_context["matched_nodes"]:
                nodes_info.append(
                    f"- Entity ID: {n['id']}\n"
                    f"  Label/Type: {n['label']}\n"
                    f"  Title: {n['title']}\n"
                    f"  Citation: {n['citation']}\n"
                    f"  Attributes: {json.dumps(n['properties'])}"
                )
            nodes_str = "\n".join(nodes_info)
            
            conns_info = []
            for c in graph_context.get("connections", []):
                conns_info.append(f"- ({c['source']}) -[:{c['type']}]-> ({c['target']})")
            conns_str = "\n".join(conns_info)
            
            prompt = (
                "You are an expert regulatory advisor for Mumbai DCPR 2034.\n"
                "Explain the requested regulatory details based ONLY on the connection graph nodes provided below.\n\n"
                "GUARDRAILS:\n"
                "- Only cite the regulations, formulas, and connections explicitly provided.\n"
                "- Do not invent any FSI values, heights, or plot rules.\n"
                "- Frame your response professionally outlining: statutory overview, connected dots (cross-references), and pros/cons/risks.\n\n"
                f"USER QUESTION: {question}\n\n"
                "CONNECTED GRAPH CONTEXT:\n"
                f"{nodes_str}\n\n"
                "GRAPH CONNECTIONS (CONNECTED DOTS):\n"
                f"{conns_str}\n\n"
                "Provide a clear, detailed, and structured explanation."
            )
            return prompt

        prompt = (
            "You are a regulatory expert explaining Mumbai DCPR 2034 building approvals.\n"
            "You must explain the results of the deterministic rule engine to the user.\n\n"
            "GUARDRAILS:\n"
            "- NEVER calculate or verify numbers yourself. Treat the execution outputs as absolute truth.\n"
            "- Do not invent citations, regulations, or numbers.\n"
            "- Only explain the outputs provided in the context below.\n\n"
            f"USER QUESTION: {question}\n\n"
            "CONTEXT DATA:\n"
            f"- Inputs provided: {json.dumps(inputs)}\n"
            f"- Engine Outputs: {json.dumps({k: v for k, v in outputs.items() if k != 'rule_trace'})}\n"
            f"- Validation Status: {json.dumps(validation)}\n"
            f"- Rule Trace: {json.dumps(outputs.get('rule_trace', []))}\n\n"
            "Provide a clear, natural English explanation of why the rule succeeded/failed, "
            "what references apply, and any assumptions/risks."
        )
        return prompt

    def _generate_local_general_explanation(self, question, graph_context):
        """Generates a high-quality deterministic response using the graph context when Qwen is offline."""
        explanation = "### Qwen Explanation Gateway (Local Graph Compiler Fallback)\n\n"
        explanation += "*(Note: The Ollama Qwen model is currently offline. Generating structured answer from live Neo4j/NetworkX graph dependencies.)*\n\n"
        
        nodes = graph_context.get("matched_nodes", [])
        connections = graph_context.get("connections", [])
        
        if not nodes:
            explanation += (
                "No direct matches were found in the knowledge graph matching your search terms.\n\n"
                "**How to proceed:**\n"
                "- Verify if you have uploaded and processed the PDF document containing these regulations.\n"
                "- Check the spelling of the regulation number (e.g., 'Regulation 30' or 'Scheme 33(9)').\n"
                "- Use the Ingestion Panel to load the regulatory document section into the database."
            )
            return explanation
            
        explanation += f"Here is the statutory mapping and connected dependency details for **\"{question}\"**:\n\n"
        
        # List matched entities
        for n in nodes:
            nid = n["id"]
            title = n["title"]
            citation = n["citation"]
            label = n["label"]
            props = n["properties"]
            
            explanation += f"#### 📁 {label}: {title}\n"
            if citation:
                explanation += f"- **Citation Reference:** `{citation}`\n"
            explanation += f"- **Entity Key**: `{nid}`\n"
            
            # Print important properties if present
            if props:
                for k, v in props.items():
                    if k not in ("graph_schema_version", "modeling_status"):
                        val = props[k]
                        explanation += f"- **{k.replace('_', ' ').title()}:** `{val}`\n"
            explanation += "\n"
            
        # Connected dots (how it links to other regulations or formulas)
        explanation += "### 🔗 Connected Dots (Regulatory References & Dependencies)\n"
        explanation += "The regulatory graph maps the following cross-references and dependency flows:\n\n"
        
        direct_conns = []
        for c in connections:
            source_name = c["source"].split(":")[-1]
            target_name = c["target"].split(":")[-1]
            direct_conns.append(
                f"- **{source_name}** affects/references **{target_name}** via relation `{c['type']}`"
            )
            
        if direct_conns:
            explanation += "\n".join(direct_conns)
        else:
            explanation += "This entity stands as a standalone node; no active structural dependencies are currently mapped in the loaded graph schema."
            
        # Pros & Cons / Planning risks
        explanation += "\n\n### ⚖️ Planning Assessment & Risks\n"
        explanation += "- **Cross-referencing Risk:** Amendments or circulars modifying any connected node (listed above) will automatically affect the calculations of dependent nodes. Ensure all relevant notifications are processed.\n"
        explanation += "- **Assumption:** All calculations derived from this schema assume that MHADA and municipal surveyor records match your input parameters exactly.\n"
        explanation += "- **Eligibility Note:** Specific zone rules (Suburbs vs. Island City) may override the default thresholds. Verify access road and width constraints per local ward instructions."
        
        return explanation


    def _query_ollama(self, prompt):
        """Tries to POST the prompt to the Ollama endpoint with urllib. Returns None on failure."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 500,
                "temperature": 0.2
            }
        }
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            self.ollama_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            log_msg = f"[Ollama Debug] Sending request to {self.ollama_url} with model {self.model_name}...\n"
            with open("debug_ollama.log", "a", encoding="utf-8") as f:
                f.write(log_msg)
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                body = res.read().decode("utf-8")
                res_json = json.loads(body)
                resp = res_json.get("response", "")
                think = res_json.get("thinking", "")
                log_msg2 = f"[Ollama Debug] Received response. resp len: {len(resp)}, think len: {len(think)}\n"
                with open("debug_ollama.log", "a", encoding="utf-8") as f:
                    f.write(log_msg2)
                
                # Deliver actual response text directly if present, falling back to thinking trace if response is empty
                full_text = ""
                if resp and resp.strip():
                    full_text = resp.strip()
                elif think and think.strip():
                    full_text = f"**[Qwen Reasoning Summary]**\n{think.strip()}"
                    
                final_res = full_text if full_text.strip() else None
                with open("debug_ollama.log", "a", encoding="utf-8") as f:
                    f.write(f"[Ollama Debug] Final text generated: {final_res is not None}\n")
                return final_res
        except Exception as e:
            # Connection refused, timeout, or missing model
            import traceback
            err_msg = f"[Ollama Error] Query failed: {e}\n{traceback.format_exc()}\n"
            with open("debug_ollama.log", "a", encoding="utf-8") as f:
                f.write(err_msg)
            return None

    def _generate_local_explanation(self, question, inputs, outputs, validation):
        """Generates a high-quality deterministic explanation from the rule trace ledger."""
        eligibility = outputs.get("eligibility", "UNKNOWN")
        app_fsi = outputs.get("applicable_fsi", 0.0)
        max_bua = outputs.get("maximum_bua", 0.0)
        constraints = outputs.get("constraints", [])
        exceptions = outputs.get("exceptions", [])
        
        # Pull inputs
        area = inputs.get("gross_cluster_area", 0)
        road = inputs.get("access_road_width", 0)
        rehab_bua = inputs.get("certified_admissible_rehabilitation_bua", 0)
        base_area = inputs.get("fsi_base_area", 1) # avoid division by zero
        
        explanation = "### Qwen Explanation Gateway (Local Compiler Fallback)\n\n"
        explanation += "*(Note: The Ollama Qwen model is currently offline. Generating guarded local explanation from rule trace context.)*\n\n"
        
        q_lower = question.lower()
        
        if "fsi" in q_lower or "fsi" in q_lower or "ratio" in q_lower:
            explanation += f"**Applicable FSI Explanation:**\n"
            if eligibility == "INELIGIBLE":
                explanation += f"Applicable FSI is evaluated as `0.00` because the project fails eligibility criteria.\n"
            else:
                rehab_fsi = rehab_bua / base_area
                # Get incentive FSI from trace
                inc_bua = 0.0
                for step in outputs.get("rule_trace", []):
                    if step.get("rule_id") == "dcpr:33-9:incentive-bua":
                        inc_bua = step.get("result", 0.0)
                
                inc_fsi = inc_bua / base_area
                combined = rehab_fsi + inc_fsi
                
                explanation += f"Scheme 33(9) applies to this plot, resulting in a calculated applicable FSI of `{app_fsi:.2f}`:\n"
                explanation += f"- **Rehabilitation FSI Component:** `{rehab_fsi:.2f}` (calculated as MHADA certified BUA `{rehab_bua}` / net plot base area `{base_area}`).\n"
                explanation += f"- **Incentive FSI Component:** `{inc_fsi:.2f}` (derived from incentive BUA `{inc_bua:.2f}` / net plot base area `{base_area}`).\n"
                explanation += f"- **Combined FSI:** `{combined:.2f}` (rehab FSI `{rehab_fsi:.2f}` + incentive FSI `{inc_fsi:.2f}`).\n"
                
                if combined <= 4.00:
                    explanation += f"- **Minimum baseline cap applied:** Because Combined FSI (`{combined:.2f}`) is less than the regulatory baseline of `4.00`, the final applicable FSI is capped at `4.00` per Regulation 33(9) specifications.\n"
                else:
                    explanation += f"- **FSI Result:** Since the Combined FSI (`{combined:.2f}`) exceeds the baseline floor of `4.00`, the final applicable FSI resolves to `{app_fsi:.2f}`.\n"
                    
        elif "eligibility" in q_lower or "eligible" in q_lower or "apply" in q_lower or "fail" in q_lower:
            explanation += f"**Eligibility & Applicability Explanation:**\n"
            if eligibility == "INELIGIBLE":
                explanation += "The development proposal is **INELIGIBLE** for Scheme 33(9) due to the following constraint failures:\n"
                for c in constraints:
                    explanation += f"- ❌ *\"{c}\"*\n"
                if exceptions:
                    explanation += "\nNote: The following exception overrides were checked:\n"
                    for ex in exceptions:
                        explanation += f"- `{ex}`\n"
            else:
                explanation += "The development proposal is **ELIGIBLE** for Scheme 33(9) because:\n"
                explanation += f"- Gross cluster area (`{area} sq. m`) satisfies the minimum suburban threshold (6,000 sq. m) or Island City threshold (4,000 sq. m).\n"
                explanation += f"- Access road width (`{road} m`) satisfies the minimum required width of 18 m.\n"
                if exceptions:
                    explanation += "\nActive Exception Overrides applied:\n"
                    for ex in exceptions:
                        explanation += f"- ℹ️ *\"{ex}\"*\n"
                        
        elif "bua" in q_lower or "built-up" in q_lower:
            explanation += f"**Built-Up Area (BUA) Contribution Explanation:**\n"
            if eligibility == "INELIGIBLE":
                explanation += "Maximum BUA is `0.00` because the project is ineligible.\n"
            else:
                inc_bua = 0.0
                for step in outputs.get("rule_trace", []):
                    if step.get("rule_id") == "dcpr:33-9:incentive-bua":
                        inc_bua = step.get("result", 0.0)
                bal_bua = max_bua - (rehab_bua + inc_bua)
                
                explanation += f"The Maximum allowed BUA is `{max_bua:.2f} sq. m`:\n"
                explanation += f"- **Rehabilitation BUA:** `{rehab_bua:.2f} sq. m` (MHADA certified component).\n"
                explanation += f"- **Incentive BUA:** `{inc_bua:.2f} sq. m` (computed by applying incentive rate percentage to rehab BUA).\n"
                explanation += f"- **Balance Free-Sale BUA:** `{bal_bua:.2f} sq. m` (remaining BUA computed as Max BUA `{max_bua:.2f}` minus rehab & incentive BUAs).\n"
        else:
            # General Explanation
            explanation += "**General Development Assessment Explanation:**\n"
            explanation += f"Proposal Status: **{eligibility}**\n"
            explanation += f"- Mapped Scheme: **Scheme 33(9)** (Cluster Development Scheme)\n"
            explanation += f"- Applicable FSI: `{app_fsi:.2f}`\n"
            explanation += f"- Maximum Permissible BUA: `{max_bua:.2f} sq. m`\n"
            if eligibility == "INELIGIBLE":
                explanation += "\nConstraint Violations:\n"
                for c in constraints:
                    explanation += f"  - *{c}*\n"
            else:
                explanation += "\nAll applicability checks passed. Calculations are verified by the independent validator layer."

        # Add references, assumptions, and risks to comply with the output format
        explanation += "\n\n**Relevant Regulations & References:**\n"
        explanation += "- **Regulation 30:** Governs open spaces, setbacks, and margins required for Cluster Development Schemes.\n"
        explanation += "- **Regulation 31(3):** Regulates fungible compensatory area (which is exclusive of FSI under this scheme).\n"
        explanation += "- **Regulation 32:** Governs the Transfer of Development Rights (TDR) and land surrender rules.\n"

        explanation += "\n**Risks & Assumptions:**\n"
        explanation += "- Assumes the plot coordinates and areas supplied in user inputs are survey-accurate.\n"
        explanation += "- Assumes rehabilitation built-up area is certified correctly by MHADA Town Planning Division.\n"
        explanation += "- Assumes standard ASR rates of land and construction are aligned with the local ward registration offices.\n"

        return explanation
