# The Antigravity IDE Complete Master Volume: 100% Potential Decoded
> **The Complete Exhaustive Reference: 3 Modalities, 7 Models, 17 Native Tools, 31 MCP Servers (373 Tools), and 57 Specialized Skills.**

---
## 1. The 3 Core AI Modalities
- **Passive: Antigravity Tab**: Real-time next-intent prediction, Tab to Jump, Tab to Import, Supercomplete floating diffs.
- **Instructive: Inline Command (`Ctrl+I` / `Cmd+I`)**: Surgical in-editor code refactoring, code generation at cursor, localized docstrings.
- **Collaborative: Sidebar Chat & Agent Mode**: Full-stack pair programming, inline code lenses, diagnostic auto-fix, visual diff overlays.

---
## 2. The 7 Exact Models & Selection Matrix
1. **Gemini 3.8 Flash (Medium/Low)**: Daily workhorse (80% of tasks), ultra-fast latency, lowest token burn.
2. **Claude Sonnet 5.5 (Medium)**: Gold standard for UI design (CSS/JS) and pristine typed Python refactors.
3. **Claude Opus 5.5 (Medium)**: Maximum cognitive depth (S-tier), novel algorithms, multi-module architecture.
4. **Gemini 3.1 Pro (Low)**: Deliberate multi-hop reasoning, subtle race conditions, memory leaks, security audits.
5. **Gemini 3.7 Flash & 3.6 Flash**: Stable JSON schema output and high-volume batch processing.
6. **GPT-OSS 120B (Medium)**: Neutral open-weights second opinions and independent code review.

---
## 3. Complete MCP Server Ecosystem (31 Servers, 373 Tools)
### 🔌 `StitchMCP` (15 Tools)
- **`apply_design_system`** *(assetId, projectId, selectedScreenInstances)*: Applies a design system to a list of screens. Use this tool when the user wants to update one or more screens to match the style of a design system.
This tool applies the selected design system's foundational design tokens (colors, fonts, shapes, etc.) to the chosen screens, modifying their appearance to align with the design system.

- **`create_design_system`** *(designSystem, projectId)*: Creates a new design system for a project. Use this tool when the user wants to set or update the overall visual theme, style, or branding of the application.
This includes configuring:
- Color Palette: Presets, custom primary colors, and saturation levels.
- Typography: Font families (e.g., Inter, Roboto, etc.).
- Shape: Corner roundness for UI elements.
- Appearance: Light and dark mode background colors.
- Design MD: Free-form design instructions in markdown.
This tool establishes the foundational design tokens that apply across all screens in the project.

**Instructions for Tool Call:**
*  Call `update_design_system` tool immediately after this tool to apply the design system to the project, and display the design system in the UI.

- **`create_design_system_from_design_md`** *(deviceType, projectId, selectedScreenInstance)*: Creates a design system for a project, with user uploaded DESIGN.md file, and displays the design system in the UI.

**Instructions for Tool Call:**
*  Should call `upload_design_md` tool first to upload DESIGN.md to a Stitch project.

- **`create_project`** *(title)*: Creates a new Stitch project. A project is a container for UI designs and frontend code.

- **`delete_project`** *(name)*: Deletes a specific Stitch project using its project name.

**Instructions for Tool Call:**

*  This action cannot be undone. Please confirm with "yes" or "no" to proceed.

- **`edit_screens`** *(deviceType, modelId, projectId, prompt)*: Edits existing screens within a project using a text prompt.

**Instructions for Tool Call:**
*  This action can take a few minutes to complete. Please be patient. DO NOT RETRY.
*  If the tool call fails due to connection error, the process may still succeed.

- **`generate_screen_from_text`** *(designSystem, deviceType, modelId, projectId)*: Generates a new screen within a project from a text prompt.

**Instructions for Tool Call:**
*  This action can take a few minutes to complete. Please be patient. DO NOT RETRY.
*  If the tool fails with a timeout, don't retry. Instead, try to get the screen with `get_screen` method every 30 seconds for up to 10 times before giving up.
*  If the tool call fails due to connection error, the generation process may still succeed. Please try to get the screen with `get_screen` method later.

**Output:**
*  **`output_components`**: If `output_components` contains text, return it to the user. If `output_components` contains suggestions (e.g. "Yes, make them all"), present these suggestions to the user. If the user accepts one of the suggestions, call `generate_screen_from_text` again with `prompt` set to the accepted suggestion.

- **`generate_variants`** *(deviceType, modelId, projectId, prompt)*: Generates variants of existing screens within a project using a text prompt.

**Instructions for Tool Call:**
*  If the tool fails with a timeout, don't retry. Instead, try to get the screen with `get_screen` method every 30 seconds for up to 10 times before giving up.

- **`get_project`** *(name)*: Retrieves the details of a specific Stitch project using its project name.

- **`get_screen`** *(name)*: Retrieves the details of a specific screen within a project.

- **`list_design_systems`** *(projectId)*: Lists all design systems for a given project.

- **`list_projects`** *(filter)*: Lists all Stitch projects accessible to the user. By default, it lists projects owned by the user.

- **`list_screens`** *(projectId)*: Lists all screens within a given Stitch project.

- **`update_design_system`** *(designSystem, name, projectId)*: Updates a design system for a project. Use this tool when the user wants to change the overall visual theme, style, or branding of the application.
This includes configuring:
- Color Palette: Presets, custom primary colors, and saturation levels.
- Typography: Font families (e.g., Inter, Roboto, etc.).
- Shape: Corner roundness for UI elements.
- Appearance: Light and dark mode background colors.
- Design MD: Free-form design instructions in markdown.
This tool establishes the foundational design tokens that apply across all screens in the project.

- **`upload_design_md`** *(designMdBase64, projectId)*: Uploads DESIGN.md to a Stitch project. Use this tool when the user wants to create a design system from a DESIGN.md file.

**Instructions for Tool Call:**
*  Call `create_design_system_from_design_md` tool immediately after this tool to create the design system from the uploaded DESIGN.md, and display the design system in the UI.


### 🔌 `android-management-api` (9 Tools)
- **`get_application`** *(languageCode, name)*: Gets application details for a given enterprise and application ID. Requires the resource name in the format: enterprises/{enterpriseId}/applications/{applicationId}.
- **`get_device`** *(name)*: Gets device details for a given enterprise and device ID. Requires the resource name in the format: enterprises/{enterpriseId}/devices/{deviceId}.
- **`get_enterprise`** *(name)*: Gets an enterprise for a given enterprise ID. Requires the enterprise ID in the name field (e.g., enterprises/{enterpriseId}).
- **`get_policy`** *(name)*: Gets a policy for a given enterprise and policy ID. Requires the resource name in the format: enterprises/{enterpriseId}/policies/{policyId}.
- **`get_web_app`** *(name)*: Gets a web app. Requires the resource name in the format: enterprises/{enterpriseId}/webApps/{webAppId}.
- **`list_devices`** *(pageSize, pageToken, parent)*: Lists devices for a given enterprise. Requires the enterprise ID in the parent field (e.g., enterprises/{enterpriseId}).
- **`list_enterprises`** *(pageSize, pageToken, projectId, view)*: Lists enterprises accessible to the caller.
- **`list_policies`** *(pageSize, pageToken, parent)*: Lists policies for a given enterprise. Requires the enterprise resource name in the parent field (e.g., enterprises/{enterpriseId}).
- **`list_web_apps`** *(pageSize, pageToken, parent)*: Lists web apps for a given enterprise. Requires the enterprise resource name in the parent field (e.g., enterprises/{enterpriseId}).

### 🔌 `arize-tracing-assistant` (3 Tools)
- **`arize_support`** *(message)*: Send *message* to the `search` tool and return the assistant reply.

    Parameters
    ----------
    message : str
        The user message to send to the assistant.

    Returns
    -------
    str
        The assistant's textual response.
    
- **`get_arize_advanced_tracing_docs`** *(language)*: 
    Get advanced docs and examples to manually instrument an app and send traces/spans to Arize.

     Parameters
    ----------:
    language: str
        "python" or "typescript" or "javascript"

    Returns:
    str
        Docs and code snippets for advanced instrumentation.
    
- **`get_arize_tracing_docs`** *(framework, language)*: 
    Get docs and examples to instrument an app and send traces/spans to Arize.
    If the framework is not in the list use manual instrumentation with open telemetry.

    Parameters
    ----------
    framework : str
        LLM provider or framework. One of:
        ["agno", "amazon-bedrock", "anthropic", "autogen", "beeai", "crewai", "dspy", "google-gen-ai", "groq", "guardrails-ai", "haystack",
        "hugging-face-smolagents", "instructor", "langchain", "langflow", "langgraph", "litellm", "llamaindex", "mistralai", "openai", "openai-agents", "prompt-flow",
        "pydantic-ai", "strands-agents", "together", "vercel", "vertexai"]
    language : str
        Programming language: "python" or "typescript"

    Returns
    -------
    str
        Example code snippets for auto/manual instrumentation for Arize.
    

### 🔌 `bigquery` (8 Tools)
- **`cancel_job`** *(jobId, location, projectId)*: Cancel a running BigQuery job.

Use this tool to cancel a query job that is currently executing (i.e. returned `job_complete: false`
with a `job_id` from `execute_sql` or `execute_sql_readonly`). Specify the `job_id` to abort.

- **`execute_sql`** *(dryRun, jobTimeoutMs, labels, projectId)*: Run a SQL query in the project and return the result. Prefer the `execute_sql_readonly`
tool if possible.

This tool can execute any query that bigquery supports including:

* SQL Queries (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, etc.)
* AI/ML functions like `AI.FORECAST`, `ML.EVALUATE`, `ML.PREDICT`
* Any other query that bigquery supports.

Example Queries:

```sql
-- Insert data into a table.
INSERT INTO `my_project.my_dataset`.my_table (name, age)
VALUES ('Alice', 30);

-- Create a table.
CREATE TABLE `my_project.my_dataset`.my_table (
  name STRING,
  age INT64);

-- DELETE data from a table.
DELETE FROM `my_project.my_dataset`.my_table WHERE name = 'Alice';

-- Create Dataset
CREATE SCHEMA `my_project.my_dataset` OPTIONS (location = 'US');

-- Drop table
DROP TABLE `my_project.my_dataset`.my_table;

-- Drop dataset
DROP SCHEMA `my_project.my_dataset`;

-- Create Model
CREATE OR REPLACE MODEL `my_project.my_dataset.my_model`
OPTIONS (
  model_type = 'LINEAR_REG'
  LS_INIT_LEARN_RATE=0.15,
  L1_REG=1,
  MAX_ITERATIONS=5,
  DATA_SPLIT_METHOD='SEQ',
  DATA_SPLIT_EVAL_FRACTION=0.3,
  DATA_SPLIT_COL='timestamp') AS
SELECT col1, col2, timestamp, label FROM `my_project.my_dataset.my_table`;
```

Queries executed using the `execute_sql` tool will always have the default job label
`goog-mcp-server: true` automatically set in addition to any custom `labels` provided in the
request. Queries are charged to the project specified in the `project_id` field.

Query Execution Behavior:
* If the query completes within the synchronous timeout (default 20 seconds or custom `timeout_ms`),
  the tool returns `job_complete: true` and the initial result rows directly. For fast queries, `job_id` may
  be omitted as no persistent background job is created; no further action or polling is needed.
* If the query takes longer than `timeout_ms`, the tool returns `job_complete: false` and a `job_id`.
  In this case, use the `get_query_results` tool with `job_id` to poll until `job_complete: true`,
  or use `cancel_job` to abort the running query.
* You can optionally specify `timeout_ms` to configure the maximum synchronous wait time in milliseconds
  (defaults to 20,000 ms), and `job_timeout_ms` to enforce a hard server-side timeout after which
  BigQuery automatically terminates the job.

- **`execute_sql_readonly`** *(dryRun, jobTimeoutMs, labels, projectId)*: Run a read-only SQL query in the project and return the result. Prefer this tool over
`execute_sql` if possible.

This tool is restricted to only `SELECT` statements. `INSERT`, `UPDATE`, and `DELETE`
statements and stored procedures aren't allowed. If the query doesn't include a `SELECT`
statement, an error is returned. For information on creating queries, see the [GoogleSQL
documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax).


Example Queries:

```sql
-- Count the number of penguins in each island.
SELECT island, COUNT(*) AS population
FROM bigquery-public-data.ml_datasets.penguins GROUP BY island

-- Evaluate a bigquery ML Model.
SELECT * FROM ML.EVALUATE(MODEL `my_dataset.my_model`)

-- Evaluate BigQuery ML model on custom data
SELECT *
FROM ML.EVALUATE(MODEL `my_dataset.my_model`, (SELECT * FROM `my_dataset.my_table`))

-- Predict using BigQuery ML model:
SELECT *
FROM ML.PREDICT(MODEL `my_dataset.my_model`, (SELECT * FROM `my_dataset.my_table`))

-- Forecast data using AI.FORECAST
SELECT *
FROM AI.FORECAST(TABLE `project.dataset.my_table`, data_col => 'num_trips',
  timestamp_col => 'date', id_cols => ['usertype'], horizon => 30)
```

Queries executed using the `execute_sql_readonly` tool will always have the job label
`goog-mcp-server: true` automatically set in addition to any custom `labels` provided in
the request. Queries are charged to the project specified in the `project_id` field.

Query Execution Behavior:
* If the query completes within the synchronous timeout (default 20 seconds or custom `timeout_ms`),
  the tool returns `job_complete: true` and the result rows directly. For fast queries, `job_id` may
  be omitted as no persistent background job is created; no further action or polling is needed.
* If the query takes longer than `timeout_ms`, the tool returns `job_complete: false` and a `job_id`.
  In this case, use the `get_query_results` tool with `job_id` to poll until `job_complete: true`,
  or use `cancel_job` to abort the running query.
* You can optionally specify `timeout_ms` to configure the maximum synchronous wait time in milliseconds
  (defaults to 20,000 ms), and `job_timeout_ms` to enforce a hard server-side timeout after which
  BigQuery automatically terminates the job.

- **`get_dataset_info`** *(datasetId, projectId)*: Get metadata information about a BigQuery dataset or BigLake namespace.
- **`get_query_results`** *(jobId, location, maxResults, pageToken)*: Get the results of a BigQuery SQL query job.

Use this tool ONLY when:
1. A previous `execute_sql` or `execute_sql_readonly` call returned `job_complete: false` with a `job_id`
   (poll with this tool until `job_complete: true`), OR
2. You need to paginate through additional rows using `page_token` or `start_index` for a previously completed job.

Do NOT call this tool if the query already returned `job_complete: true` with all rows.

Supports pagination. Use `max_results` to limit results and `page_token` to retrieve the next page of results.

- **`get_table_info`** *(datasetId, projectId, tableId)*: Get metadata information about a BigQuery table or BigLake table.
- **`list_dataset_ids`** *(pageSize, pageToken, projectId)*: List BigQuery dataset IDs and BigLake namespaces in a Google Cloud project.
Supports pagination. Use `page_size` to limit results and `page_token` to retrieve next page.

- **`list_table_ids`** *(datasetId, pageSize, pageToken, projectId)*: List table ids in a BigQuery dataset or BigLake namespace.
Supports pagination. Use `page_size` to limit results and `page_token` to retrieve next page.


### 🔌 `bionemo-tools` (8 Tools)
- **`bionemo_compare_known_inhibitors`** *(candidate_affinity_kcal_mol, target_name)*: 
    Benchmark AI-generated candidate molecules against clinically approved reference drugs.
    
    Args:
        target_name: Target identifier or disease (e.g. 'EGFR', 'Mpro', 'HER2', 'KRAS', 'PARP1').
        candidate_affinity_kcal_mol: Optional predicted affinity of candidate (in kcal/mol, e.g. -9.5).
        
    Returns:
        Clinical reference drug benchmarks with IC50, experimental affinity, and comparative score.
    
- **`bionemo_fetch_rcsb_pdb`** *(pdb_id)*: 
    Fetch, clean, and validate macromolecular structures directly from RCSB PDB.
    Strips solvent, crystallographic waters, and isolates canonical protein chains.
    
    Args:
        pdb_id: 4-character PDB code (e.g. '2ITZ', '6LU7', '8AZV', '4MNE').
        
    Returns:
        Dictionary with status, clean PDB atom count, residue count, and extracted sequence.
    
- **`bionemo_query_diffdock`** *(ligand_smiles, mock, pdb_content, protein_sequence)*: 
    Predict small molecule binding poses and affinities using NVIDIA NIM DiffDock.
    
    Args:
        protein_sequence: Amino acid sequence of the target protein.
        ligand_smiles: SMILES string of the small molecule drug/ligand.
        pdb_content: Optional raw PDB file string. If not provided, a synthetic backbone is generated.
        mock: If True, uses simulated realistic response. If False, calls live NIM endpoint.
        
    Returns:
        Docking results including top affinity (kcal/mol), number of poses, and latency profile.
    
- **`bionemo_query_esm2_embedding`** *(mock, sequence)*: 
    Query NVIDIA NIM ESM-2 (650M) for per-residue embeddings.
    
    Args:
        sequence: Valid IUPAC protein amino acid sequence.
        mock: If True, uses the realistic simulation mock (zero API credits required).
              If False, calls live NVIDIA NIM microservice using NVIDIA_API_KEY.
              
    Returns:
        Summary of sequence length, hidden dimension, latency breakdown, and embedding shape.
    
- **`bionemo_query_esmfold`** *(mock, sequence)*: 
    Predict atomic 3D protein structure from amino acid sequence via NVIDIA BioNeMo ESMFold NIM.
    
    Args:
        sequence: IUPAC protein amino acid sequence.
        mock: If True, uses zero-credit realistic simulation with predicted pLDDT confidence.
              If False, calls live NVIDIA NIM ESMFold endpoint.
              
    Returns:
        Dictionary with predicted structure status, average pLDDT confidence, and atom records.
    
- **`bionemo_run_benchmark`** *(complexes_path, mock, save_plots)*: 
    Execute the NVIDIA BioNeMo & NIM Inference Benchmark Suite across the sample complexes.
    
    Args:
        mock: If True, executes using zero-configuration simulated responses.
              If False, connects to live NVIDIA NIM endpoints using NVIDIA_API_KEY.
        complexes_path: Path to JSON file containing complexes (default: data/sample_complexes.json).
        save_plots: Whether to save visualization PNG charts to results/.
        
    Returns:
        Consolidated summary metrics table, speedup factors, and throughput.
    
- **`bionemo_sanitize_smiles`** *(smiles)*: 
    Validate, sanitize, and extract physicochemical descriptors for a small molecule SMILES
    before dispatching to NVIDIA NIM DiffDock or MolMIM.
    
    Args:
        smiles: Chemical structure SMILES string.
        
    Returns:
        Dictionary containing canonical SMILES, Molecular Weight, LogP, TPSA, HBD, HBA.
    
- **`bionemo_validate_sequence`** *(sequence)*: 
    Validate and profile a protein amino acid sequence for NVIDIA BioNeMo / ESM-2.
    
    Args:
        sequence: Single-letter amino acid sequence (IUPAC format).
        
    Returns:
        Dictionary with validation status, clean sequence, length, and residue frequency.
    

### 🔌 `chrome-devtools-mcp` (30 Tools)
- **`click`** *(dblClick, includeSnapshot, pageId, uid)*: Clicks on the provided element
- **`close_page`** *(pageId)*: Closes the page by its index. The last open page cannot be closed.
- **`drag`** *(from_uid, includeSnapshot, pageId, to_uid)*: Drag an element onto another element
- **`emulate`** *(colorScheme, cpuThrottlingRate, extraHttpHeaders, geolocation)*: Emulates various features on the target page.
- **`evaluate_script`** *(args, dialogAction, filePath, function)*: Evaluate a JavaScript function inside the target page. Returns the response as JSON, so returned values have to be JSON-serializable.
- **`fill`** *(includeSnapshot, pageId, uid, value)*: Type text into an input, text area or select an option from a <select> element.
- **`fill_form`** *(elements, includeSnapshot, pageId)*: Fill out multiple form elements (inputs, selects, checkboxes, radios) at once. ALWAYS prefer this tool over multiple individual 'fill' or 'click' calls when interacting with forms. It is significantly faster, more reliable, and reduces turn count. Example: Fill username, password, and check "Remember Me" in one call.
- **`get_console_message`** *(msgid, pageId)*: Gets a console message by its ID. You can get all messages by calling list_console_messages.
- **`get_css_styles`** *(pageId, pageIdx, pageSize, uid)*: Retrieve matched CSS rules, inline styles, inherited styles, and cascade information for an element identified by its UID.
Use this tool to debug why specific CSS properties are applied, overridden, or conflicting. Results are paginated and return 10 rules per page by default; use pageIdx to page through the remaining rules. Requires a UID from take_snapshot.
- **`get_network_request`** *(pageId, reqid, requestFilePath, responseFilePath)*: Gets a network request by an optional reqid, if omitted returns the currently selected request in the DevTools Network panel. Useful for inspecting request headers (including 'Cookie') and response headers (including 'Set-Cookie' and directives).
- **`handle_dialog`** *(action, pageId, promptText)*: If a browser dialog was opened, use this command to handle it
- **`hover`** *(includeSnapshot, pageId, uid)*: Hover over the provided element
- **`lighthouse_audit`** *(device, mode, outputDirPath, pageId)*: Get Lighthouse score and reports for accessibility, SEO, best practices, and agentic browsing. This excludes performance. For performance audits, run performance_start_trace
- **`list_console_messages`** *(includePreservedMessages, includeStackTraces, pageId, pageIdx)*: List all console messages for the target page since the last navigation.
- **`list_network_requests`** *(includePreservedRequests, pageId, pageIdx, pageSize)*: Lists the most recent requests for the target page since the last navigation.
- **`list_pages`**: Get a list of pages open in the browser.
- **`navigate_page`** *(handleBeforeUnload, ignoreCache, initScript, pageId)*: Go to a URL, or back, forward, or reload. Use project URL if not specified otherwise.
- **`new_page`** *(background, isolatedContext, timeout, url)*: Open a new tab and load a URL. Use project URL if not specified otherwise.
- **`performance_analyze_insight`** *(insightName, insightSetId, pageId)*: Provides more detailed information on a specific Performance Insight of an insight set that was highlighted in the results of a trace recording.
- **`performance_start_trace`** *(autoStop, filePath, pageId, reload)*: Start a performance trace on the target webpage. Use to find frontend performance issues, Core Web Vitals (LCP, INP, CLS), and improve page load speed.
- **`performance_stop_trace`** *(filePath, pageId)*: Stop the active performance trace recording on the target webpage.
- **`press_key`** *(includeSnapshot, key, pageId)*: Press a key or key combination. Use this when other input methods like fill() cannot be used (e.g., keyboard shortcuts, navigation keys, or special key combinations).
- **`resize_page`** *(height, pageId, width)*: Resizes the page's window so that the page has specified dimension
- **`select_page`** *(bringToFront, pageId)*: Select a page as a context for future tool calls.
- **`take_heapsnapshot`** *(filePath, pageId)*: Capture a heap snapshot of the target page. Use to analyze the memory distribution of JavaScript objects and debug memory leaks.
- **`take_screenshot`** *(filePath, format, fullPage, pageId)*: Take a screenshot of the page or element.
- **`take_snapshot`** *(filePath, pageId, verbose)*: Take a text snapshot of the target page based on the a11y tree. The snapshot lists page elements along with a unique
identifier (uid). Always use the latest snapshot. Prefer taking a snapshot over taking a screenshot. The snapshot indicates the element selected
in the DevTools Elements panel (if any).
- **`type_text`** *(pageId, submitKey, text)*: Type text using keyboard into a previously focused input
- **`upload_file`** *(filePaths, includeSnapshot, pageId, uid)*: Upload a file through a provided element.
- **`wait_for`** *(pageId, text, timeout)*: Wait for the specified text to appear on the selected page.

### 🔌 `clickhouse` (17 Tools)
- **`get_clickpipe`** *(clickPipeId, organizationId, serviceId)*: Returns the specified ClickPipe.
- **`get_organization_cost`** *(from_date, organizationId, to_date)*: Retrieves billing and usage cost data for a ClickHouse Cloud organization. Returns a grand total and a list of daily, per-entity organization usage cost records for the organization in the queried time period (maximum 31 days).
- **`get_organization_details`** *(organizationId)*: Returns details of a single organization. The auth key must belong to the organization.
- **`get_organizations`**: Retrieves all accessible ClickHouse Cloud organizations.
- **`get_postgres_metrics`** *(bucketSizeSeconds, fromDate, organizationId, serviceId)*: Returns bucketed time-series metrics for a Postgres service over a time window (CPU, memory, disk, network, connections, cache hit ratio, throughput, transactions, and more). Each metric has a key, name, unit, description, and one series per label dimension, where each series is a list of (timestamp, value) data points. Timestamps are Unix seconds at the bucket start. Provide fromDate and toDate to bound the window; omit bucketSizeSeconds to let the server pick a bucket granularity for the window. Use this to chart or analyze how a service behaved over time.
- **`get_postgres_slow_query_pattern_details`** *(app, dbName, dbOperation, dbUser)*: Returns up to the 10 most recent individual executions for a single Postgres slow query pattern from the last 24 hours, plus aggregate metrics for the pattern when available. For exact drill-down from list_postgres_slow_query_patterns, pass queryId, dbName, dbUser, dbOperation, and app exactly as returned; pass app as an empty string when the selected pattern has no application_name. Omit app only when intentionally querying across all applications. Each execution includes duration, rows, buffer/temp/WAL/JIT/CPU counters, and the error message and SQLSTATE if it failed. Durations are in microseconds. The execution sample is capped at 10 rows, so when aggregate is present rely on its fields for totals.
- **`get_service_backup_configuration`** *(organizationId, serviceId)*: Returns the service backup configuration.
- **`get_service_backup_details`** *(backupId, organizationId, serviceId)*: Returns a single backup info.
- **`get_service_details`** *(organizationId, serviceId)*: Returns a service that belongs to the organization. Supports both ClickHouse services and Managed Postgres services; the service type is detected automatically from the service id and is reported in the `serviceType` field of the response.
- **`get_services_list`** *(organizationId)*: Retrieves all ClickHouse and Managed Postgres services in a ClickHouse Cloud organization.
- **`list_clickpipes`** *(organizationId, serviceId)*: Retrieves all ClickPipes configured for a specific service.
- **`list_databases`** *(serviceId)*: Retrieves all databases available in a ClickHouse service.
- **`list_postgres_slow_query_patterns`** *(app, dbName, dbOperation, dbUser)*: Lists the slowest query patterns observed on a Postgres service in a time window, with aggregate metrics per pattern (call count, total/avg/p50/p95/p99/max duration, rows, shared buffer cache hits and reads, CPU time, WAL bytes, error count). Durations are in microseconds. Use this first to find which queries dominate execution time, CPU, I/O, or WAL, then pass a selected pattern queryId, dbName, dbUser, dbOperation, and app exactly as returned to get_postgres_slow_query_pattern_details for its recent executions. Pass app as an empty string when the selected pattern has no application_name; omit the app filter only when intentionally querying across all applications. The queryText is normalized with $1-style placeholders.
- **`list_service_backups`** *(organizationId, serviceId)*: Returns a list of all backups for the service. The most recent backups comes first in the list.
- **`list_tables`** *(database, like, notLike, serviceId)*: Retrieves a comprehensive list of tables in a ClickHouse database, including columns.
- **`run_postgres_select_query`** *(database, organizationId, query, serviceId)*: Executes a read-only SELECT query against a Postgres service. The query is routed through the Postgres query endpoint with the read-only role and only read-style statements are permitted.
- **`run_select_query`** *(query, serviceId, timeoutSeconds)*: Executes a SELECT query against a ClickHouse service. Runs a read-only SELECT query on the specified ClickHouse service via the Query API endpoint. This function provides direct access to database content through SQL queries while ensuring that only read operations are permitted.

### 🔌 `cloud-sql` (15 Tools)
- **`clone_instance`** *(body, instance, location, project)*: Create a Cloud SQL instance as a clone of a source instance.

* This tool returns a long-running operation. Use the `get_operation` tool to poll its
  status until the operation completes.
* The clone operation can take several minutes. Use a command line tool to pause for 30
  seconds before rechecking the status.

- **`create_backup`** *(description, instance, location, project)*: Takes a backup on a Cloud SQL instance. Always populate the project and instance fields on
the request. The location (region) and description of the backup may also be optionally
provided, in which case the corresponding request fields should also be populated.

- **`create_instance`** *(availabilityType, dataCacheEnabled, dataDiskSizeGb, databaseVersion)*: Initiates the creation of a Cloud SQL instance.

* The tool returns a long-running operation. Use the `get_operation` tool to poll its status
  until the operation completes.
* The instance creation operation can take several minutes. Use a command line tool to pause
  for 30 seconds before rechecking the status.
* After you use the `create_instance` tool to create an instance,
  you can use the `create_user` tool to create an
  IAM user account for the user currently logged in to the project.
* IMPORTANT: Set `ipv4_enabled` to 'false' if creating a Private Service Connect
  or a Private Service Access instance.
* Set `free_trial` to 'true' to create a free trial instance. Free trial instances
  let you test majority of Cloud SQL features for up to 30 days without financial
  commitment. Subject to eligibility and availability.

* The value of `data_api_access` is set to `ALLOW_DATA_API` by default. This setting
  lets you execute SQL statements using the `execute_sql` tool and the `executeSql` API.

  Unless otherwise specified, a newly created instance uses the default
  instance configuration of a development environment.

  The following is the default configuration for an instance in a
  development environment:

```
{
  "tier": "db-perf-optimized-N-2",
  "data_disk_size_gb": 100,
  "region": "us-central1",
  "database_version": "POSTGRES_18",
  "edition": "ENTERPRISE_PLUS",
  "availability_type": "ZONAL",
  "tags": [{"environment": "dev"}]
}
```

The following configuration is recommended for an instance in a
production environment:

```
{
  "tier": "db-perf-optimized-N-8",
  "data_disk_size_gb": 250,
  "region": "us-central1",
  "database_version": "POSTGRES_18",
  "edition": "ENTERPRISE_PLUS",
  "availability_type": "REGIONAL",
  "tags": [{"environment": "prod"}]
}
```

The following instance configuration is recommended for SQL Server:

```
{
  "tier": "db-perf-optimized-N-8",
  "data_disk_size_gb": 250,
  "region": "us-central1",
  "database_version": "SQLSERVER_2022_STANDARD",
  "edition": "ENTERPRISE",
  "availability_type": "REGIONAL",
  "tags": [{"environment": "prod"}]
}
```

- **`create_user`** *(databaseRoles, instance, name, passwordSecretVersion)*: Create a database user for a Cloud SQL instance.

* This tool returns a long-running operation. Use the `get_operation` tool to poll
  its status until the operation completes.
* When you use the `create_user` tool, specify the type of user:
 `CLOUD_IAM_USER`, `CLOUD_IAM_SERVICE_ACCOUNT`, or `BUILT_IN`.
* By default the newly created user is assigned the `cloudsqlsuperuser` role, unless
  you specify other database roles explicitly in the request.
* You can use a newly created user with the `execute_sql` tool if the user is a
  currently logged in IAM user. The `execute_sql` tool executes the SQL statements
  using the privileges of the database user logged in using IAM database
  authentication.

The `create_user` tool has the following limitations:

* To create a built-in user with password, use the `password_secret_version` field to provide password using the
  Google Cloud Secret Manager. The value of `password_secret_version` should be the resource name of
  the secret version, like `projects/12345/locations/us-central1/secrets/my-password-secret/versions/1` or
  `projects/12345/locations/us-central1/secrets/my-password-secret/versions/latest`. The caller needs to have
  `secretmanager.secretVersions.access` permission on the secret version.
* The `create_user` tool doesn't support creating a user for SQL Server.

To create an IAM user in PostgreSQL:

* The database username must be the IAM user's email address and all lowercase.
  For example, to create user for PostgreSQL IAM user `example-user@example.com`,
  you can use the following request:

```
{
  "name": "example-user@example.com",
  "type": "CLOUD_IAM_USER",
  "instance":"test-instance",
  "project": "test-project"
}
```

The created database username for the IAM user is `example-user@example.com`.

To create an IAM service account in PostgreSQL:

* The database username must be created without the `.gserviceaccount.com` suffix even though
  the full email address for the account is`service-account-name@project-id.iam.gserviceaccount.com`.
  For example, to create an IAM service account for PostgreSQL you can use the following request
  format:

```
{
   "name": "test@test-project.iam",
   "type": "CLOUD_IAM_SERVICE_ACCOUNT",
   "instance": "test-instance",
   "project": "test-project"
}
```

The created database username for the IAM service account is `test@test-project.iam`.

To create an IAM user or IAM service account in MySQL:

* When Cloud SQL for MySQL stores a username, it truncates the @ and the domain name from
  the user or service account's email address.
  For example, `example-user@example.com` becomes `example-user`.
* For this reason, you can't add two IAM users or service accounts
 with the same username but different domain names to the same Cloud SQL instance.
* For example, to create user for the MySQL IAM user `example-user@example.com`,
  use the following request:

```
{
   "name": "example-user@example.com",
   "type": "CLOUD_IAM_USER",
   "instance": "test-instance",
   "project": "test-project"
}
```

The created database username for the IAM user is `example-user`.

* For example, to create the MySQL IAM service account
`service-account-name@project-id.iam.gserviceaccount.com`, use the
following request:

```
{
   "name": "service-account-name@project-id.iam.gserviceaccount.com",
   "type": "CLOUD_IAM_SERVICE_ACCOUNT",
   "instance": "test-instance",
   "project": "test-project"
}
```

The created database username for the IAM service account is
`service-account-name`.

- **`execute_sql`** *(database, instance, passwordSecretVersion, project)*: Execute any valid SQL statement, including data definition language (DDL),
data control language (DCL), data query language (DQL), or
data manipulation language (DML) statements, on a Cloud SQL instance.

To support the `execute_sql` tool, a Cloud SQL instance must meet
the following requirements:

* The value of `data_api_access` must be set to `ALLOW_DATA_API`.
* For built_in users password_secret_version must be set.
* Otherwise, for IAM users, for a MySQL instance, the database flag
  `cloudsql_iam_authentication` must be set to `on`.
  For a PostgreSQL instance, the database flag `cloudsql.iam_authentication` must be set
  to `on`.
* After you use the `create_instance` tool to create an instance,
  you can use the `create_user` tool to create an
  IAM user account for the user currently logged in to the project.

  The `execute_sql` tool has the following limitations:

* If a SQL statement returns a response larger than 10&nbsp;MB,
  then the response will be truncated.
* The `execute_sql` tool has a default timeout of 30 seconds.
  If a query runs longer than 30 seconds, then the tool returns a
 `DEADLINE_EXCEEDED` error.

 If you receive errors similar to "IAM authentication is not enabled for the instance",
 then you can use the `get_instance` tool to check the value of the IAM
 database authentication flag for the instance.

 If you receive errors like "The instance doesn't allow using executeSql to access this
 instance", then you can use `get_instance` tool to check the `data_api_access` setting.

 When you receive authentication errors:

 1. Check if the currently logged-in user account exists as an IAM user on the
    instance using the `list_users` tool.
 2. If the IAM user account doesn't exist, then use the `create_user` tool to
    create the IAM user account for the logged-in user.
 3. If the currently logged in user doesn't have the proper database user roles, then
    you can use `update_user` tool to grant database roles to the user. For example,
    `cloudsqlsuperuser` role can provide an IAM user with many required permissions.
 4. Check if the currently logged in user has the correct IAM permissions assigned for
    the project. You can use `gcloud projects get-iam-policy [PROJECT_ID]` command to
    check if the user has the proper IAM roles or permissions assigned for the project.

     * The user must have `cloudsql.instance.login` permission to do automatic IAM database
       authentication.
     * The user must have `cloudsql.instances.executeSql` permission to execute SQL statements
       using the `execute_sql` tool or `executeSql` API.
    *  Common IAM roles that contain the required permissions: Cloud SQL Instance User
      (`roles/cloudsql.instanceUser`) or Cloud SQL Admin (`roles/cloudsql.admin`)

When receiving an `ExecuteSqlResponse`, always check the `message` and `status` fields
within the response body. A successful HTTP status code doesn't guarantee full success of
all SQL statements.
The `message` and `status` fields will indicate if there were any partial errors or
warnings during SQL statement execution.

- **`execute_sql_readonly`** *(database, instance, passwordSecretVersion, project)*: Execute any valid read only SQL statement on a Cloud SQL instance.

To support the `execute_sql_readonly` tool, a Cloud SQL instance must meet
the following requirements:

* The value of `data_api_access` must be set to `ALLOW_DATA_API`.
* For a MySQL instance, the database flag `cloudsql_iam_authentication` must be set to `on`.
  For a PostgreSQL instance, the database flag `cloudsql.iam_authentication` must be set
  to `on`.
* An IAM user account or IAM service account (`CLOUD_IAM_USER` or `CLOUD_IAM_SERVICE_ACCOUNT`)
  is required to call the `execute_sql_readonly` tool.
  The tool executes the SQL statements using the privileges of the database user
  logged with IAM database authentication.

  After you use the `create_instance` tool to create an instance,
  you can use the `create_user` tool to create an
  IAM user account for the user currently logged in to the project.

  The `execute_sql_readonly` tool has the following limitations:

* If a SQL statement returns a response larger than 10&nbsp;MB,
  then the response will be truncated.
* The tool has a default timeout of 30 seconds.
  If a query runs longer than 30 seconds, then the tool returns a
 `DEADLINE_EXCEEDED` error.

 If you receive errors similar to "IAM authentication is not enabled for the instance",
 then you can use the `get_instance` tool to check the value of the IAM
 database authentication flag for the instance.

 If you receive errors like "The instance doesn't allow using executeSql to access this
 instance", then you can use `get_instance` tool to check the `data_api_access` setting.

 When you receive authentication errors:

 1. Check if the currently logged-in user account exists as an IAM user on the
    instance using the `list_users` tool.
 2. If the IAM user account doesn't exist, then use the `create_user` tool to
    create the IAM user account for the logged-in user.
 3. If the currently logged in user doesn't have the proper database user roles, then
    you can use `update_user` tool to grant database roles to the user. For example,
    `cloudsqlsuperuser` role can provide an IAM user with many required permissions.
 4. Check if the currently logged in user has the correct IAM permissions assigned for
    the project. You can use `gcloud projects get-iam-policy [PROJECT_ID]` command to
    check if the user has the proper IAM roles or permissions assigned for the project.

     * The user must have `cloudsql.instance.login` permission to do automatic IAM database
       authentication.
     * The user must have `cloudsql.instances.executeSql` permission to execute SQL statements
       using the `execute_sql_readonly` tool or `executeSql` API.
    *  Common IAM roles that contain the required permissions: Cloud SQL Instance User
      (`roles/cloudsql.instanceUser`) or Cloud SQL Admin (`roles/cloudsql.admin`)

When receiving an `ExecuteSqlResponse`, always check the `message` and `status` fields
within the response body. A successful HTTP status code doesn't guarantee full success of
all SQL statements.
The `message` and `status` fields will indicate if there were any partial errors or
warnings during SQL statement execution.

- **`get_instance`** *(instance, location, project)*: Get the details of a Cloud SQL instance.
- **`get_operation`** *(location, operation, project)*: Get the status of a long-running operation. A long-running operation can take several
minutes to complete. If an operation takes an extended amount of time, then use a command
line tool to pause for 30 seconds before rechecking the status of the operation.

- **`import_data`** *(body, instance, location, project)*: Import data into a Cloud SQL instance.

If the file doesn't start with `gs://`, then the assumption is that the file is stored
locally. If the file is local, then the file must be uploaded to Cloud Storage
before you can make the actual `import_data` call. To upload the file to Cloud Storage,
you can use the `gcloud` or `gsutil` commands.

Before you upload the file to Cloud Storage, consider whether you want to use an existing
bucket or create a new bucket in the provided project.

After the file is uploaded to Cloud Storage, the instance service account must have
sufficient permissions to read the uploaded file from the Cloud Storage bucket.

This can be accomplished as follows:

1. Use the `get_instance` tool to get the email address of the instance service account.
   From the output of the tool, get the value of the `serviceAccountEmailAddress` field.
2. Grant the instance service account the `storage.objectAdmin` role on the
   provided Cloud Storage bucket. Use a command like `gcloud storage buckets
   add-iam-policy-binding` or a request to the Cloud Storage API. It can take from
   two to up to seven minutes or more for the role to be granted and the permissions to be
   propagated to the service account in Cloud Storage. If you encounter a permissions error
   after updatingthe IAM policy, then wait a few minutes and try again.

After permissions are granted, you can import the data. We recommend that you leave optional
parameters empty and use the system defaults. The file type can typically be determined by
the file extension. For example, if the file is a SQL file, `.sql` or `.csv` for CSV file.

The following is a sample SQL `importContext` for MySQL.

```
{
  "uri": "gs://sample-gcs-bucket/sample-file.sql",
  "kind": "sql#importContext",
  "fileType": "SQL"
}
```

There is no `database` parameter present for MySQL since the database name is
expected to be present in the SQL file. Specify only one URI.
No other fields are required outside of `importContext`.

For PostgreSQL, the `database` field is required. The following is a sample
PostgreSQL `importContext` with the `database` field specified.

```
{
  "uri": "gs://sample-gcs-bucket/sample-file.sql",
  "kind": "sql#importContext",
  "fileType": "SQL",
  "database": "sample-db"
}
```

The `import_data` tool returns a long-running operation. Use the `get_operation` tool
to poll its status until the operation completes.

- **`list_instances`** *(filter, location, maxResults, pageToken)*: List all Cloud SQL instances in the project.
- **`list_users`** *(instance, location, project)*: List all database users for a Cloud SQL instance.
- **`postgres_upgrade_precheck`** *(body, instance, location, project)*: Checks if a Cloud SQL for PostgreSQL instance is ready for a major version upgrade to the
specified target version.

The `target_database_version` MUST be provided in the request (e.g., `POSTGRES_15`).

This tool helps identify potential issues *before*
attempting the actual upgrade, reducing the risk of failure or downtime.

This tool is only supported for PostgreSQL primary instances and does not run on read replicas.

The precheck typically evaluates:

- Database schema compatibility with the target version.
- Cloud SQL limitations and unsupported features.
- Instance resource constraints (e.g., number of relations).
- Compatibility of current database settings and extensions.
- Overall instance health and readiness.

This tool returns a long-running operation. Use the `get_operation`
tool with the operation name returned by this call to poll its status.

IMPORTANT: Once the operation status is DONE, the detailed precheck results are
available within the `Operation` resource. You will need to inspect
the response from `get_operation`. The findings are located in the
`pre_check_major_version_upgrade_context.pre_check_response` field.

The findings are structured, indicating:

  - INFO: General information.
  - WARNING: Potential issues that don't block the upgrade but should be reviewed.
  - ERROR: Critical issues that MUST be resolved before attempting the upgrade.

Each finding should include a message and any required actions. Addressing
any reported issues is crucial before proceeding with the major version upgrade.
If `pre_check_response` is empty or missing, it indicates that no issues were
identified during the precheck.

Running this precheck does not impact the instance's availability.

- **`restore_backup`** *(backupId, sourceInstance, sourceProject, targetInstance)*: Restores a backup to a Cloud SQL instance.

The target_instance and target_project must be provided and populated in the request.

The backup identifier can be provided in several ways:

1. A backup_run_id (which is an integer).
2. A backup URI of the format `projects/{project-id}/backups/{backup-uid}`.
3. A backup URI of the format `projects/{project-id}/locations/{location}/backupVaults/{backupvault}/dataSources/{datasource}/backups/{backup-uid}`.

Use the identifier to populate the `backup_id` field in the request.

The source_project must be populated in the request. If the identifier is a backup_run_id,
the source_project will be provided. If the identifier is a backup URI, the source_project
may need to be extracted from the URI. Do not confuse the extracted source_project with the
target_project, which will be provided in other ways.

In addition, if the identifier is a backup_run_id, the source_instance must be provided and
populated in the request.

Do not try to create the instance before the restore, the restore itself will create the
instance if needed.

Confirm the parameters with the user before executing the restore.

- **`update_instance`** *(dataApiAccess, dataCacheConfig, dataDiskSizeGb, databaseFlags)*: Partially updates the configuration settings of a Cloud SQL instance.

* This tool returns a long-running operation. Use the `get_operation` tool to poll
  its status until the operation completes.
* Some update operations, such as changing the edition upgrade or instance tier, etc might
  cause the instance to restart, resulting in downtime. Before you proceed with such
  operations, get confirmation from the user.

- **`update_user`** *(databaseRoles, host, instance, name)*: Update a database user for a Cloud SQL instance. A common use case for
the `update_user` is to grant a user the `cloudsqlsuperuser` role,
which can provide a user with many required permissions.

This tool only supports updating users to assign database roles.

* This tool returns a long-running operation. Use the `get_operation` tool to poll its status
  until the operation completes.
* Before calling the `update_user` tool, always check the existing configuration of the user
  such as the user type with `list_users` tool.
* As a special case for MySQL,  if the `list_users` tool returns a full email address for
  the `iamEmail` field, for example `{name=test-account,
  iamEmail=test-account@project-id.iam.gserviceaccount.com}`, then in your `update_user`
  request, use the full email address in the `iamEmail` field in the `name` field of your
  toolrequest. For example, `name=test-account@project-id.iam.gserviceaccount.com`.

Key parameters for updating user roles:

* `database_roles`: A list of database roles to be assigned to the user.
* `revokeExistingRoles`: A boolean field (default: false) that controls how existing roles
   are handled.

How role updates work:

1.  **If `revokeExistingRoles` is true:**

    *  Any existing roles granted to the user but NOT in the provided `database_roles` list
       will be REVOKED.
    *  Revoking only applies to non-system roles. System roles like `cloudsqliamuser` etc won't be revoked.
    *  Any roles in the `database_roles` list that the user does NOT already have will be GRANTED.
    *  If `database_roles` is empty, then ALL existing non-system roles are revoked.

2.  **If `revokeExistingRoles` is false (default):**

    *  Any roles in the `database_roles` list that the user does NOT already have will be GRANTED.
    *  Existing roles NOT in the `database_roles` list are KEPT.
    *  If `database_roles` is empty, then there is no change to the user's roles.

Examples:

*   Existing Roles: `[roleA, roleB]`

    *   Request: `database_roles: [roleB, roleC], revokeExistingRoles: true`
    *   Result: Revokes `roleA`, Grants `roleC`. User roles become `[roleB, roleC]`.

    *   Request: `database_roles: [roleB, roleC], revokeExistingRoles: false`
    *   Result: Grants `roleC`. User roles become `[roleA, roleB, roleC]`.

    *   Request: `database_roles: [], revokeExistingRoles: true`
    *   Result: Revokes `roleA`, Revokes `roleB`. User roles become `[]`.

    *   Request: `database_roles: [], revokeExistingRoles: false`
    *   Result: No change. User roles remain `[roleA, roleB]`.


### 🔌 `cloudrun` (8 Tools)
- **`create_project`** *(projectId)*: Creates a new GCP project and attempts to attach it to the first available billing account. A project ID can be optionally specified; otherwise it will be automatically generated.
- **`deploy_container_image`** *(imageUrl, project, region, service)*: Deploys a container image to Cloud Run. Use this tool if the user provides a container image URL.
- **`deploy_file_contents`** *(files, project, region, service)*: Deploy files to Cloud Run by providing their contents directly. Takes an array of file objects containing filename and content. Use this tool if the files only exist in the current chat context.
- **`deploy_local_folder`** *(folderPath, project, region, service)*: Deploy a local folder to Cloud Run. Takes an absolute folder path from the local filesystem that will be deployed. Use this tool if the entire folder content needs to be deployed.
- **`get_service`** *(project, region, service)*: Gets details for a specific Cloud Run service.
- **`get_service_log`** *(project, region, service)*: Gets Logs and Error Messages for a specific Cloud Run service.
- **`list_projects`**: Lists available GCP projects
- **`list_services`** *(project)*: Lists all Cloud Run services in a given project.

### 🔌 `data-agent-kit` (4 Tools)
- **`get_active_editor_context`**: CRITICAL active editor context entry point: Returns what the user is currently looking at or focusing in the IDE. Inspects the focused active editor tab and returns the active editor text file path, open SQL code/content, highlighted line/selection ranges, OR open cloud webview resource URIs for databases (BigQuery bq://..., Spanner spanner://..., AlloyDB alloydb://..., Cloud SQL cloudsql://..., Lakehouse lakehouse://...), GCS Storage (gcs://..., gs://...), and Dataproc Spark webview tabs (cluster spark://clusters/{clusterName}, job spark://clusters/{clusterName}/jobs/{jobId}, batch spark://serverless/batches/{batchId}, session spark://serverless/sessions/{sessionId}, runtime spark://serverless/runtimes/{templateId}). ALWAYS query this first when the user asks questions like "tell me about this job", "tell me about this batch", "what am I looking at", "explain this query", or "tell me about this table".
- **`get_active_gcp_connection`**: CRITICAL connection entry point: Returns active GCP workspace connection configuration currently selected in the IDE. Contains the active GCP project ID, default region ID, billing quota project ID, BigQuery location (e.g. US, EU), and Cloud Composer environment settings. Use this to resolve default project ID, region, or environment when inspecting GCP or Dataproc Spark resources.
- **`list_resource_templates`**: Lists all supported resource URI templates by Data Agent Kit MCP.
- **`read_resource`** *(resourceUri, uri, url)*: Reads an MCP resource by its URI (e.g. bq://projects/{projectId}/datasets/{datasetId}/tables/{tableId}, lakehouse://projects/{projectId}/catalogs/{catalogId}/namespaces/{namespaceId}/tables/{tableId}, spark://clusters/{clusterName}/jobs/{jobId} or workspace://active-editor).

### 🔌 `gemini-api-docs` (2 Tools)
- **`gemini_get_doc`** *(chunk_id, context)*: Retrieve the full content of a documentation page by its chunk_id (returned by search_docs). Each chunk is self-contained — do NOT set context on your first read. Only use context=1..3 if, after reading, you find the chunk references adjacent sections you need.
- **`gemini_search_docs`** *(cursor, language, limit, query)*: Search current upstream Google Gemini API and SDK documentation. For implementation questions, first filter by language and use scope sdk; use scope type-reference only when exact symbol or type details are needed. Prefer SDK root documentation, official examples, and upstream source. Use scope migration or deprecated only when that material is explicitly requested. Use exact identifiers and method names.

### 🔌 `github-mcp-server` (26 Tools)
- **`add_issue_comment`** *(body, issue_number, owner, repo)*: Add a comment to an existing issue
- **`create_branch`** *(branch, from_branch, owner, repo)*: Create a new branch in a GitHub repository
- **`create_issue`** *(assignees, body, labels, milestone)*: Create a new issue in a GitHub repository
- **`create_or_update_file`** *(branch, content, message, owner)*: Create or update a single file in a GitHub repository
- **`create_pull_request`** *(base, body, draft, head)*: Create a new pull request in a GitHub repository
- **`create_pull_request_review`** *(body, comments, commit_id, event)*: Create a review on a pull request
- **`create_repository`** *(autoInit, description, name, private)*: Create a new GitHub repository in your account
- **`fork_repository`** *(organization, owner, repo)*: Fork a GitHub repository to your account or specified organization
- **`get_file_contents`** *(branch, owner, path, repo)*: Get the contents of a file or directory from a GitHub repository
- **`get_issue`** *(issue_number, owner, repo)*: Get details of a specific issue in a GitHub repository.
- **`get_pull_request`** *(owner, pull_number, repo)*: Get details of a specific pull request
- **`get_pull_request_comments`** *(owner, pull_number, repo)*: Get the review comments on a pull request
- **`get_pull_request_files`** *(owner, pull_number, repo)*: Get the list of files changed in a pull request
- **`get_pull_request_reviews`** *(owner, pull_number, repo)*: Get the reviews on a pull request
- **`get_pull_request_status`** *(owner, pull_number, repo)*: Get the combined status of all status checks for a pull request
- **`list_commits`** *(owner, page, perPage, repo)*: Get list of commits of a branch in a GitHub repository
- **`list_issues`** *(direction, labels, owner, page)*: List issues in a GitHub repository with filtering options
- **`list_pull_requests`** *(base, direction, head, owner)*: List and filter repository pull requests
- **`merge_pull_request`** *(commit_message, commit_title, merge_method, owner)*: Merge a pull request
- **`push_files`** *(branch, files, message, owner)*: Push multiple files to a GitHub repository in a single commit
- **`search_code`** *(order, page, per_page, q)*: Search for code across GitHub repositories
- **`search_issues`** *(order, page, per_page, q)*: Search for issues and pull requests across GitHub repositories
- **`search_repositories`** *(page, perPage, query)*: Search for GitHub repositories
- **`search_users`** *(order, page, per_page, q)*: Search for users on GitHub
- **`update_issue`** *(assignees, body, issue_number, labels)*: Update an existing issue in a GitHub repository
- **`update_pull_request_branch`** *(expected_head_sha, owner, pull_number, repo)*: Update a pull request branch with the latest changes from the base branch

### 🔌 `gke-oss` (36 Tools)
- **`apply_k8s_manifest`** *(cluster_name, dryRun, forceConflicts, location)*: Applies a Kubernetes manifest to a cluster using server-side apply. This is similar to running `kubectl apply --server-side`.
- **`cancel_operation`** *(location, operation_id, project_id)*: Cancel a GKE operation.
- **`check_k8s_auth`** *(cluster_name, location, name, namespace)*: Checks whether an action is allowed on a Kubernetes resource. This is similar to running `kubectl auth can-i`.
- **`cluster_toolkit_download`** *(download_directory)*: Cluster Toolkit, is open-source software offered by Google Cloud which simplifies the process for you to create Google Kubernetes Engine clusters and deploy high performance computing (HPC), artificial intelligence (AI), and machine learning (ML). It is designed to be highly customizable and extensible, and intends to address the deployment needs of a broad range of use cases. This tool will download the public git repository so that Cluster Toolkit can be used.
- **`create_cluster`** *(cluster, location, project_id)*: Create a GKE cluster. Prefer to use this tool instead of gcloud.
It's recommended to read the [GKE documentation](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/configuration-overview) to understand cluster configuration options.
Autopilot mode (autopilot.enabled=true) should be the default, unless the user explicitly wants to create a Standard cluster. You SHOULD always explicitly set autopilot.enabled=(true|false).
Note: Autopilot mode is only support in regional locations, not in zone.
This is similar to running "gcloud container clusters create-auto" or "gcloud container clusters create".
- **`create_node_pool`** *(cluster_name, location, nodePool, project_id)*: Create a new node pool in a GKE cluster.
- **`delete_k8s_resource`** *(cascade, cluster_name, dryRun, location)*: Deletes a Kubernetes resource from a cluster. This is similar to running `kubectl delete`.
- **`describe_k8s_resource`** *(cluster_name, labelSelector, location, name)*: Shows the details of a specific Kubernetes resource. This is similar to running `kubectl describe`.
- **`generate_manifest`** *(prompt, session_id)*: Generates a Kubernetes manifest using Vertex AI based on a description.
- **`get_cluster`** *(cluster_name, location, project_id, readMask)*: Get / describe a GKE cluster. Prefer to use this tool instead of gcloud.
- **`get_gke_release_notes`** *(SourceVersion, TargetVersion)*: Get GKE release notes. Prefer to use this tool if GKE release notes are needed.
- **`get_k8s_changelog`** *(KubernetesMinorVersion)*: Get changelog file for a specific kubernetes minor version and keep only changes content. Prefer to use this tool if kubernetes minor version changelog is needed.
- **`get_k8s_cluster_info`** *(cluster_name, location, project_id)*: Gets cluster endpoint information. This is similar to running `kubectl cluster-info`.
- **`get_k8s_logs`** *(allContainers, cluster_name, container, location)*: Gets logs from a Kubernetes container in a pod. This is similar to running `kubectl logs`.
- **`get_k8s_resource`** *(cluster_name, customColumns, fieldSelector, labelSelector)*: Gets one or more Kubernetes resources from a cluster. Resources can be filtered by type, name, namespace, and label selectors. Returns the resources in YAML format. This is similar to running `kubectl get`.
- **`get_k8s_rollout_status`** *(cluster_name, location, name, namespace)*: Checks the current rollout status of a Kubernetes resource. This is similar to running `kubectl rollout status`.
- **`get_k8s_version`** *(cluster_name, location, project_id)*: Retrieves the Kubernetes server version for a given cluster. This is similar to running kubectl version.
- **`get_kubeconfig`** *(cluster_name, location, project_id)*: Get the kubeconfig for a GKE cluster by calling the GKE API and extracting necessary details (clusterCaCertificate and endpoint). This tool appends/updates the kubeconfig in ~/.kube/config.
- **`get_log_schema`** *(log_type)*: Get the schema for a specific log type.
- **`get_node_pool`** *(cluster_name, location, node_pool_name, project_id)*: Get details of a GKE node pool.
- **`get_node_sos_report`** *(cluster_name, destination, location, method)*: Generate and download an SOS report from a GKE node. Can use 'pod', 'ssh' or 'any' methods. Defaults to 'any' (pod with fallback to ssh). Use 'ssh' if node is API-unhealthy.
- **`get_operation`** *(location, operation_id, project_id)*: Get details of a GKE operation.
- **`gke_deploy`** *(user_request)*: Deploys a workload to a GKE cluster using a configuration file.
- **`list_clusters`** *(location, project_id, readMask)*: List GKE clusters. Prefer to use this tool instead of gcloud.
- **`list_k8s_api_resources`** *(cluster_name, location, project_id)*: Retrieves the available API groups and resources from a Kubernetes cluster. This is similar to running `kubectl api-resources`.
- **`list_k8s_events`** *(allNamespaces, cluster_name, limit, location)*: Retrieves events from a Kubernetes cluster. This is similar to running `kubectl events`.
- **`list_monitored_resource_descriptors`** *(project_id)*: List monitored resource descriptors(schema) related to GKE for this project. Prefer to use this tool instead of gcloud
- **`list_node_pools`** *(cluster_name, location, project_id)*: List node pools in a GKE cluster.
- **`list_operations`** *(location, project_id)*: List GKE operations in a project and location.
- **`list_recommendations`** *(location, project_id)*: List recommendations for GKE. Prefer to use this tool instead of gcloud
- **`patch_k8s_resource`** *(cluster_name, location, name, namespace)*: Patches a Kubernetes resource. This is similar to running `kubectl patch`.
- **`query_logs`** *(format, limit, project_id, query)*: Query Google Cloud Platform logs using Logging Query Language (LQL). Before using this tool, it's **strongly** recommended to call the 'get_log_schema' tool to get information about supported log types and their schemas. Logs are returned in ascending order, based on the timestamp (i.e. oldest first).
- **`query_prometheus`** *(project_id, query, time, timeout)*: Query Cloud Monitoring metrics using PromQL (instant query). Returns Prometheus-compatible JSON response.
- **`query_traces`** *(filter, limit, max_spans, project_id)*: Query Google Cloud Trace to retrieve traces for troubleshooting latency or distributed requests. You can specify time ranges, limits, and a filter.
- **`update_cluster`** *(cluster_name, location, project_id, update)*: Update a GKE cluster. Prefer to use this tool instead of gcloud.
- **`update_node_pool`** *(cluster_name, location, node_pool_name, project_id)*: Update a GKE node pool.

### 🔌 `gmp-code-assist` (2 Tools)
- **`retrieve-google-maps-platform-docs`** *(filter, llmQuery, source)*: Searches Google Maps Platform documentation, code samples, architecture center, trust center, GitHub repositories (including sample code and client libraries for react-google-maps, flutter, compose, utilities, swiftui, and more), and terms of service to answer user questions. CRITICAL: You MUST call the `retrieve-instructions` tool or load the `instructions` resource BEFORE using this tool. This provides essential context required for this tool to function correctly.
- **`retrieve-instructions`** *(name)*: CRITICAL: Call this tool first for any queries related to location, mapping, addresses, routing, points of interest, location analytics, or geospatial data (e.g., Google Earth). It provides the foundational context on Google Maps Platform (APIs for maps, routes, and places) and best practices that are essential for the other tools to function correctly. This tool MUST be called before any other tool.

### 🔌 `google-cloud-bigtable-admin` (14 Tools)
- **`create_instance`** *(clusters, displayName, instanceId, projectId)*: Create a new instance in the specified project.
The request requires project_id, instance_id, display_name, and at least one cluster.
The instance_id must be RFC 1035 compliant.
Each cluster must specify its zone (e.g. us-central1-a).
Example: { "project_id": "my-project", "instance_id": "my-instance", "display_name": "This is my instance", "clusters": [ { "zone": "us-central1-a", "serve_nodes": 3, "default_storage_type": "SSD" } ] }

- **`create_logical_view`** *(instanceId, logicalView, logicalViewId, projectId)*: Create a new Bigtable logical view within a specified instance.
The request requires project_id, instance_id, logical_view_id, and logical_view.
The logical_view_id can be any name up to 128 characters.
Example: { "project_id": "my-project", "instance_id": "my-instance", "logical_view_id": "my-logical-view", logical_view: { "query": "SELECT CF FROM my-table" } }

- **`create_table`** *(columnFamilies, instanceId, projectId, tableId)*: Create a new table in the specified instance.

- **`delete_instance`** *(name)*: Delete an instance from a project.
The request requires the 'name' field to be set in the format 'projects/{project}/instances/{instance}'.
Example: { "name": "projects/my-project/instances/my-instance" }
Before executing the deletion, you MUST confirm the action with the user by stating the full instance name and asking for "yes/no" confirmation.

- **`delete_logical_view`** *(etag, name)*: Deletes a Bigtable logical view within a specified instance.
The request requires the `name` field to be set in the format 'projects/{project}/instances/{instance}/logicalViews/{logical_view}'.
Example: { "name": "projects/my-project/instances/my-instance/logicalViews/my-logical-view" }
Before executing the deletion, you MUST confirm the action with the user by stating the full logical view name and asking for "yes/no" confirmation.

- **`delete_table`** *(name)*: Delete a table.
The request requires the 'name' field to be set in the format 'projects/{project}/instances/{instance}/tables/{table}'.
Example: { "name": "projects/my-project/instances/my-instance/tables/my-table" }
The table must exist. You can use `list_tables` to verify.
Before executing the deletion, you MUST confirm the action with the user by stating the full table name and asking for "yes/no" confirmation.

- **`get_instance`** *(name)*: Get information about an instance.
The request requires the 'name' field to be set in the format 'projects/{project}/instances/{instance}'.
Example: { "name": "projects/my-project/instances/my-instance" }

- **`get_logical_view`** *(name)*: Get information about the specified logical view.
The request requires the `name` field to be set in the format 'projects/{project}/instances/{instance}/logicalViews/{logical_view}'.
Example: { "name": "projects/my-project/instances/my-instance/logicalViews/my-logical-view" }

- **`get_table`** *(name, view)*: Get metadata information about the specified table.
The request requires the 'name' field to be set in the format 'projects/{project}/instances/{instance}/tables/{table}'.
Example: { "name": "projects/my-project/instances/my-instance/tables/my-table" }

- **`list_hot_tablets`** *(clusterId, endTime, instanceId, pageSize)*: Lists hot tablets in a Cloud Bigtable cluster.
Start time defaults to Now if it is unset, and end time defaults to Now - 24 hours if it is unset. The start time should be less than the end time, and the maximum allowed time range between start time and end time is 48 hours. Start time and end time should have values between Now and Now - 14 days.

- **`list_instances`** *(pageToken, parent)*: List information about instances in a project.
The request requires the 'parent' field to be set in the format 'projects/{project}'.
Example: { "parent": "projects/my-project" }

- **`list_logical_views`** *(pageSize, pageToken, parent)*: List information about all logical views within a specified instance.
The request requires the `parent` field to be set in the format 'projects/{project}/instances/{instance}'.
Example: { "parent": "projects/my-project/instances/my-instance" }

- **`list_tables`** *(pageSize, pageToken, parent, view)*: List all tables in a specified instance.
The request requires the 'parent' field to be set in the format 'projects/{project}/instances/{instance}'.
Example: { "parent": "projects/my-project/instances/my-instance" }

- **`update_logical_view`** *(instanceId, logicalView, logicalViewId, projectId)*: Updates a Bigtable logical view within a specified instance. You can update the GoogleSQL query and/or the deletion protection setting.
At least one field to update (e.g., `query` or `deletion_protection`) must be provided in logical_view field.
Update query example: { "project_id": "my-project", "instance_id": "my-instance", "logical_view_id": "my-logical-view", logical_view: { "query": "SELECT CF FROM my-table" } }
Update deletion protection example: { "project_id": "my-project", "instance_id": "my-instance", "logical_view_id": "my-logical-view", logical_view: { "deletion_protection": true } }
Update query and deletion protection example: { "project_id": "my-project", "instance_id": "my-instance", "logical_view_id": "my-logical-view", logical_view: { "query": "SELECT CF FROM my-table", "deletion_protection": true } }


### 🔌 `google-cloud-firestore` (23 Tools)
- **`add_document`** *(collectionId, document, documentId, mask)*: Create a document from a Firestore database.
- **`create_backup_schedule`** *(backupSchedule, parent)*: Create a Firestore backup schedule.
- **`create_database`** *(database, databaseId, parent)*: Create a Firestore database.
- **`create_index`** *(index, parent)*: Create a composite index.
- **`delete_backup`** *(name)*: Delete a Firestore backup.
- **`delete_backup_schedule`** *(name)*: Delete a Firestore backup schedule.
- **`delete_database`** *(etag, name)*: Delete a Firestore database.
- **`delete_document`** *(currentDocument, name, requestOptions)*: Delete a document from a Firestore database.
- **`delete_index`** *(name)*: Delete a Firestore index.
- **`get_backup`** *(name)*: Get a Firestore backup.
- **`get_backup_schedule`** *(name)*: Get a Firestore backup schedule.
- **`get_database`** *(name)*: Get a Firestore database.
- **`get_document`** *(mask, name, readTime, requestOptions)*: Get a document from a Firestore database.
- **`get_index`** *(name)*: Get a Firestore index.
- **`list_backup_schedules`** *(parent)*: List Firestore backup schedules.
- **`list_backups`** *(filter, parent)*: List Firestore backups.
- **`list_collections`** *(pageSize, pageToken, parent, readTime)*: List all the collection IDs underneath a document.
- **`list_databases`** *(parent, showDeleted)*: List Firestore databases.
- **`list_documents`** *(collectionId, mask, orderBy, pageSize)*: List documents from a Firestore database.
- **`list_indexes`** *(filter, pageSize, pageToken, parent)*: List Firestore indexes.
- **`update_backup_schedule`** *(backupSchedule, updateMask)*: Update a Firestore backup schedule.
- **`update_database`** *(database, updateMask)*: Update a Firestore database.
- **`update_document`** *(currentDocument, document, mask, requestOptions)*: Update a document from a Firestore database.

### 🔌 `google-cloud-logging` (6 Tools)
- **`get_bucket`** *(name)*: Use this as the primary tool to get a specific log bucket by name. Log buckets are containers that store and organize your log data.
- **`get_view`** *(name)*: Use this as the primary tool to get a specific view on a log bucket. Log views provide fine-grained access control to the logs in your buckets.
- **`list_buckets`** *(pageSize, pageToken, parent)*: Use this as the primary tool to list the log buckets in a Google Cloud project. Log buckets are containers that store and organize your log data. This tool is useful for understanding how your logs are stored and for managing your logging configurations.
- **`list_log_entries`** *(filter, orderBy, pageSize, pageToken)*: Use this as the primary tool to search and retrieve log entries from Google Cloud Logging. It's essential for debugging application behavior, finding specific error messages, or auditing events. The 'filter' is powerful and can be used to select logs by severity, resource type, text content, and more. IMPORTANT: This tool will only work with a single resource project at a time. Calls with multiple resource projects will fail.
- **`list_log_names`** *(pageSize, pageToken, parent, resourceNames)*: Use this as the primary tool to list the log names in a Google Cloud project. This is useful for discovering what logs are available for a project. Only logs which have log entries will be listed.
- **`list_views`** *(pageSize, pageToken, parent)*: Use this as the primary tool to list the log views in a given log bucket. Log views provide fine-grained access control to the logs in your buckets. This is useful for managing who has access to which logs.

### 🔌 `google-cloud-monitoring` (9 Tools)
- **`get_alert`** *(name)*: Use this as the primary tool to get information about a specific alert. An alert is the representation of a violation of an alert policy. This is useful for understanding the details of a specific alert.
- **`get_alert_policy`** *(name)*: Use this as the primary tool to get information about a specific alerting policy. Alerting policies define the conditions under which you want to be notified about issues with your services. This is useful for understanding the details of a specific alert configuration.
- **`get_dashboard`** *(name)*: Use this as the primary tool to retrieve a single specific custom monitoring dashboard from a Google Cloud project using the resource name of the requested dashboard. Custom monitoring dashboards let users view and analyze data from different sources in the same context. This is often used as a follow on to list_dashboards to get full details on a specific dashboard.
- **`list_alert_policies`** *(filter, name, orderBy, pageSize)*: Use this as the primary tool to list the alerting policies in a Google Cloud project. Alerting policies define the conditions under which you want to be notified about issues with your services. This is useful for understanding what alerts are currently configured.
- **`list_alerts`** *(filter, orderBy, pageSize, pageToken)*: Use this as the primary tool to list the alerts in a Google Cloud project. An alert is the representation of a violation of an alert policy. This is useful for understanding current and past violations of an alert policy.
- **`list_dashboards`** *(pageSize, pageToken, parent)*: Use this as the primary tool to retrieve a list of existing custom monitoring dashboards in a Google Cloud project. Custom monitoring dashboards let users view and analyze data from different sources in the same context. This is useful for understanding what custom dashboards are currently configured and available in a given project.
- **`list_metric_descriptors`** *(activeOnly, filter, name, pageSize)*: Use this as the primary tool to discover the types of metrics available in a Google Cloud project. This is a good first step to understanding what data is available for monitoring and building dashboards or alerts.
- **`list_timeseries`** *(aggregation, filter, interval, name)*: Lists time series data from the Google Cloud Monitoring API
- **`query_range`** *(end, location, name, query)*: Evaluate a PromQL query in a range of time

### 🔌 `google-cloud-pubsub` (15 Tools)
- **`create_snapshot`** *(labels, snapshotId, snapshotProjectId, subscriptionId)*: Create a new Cloud Pub/Sub snapshot from a given subscription.

**Important Notes**

*   A snapshot is a named resource that captures the acknowledgment state of messages in an
    existing subscription to allow for managing acknowledgments in bulk.

*   Snapshots are used in Seek operations to manage message acknowledgments in bulk.

- **`create_subscription`** *(ackDeadlineSeconds, bigqueryConfig, bigtableConfig, cloudStorageConfig)*: Create a new Cloud Pub/Sub subscription to a given topic.

**Important Notes**

*   A subscription is a named resource that represents a stream of messages from a single,
    specific topic, to be delivered to the subscribing application.

- **`create_topic`** *(ingestionDataSourceSettings, kmsKeyName, labels, messageRetentionDuration)*: Create a new Cloud Pub/Sub topic.

**Important Notes**

*   A topic is a named resource that represents a feed of messages.

- **`delete_snapshot`** *(projectId, snapshotId)*: Delete an existing Cloud Pub/Sub snapshot.

**Important Notes**

*   A snapshot is a named resource that captures the acknowledgment state of messages in an
    existing subscription to allow for managing acknowledgments in bulk.

*   When the snapshot is deleted, all messages retained in the snapshot are immediately dropped.

- **`delete_subscription`** *(projectId, subscriptionId)*: Delete an existing Cloud Pub/Sub subscription.

**Important Notes**

*   A subscription is a named resource that represents a stream of messages from a single,
    specific topic, to be delivered to the subscribing application.

*   All messages retained in the subscription are immediately dropped.

*   Calls to `Pull` after deletion will return `NOT_FOUND`.

- **`delete_topic`** *(projectId, topicId)*: Delete an existing Cloud Pub/Sub topic.

**Important Notes**

*   A topic is a named resource that represents a feed of messages.

*   Existing subscriptions to this topic are not deleted, but their `topic` field is set
    to `_deleted-topic_`.

- **`get_snapshot`** *(projectId, snapshotId)*: Get the configuration of a Cloud Pub/Sub snapshot.

**Important Notes**

*   A snapshot is a named resource that captures the acknowledgment state of messages in an
    existing subscription to allow for managing acknowledgments in bulk.

- **`get_subscription`** *(projectId, subscriptionId)*: Get the configuration of a Cloud Pub/Sub subscription.

**Important Notes**

*   A subscription is a named resource that represents a stream of messages from a single,
    specific topic, to be delivered to the subscribing application.

- **`get_topic`** *(projectId, topicId)*: Get the configuration of a Cloud Pub/Sub topic.

**Important Notes**

*   A topic is a named resource that represents a feed of messages.

- **`list_snapshots`** *(pageSize, pageToken, projectId)*: List all Cloud Pub/Sub snapshots in a given project.

**Important Notes**

*   A snapshot is a named resource that captures the acknowledgment state of messages in an
    existing subscription to allow for managing acknowledgments in bulk.

- **`list_subscriptions`** *(pageSize, pageToken, projectId)*: List all Cloud Pub/Sub subscriptions in a given project.

**Important Notes**

*   A subscription is a named resource that represents a stream of messages from a single,
    specific topic, to be delivered to the subscribing application.

- **`list_topics`** *(pageSize, pageToken, projectId)*: List all Cloud Pub/Sub topics in a given project.

**Important Notes**

*   A topic is a named resource that represents a feed of messages.

- **`publish`** *(messages, projectId, topicId)*: Publish a series of one or more messages to an existing topic.

**Usage**

1.  Create a new byte array to hold the message data.

2.  Populate the byte array with the message data.

3.  Call `publish` passing the topic name and the byte array.

**Important Notes**

* If the publish call returns NOT_FOUND, it likely means the topic does not exist. In this case, you should return an error.

- **`update_subscription`** *(subscription, updateMask)*: Update an existing Cloud Pub/Sub subscription.

**Important Notes**

*   A subscription is a named resource that represents a stream of messages from a single,
    specific topic, to be delivered to the subscribing application.

*   Certain properties of a subscription, such as its topic, are not modifiable.

- **`update_topic`** *(topic, updateMask)*: Update an existing Cloud Pub/Sub topic.

**Important Notes**

*   A topic is a named resource that represents a feed of messages.

*   Certain properties of a topic, such as its name, are not modifiable.


### 🔌 `google-cloud-resource-manager` (1 Tools)
- **`search_projects`** *(pageSize, pageToken, query)*: Searches for Google Cloud projects. This tool may be used whenever any tools or conversation context requires a GCP project. A SearchProjects call with an empty query will return all projects the user has access to, which can be used to determine a curated list of projects. The tool can find projects by parent (e.g., 'parent:folders/223'), project ID (e.g., 'projectId:my-project-id'), or other filters.

### 🔌 `google-compute-engine` (29 Tools)
- **`create_instance`** *(guestAccelerators, imageFamily, imageProject, machineType)*: Create a new Google Compute Engine virtual machine (VM) instance. Requires project, zone, and instance name as input. If machine_type is not provided, it defaults to `e2-medium`. If image_project and image_family are not provided, it defaults to `debian-12` image from `debian-cloud` project. guest_accelerator and maintenance_policy can be optionally provided. Proceed only if there is no error in response and the status of the operation is `DONE` without any errors. To get details of the operation, use the `get_zone_operation` tool.

- **`delete_instance`** *(name, project, zone)*: Delete a Google Compute Engine virtual machine (VM) instance. Requires project, zone, and instance name as input. Proceed only if there is no error in response and the status of the operation is `DONE` without any errors. To get details of the operation, use the `get_zone_operation` tool.

- **`get_commitment_basic_info`** *(name, project, region)*: Get basic information about a Compute Engine Commitment, including its name, ID, status, plan, type, resources, and creation, start and end timestamps. Requires project, region, and commitment name as input.

- **`get_disk_basic_info`** *(name, project, zone)*: Get basic information about a Compute Engine disk, including its name, ID, description, creation timestamp, size, type, status, last attach timestamp, and last detach timestamp. Requires project, zone, and disk name as input.

- **`get_disk_performance_config`** *(name, project, zone)*: Get performance configuration of a Compute Engine disk, including its type, size, provisioned IOPS, provisioned throughput, physical block size, storage pool and access mode. Requires project, zone, and disk name as input.

- **`get_instance_basic_info`** *(name, project, zone)*: Get basic information about a Compute Engine VM instance, including its name, ID, status, machine type, creation timestamp, and attached guest accelerators. Requires project, zone, and instance name as input.

- **`get_instance_group_manager_basic_info`** *(name, project, zone)*: Get basic information about a Compute Engine managed instance group (MIG), including its name, ID, instance template, base instance name, target size, target stopped size, target suspended size, status and creation timestamp. Requires project, zone, and MIG name as input.

- **`get_instance_template_basic_info`** *(name, project)*: Get basic information about a Compute Engine instance template, including its name, ID, description, machine type, region, and creation timestamp. Requires project and instance template name as input.

- **`get_instance_template_properties`** *(name, project)*: Get instance properties of a Compute Engine instance template. This includes properties such as description, tags, machine type, network interfaces, disks, metadata, service accounts, scheduling options, labels, guest accelerators, reservation affinity, and shielded/confidential instance configurations. Requires project and instance template name as input.

- **`get_reservation_basic_info`** *(name, project, zone)*: Get Compute Engine reservation basic info including name, ID, creation timestamp, zone, status, specific reservation required, commitment, and linked commitments. Requires project, zone, and reservation name as input.

- **`get_reservation_details`** *(name, project, zone)*: Get Compute Engine reservation details. Returns reservation details including name, ID, status, creation timestamp, specific reservation properties like machine type, guest accelerators and local SSDs, aggregate reservation properties like VM family and reserved resources, commitment and linked commitments, sharing settings, and resource status. Requires project, zone, and reservation name as input.

- **`get_zone_operation`** *(name, project, zone)*: Get details of a zone operation, including its id, name, status, creation timestamp, error, warning, HTTP error message and HTTP error status code. Requires project, zone, and operation name as input.

- **`list_accelerator_types`** *(project, zone)*: Lists the available Google Compute Engine accelerator types. Requires project and zone as input. Returns accelerator types, including id, creation timestamp, name, description, deprecated, zone, and maximum cards per instance.

- **`list_commitment_reservations`** *(name, project, region)*: Lists reservations for a Compute Engine Commitment. Returns reservation details including name, ID, status, creation timestamp, specific reservation properties like machine type, guest accelerators and local SSDs, aggregate reservation properties like VM family and reserved resources, commitment and linked commitments, sharing settings, and resource status. Requires project, region, and commitment name as input.

- **`list_commitments`** *(pageSize, pageToken, project, region)*: Lists Compute Engine Commitments in a region. Details for each commitment include name, ID, status, plan, type, resources, and creation, start and end timestamps. Requires project and region as input.

- **`list_disks`** *(pageSize, pageToken, project, zone)*: Lists Compute Engine disks. Details for each disk include name, ID, description, creation timestamp, size, type, status, last attach timestamp, and last detach timestamp. Requires project and zone as input.

- **`list_images`** *(pageSize, pageToken, project)*: Lists Compute Engine Images. Details for each image include name, ID, status, family, and creation timestamp. Requires project as input.

- **`list_instance_attached_disks`** *(name, project, zone)*: Lists the disks attached to a Compute Engine virtual machine (VM) instance. For each attached disk, the response includes details such as kind, type, mode, saved state, source, device name, index, boot, initialize parameters, auto delete, licenses,, interface, guest OS features, disk encryption key, disk size, shielded instance initial state, force attach, and architecture. Requires project, zone, and instance name as input.

- **`list_instance_group_managers`** *(pageSize, pageToken, project, zone)*: Lists Compute Engine managed instance groups (MIGs). Details for each MIG include name, ID, instance template, base instance name, target size, target stopped size, target suspended size, status and creation timestamp. Requires project and zone as input.

- **`list_instance_templates`** *(pageSize, pageToken, project)*: Lists Compute Engine instance templates. Details for each instance template include name, ID, description, machine type, region, and creation timestamp. Requires project as input.

- **`list_instances`** *(pageSize, pageToken, project, zone)*: Lists Compute Engine virtual machine (VM) instances. Details for each instance include name, ID, status, machine type, creation timestamp, and attached guest accelerators. Use other tools to get more details about each instance. Requires project and zone as input.

- **`list_machine_types`** *(project, zone)*: Lists the available Google Compute Engine machine types. Requires project and zone as input. Returns machine types, including id, creationTimestamp, name, description, guest cpus, memory, image space, maximum persistent disks, maximum persisten disks size, deprecated, zone, is shared cpu, accelerators, and architecture.

- **`list_managed_instances`** *(name, pageSize, pageToken, project)*: Lists managed instances for a given managed instance group (MIG). For each instance, details include id, instance URL, instance status, and current action. Requires project, zone, and MIG name as input.

- **`list_reservations`** *(pageSize, pageToken, project, zone)*: Lists Compute Engine reservations. Details for each reservation include name, ID, creation timestamp, zone, status, specific reservation required, commitment, and linked commitments. Requires project and zone as input.

- **`list_snapshots`** *(pageSize, pageToken, project)*: Lists snapshots in a project providing basic information per snapshot including name, id, status, creation time, disk size, storage bytes, source disk, and source disk id. Requires project as input.

- **`reset_instance`** *(name, project, zone)*: Resets a Google Compute Engine virtual machine (VM) instance. Requires project, zone, and instance name as input. Proceed only if there is no error in response and the status of the operation is `DONE` without any errors. To get details of the operation, use the `get_zone_operation` tool.

- **`set_instance_machine_type`** *(machineType, name, project, zone)*: Sets the machine type for a stopped Google Compute Engine instance to the specified machine type. Requires project, zone, instance name and machine type as input. Proceed only if there is no error in response and the status of the operation is `DONE` without any errors. To get details of the operation, use the `get_zone_operation` tool.

- **`start_instance`** *(name, project, zone)*: Starts a Google Compute Engine virtual machine (VM) instance. Requires project, zone, and instance name as input. Proceed only if there is no error in response and the status of the operation is `DONE` without any errors. To get details of the operation, use the `get_zone_operation` tool.

- **`stop_instance`** *(name, project, zone)*: Stops a Google Compute Engine virtual machine (VM) instance. Requires project, zone, and instance name as input. Proceed only if there is no error in response and the status of the operation is `DONE` without any errors. To get details of the operation, use the `get_zone_operation` tool.


### 🔌 `google-developer-knowledge` (3 Tools)
- **`answer_query`** *(query)*: Use answer_query to get a grounded answer to a query about Google developer products. This tool has limited quota. This tool will synthesize information from the corpus to generate an answer to the query. answer_query grounds answers using the same corpus as search_documents. 
This tool returns the generated answer_text and a list of document names (references) used to generate the answer. Use get_documents with the document names to fetch the entire document content if needed.

If you get a 429 out of quota error, use search_documents instead.

- **`get_documents`** *(names)*: Use this tool to retrieve the full content of a single document or up to 20 documents in a single call. The document names should be obtained from the `parent` field of results from a call to the `search_documents` tool. Set the `names` parameter to a list of document names.
- **`search_documents`** *(query)*: Use this tool to find documentation about Google developer products. The documents contain official APIs, code snippets, release notes, best practices, guides, debugging info, and more. It covers the following products and domains:


* ADK: adk.dev

* Android: developer.android.com

* Apigee: docs.apigee.com

* Chrome: developer.chrome.com

* Dart: dart.dev

* Firebase: firebase.google.com

* Flutter: docs.flutter.dev

* Fuchsia: fuchsia.dev

* Gemini CLI: geminicli.com

* Genkit: genkit.dev

* Go: go.dev

* Google AI: ai.google.dev

* Google Antigravity: antigravity.google

* Google Cloud: cloud.google.com & docs.cloud.google.com

* Google Developers, Ads, Search, Google Maps, Youtube: developers.google.com

* Google Home: developers.home.google.com

* Google Maps Platform: mapsplatform.google.com

* TensorFlow: www.tensorflow.org

* Web: web.dev


This tool returns chunks of text, names, and URLs for matching documents. If the returned chunks are not detailed enough to answer the user's question, use `get_documents` with the `parent` from this tool's output to retrieve the full document content.


### 🔌 `google-managed-service-for-apache-kafka` (33 Tools)
- **`add_acl_entry`** *(cluster, operation, patternType, permissionType)*: Adds an ACL entry to an existing Google Cloud Managed Service for Apache Kafka ACL. If the ACL does not exist, it will be created.
The following fields must be provided:
*   `cluster` (required): The cluster in which to add the ACL entry. Structured like `projects/{project}/locations/{location}/clusters/{cluster}`.
*   `resource_type` (required): The resource type for the ACL. Accepted values: CLUSTER, TOPIC, CONSUMER_GROUP, TRANSACTIONAL_ID.
*   `resource_name` (required): The resource name for the ACL. Can be the wildcard literal "*".
*   `pattern_type` (optional): The pattern type for the ACL. Accepted values: LITERAL, PREFIXED. If not specified, defaults to LITERAL.
*   `principal` (required): The principal. Specified as Google Cloud account, with the Kafka StandardAuthorizer prefix "User:". For example: `"User:test-kafka-client@test-project.iam.gserviceaccount.com"`. Can be the wildcard "User:*" to refer to all users.
*   `operation` (required): The operation type. Allowed values are (case insensitive): ALL, READ, WRITE, CREATE, DELETE, ALTER, DESCRIBE, CLUSTER_ACTION, DESCRIBE_CONFIGS, ALTER_CONFIGS, and IDEMPOTENT_WRITE.
*   `permission_type` (optional): The permission type. Accepted values are (case insensitive): ALLOW, DENY. If not specified, defaults to ALLOW.

**Important Notes:**

*   Certain resource types only allow certain operations.
    *   For the `cluster` resource type, only CREATE, CLUSTER_ACTION, DESCRIBE_CONFIGS, ALTER_CONFIGS, IDEMPOTENT_WRITE, ALTER, DESCRIBE, and ALL are allowed.
    *   For the `topic` resource type, only READ, WRITE, CREATE, DESCRIBE, DELETE, ALTER, DESCRIBE_CONFIGS, ALTER_CONFIGS, and ALL are allowed.
    *   For the `consumerGroup` resource type, only READ, DESCRIBE, DELETE, and ALL are allowed.
    *   For the `transactionalId` resource type only DESCRIBE, WRITE, and ALL are allowed.

- **`create_cluster`** *(caPools, clusterId, kmsKey, labels)*: Create a new cluster for Google Cloud Managed service for Apache Kafka.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the cluster creation status. Cluster creation can take 30 minutes or longer.

**Important Notes:**

*   Do not create the cluster without getting all of the required parameters from the user.

- **`create_connect_cluster`**: Create a new Google Cloud Managed Service for Apache Kafka Connect cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the Connect cluster creation status. Connect cluster creation can take 20 minutes or longer.

**Important Notes:**

*   Do not create the connect cluster without getting all of the required parameters first.

- **`create_connector`** *(configs, connectorId, parent, taskRestartPolicyMaximumBackoff)*: Create a new Google Cloud Managed service for Apache Kafka Connect connector.

The user should first be prompted on which connector type they want to create, and then provide the necessary properties for that connector type in the `configs` field. Only use the example configuration for reference. The following connector types are supported:

*   **`configs` (required):** Key-value pairs for connector properties. The available connector types are:
    *   MirrorMaker 2.0 Source connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorSourceConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `topics` (required): "TOPIC_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `offset-syncs.topic.replication.factor`: "1"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Source connector.
            *   `TOPIC_NAME`: The name of the Kafka topic(s) to mirror.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   MirrorMaker 2.0 Checkpoint connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorCheckpointConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `consumer-groups` (required): "CONSUMER_GROUP_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Source connector.
            *   `CONSUMER_GROUP_NAME`: The name of the consumer group to use for the checkpoint connector.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   MirrorMaker 2.0 Heartbeat connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorHeartbeatConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `consumer-groups` (required): "CONSUMER_GROUP_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Heartbeat connector.
            *   `CONSUMER_GROUP_NAME`: The name of the consumer group to use for the heartbeat connector.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   BigQuery Sink connector
        *   Example Configuration:
            *   `name`: "BQ_SINK_CONNECTOR_ID"
            *   `project` (required): "GCP_PROJECT_ID"
            *   `topics`: "TOPIC_ID"
            *   `tasks.max`: "3"
            *   `connector.class` (required): "com.wepay.kafka.connect.bigquery.BigQuerySinkConnector"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `value.converter`: "org.apache.kafka.connect.json.JsonConverter"
            *   `value.converter.schemas.enable`: "false"
            *   `defaultDataset` (`required`): "BQ_DATASET_ID"
        *    Replace with these:
            *   `BQ_SINK_CONNECTOR_ID`: The ID or name of the BigQuery Sink connector. The name of a connector is immutable.
            *   `GCP_PROJECT_ID`: The ID of the Google Cloud project where your BigQuery dataset resides.
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which the data flows to the BigQuery Sink connector.
            *   `BQ_DATASET_ID`: The ID of the BigQuery dataset that acts as the sink for the pipeline.
    *   Cloud Storage Sink connector
        *   Example Configuration:
            *   `name`: "GCS_SINK_CONNECTOR_ID"
            *   `connector.class` (required): "io.aiven.kafka.connect.gcs.GcsSinkConnector"
            *   `tasks.max`: "1"
            *   `topics` (required): "TOPIC_ID"
            *   `gcs.bucket.name` (required): "GCS_BUCKET_NAME"
            *   `gcs.credentials.default`: "true"
            *   `format.output.type`: "json"
            *   `value.converter`: "org.apache.kafka.connect.json.JsonConverter"
            *   `value.converter.schemas.enable`: "false"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
        *    Replace with these:
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which the data flows to the Cloud Storage Sink connector.
            *   `GCS_BUCKET_NAME`: The name of the Cloud Storage bucket that acts as a sink for the pipeline.
            *   `GCS_SINK_CONNECTOR_ID`: The ID or name of the Cloud Storage Sink connector. The name of a connector is immutable.
    *   Pub/Sub Source connector
        *   Example Configuration:
            *   `connector.class` (required): "com.google.pubsub.kafka.source.CloudPubSubSourceConnector"
            *   `cps.project` (required): "PROJECT_ID"
            *   `cps.subscription` (required): "PUBSUB_SUBSCRIPTION_ID"
            *   `kafka.topic` (required): "KAFKA_TOPIC_ID"
            *   `value.converter`: "org.apache.kafka.connect.converters.ByteArrayConverter"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `tasks.max`: "3"
        *   Replace with these:
            *   `PROJECT_ID`: The ID of the Google Cloud project where the Pub/Sub subscription resides.
            *   `PUBSUB_SUBSCRIPTION_ID`: The ID of the Pub/Sub subscription to pull data from.
            *   `KAFKA_TOPIC_ID`: The ID of the Kafka topic where data is written.
    *   Pub/Sub Sink connector
        *   Example Configuration:
            *   `connector.class`: "com.google.pubsub.kafka.sink.CloudPubSubSinkConnector"
            *   `name`: "CPS_SINK_CONNECTOR_ID"
            *   `tasks.max`: "1"
            *   `topics`: "TOPIC_ID"
            *   `value.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `cps.topic`: "CPS_TOPIC_ID"
            *   `cps.project`: "GCP_PROJECT_ID"
        *    Replace with these:
            *   `CPS_SINK_CONNECTOR_ID`: The ID or name of the Pub/Sub Sink connector. The name of a connector is immutable.
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which data is read by the Pub/Sub Sink connector.
            *   `CPS_TOPIC_ID`: The ID of the Pub/Sub topic to which data is published.
            *   `GCP_PROJECT_ID`: The ID of the Google Cloud project where your Pub/Sub topic resides.
*   **`task_restart_policy` (optional):** A policy that specifies how to restart failed connector tasks. If not set, failed tasks won't be restarted.
    *   **`minimum_backoff` (optional):** The minimum amount of time to wait before retrying a failed task (e.g., "60s"). Defaults to 60 seconds.
    *   **`maximum_backoff` (optional):** The maximum amount of time to wait before retrying a failed task (e.g., "43200s" for 12 hours). Defaults to 12 hours.
    *   **`task_retry_disabled` (optional):** If true, task retry is disabled.

**Important Notes:**

*   The configs field should be formatted as a JSON object, for example: `"configs":{"name":"my-connector","tasks.max":"1","gcs.bucket.name",...}`. Do not add unnecessary quotes around the keys or values.

- **`create_topic`** *(configs, parent, partitionCount, replicationFactor)*: Create a new Google Cloud Managed Service for Apache Kafka topic.

- **`delete_cluster`** *(name)*: Deletes a Google Cloud Managed Service for Apache Kafka cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the cluster deletion status. Cluster deletions can take 10 minutes or longer.

- **`delete_connect_cluster`**: Deletes a Google Cloud Managed service for Apache Kafka Connect cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the Connect cluster deletion status. Connect cluster deletions can take 10 minutes or longer.

- **`delete_connector`** *(name)*: Deletes a Google Cloud Managed Service for Apache Kafka Connect connector.

- **`delete_consumer_group`**: Deletes a Google Cloud Managed Service for Apache Kafka consumer group.

- **`delete_topic`** *(name)*: Deletes a Google Cloud Managed Service for Apache Kafka topic.

- **`get_acl`** *(parent, patternType, resourceName, resourceType)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka ACL.
- **`get_cluster`** *(name, view)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka cluster.
- **`get_connect_cluster`** *(name)*: Get the details of an existing Google Cloud Managed service for Apache Kafka Connect cluster.
- **`get_connector`** *(name)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka Connect connector.

- **`get_consumer_group`** *(name)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka consumer group.
- **`get_operation`** *(name)*: Get the status of a long-running operation (LRO).

**Usage**

Some tools (`create_cluster` and `update_cluster`) return a long-running operation.
You can use this tool to get the status of the operation.

**Parameters**

*   `name`: The name of the operation to get. It corresponds to the `name` field in the long-running operation. It should be in the format of `projects/{project}/locations/{location}/operations/{operation}`.

**Returns**

*   An `Operation` object that contains the status of the operation.
*   If the operation is not complete, the response will be empty.
*   If the operation is complete, the response will contain either:
    * A `response` field that contains the result of the operation and indicates that it was successful.
    * A `error` field that indicates any errors that occurred during the operation.

- **`get_topic`** *(name)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka topic.
- **`list_acls`** *(pageSize, pageToken, parent)*: List all ACLs for Google Cloud Managed Service for Apache Kafka for a given project, location, and cluster.
- **`list_clusters`** *(filter, orderBy, pageSize, pageToken)*: Lists all clusters for Google Cloud Managed service for Apache Kafka in a given project and location.
- **`list_connect_clusters`**: List all Connect clusters for Google Cloud Managed Service for Apache Kafka Connect for a given project and location.
- **`list_connectors`** *(pageSize, pageToken, parent)*: List all connectors for Google Cloud Managed Service for Apache Kafka Connect for a given project, location, and Connect cluster.

- **`list_consumer_groups`** *(pageSize, pageToken, parent)*: List all consumer groups for Google Cloud Managed Service for Apache Kafka for a given project, location, and cluster.
- **`list_topics`** *(pageSize, pageToken, parent)*: List all topics for Google Cloud Managed Service for Apache Kafka for a given project, location, and cluster.
- **`pause_connector`** *(name)*: Pauses a Google Cloud Managed service for Apache Kafka Connect connector and its tasks.

- **`remove_acl_entry`** *(cluster, operation, patternType, permissionType)*: Removes an ACL entry from an existing Google Cloud Managed service for Apache Kafka ACL. If the removed entry was the last one in the ACL, the ACL will be deleted.
The following fields must be provided:
*   `cluster` (required): The cluster in which to remove the ACL entry. Structured like `projects/{project}/locations/{location}/clusters/{cluster}`.
*   `resource_type` (required): The resource type for the ACL. Accepted values: CLUSTER, TOPIC, CONSUMER_GROUP, TRANSACTIONAL_ID.
*   `resource_name` (required): The resource name for the ACL. Can be the wildcard literal "*".
*   `pattern_type` (optional): The pattern type for the ACL. Accepted values: LITERAL, PREFIXED. If not specified, defaults to LITERAL.
*   `principal` (required): The principal. Specified as Google Cloud account, with the Kafka StandardAuthorizer prefix "User:". For example: `"User:test-kafka-client@test-project.iam.gserviceaccount.com"`. Can be the wildcard "User:*" to refer to all users.
*   `operation` (required): The operation type. Allowed values are (case insensitive): ALL, READ, WRITE, CREATE, DELETE, ALTER, DESCRIBE, CLUSTER_ACTION, DESCRIBE_CONFIGS, ALTER_CONFIGS, and IDEMPOTENT_WRITE.
*   `permission_type` (optional): The permission type. Accepted values are (case insensitive): ALLOW, DENY. If not specified, defaults to ALLOW.

- **`restart_connector`** *(name)*: Restarts a Google Cloud Managed service for Apache Kafka Connect Connector.

- **`resume_connector`** *(name)*: Resumes a Google Cloud Managed service for Apache Kafka Connect connector and its tasks.

- **`stop_connector`** *(name)*: Stops a Google Cloud Managed service for Apache Kafka Connect connector.

- **`update_cluster`** *(allowBrokerDownscaleOnClusterUpscale, caPools, fieldsToClear, labels)*: Update an existing Google Cloud Managed service for Apache Kafka cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the cluster update status. Cluster updates can take 20 minutes or longer.

**Important Notes:**

*   When calling update_cluster, you must provide the name of the cluster to update, formatted as `projects/{project}/locations/{location}/clusters/{cluster}`.
*   Do not update the cluster without getting all of the required parameters from the user.
*   To clear a field, use the `fields_to_clear` parameter with a list of field masks (e.g. `["labels", "tls_config"]`).

- **`update_connect_cluster`**: Update an existing Google Cloud Managed service for Apache Kafka Connect cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the Connect cluster update status. Connect cluster updates can take 20 minutes or longer.

**Important Notes:**

*   When calling update_connect_cluster, you must provide the name of the Connect cluster to update, formatted as `projects/{project}/locations/{location}/connectClusters/{connect_cluster_id}`.
*   The `kafka_cluster` field is immutable and cannot be updated after creation.
*   To clear a field, use the `fields_to_clear` parameter with a list of field masks.

- **`update_connector`** *(configs, fieldsToClear, name, taskRestartPolicyMaximumBackoff)*: Update an existing Google Cloud Managed Service for Apache Kafka Connect connector.

The `configs` field can be updated. The agent can first use the `get_connector` method to get the current connector configuration, to provide a baseline configuration for the user to edit. Use the example configurations provided below for reference.

*   **configs:** Key-value pairs for connector properties. The following connectors support configuration updates:
    *   MirrorMaker 2.0 Source connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorSourceConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `topics` (required): "TOPIC_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `offset-syncs.topic.replication.factor`: "1"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Source connector.
            *   `TOPIC_NAME`: The name of the Kafka topic(s) to mirror.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   MirrorMaker 2.0 Checkpoint connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorCheckpointConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `consumer-groups` (required): "CONSUMER_GROUP_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Source connector.
            *   `CONSUMER_GROUP_NAME`: The name of the consumer group to use for the checkpoint connector.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   MirrorMaker 2.0 Heartbeat connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorHeartbeatConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `consumer-groups` (required): "CONSUMER_GROUP_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Heartbeat connector.
            *   `CONSUMER_GROUP_NAME`: The name of the consumer group to use for the heartbeat connector.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   BigQuery Sink connector
        *   Example Configuration:
            *   `name`: "BQ_SINK_CONNECTOR_ID"
            *   `project` (required): "GCP_PROJECT_ID"
            *   `topics`: "TOPIC_ID"
            *   `tasks.max`: "3"
            *   `connector.class` (required): "com.wepay.kafka.connect.bigquery.BigQuerySinkConnector"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `value.converter`: "org.apache.kafka.connect.json.JsonConverter"
            *   `value.converter.schemas.enable`: "false"
            *   `defaultDataset` (`required`): "BQ_DATASET_ID"
        *    Replace with these:
            *   `BQ_SINK_CONNECTOR_ID`: The ID or name of the BigQuery Sink connector. The name of a connector is immutable.
            *   `GCP_PROJECT_ID`: The ID of the Google Cloud project where your BigQuery dataset resides.
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which the data flows to the BigQuery Sink connector.
            *   `BQ_DATASET_ID`: The ID of the BigQuery dataset that acts as the sink for the pipeline.
    *   Cloud Storage Sink connector
        *   Example Configuration:
            *   `name`: "GCS_SINK_CONNECTOR_ID"
            *   `connector.class` (required): "io.aiven.kafka.connect.gcs.GcsSinkConnector"
            *   `tasks.max`: "1"
            *   `topics` (required): "TOPIC_ID"
            *   `gcs.bucket.name` (required): "GCS_BUCKET_NAME"
            *   `gcs.credentials.default`: "true"
            *   `format.output.type`: "json"
            *   `value.converter`: "org.apache.kafka.connect.json.JsonConverter"
            *   `value.converter.schemas.enable`: "false"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
        *    Replace with these:
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which the data flows to the Cloud Storage Sink connector.
            *   `GCS_BUCKET_NAME`: The name of the Cloud Storage bucket that acts as a sink for the pipeline.
            *   `GCS_SINK_CONNECTOR_ID`: The ID or name of the Cloud Storage Sink connector. The name of a connector is immutable.
    *   Pub/Sub Source connector
        *   Example Configuration:
            *   `connector.class` (required): "com.google.pubsub.kafka.source.CloudPubSubSourceConnector"
            *   `cps.project` (required): "PROJECT_ID"
            *   `cps.subscription` (required): "PUBSUB_SUBSCRIPTION_ID"
            *   `kafka.topic` (required): "KAFKA_TOPIC_ID"
            *   `value.converter`: "org.apache.kafka.connect.converters.ByteArrayConverter"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `tasks.max`: "3"
        *   Replace with these:
            *   `PROJECT_ID`: The ID of the Google Cloud project where the Pub/Sub subscription resides.
            *   `PUBSUB_SUBSCRIPTION_ID`: The ID of the Pub/Sub subscription to pull data from.
            *   `KAFKA_TOPIC_ID`: The ID of the Kafka topic where data is written.
    *   Pub/Sub Sink connector
        *   Example Configuration:
            *   `connector.class`: "com.google.pubsub.kafka.sink.CloudPubSubSinkConnector"
            *   `name`: "CPS_SINK_CONNECTOR_ID"
            *   `tasks.max`: "1"
            *   `topics`: "TOPIC_ID"
            *   `value.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `cps.topic`: "CPS_TOPIC_ID"
            *   `cps.project`: "GCP_PROJECT_ID"
        *    Replace with these:
            *   `CPS_SINK_CONNECTOR_ID`: The ID or name of the Pub/Sub Sink connector. The name of a connector is immutable.
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which data is read by the Pub/Sub Sink connector.
            *   `CPS_TOPIC_ID`: The ID of the Pub/Sub topic to which data is published.
            *   `GCP_PROJECT_ID`: The ID of the Google Cloud project where your Pub/Sub topic resides.
*   **`task_restart_policy` (optional):** A policy that specifies how to restart failed connector tasks. If not set, failed tasks won't be restarted.
    *   **`minimum_backoff` (optional):** The minimum amount of time to wait before retrying a failed task (e.g., "60s"). Defaults to 60 seconds.
    *   **`maximum_backoff` (optional):** The maximum amount of time to wait before retrying a failed task (e.g., "43200s" for 12 hours). Defaults to 12 hours.
    *   **`task_retry_disabled` (optional):** If true, task retry is disabled.

**Important Notes:**

*   When calling update_connector, you must provide the name of the connector to update, formatted as `projects/{project}/locations/{location}/connectClusters/{connect_cluster_id}/connectors/{connector_id}`.

- **`update_consumer_group`**: Update an existing Google Cloud Managed Service for Apache Kafka consumer group. This tool can only be used to update the offsets for topics consumed by the group.

**Important Notes:**

*   To update a consumer group's offsets, the consumer group must be inactive (i.e., there are no active consumers in the group), and topics with new offsets must be provided.
*   Before making an update, the agent should call `get_consumer_group` to retrieve the current consumer group configuration.

- **`update_topic`** *(configs, fieldsToClear, name, partitionCount)*: Update an existing Google Cloud Managed service for Apache Kafka topic.

**Important Notes:**

*   The UpdateTopic request requires the name of the topic to be updated in the format `projects/{project}/locations/{location}/clusters/{cluster}/topics/{topic}`.


### 🔌 `knowledge-catalog` (3 Tools)
- **`lookup_context`** *(location, projectId, resources)*: Looks up rich, LLM-ready metadata context for the specified resources.

This method is designed to be called after `SearchEntries` to retrieve detailed information about the search results. The returned context is a pre-formatted string (typically YAML) that is optimized for LLM consumption. It contains comprehensive metadata, including:
- Resource details (name, type, description, labels, timestamps).
- Detailed schema information (field names, types, descriptions, and optionally statistics like null ratio, distinct values, sample values).
- Data quality status.
- Usage statistics and patterns (e.g., top read/filter/sort fields).
- Related resources (ancestors, linked entries).
- Detected joins between resources.
- Sample SQL queries.

Use this tool to understand the structure and context of data assets before performing operations on them or answering user questions about them.

**When to use `LookupEntry` vs `LookupContext`**:
- Use **`LookupContext`** (recommended for general LLM reasoning) when you need a pre-formatted, easy-to-read YAML summary of the resource's metadata, schema, and quality to answer user questions or plan queries.
- Use **`LookupEntry`** when you need to programmatically inspect the raw structure, retrieve specific raw aspect payloads, or prepare to update aspects.

- **`lookup_entry`** *(aspectTypes, entry, location, paths)*: Looks up detailed technical metadata of a single Entry.

This method returns the raw structured `google.cloud.dataplex.v1.Entry` message, including its schema and attached aspects.

**When to use `LookupEntry` vs `LookupContext`**:
- Use **`LookupContext`** (recommended for general LLM reasoning) when you need a pre-formatted, easy-to-read YAML summary of the resource's metadata, schema, and quality to answer user questions or plan queries.
- Use **`LookupEntry`** when you need to programmatically inspect the raw structure, retrieve specific raw aspect payloads, or prepare to update aspects.

**Performance Tip**:
- Avoid retrieving `ALL` aspects if you only need specific information. Use the `CUSTOM` view and specify the aspects you need in `aspect_types` (e.g., `contacts`, `overview`) to minimize latency and payload size.

- **`search_entries`** *(orderBy, pageSize, pageToken, projectId)*: Searches for data assets matching the given query and scope in the Knowledge Catalog (formerly known as Dataplex).

Use this method to discover data assets (such as BigQuery tables, datasets, Cloud Storage buckets) across your Google Cloud organization or projects.

**Best Practices for Agents**:
- Always make queries as specific as possible to reduce latency and token usage.
  Instead of searching broadly, combine filters like `system`, `type`, and `name`. Example: `system:bigquery AND type:table AND name:customers`
- Use `page_size` to limit the volume of returned results, especially during exploratory phases.
- This method returns basic entry information. To retrieve rich, LLM-ready metadata (including schemas, quality scores, and usage patterns), parse the `dataplex_entry.name` from the results and pass them to `LookupContext`. Alternatively, you can use `LookupEntry` to get detailed metadata about the entry.


### 🔌 `managed-kafka` (33 Tools)
- **`add_acl_entry`** *(cluster, operation, patternType, permissionType)*: Adds an ACL entry to an existing Google Cloud Managed Service for Apache Kafka ACL. If the ACL does not exist, it will be created.
The following fields must be provided:
*   `cluster` (required): The cluster in which to add the ACL entry. Structured like `projects/{project}/locations/{location}/clusters/{cluster}`.
*   `resource_type` (required): The resource type for the ACL. Accepted values: CLUSTER, TOPIC, CONSUMER_GROUP, TRANSACTIONAL_ID.
*   `resource_name` (required): The resource name for the ACL. Can be the wildcard literal "*".
*   `pattern_type` (optional): The pattern type for the ACL. Accepted values: LITERAL, PREFIXED. If not specified, defaults to LITERAL.
*   `principal` (required): The principal. Specified as Google Cloud account, with the Kafka StandardAuthorizer prefix "User:". For example: `"User:test-kafka-client@test-project.iam.gserviceaccount.com"`. Can be the wildcard "User:*" to refer to all users.
*   `operation` (required): The operation type. Allowed values are (case insensitive): ALL, READ, WRITE, CREATE, DELETE, ALTER, DESCRIBE, CLUSTER_ACTION, DESCRIBE_CONFIGS, ALTER_CONFIGS, and IDEMPOTENT_WRITE.
*   `permission_type` (optional): The permission type. Accepted values are (case insensitive): ALLOW, DENY. If not specified, defaults to ALLOW.

**Important Notes:**

*   Certain resource types only allow certain operations.
    *   For the `cluster` resource type, only CREATE, CLUSTER_ACTION, DESCRIBE_CONFIGS, ALTER_CONFIGS, IDEMPOTENT_WRITE, ALTER, DESCRIBE, and ALL are allowed.
    *   For the `topic` resource type, only READ, WRITE, CREATE, DESCRIBE, DELETE, ALTER, DESCRIBE_CONFIGS, ALTER_CONFIGS, and ALL are allowed.
    *   For the `consumerGroup` resource type, only READ, DESCRIBE, DELETE, and ALL are allowed.
    *   For the `transactionalId` resource type only DESCRIBE, WRITE, and ALL are allowed.

- **`create_cluster`** *(caPools, clusterId, kmsKey, labels)*: Create a new cluster for Google Cloud Managed service for Apache Kafka.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the cluster creation status. Cluster creation can take 30 minutes or longer.

**Important Notes:**

*   Do not create the cluster without getting all of the required parameters from the user.

- **`create_connect_cluster`** *(connectClusterId, dnsDomainNames, kafkaCluster, labels)*: Create a new Google Cloud Managed Service for Apache Kafka Connect cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the Connect cluster creation status. Connect cluster creation can take 20 minutes or longer.

**Important Notes:**

*   Do not create the connect cluster without getting all of the required parameters first.

- **`create_connector`** *(configs, connectorId, parent, taskRestartPolicyMaximumBackoff)*: Create a new Google Cloud Managed service for Apache Kafka Connect connector.

The user should first be prompted on which connector type they want to create, and then provide the necessary properties for that connector type in the `configs` field. Only use the example configuration for reference. The following connector types are supported:

*   **`configs` (required):** Key-value pairs for connector properties. The available connector types are:
    *   MirrorMaker 2.0 Source connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorSourceConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `topics` (required): "TOPIC_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `offset-syncs.topic.replication.factor`: "1"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Source connector.
            *   `TOPIC_NAME`: The name of the Kafka topic(s) to mirror.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   MirrorMaker 2.0 Checkpoint connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorCheckpointConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `consumer-groups` (required): "CONSUMER_GROUP_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Source connector.
            *   `CONSUMER_GROUP_NAME`: The name of the consumer group to use for the checkpoint connector.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   MirrorMaker 2.0 Heartbeat connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorHeartbeatConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `consumer-groups` (required): "CONSUMER_GROUP_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Heartbeat connector.
            *   `CONSUMER_GROUP_NAME`: The name of the consumer group to use for the heartbeat connector.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   BigQuery Sink connector
        *   Example Configuration:
            *   `name`: "BQ_SINK_CONNECTOR_ID"
            *   `project` (required): "GCP_PROJECT_ID"
            *   `topics`: "TOPIC_ID"
            *   `tasks.max`: "3"
            *   `connector.class` (required): "com.wepay.kafka.connect.bigquery.BigQuerySinkConnector"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `value.converter`: "org.apache.kafka.connect.json.JsonConverter"
            *   `value.converter.schemas.enable`: "false"
            *   `defaultDataset` (`required`): "BQ_DATASET_ID"
        *    Replace with these:
            *   `BQ_SINK_CONNECTOR_ID`: The ID or name of the BigQuery Sink connector. The name of a connector is immutable.
            *   `GCP_PROJECT_ID`: The ID of the Google Cloud project where your BigQuery dataset resides.
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which the data flows to the BigQuery Sink connector.
            *   `BQ_DATASET_ID`: The ID of the BigQuery dataset that acts as the sink for the pipeline.
    *   Cloud Storage Sink connector
        *   Example Configuration:
            *   `name`: "GCS_SINK_CONNECTOR_ID"
            *   `connector.class` (required): "io.aiven.kafka.connect.gcs.GcsSinkConnector"
            *   `tasks.max`: "1"
            *   `topics` (required): "TOPIC_ID"
            *   `gcs.bucket.name` (required): "GCS_BUCKET_NAME"
            *   `gcs.credentials.default`: "true"
            *   `format.output.type`: "json"
            *   `value.converter`: "org.apache.kafka.connect.json.JsonConverter"
            *   `value.converter.schemas.enable`: "false"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
        *    Replace with these:
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which the data flows to the Cloud Storage Sink connector.
            *   `GCS_BUCKET_NAME`: The name of the Cloud Storage bucket that acts as a sink for the pipeline.
            *   `GCS_SINK_CONNECTOR_ID`: The ID or name of the Cloud Storage Sink connector. The name of a connector is immutable.
    *   Pub/Sub Source connector
        *   Example Configuration:
            *   `connector.class` (required): "com.google.pubsub.kafka.source.CloudPubSubSourceConnector"
            *   `cps.project` (required): "PROJECT_ID"
            *   `cps.subscription` (required): "PUBSUB_SUBSCRIPTION_ID"
            *   `kafka.topic` (required): "KAFKA_TOPIC_ID"
            *   `value.converter`: "org.apache.kafka.connect.converters.ByteArrayConverter"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `tasks.max`: "3"
        *   Replace with these:
            *   `PROJECT_ID`: The ID of the Google Cloud project where the Pub/Sub subscription resides.
            *   `PUBSUB_SUBSCRIPTION_ID`: The ID of the Pub/Sub subscription to pull data from.
            *   `KAFKA_TOPIC_ID`: The ID of the Kafka topic where data is written.
    *   Pub/Sub Sink connector
        *   Example Configuration:
            *   `connector.class`: "com.google.pubsub.kafka.sink.CloudPubSubSinkConnector"
            *   `name`: "CPS_SINK_CONNECTOR_ID"
            *   `tasks.max`: "1"
            *   `topics`: "TOPIC_ID"
            *   `value.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `cps.topic`: "CPS_TOPIC_ID"
            *   `cps.project`: "GCP_PROJECT_ID"
        *    Replace with these:
            *   `CPS_SINK_CONNECTOR_ID`: The ID or name of the Pub/Sub Sink connector. The name of a connector is immutable.
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which data is read by the Pub/Sub Sink connector.
            *   `CPS_TOPIC_ID`: The ID of the Pub/Sub topic to which data is published.
            *   `GCP_PROJECT_ID`: The ID of the Google Cloud project where your Pub/Sub topic resides.
*   **`task_restart_policy` (optional):** A policy that specifies how to restart failed connector tasks. If not set, failed tasks won't be restarted.
    *   **`minimum_backoff` (optional):** The minimum amount of time to wait before retrying a failed task (e.g., "60s"). Defaults to 60 seconds.
    *   **`maximum_backoff` (optional):** The maximum amount of time to wait before retrying a failed task (e.g., "43200s" for 12 hours). Defaults to 12 hours.
    *   **`task_retry_disabled` (optional):** If true, task retry is disabled.

**Important Notes:**

*   The configs field should be formatted as a JSON object, for example: `"configs":{"name":"my-connector","tasks.max":"1","gcs.bucket.name",...}`. Do not add unnecessary quotes around the keys or values.

- **`create_topic`** *(configs, parent, partitionCount, replicationFactor)*: Create a new Google Cloud Managed Service for Apache Kafka topic.

- **`delete_cluster`** *(name)*: Deletes a Google Cloud Managed Service for Apache Kafka cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the cluster deletion status. Cluster deletions can take 10 minutes or longer.

- **`delete_connect_cluster`** *(name)*: Deletes a Google Cloud Managed service for Apache Kafka Connect cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the Connect cluster deletion status. Connect cluster deletions can take 10 minutes or longer.

- **`delete_connector`** *(name)*: Deletes a Google Cloud Managed Service for Apache Kafka Connect connector.

- **`delete_consumer_group`** *(name)*: Deletes a Google Cloud Managed Service for Apache Kafka consumer group.

- **`delete_topic`** *(name)*: Deletes a Google Cloud Managed Service for Apache Kafka topic.

- **`get_acl`** *(parent, patternType, resourceName, resourceType)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka ACL.
- **`get_cluster`** *(name, view)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka cluster.
- **`get_connect_cluster`** *(name)*: Get the details of an existing Google Cloud Managed service for Apache Kafka Connect cluster.
- **`get_connector`** *(name)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka Connect connector.

- **`get_consumer_group`** *(name)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka consumer group.
- **`get_operation`** *(name)*: Get the status of a long-running operation (LRO).

**Usage**

Some tools (`create_cluster` and `update_cluster`) return a long-running operation.
You can use this tool to get the status of the operation.

**Parameters**

*   `name`: The name of the operation to get. It corresponds to the `name` field in the long-running operation. It should be in the format of `projects/{project}/locations/{location}/operations/{operation}`.

**Returns**

*   An `Operation` object that contains the status of the operation.
*   If the operation is not complete, the response will be empty.
*   If the operation is complete, the response will contain either:
    * A `response` field that contains the result of the operation and indicates that it was successful.
    * A `error` field that indicates any errors that occurred during the operation.

- **`get_topic`** *(name)*: Get the details of an existing Google Cloud Managed Service for Apache Kafka topic.
- **`list_acls`** *(pageSize, pageToken, parent)*: List all ACLs for Google Cloud Managed Service for Apache Kafka for a given project, location, and cluster.
- **`list_clusters`** *(filter, orderBy, pageSize, pageToken)*: Lists all clusters for Google Cloud Managed service for Apache Kafka in a given project and location.
- **`list_connect_clusters`** *(filter, orderBy, pageSize, pageToken)*: List all Connect clusters for Google Cloud Managed Service for Apache Kafka Connect for a given project and location.
- **`list_connectors`** *(pageSize, pageToken, parent)*: List all connectors for Google Cloud Managed Service for Apache Kafka Connect for a given project, location, and Connect cluster.

- **`list_consumer_groups`** *(pageSize, pageToken, parent)*: List all consumer groups for Google Cloud Managed Service for Apache Kafka for a given project, location, and cluster.
- **`list_topics`** *(pageSize, pageToken, parent)*: List all topics for Google Cloud Managed Service for Apache Kafka for a given project, location, and cluster.
- **`pause_connector`** *(name)*: Pauses a Google Cloud Managed service for Apache Kafka Connect connector and its tasks.

- **`remove_acl_entry`** *(cluster, operation, patternType, permissionType)*: Removes an ACL entry from an existing Google Cloud Managed service for Apache Kafka ACL. If the removed entry was the last one in the ACL, the ACL will be deleted.
The following fields must be provided:
*   `cluster` (required): The cluster in which to remove the ACL entry. Structured like `projects/{project}/locations/{location}/clusters/{cluster}`.
*   `resource_type` (required): The resource type for the ACL. Accepted values: CLUSTER, TOPIC, CONSUMER_GROUP, TRANSACTIONAL_ID.
*   `resource_name` (required): The resource name for the ACL. Can be the wildcard literal "*".
*   `pattern_type` (optional): The pattern type for the ACL. Accepted values: LITERAL, PREFIXED. If not specified, defaults to LITERAL.
*   `principal` (required): The principal. Specified as Google Cloud account, with the Kafka StandardAuthorizer prefix "User:". For example: `"User:test-kafka-client@test-project.iam.gserviceaccount.com"`. Can be the wildcard "User:*" to refer to all users.
*   `operation` (required): The operation type. Allowed values are (case insensitive): ALL, READ, WRITE, CREATE, DELETE, ALTER, DESCRIBE, CLUSTER_ACTION, DESCRIBE_CONFIGS, ALTER_CONFIGS, and IDEMPOTENT_WRITE.
*   `permission_type` (optional): The permission type. Accepted values are (case insensitive): ALLOW, DENY. If not specified, defaults to ALLOW.

- **`restart_connector`** *(name)*: Restarts a Google Cloud Managed service for Apache Kafka Connect Connector.

- **`resume_connector`** *(name)*: Resumes a Google Cloud Managed service for Apache Kafka Connect connector and its tasks.

- **`stop_connector`** *(name)*: Stops a Google Cloud Managed service for Apache Kafka Connect connector.

- **`update_cluster`** *(allowBrokerDownscaleOnClusterUpscale, caPools, fieldsToClear, labels)*: Update an existing Google Cloud Managed service for Apache Kafka cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the cluster update status. Cluster updates can take 20 minutes or longer.

**Important Notes:**

*   When calling update_cluster, you must provide the name of the cluster to update, formatted as `projects/{project}/locations/{location}/clusters/{cluster}`.
*   Do not update the cluster without getting all of the required parameters from the user.
*   To clear a field, use the `fields_to_clear` parameter with a list of field masks (e.g. `["labels", "tls_config"]`).

- **`update_connect_cluster`** *(dnsDomainNames, fieldsToClear, labels, memoryBytes)*: Update an existing Google Cloud Managed service for Apache Kafka Connect cluster.

This tool returns a long-running operation (LRO) that you can poll using the `get_operation` tool to track the Connect cluster update status. Connect cluster updates can take 20 minutes or longer.

**Important Notes:**

*   When calling update_connect_cluster, you must provide the name of the Connect cluster to update, formatted as `projects/{project}/locations/{location}/connectClusters/{connect_cluster_id}`.
*   The `kafka_cluster` field is immutable and cannot be updated after creation.
*   To clear a field, use the `fields_to_clear` parameter with a list of field masks.

- **`update_connector`** *(configs, fieldsToClear, name, taskRestartPolicyMaximumBackoff)*: Update an existing Google Cloud Managed Service for Apache Kafka Connect connector.

The `configs` field can be updated. The agent can first use the `get_connector` method to get the current connector configuration, to provide a baseline configuration for the user to edit. Use the example configurations provided below for reference.

*   **configs:** Key-value pairs for connector properties. The following connectors support configuration updates:
    *   MirrorMaker 2.0 Source connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorSourceConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `topics` (required): "TOPIC_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `offset-syncs.topic.replication.factor`: "1"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Source connector.
            *   `TOPIC_NAME`: The name of the Kafka topic(s) to mirror.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   MirrorMaker 2.0 Checkpoint connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorCheckpointConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `consumer-groups` (required): "CONSUMER_GROUP_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Source connector.
            *   `CONSUMER_GROUP_NAME`: The name of the consumer group to use for the checkpoint connector.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   MirrorMaker 2.0 Heartbeat connector
        *   Example Configuration:
            *   `connector.class` (required): "org.apache.kafka.connect.mirror.MirrorHeartbeatConnector"
            *   `name`: "MM2_CONNECTOR_ID"
            *   `source.cluster.alias` (required): "source"
            *   `target.cluster.alias` (required): "target"
            *   `consumer-groups` (required): "CONSUMER_GROUP_NAME"
            *   `source.cluster.bootstrap.servers` (required): "SOURCE_CLUSTER_DNS"
            *   `target.cluster.bootstrap.servers` (required): "TARGET_CLUSTER_DNS"
            *   `source.cluster.security.protocol`: "SASL_SSL"
            *   `source.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `source.cluster.sasl.login.callback.handler.class`: com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler
            *   `source.cluster.sasl.jaas.config`: org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;
            *   `target.cluster.security.protocol`: "SASL_SSL"
            *   `target.cluster.sasl.mechanism`: "OAUTHBEARER"
            *   `target.cluster.sasl.login.callback.handler.class`: "com.google.cloud.hosted.kafka.auth.GcpLoginCallbackHandler"
            *   `target.cluster.sasl.jaas.config`: "org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required;"
        *   Replace with these:
            *   `MM2_CONNECTOR_ID`: The ID or name of the MirrorMaker 2.0 Heartbeat connector.
            *   `CONSUMER_GROUP_NAME`: The name of the consumer group to use for the heartbeat connector.
            *   `SOURCE_CLUSTER_DNS`: The DNS endpoint for the source Kafka cluster.
            *   `TARGET_CLUSTER_DNS`: The DNS endpoint for the target Kafka cluster.
    *   BigQuery Sink connector
        *   Example Configuration:
            *   `name`: "BQ_SINK_CONNECTOR_ID"
            *   `project` (required): "GCP_PROJECT_ID"
            *   `topics`: "TOPIC_ID"
            *   `tasks.max`: "3"
            *   `connector.class` (required): "com.wepay.kafka.connect.bigquery.BigQuerySinkConnector"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `value.converter`: "org.apache.kafka.connect.json.JsonConverter"
            *   `value.converter.schemas.enable`: "false"
            *   `defaultDataset` (`required`): "BQ_DATASET_ID"
        *    Replace with these:
            *   `BQ_SINK_CONNECTOR_ID`: The ID or name of the BigQuery Sink connector. The name of a connector is immutable.
            *   `GCP_PROJECT_ID`: The ID of the Google Cloud project where your BigQuery dataset resides.
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which the data flows to the BigQuery Sink connector.
            *   `BQ_DATASET_ID`: The ID of the BigQuery dataset that acts as the sink for the pipeline.
    *   Cloud Storage Sink connector
        *   Example Configuration:
            *   `name`: "GCS_SINK_CONNECTOR_ID"
            *   `connector.class` (required): "io.aiven.kafka.connect.gcs.GcsSinkConnector"
            *   `tasks.max`: "1"
            *   `topics` (required): "TOPIC_ID"
            *   `gcs.bucket.name` (required): "GCS_BUCKET_NAME"
            *   `gcs.credentials.default`: "true"
            *   `format.output.type`: "json"
            *   `value.converter`: "org.apache.kafka.connect.json.JsonConverter"
            *   `value.converter.schemas.enable`: "false"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
        *    Replace with these:
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which the data flows to the Cloud Storage Sink connector.
            *   `GCS_BUCKET_NAME`: The name of the Cloud Storage bucket that acts as a sink for the pipeline.
            *   `GCS_SINK_CONNECTOR_ID`: The ID or name of the Cloud Storage Sink connector. The name of a connector is immutable.
    *   Pub/Sub Source connector
        *   Example Configuration:
            *   `connector.class` (required): "com.google.pubsub.kafka.source.CloudPubSubSourceConnector"
            *   `cps.project` (required): "PROJECT_ID"
            *   `cps.subscription` (required): "PUBSUB_SUBSCRIPTION_ID"
            *   `kafka.topic` (required): "KAFKA_TOPIC_ID"
            *   `value.converter`: "org.apache.kafka.connect.converters.ByteArrayConverter"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `tasks.max`: "3"
        *   Replace with these:
            *   `PROJECT_ID`: The ID of the Google Cloud project where the Pub/Sub subscription resides.
            *   `PUBSUB_SUBSCRIPTION_ID`: The ID of the Pub/Sub subscription to pull data from.
            *   `KAFKA_TOPIC_ID`: The ID of the Kafka topic where data is written.
    *   Pub/Sub Sink connector
        *   Example Configuration:
            *   `connector.class`: "com.google.pubsub.kafka.sink.CloudPubSubSinkConnector"
            *   `name`: "CPS_SINK_CONNECTOR_ID"
            *   `tasks.max`: "1"
            *   `topics`: "TOPIC_ID"
            *   `value.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `key.converter`: "org.apache.kafka.connect.storage.StringConverter"
            *   `cps.topic`: "CPS_TOPIC_ID"
            *   `cps.project`: "GCP_PROJECT_ID"
        *    Replace with these:
            *   `CPS_SINK_CONNECTOR_ID`: The ID or name of the Pub/Sub Sink connector. The name of a connector is immutable.
            *   `TOPIC_ID`: The ID of the Managed Service for Apache Kafka topic from which data is read by the Pub/Sub Sink connector.
            *   `CPS_TOPIC_ID`: The ID of the Pub/Sub topic to which data is published.
            *   `GCP_PROJECT_ID`: The ID of the Google Cloud project where your Pub/Sub topic resides.
*   **`task_restart_policy` (optional):** A policy that specifies how to restart failed connector tasks. If not set, failed tasks won't be restarted.
    *   **`minimum_backoff` (optional):** The minimum amount of time to wait before retrying a failed task (e.g., "60s"). Defaults to 60 seconds.
    *   **`maximum_backoff` (optional):** The maximum amount of time to wait before retrying a failed task (e.g., "43200s" for 12 hours). Defaults to 12 hours.
    *   **`task_retry_disabled` (optional):** If true, task retry is disabled.

**Important Notes:**

*   When calling update_connector, you must provide the name of the connector to update, formatted as `projects/{project}/locations/{location}/connectClusters/{connect_cluster_id}/connectors/{connector_id}`.

- **`update_consumer_group`** *(name, topics)*: Update an existing Google Cloud Managed Service for Apache Kafka consumer group. This tool can only be used to update the offsets for topics consumed by the group.

**Important Notes:**

*   To update a consumer group's offsets, the consumer group must be inactive (i.e., there are no active consumers in the group), and topics with new offsets must be provided.
*   Before making an update, the agent should call `get_consumer_group` to retrieve the current consumer group configuration.

- **`update_topic`** *(configs, fieldsToClear, name, partitionCount)*: Update an existing Google Cloud Managed service for Apache Kafka topic.

**Important Notes:**

*   The UpdateTopic request requires the name of the topic to be updated in the format `projects/{project}/locations/{location}/clusters/{cluster}/topics/{topic}`.


### 🔌 `notebooks` (11 Tools)
- **`create_notebook`** *(directory, filename)*: Create a new notebook file in the workspace and open it.
- **`delete_cell`** *(index, path)*: Delete a cell at the given index from a Jupyter notebook (.ipynb) using the Notebook API.
- **`get_cell_outputs`** *(index, path)*: Read outputs from a code cell by index: execution summary and output items.
- **`get_cell_range`** *(end_index, path, start_index)*: Read a range of cells from a notebook, from start_index to end_index (inclusive).
- **`get_notebook_info`** *(path)*: Get high-level information about a notebook: cell counts, type distribution, kernel metadata, and last modified time.
- **`insert_code_cell`** *(code, index, languageId, path)*: Insert a code cell into a Jupyter notebook (.ipynb) at a given index using the Notebook API.
- **`insert_markdown_cell`** *(index, markdown, path)*: Insert a markdown cell into a Jupyter notebook (.ipynb) at a given index using the Notebook API.
- **`list_cells`** *(path, preview_length, type_filter)*: List cells in a notebook with index, type, source preview, and execution status.
- **`read_cell`** *(index, path)*: Read a specific cell by index: type, source, execution info, and outputs (for code cells).
- **`replace_cell`** *(code, index, languageId, path)*: Replace the content (and optionally language) of an existing cell at the given index in a Jupyter notebook (.ipynb) using the Notebook API.
- **`search_cells`** *(case_sensitive, path, preview_length, query)*: Search notebook cells for text, optionally filtering by cell type.

### 🔌 `perplexity-ask` (1 Tools)
- **`perplexity_ask`** *(messages)*: Engages in a conversation using the Sonar API. Accepts an array of messages (each with a role and content) and returns a ask completion response from the Perplexity model.

### 🔌 `prisma-mcp-server` (4 Tools)
- **`Prisma-Studio`** *(projectCWD)*: Open Prisma Studio to view and edit data visually.
- **`migrate-dev`** *(name, projectCWD)*: Prisma Migrate Dev is used to update Prisma whenever schema.prisma has been modified.
- **`migrate-reset`** *(projectCWD)*: Prisma Migrate Reset --force is used to reset the database and migration history.
- **`migrate-status`** *(projectCWD)*: Check the status of migrations in database and ./prisma/migrations.

### 🔌 `sequential-thinking` (1 Tools)
- **`sequentialthinking`** *(branchFromThought, branchId, isRevision, needsMoreThoughts)*: A detailed tool for dynamic and reflective problem-solving through thoughts.
This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
Each thought can build on, question, or revise previous insights as understanding deepens.

When to use this tool:
- Breaking down complex problems into steps
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where the full scope might not be clear initially
- Problems that require a multi-step solution
- Tasks that need to maintain context over multiple steps
- Situations where irrelevant information needs to be filtered out

Key features:
- You can adjust total_thoughts up or down as you progress
- You can question or revise previous thoughts
- You can add more thoughts even after reaching what seemed like the end
- You can express uncertainty and explore alternative approaches
- Not every thought needs to build linearly - you can branch or backtrack
- Generates a solution hypothesis
- Verifies the hypothesis based on the Chain of Thought steps
- Repeats the process until satisfied
- Provides a correct answer

Parameters explained:
- thought: Your current thinking step, which can include:
  * Regular analytical steps
  * Revisions of previous thoughts
  * Questions about previous decisions
  * Realizations about needing more analysis
  * Changes in approach
  * Hypothesis generation
  * Hypothesis verification
- nextThoughtNeeded: True if you need more thinking, even if at what seemed like the end
- thoughtNumber: Current number in sequence (can go beyond initial total if needed)
- totalThoughts: Current estimate of thoughts needed (can be adjusted up/down)
- isRevision: A boolean indicating if this thought revises previous thinking
- revisesThought: If is_revision is true, which thought number is being reconsidered
- branchFromThought: If branching, which thought number is the branching point
- branchId: Identifier for the current branch (if any)
- needsMoreThoughts: If reaching end but realizing more thoughts needed

You should:
1. Start with an initial estimate of needed thoughts, but be ready to adjust
2. Feel free to question or revise previous thoughts
3. Don't hesitate to add more thoughts if needed, even at the "end"
4. Express uncertainty when present
5. Mark thoughts that revise previous thinking or branch into new paths
6. Ignore information that is irrelevant to the current step
7. Generate a solution hypothesis when appropriate
8. Verify the hypothesis based on the Chain of Thought steps
9. Repeat the process until satisfied with the solution
10. Provide a single, ideally correct answer as the final output
11. Only set nextThoughtNeeded to false when truly done and a satisfactory answer is reached

### 🔌 `vertex-ai-search` (3 Tools)
- **`conversational_search`** *(answerGenerationSpec, asynchronousMode, endUserSpec, groundingSpec)*: Perform a conversational search on ingested data in Google owned data stores
- **`list_engines`** *(filter, pageSize, pageToken, parent)*: List the engines (apps) under a collection.
- **`search`** *(boostSpec, branch, canonicalFilter, contentSearchSpec)*: Perform a search on ingested data in Google owned data stores

### 🔌 `visualization` (1 Tools)
- **`render_chart`** *(height, spec, width)*: Renders a complete Apache ECharts V5 specification object into an SVG chart and returns it as a local file link for display in the chat.


---
## 4. Complete 57-Skills Encyclopedia

### 🏷️ BioNeMo & NIM Inference
- **`bionemo-benchmark-profiler`**: >-
- **`bionemo-esmfold-generation`**: Use this skill when predicting atomic-resolution 3D macromolecular structures from raw protein sequences using NVIDIA BioNeMo ESMFold NIM. Covers pLDDT extraction, per-residue confidence evaluation, and structure export for docking.
- **`bionemo-nim-inference`**: >-
- **`cheminformatics-rdkit-bionemo`**: >-
- **`macromolecular-pdb-prep`**: >-
- **`target-druggability-assessment`**: Use this skill to evaluate macromolecular binding pocket volume, hydrophobicity, enclosure, and druggability scores before initiating high-throughput molecular docking or generative design campaigns.

### 🏷️ Bioinformatics & Science
- **`alphafold_database_fetch_and_analyze`**: >
- **`alphagenome_atlas_website_links`**: >-
- **`alphagenome_single_variant_analysis`**: >
- **`alphagenome_variant_impact_score`**: >-
- **`chembl_database`**: >
- **`clinical_trials_database`**: >
- **`clinvar_database`**: >
- **`credentials`**: >-
- **`dbsnp_database`**: >
- **`embl_ebi_ols`**: >
- **`encode_ccres_database`**: >
- **`ensembl_database`**: >
- **`foldseek_structural_search`**: >
- **`gnomad_database`**: >
- **`gtex_database`**: >
- **`human_protein_atlas_database`**: >
- **`interpro_database`**: >
- **`jaspar_database`**: >
- **`literature_search_arxiv`**: >
- **`literature_search_biorxiv`**: >
- **`literature_search_europepmc`**: >
- **`literature_search_openalex`**: >
- **`ncbi_sequence_fetch`**: >
- **`openfda_database`**: >
- **`opentargets_database`**: >
- **`pdb_database`**: >
- **`predictingthepast`**: >
- **`protein_sequence_msa`**: >
- **`protein_sequence_similarity_search`**: >
- **`pubchem_database`**: >
- **`pubmed_database`**: >-
- **`pymol`**: >
- **`quickgo_database`**: >
- **`reactome_database`**: >
- **`string_database`**: >
- **`ucsc_conservation_and_tfbs`**: >
- **`unibind_database`**: >-
- **`uniprot_database`**: >-
- **`uv`**: >-
- **`workflow_skill_creator`**: >

### 🏷️ Browser & QA
- **`a11y-debugging`**: Uses Chrome DevTools MCP for accessibility (a11y) debugging and auditing based on web.dev guidelines. Use when testing semantic HTML, ARIA labels, focus states, keyboard navigation, tap targets, and color contrast.
- **`chrome-devtools`**: Uses Chrome DevTools via MCP for efficient debugging, troubleshooting and browser automation. Use when debugging web pages, automating browser interactions, analyzing performance, or inspecting network requests. This skill does not apply to `--slim` mode (MCP configuration).
- **`debug-optimize-lcp`**: Guides debugging and optimizing Largest Contentful Paint (LCP) using Chrome DevTools MCP tools. Use this skill whenever the user asks about LCP performance, slow page loads, Core Web Vitals optimization, or wants to understand why their page's main content takes too long to appear. Also use when the user mentions "largest contentful paint", "page load speed", "CWV", or wants to improve how fast their hero image or main content renders.
- **`memory-leak-debugging`**: Diagnoses and resolves memory leaks in JavaScript/Node.js applications. Use when a user reports high memory usage, OOM errors, or wants to analyze heapsnapshots or run memory leak detection tools like memlab.
- **`troubleshooting`**: Uses Chrome DevTools MCP and documentation to troubleshoot connection and target issues. Trigger this skill when list_pages, new_page, or navigate_page fail, or when the server initialization fails.

### 🏷️ Core IDE & Governance
- **`accidental-data-loss-prevention`**: |
- **`agy-customizations`**: >-
- **`antigravity_guide`**: Provides a comprehensive guide, quick reference, and sitemap for Google Antigravity (AGY), including the Antigravity CLI (agy), Antigravity 2.0, Antigravity IDE, Python SDK, slash commands, keybindings, and customizations (skills, rules, MCP, sidecars). Activate this skill when the user asks questions about how to use, configure, or customize Antigravity, AGY, the agy CLI, the Antigravity IDE, or Antigravity 2.0.
- **`managing-python-dependencies`**: |
- **`permissioned-github`**: Guidelines for interacting with GitHub and request permissions from the user when commands fail due to restrictions in the agent environment.
- **`skill-repair`**: |
