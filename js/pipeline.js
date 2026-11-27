/**
 * BioNeMo NIM Inference Benchmark - Pipeline Architecture & Schema Inspector
 * Module: ./js/pipeline.js
 * 
 * Implements:
 * 1. 5-Stage Agentic Pipeline data flow orchestration.
 * 2. Stage 04 ADMET filter gate highlighted in semantic amber.
 * 3. Reactive Slide-Over Schema Inspector with Input/Output schemas, resilience policies, and copyable payloads.
 * 4. Keyboard accessibility (Escape, Enter, Space).
 */

import { escapeHtml, copyToClipboard } from './shared/dom-utils.js';

  const PIPELINE_STAGES = [
    {
      id: 'stage_01',
      stageNum: '01',
      title: 'Target & Ligand Ingestion',
      service: 'RDKit C++ / PDB REST Gateway',
      isAmber: false,
      desc: 'Canonical 20 IUPAC amino acid verification, PDB/UniProt coordinate normalization, and explicit SMILES valence sanitization.',
      inputSchema: {
        target_seq: "string (IUPAC 20 aa)",
        uniprot_id: "string (e.g. P01116)",
        ligand_smiles: "string",
        force_sanitize: true
      },
      outputSchema: {
        clean_sequence: "string",
        sanitized_mol_block: "string",
        heavy_atom_count: "integer",
        is_chemically_valid: true
      },
      resilience: "Rejects non-canonical residues with HTTP 422; exponential backoff (n=3, jittered) on upstream RCSB PDB queries with fallback to local bundled coordinates.",
      samplePayload: {
        target: "KRAS_G12D",
        uniprot: "P01116",
        smiles: "O=C(N1CCN(C2=NC=C(F)C3=C2C(C4=C(F)C=CC=C4F)=CC=C3)CC1)C5=C(N)N=C6C(F)=CC=CC6=C5"
      }
    },
    {
      id: 'stage_02',
      stageNum: '02',
      title: 'NVIDIA BioNeMo NIM Inference',
      service: 'ESM-2 (650M) · ESMFold · MolMIM 70M',
      isAmber: false,
      desc: 'GPU-accelerated inference across TensorRT-optimized biological containers. Dispatches token PLM embeddings, 3D structure prediction, and CMA-ES analog exploration.',
      inputSchema: {
        model: "nvidia/esmfold:24.03 | nvidia/molmim:24.03 | nvidia/esm2-650m:24.03",
        sequence: "string",
        sampling_temperature: 0.2,
        precision: "FP16 | FP8"
      },
      outputSchema: {
        folded_pdb: "string (atomic coords)",
        mean_plddt: 84.4,
        analogues: ["string (SMILES)"],
        inference_latency_ms: 720.0
      },
      resilience: "Warm-pool container keep-alive; automatic retry with sequence chunking upon CUDA OOM; zero-credit hermetic mock fallback for testing.",
      samplePayload: {
        nim_endpoint: "https://health.api.nvidia.com/v1/biology/meta/esmfold",
        model: "nvidia/esmfold:24.03",
        sequence_length: 186
      }
    },
    {
      id: 'stage_03',
      stageNum: '03',
      title: 'DiffDock SE(3) Pose Scoring',
      service: 'nvcr.io/nim/mit/diffdock:24.03',
      isAmber: false,
      desc: 'Score-based generative reverse diffusion across 10 steps in SE(3) manifold space. Generates 5 ranked ligand binding poses with atomic contact vectors.',
      inputSchema: {
        receptor_pdb: "string",
        ligand_sdf: "string",
        diffusion_steps: 10,
        poses_to_generate: 5
      },
      outputSchema: {
        ranked_poses: [
          { pose_id: 1, confidence: 0.98, rmsd_to_reference: 0.42, delta_g_kcal_mol: -4.81 }
        ],
        pocket_contacts: ["Asp12", "Tyr96", "Gln61"]
      },
      resilience: "Automatic bounding-box re-centering on pocket centroids if ligand drifts outside catalytic radius (> 15 Å).",
      samplePayload: {
        target: "8AZV",
        ligand: "MRTX1133_bioisostere",
        poses: 5,
        docking_mode: "focused_pocket"
      }
    },
    {
      id: 'stage_04',
      stageNum: '04',
      title: 'ADMET & Physicochemical Gate',
      service: 'RDKit ADMET Filter Suite',
      isAmber: true,
      desc: 'Strict drug-likeness gating. Evaluates Lipinski Rule of 5, Veber criteria, synthetic accessibility (SAScore), quantitative drug-likeness (QED), and PAINS alert screening.',
      inputSchema: {
        candidates: [{ id: "string", smiles: "string" }],
        max_mw: 600.0,
        max_logp: 5.5,
        filter_pains: true
      },
      outputSchema: {
        gated_candidates: [
          { id: "NIM-LEAD-01-03", qed: 0.309, sascore: 7.74, ro5_violations: 2, status: "FLAGGED_FOR_OPTIMIZATION" }
        ],
        pareto_optimal_ids: ["NIM-LEAD-01-03"]
      },
      resilience: "Unparsable chemical structures flagged with explicit valence diagnostics without interrupting downstream batch execution.",
      samplePayload: {
        screening_mode: "strict_admet",
        pains_check: true,
        ro5_tolerance: 2,
        biosecurity_screen: "Tier 1 Cleared"
      }
    },
    {
      id: 'stage_05',
      stageNum: '05',
      title: 'Telemetry & OT-2 Synthesis Export',
      service: 'Telemetry Logger & Opentrons API v2.15',
      isAmber: false,
      desc: 'Aggregates latency, throughput, and hardware speedups into canonical JSON/CSV summaries. Synthesizes executable Python protocols for Opentrons liquid handlers.',
      inputSchema: {
        nominated_lead_id: "string",
        dilution_factor: 2,
        plate_type: "corning_96_wellplate_360ul_flat"
      },
      outputSchema: {
        python_protocol: "string (Python 3.12)",
        summary_json: "object",
        time_saved_hours: 88.5
      },
      resilience: "Generates syntax-verified, self-contained Python scripts adhering strictly to Opentrons API v2.15 safety and volume constraints.",
      samplePayload: {
        script_output: "results/ot2_synthesis_protocol_KRAS_G12D.py",
        aspirate_rate_ul_s: 25,
        target_assay: "KRAS G12D Serial Dilution"
      }
    }
  ];

  let currentStageIdx = 0;

  // DOM Elements cache
  let nodesContainerEl = null;
  let drawerHeaderTitleEl = null;
  let drawerServiceEl = null;
  let inputSchemaEl = null;
  let outputSchemaEl = null;
  let resilienceEl = null;
  let samplePayloadEl = null;
  let copyPayloadBtn = null;

  function renderStageDetails(idx) {
    currentStageIdx = idx;
    const stage = PIPELINE_STAGES[idx];

    // Update node active states
    const nodeCards = document.querySelectorAll('.pipeline-node-card');
    nodeCards.forEach((card, i) => {
      card.classList.toggle('active', i === idx);
      card.setAttribute('aria-expanded', i === idx ? 'true' : 'false');
    });

    // Populate drawer elements
    if (drawerHeaderTitleEl) {
      drawerHeaderTitleEl.textContent = `Stage ${stage.stageNum}: ${stage.title}`;
    }
    if (drawerServiceEl) {
      drawerServiceEl.textContent = stage.service;
    }
    if (inputSchemaEl) {
      inputSchemaEl.textContent = JSON.stringify(stage.inputSchema, null, 2);
    }
    if (outputSchemaEl) {
      outputSchemaEl.textContent = JSON.stringify(stage.outputSchema, null, 2);
    }
    if (resilienceEl) {
      resilienceEl.textContent = stage.resilience;
    }
    if (samplePayloadEl) {
      samplePayloadEl.textContent = JSON.stringify(stage.samplePayload, null, 2);
    }
  }

  function init() {
    nodesContainerEl = document.getElementById('pipeline-nodes-container');
    drawerHeaderTitleEl = document.getElementById('schema-drawer-title');
    drawerServiceEl = document.getElementById('schema-drawer-service');
    inputSchemaEl = document.getElementById('schema-input-code');
    outputSchemaEl = document.getElementById('schema-output-code');
    resilienceEl = document.getElementById('schema-resilience-text');
    samplePayloadEl = document.getElementById('schema-payload-code');
    copyPayloadBtn = document.getElementById('btn-copy-schema-payload');

    // Build Node Cards
    if (nodesContainerEl) {
      let cardsHtml = '';
      PIPELINE_STAGES.forEach((stage, idx) => {
        const amberClass = stage.isAmber ? 'stage-amber' : '';
        cardsHtml += `
          <button
            type="button"
            class="pipeline-node-card ${amberClass} ${idx === 0 ? 'active' : ''}"
            data-stage-idx="${idx}"
            aria-expanded="${idx === 0 ? 'true' : 'false'}"
            aria-controls="schema-drawer-panel"
          >
            <div class="node-stage-numeral">STAGE ${stage.stageNum}</div>
            <div class="node-title">${escapeHtml(stage.title)}</div>
            <div class="node-desc">${escapeHtml(stage.desc)}</div>
            <div class="node-inspect-cta">
              <span>Inspect Schema</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
            </div>
          </button>
        `;
      });
      nodesContainerEl.innerHTML = cardsHtml;

      const cards = nodesContainerEl.querySelectorAll('.pipeline-node-card');
      cards.forEach((card) => {
        const idx = parseInt(card.getAttribute('data-stage-idx'), 10);
        card.addEventListener('click', () => renderStageDetails(idx));
      });
    }

    if (copyPayloadBtn) {
      copyPayloadBtn.addEventListener('click', async () => {
        const stage = PIPELINE_STAGES[currentStageIdx];
        const payloadText = JSON.stringify(stage.samplePayload, null, 2);
        const ok = await copyToClipboard(payloadText);
        if (ok) {
          const originalText = copyPayloadBtn.innerHTML;
          copyPayloadBtn.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
            <span>Copied!</span>
          `;
          setTimeout(() => {
            copyPayloadBtn.innerHTML = originalText;
          }, 2000);
        }
      });
    }

    const btnCopyOt2 = document.getElementById('btn-copy-ot2-code');
    if (btnCopyOt2) {
      btnCopyOt2.addEventListener('click', async () => {
        const code = document.getElementById('ot2-protocol-code')?.textContent || '';
        const ok = await copyToClipboard(code);
        if (ok) {
          const originalText = btnCopyOt2.innerHTML;
          btnCopyOt2.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
            <span>Protocol Copied!</span>
          `;
          setTimeout(() => {
            btnCopyOt2.innerHTML = originalText;
          }, 2000);
        }
      });
    }

    renderStageDetails(0);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.BioNeMoPipeline = {
    setStage: renderStageDetails,
    getStages: () => PIPELINE_STAGES
  };
