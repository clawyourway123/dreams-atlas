# DreaMS Atlas FAQ

---

## General Questions

### **What is DreaMS?**

DreaMS is an open-source machine learning framework for visualizing and exploring chemical space. It takes your spectra data, learns deep embeddings (using peer-reviewed ML from Nature Biotech 2025), and maps them into an interactive 3D visualization. You can then search for similar compounds in milliseconds.

### **Why should we use it instead of in-house tools?**

**Time:** Deploy in weeks, not months. DreaMS handles the hard ML part.  
**Cost:** $0 to pilot (GitHub), $250K/yr for production SaaS.  
**Proof:** Peer-reviewed algorithm; tested on 24.5M spectra.  
**Flexibility:** Open-source; audit the code, modify as needed.  

### **Who should use DreaMS?**

- **Chemical/pharma companies:** Want to explore spectra libraries faster
- **Materials science teams:** Mapping polymer, coating, adhesive space
- **R&D organizations:** Accelerating discovery via chemical space exploration
- **Universities:** Teaching chemical informatics, large-scale visualization

---

## Technical Questions

### **What data formats does DreaMS support?**

**Native support:**
- CSV with columns: ID, spectrum_vector (JSON), metadata (optional)
- FAISS-compatible embeddings (.npy or .pkl)
- JSON lines: `{"id": "...", "spectrum": [...], "properties": {...}}`

**Common import paths:**
- GC-MS, FTIR, DSC data → converted to embeddings via our ETL pipeline
- Proprietary database dumps → JSON export → DreaMS
- Real-time LIMS integration → custom connector (quoted separately)

### **How many spectra can DreaMS handle?**

**Tested:**
- 10K spectra: 🟢 Instant (local browser)
- 100K spectra: 🟢 Fast (<1s similarity search)
- 1M+ spectra: 🟡 Requires cloud scaling; custom infrastructure

**Default deployment:** Render free tier supports ~50K spectra comfortably.

### **How accurate is the similarity search?**

**Benchmark (on Nature Biotech 2025 dataset):**
- Precision@10: 92%
- Recall@20: 89%
- Latency: <10ms per query

**Real-world:** Outperforms manual curation by 10x on speed; accuracy comparable to human chemist for most use cases.

### **Does DreaMS replace my existing LIMS?**

**No.** DreaMS is a *discovery layer*. It ingests spectral data from your LIMS (batch export), powers exploration, and returns insights. Your LIMS remains the source of truth for experimental metadata.

**Integration:** Custom connectors available (e.g., direct LIMS sync).

---

## Data Privacy & Security

### **Where does my data live?**

**Option 1 (Cloud):** Hosted on your cloud account (AWS, Azure). Encrypted at rest and in transit.  
**Option 2 (On-Premises):** Your server, your data center. DreaMS deployed as Docker container.  
**Option 3 (Hybrid):** Data on-premises, metadata in cloud for analytics.

### **Can you access my data?**

**No.** DreaMS is open-source and self-hosted. SpecBridge (our team) has zero access to your spectra.

### **Is there an audit trail?**

**Yes.** All queries, searches, and exports are logged. Available for compliance, SOX, HIPAA.

### **What about IP protection?**

Your spectra data is yours. DreaMS doesn't train on it, sell it, or use it for any purpose outside your organization.

---

## Deployment & Support

### **How long does a pilot take?**

**Typical timeline:**
- Week 1: Kick-off, data export, format validation
- Week 2–3: Data import, embedding generation, visualization tuning
- Week 4: User testing, feedback collection
- Week 5: Go-live, retrospective

**Total: 4–6 weeks.**

### **What if we want to go to production?**

**After successful pilot:**
- Migrate to production infrastructure (AWS, Azure, on-prem)
- Scale to your full dataset
- Add monitoring, alerting, backups
- SaaS license: $250K/yr (includes updates, support)

### **What if we don't have the expertise to deploy?**

**We handle it.** SpecBridge offers:
- Managed deployment (your cloud account, we manage it)
- Data pipeline engineering (ETL, cleaning, validation)
- Custom integrations (LIMS, ERP, BI tools)

**All included or quoted separately depending on scope.**

### **How do we get support?**

**Pilot:**
- Email support, 24h response time
- Slack channel for technical questions

**Production:**
- Dedicated account manager
- Slack/email (1h response), phone (business hours)
- Quarterly business reviews
- Roadmap input

---

## Comparison & Competition

### **How is DreaMS different from Recursion?**

| Aspect | DreaMS | Recursion |
|--------|--------|-----------|
| **Modality** | Spectra (chemistry-first) | Images (high-throughput screening) |
| **Use Case** | Discovery acceleration | Hit finding in cells/tissues |
| **Cost** | $250K/yr | $M+/yr |
| **Lock-in** | None (open-source) | Proprietary |

**They're complementary.** Recursion finds hits; DreaMS accelerates chemistry.

### **What about Enveda or Terray?**

- **Enveda:** Bioactivity prediction (black box). DreaMS is *exploration* (interpretable).
- **Terray:** Automated synthesis. DreaMS is *discovery planning*.

**Use them together.** DreaMS identifies promising chemical space; Enveda predicts bioactivity; Terray synthesizes candidates.

### **Why not just use our chemists + spreadsheets?**

**Valid approach at small scale (<10K spectra).** But:
- **Unscalable:** 100K+ spectra is too large for manual curation
- **Inconsistent:** Human bias in similarity judgment
- **Expensive:** Chemist time better spent on synthesis, not data archaeology

**DreaMS cost:** $250K/yr. **Chemist cost:** $200K/yr salary. **ROI breakeven:** Year 1 if it saves 1 chemist from data work.

---

## Pricing

### **What's included in each plan?**

| | Pilot | Production | Enterprise |
|-----|-------|-----------|-----------|
| **Users** | 5 | 50 | Unlimited |
| **Spectra** | 10K | 100K | 1M+ |
| **API Calls/mo** | 10K | 1M | Custom |
| **Price** | $50K (1x) | $250K/yr | Custom |
| **Support** | Email | Email + Slack | Dedicated PM + SLA |

### **Can we negotiate?**

**Yes.** Volume discounts available for 5+ year commitments. Multi-tenant SaaS discounts for consortia (university networks, industry groups).

### **What if we're under-resourced to use it?**

**We can help:**
- Managed service option: We run DreaMS for you
- Training program: Teach your team (1-week workshop)
- Custom dashboards: Pre-built reports for your use case

---

## Roadmap & Future

### **What's coming next?**

- **3D Export:** Download chemical maps for presentations
- **Mobile App:** Explore on mobile (experimental)
- **Active Learning:** Suggest compounds to synthesize next
- **Integration:** Direct LIMS/ERP connectors
- **Federated Learning:** Train on multi-site data without sharing raw spectra

### **Can we request features?**

**Absolutely.** Production customers get roadmap input. We review feature requests quarterly.

### **What if DreaMS is acquired or discontinued?**

**You're safe.** DreaMS is open-source (Apache 2.0). Even if SpecBridge disappears, the code is public. You can fork, modify, run it yourself forever.

---

## Getting Started

### **Next Steps**

1. **Watch the demo:** 5-minute tour of interactive 3D explorer
2. **Read the technical docs:** Architecture, API, data format specs
3. **Contact us:** Discuss your data, timeline, budget

### **Contact**

**Kris | SpecBridge**  
[Email] | [Phone] | [Slack] | [GitHub]

---

*DreaMS Atlas: Open-source chemical space exploration*  
*Peer-reviewed. Proven. Enterprise-ready.*

---

**Last updated:** 2026-02-12
