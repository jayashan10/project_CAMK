
# Knowledge Graph-Driven and Retrieval-Augmented Generation Clinical Decision Support for Rare Muscular Dystrophies

**Group Members:** Shradha Gajelli, Jayashanmuhesh Rajasekar, Shrikesh Chaudhari  
**Date:** 10/21/2025

## Introduction:
Rare genetic diseases affect 30 million Americans, with 80% having genetic origins. Muscular dystrophies represent a clinically heterogeneous group with over 30 genetic subtypes, presenting significant diagnostic challenges. The diagnostic journey typically spans 2-5 years from symptom onset to genetic confirmation, during which patients consult multiple specialists and undergo numerous tests before receiving definitive diagnosis (National Institutes of Health, Rare Diseases, Global Genes).

Clinicians face mounting complexity in genomic medicine: they must interpret variants across 200+ genes associated with neuromuscular disorders while synthesizing fragmented data from disparate databases including ClinVar (2.5+ million variants), OMIM (16,000+ gene-disease relationships), GeneReviews (clinical management summaries), and PubMed (Landrum et al., 2018, Amberger et al., 2015). This fragmentation creates critical gaps, about 40-50% of genetic tests return Variants of Uncertain Significance (VUS) requiring extensive literature review consuming 30-60 minutes per variant (Richards et al., 2015). The emergence of mutation-specific therapies, such as exon-skipping drugs for Duchenne Muscular Dystrophy, elevates the urgency of rapid, accurate genetic diagnosis.

Knowledge graphs offer structured representation of biomedical entities (genes, variants, diseases, phenotypes, treatments) and their complex interrelationships. When integrated with Retrieval-Augmented Generation (RAG), a technique enhancing large language models through external, curated data sources, knowledge graphs enable real-time, evidence-based recommendations at the point of care. RAG addresses fundamental AI limitations including hallucinated content and lack of current medical literature access by grounding responses in vetted, domain-specific knowledge.

## Problem Statement & Opportunity
The genomic medicine landscape suffers from profound information silos impeding clinical decision-making. ClinVar provides variant pathogenicity classifications, yet cross-referencing with phenotypic databases (OMIM) and therapeutic guidelines (GeneReviews) requires manual navigation of disparate interfaces. The UMD-DMD database catalogs 10,000+ DMD variants but exists independently from clinical management resources. This fragmentation creates four critical gaps:


---


1. Variant Interpretation Delays: VUS constitute 40-50% of genetic test results, requiring evidence synthesis from population databases, functional studies, and segregation data. For DMD, delays are particularly consequential given mutation-specific therapies, eteplirsen (exon 51 skipping, FDA approved 2016), golodirsen/viltolarsen (exon 53, 2019-2020), and casimersen (exon 45, 2021), each targeting specific deletion patterns in 8-13% of patients (Shirley, 2021; Dhillon, 2020).

2. Differential Diagnosis Complexity: LGMDR1, BMD, and other LGMD subtypes share proximal muscle weakness, elevated creatine kinase, and variable onset, yet require different management (Vissing et al., 2016; Fanin et al., 2005). LGMDR1 typically lacks cardiac involvement, obviating intensive surveillance required for DMD/BMD.

3. Treatment Selection Challenges: Determining exon-skipping drug eligibility requires computational reading frame analysis to predict whether skipping specific exons restores dystrophin function, that's beyond most clinicians' capabilities without bioinformatics support (Frank et al., 2020).

4. Genotype-Phenotype Correlation: The DMD gene exemplifies single-locus variability: out-of-frame deletions cause severe DMD (wheelchair by age 12), while in-frame deletions produce milder BMD (ambulation into 30s-50s). The "reading frame rule" demonstrates 90% predictive accuracy but requires molecular genetics expertise (Monaco et al., 1988).

> **Opportunity:** A unified, AI-enhanced knowledge framework can provide actionable insights at point of care, accelerating precision medicine. By integrating structured genomic knowledge with RAG, clinicians access real-time, evidence-based recommendations for variant interpretation, differential diagnosis, and treatment selection, reducing diagnostic delays from years to days and enabling timely access to life-altering therapies. This democratizes subspecialty expertise, particularly benefiting community hospitals and rural settings lacking genetic specialists.

**Clinical Rationale**  
Muscular dystrophies illustrate the diagnostic and therapeutic challenges of precision medicine. Despite next-generation sequencing, interpretation bottlenecks persist due to fragmented information sources (Landrum et al., 2018; Amberger et al., 2015). Knowledge Graph–Driven Clinical Decision Support (KG-CDS) systems consolidate multi-omic, clinical, and therapeutic data, enhancing interpretability and clinical utility.

Integrating symbolic reasoning (knowledge graphs) with neural retrieval (RAG) ensures that recommendations are traceable to evidence sources, consistent with the principles of Evidence-Based Medicine (EBM; Sackett et al., 1996). Key clinical applications include:

* Rapid ACMG-guided variant interpretation (Richards et al., 2015)


---


* Phenotype-driven differential diagnosis using Human Phenotype Ontology (HPO) mapping

* Therapy matching based on FDA-approved and investigational treatments

### Integration of Evidence-Based Medicine
The integration of Evidence-Based Medicine (EBM) principles is paramount in developing a clinical decision support (CDS) system for rare muscular dystrophies. EBM emphasizes the use of the best available clinical evidence, patient preferences, and clinical expertise in decision-making. This approach ensures that the CDS system provides recommendations that are not only scientifically sound but also tailored to individual patient contexts.

### Key Epidemiologic Statistics

* **Global Rare Disease Burden**: Approximately 300 million people worldwide are affected by rare diseases, underscoring the significant global health challenge posed by these conditions. BioMed Central

* **Duchenne Muscular Dystrophy (DMD)**: The global prevalence of DMD is estimated at 7.1 cases per 100,000 males. The incidence is approximately 1 in every 3,500 male births. National Organization for Rare Disorders

* **Becker Muscular Dystrophy (BMD)**: The estimated prevalence of BMD ranges from 17 to 27 cases per million population, with an incidence of 1 in every 30,000 male births. Medscape

* **Limb-Girdle Muscular Dystrophy Type 2A (LGMD2A)**: Caused by variants in the CAPN3 gene, LGMD2A is the most prevalent autosomal recessive limb-girdle muscular dystrophy. PubMed Central

* **Laminin Subunit Alpha 2–Related Congenital Muscular Dystrophy (LAMA2-CMD)**: The global prevalence of LAMA2-CMD is estimated at approximately 1 in 120,000 individuals, with considerable regional variations.

### Authoritative Clinical Guidelines and Standards

* **DMD Care Considerations**: The Lancet Neurology provides comprehensive care considerations for DMD, emphasizing the importance of early diagnosis and multidisciplinary management. BioMed Central


---


* ACMG Standards for Variant Interpretation: The American College of Medical Genetics and Genomics (ACMG) provides guidelines for the interpretation of genetic variants, ensuring consistent and accurate classification. BioMed Central

* GeneReviews Entries: GeneReviews offers detailed clinical descriptions for MECP2 (associated with Rett syndrome) and HEXA (associated with Tay-Sachs disease), aiding in the understanding of genotype-phenotype correlations. BioMed Central

### Clinical Vignettes

* DMD Exon 51 Skipping: A synthetic patient with a DMD exon 51 skipping mutation demonstrates how the CDS system can support therapy selection, such as exon-skipping or trial eligibility, by integrating genetic data with clinical guidelines.
* MECP2 Variant in Rett Syndrome: A patient with a MECP2 variant illustrates how the system maps phenotype data to clinical management strategies, including monitoring and therapeutic interventions.
* LGMD2A (Calpain-3 Variant) Case Example: A patient with a CAPN3 pathogenic variant and *proximal muscle weakness* is identified as having LGMD2A. The CDS system links HPO phenotypes with evidence-based management, recommending physiotherapy and orthopedic support while excluding DMD-specific cardiac monitoring (Birnkrant et al., 2018; Lin et al., 2023; Banerjee et al., 2024). This demonstrates the system’s precision in distinguishing disease-specific therapeutic pathways.

<table>
    <tr>
        <td>Knowledge Graph layer</td>
<td>Data Source</td>
<td>Description</td>
    </tr>
<tr>
        <td>Variants</td>
<td>ClinVar</td>
<td>Genetic variant information</td>
    </tr>
<tr>
        <td>Phenotypes</td>
<td>HPO</td>
<td>Human Phenotype Ontology</td>
    </tr>
<tr>
        <td>Disease Description</td>
<td>OMIM/GeneReviews</td>
<td>Detailed disease and gene
<br/>
information</td>
    </tr>
<tr>
        <td>Clinical Trials</td>
<td>ClinicalTrials.gov</td>
<td>Information on ongoing
<br/>
clinical trials</td>
    </tr>
</table>

### Limitations and Validation Plan

* **Evidence Gaps:** The rarity of these diseases limits the availability of randomized controlled trials, necessitating reliance on observational studies and expert consensus.

* **LLM Hallucination Risk:** Large Language Models (LLMs) may generate plausible but incorrect information; therefore, outputs will be cross-verified with authoritative sources.


---


* **Human Curation**: Expert review of generated recommendations will be conducted to ensure clinical relevance and accuracy.

* **Pilot Testing**: A small-scale pilot using synthetic cases will be implemented to assess the system's performance and identify areas for improvement.

### Regulatory and Ethical Considerations

* **Data Licensing**: Compliance with data licensing policies of ClinVar, OMIM, and other data sources will be ensured.

* **Patient Privacy**: No Protected Health Information (PHI) will be used; all data will be anonymized.

* **Clinical Responsibility**: The CDS system will serve as a support tool, not a replacement for clinical judgment.

### Data Provenance Plan:

Adhering to FAIR principles ensures that all data within the CDS framework are Findable, Accessible, Interoperable, and Reusable (Wilkinson et al., 2016).

* Data Sources: ClinVar, gnomAD, OMIM, Orphanet, GeneReviews, and PubMed.

* Provenance Metadata: Each knowledge graph edge includes source, PMID/DOI, confidence score, and last verification date.

* Audit and Versioning: Version-controlled graph snapshots ensure reproducibility and regulatory compliance.

### System Concept & Technical Overview:
The proposed Clinical Decision Support (CDS) system integrates Knowledge Graphs and Retrieval-Augmented Generation (RAG) to deliver transparent, evidence-based recommendations for rare muscular dystrophies.  
It comprises four layers:

1. Data Integration: Aggregates and standardizes genomic, phenotypic, and therapeutic data from ClinVar, OMIM, GeneReviews, and PubMed, following FAIR data principles


---


2. Knowledge Graph: Represents gene–variant–disease–therapy relationships with provenance metadata, enabling interpretable reasoning (Landrum et al., 2018).

3. RAG Engine: Combines structured graph reasoning with real-time literature retrieval to ground model outputs in verified evidence (Richards et al., 2015; Frank et al., 2020).

The **Retrieval-Augmented Generation (RAG)** module serves as the critical bridge between information retrieval and clinical recommendation synthesis. It first identifies and retrieves the most relevant genomic, phenotypic, and therapeutic evidence from trusted biomedical repositories such as **PubMed**, **GeneReviews**, and **ClinicalTrials.gov** using **vector-based semantic similarity search**. These retrieved texts are then passed to a **fine-tuned large language model**, which summarizes key findings into concise, clinician-oriented recommendations. Each generated output includes **traceable evidence citations**, ensuring that every clinical suggestion is grounded in verifiable data and transparent reasoning. This design significantly enhances clinician trust and interpretability, addressing one of the key challenges in implementing AI-driven CDS tools.

4. Clinical Interface: A FHIR-compliant dashboard integrated into EHRs provides variant classification, diagnostic insights, and therapy suggestions (e.g., exon-skipping options) with citations (Shirley, 2021).

<table>
  <tr>
    <td>Data Sources (ClinVar, OMIM, Orphanet, PubMed)</td>
<td>Knowledge Graph (Genes-Variants-Phenotypes-Drugs)</td>
<td>RAG Engine (Retrieve & Summarize Evidence)</td>
<td>CDS Dashboard (Clinician View)</td>
  </tr>
</table>

**Figure 1** - illustrates the four-layer CDS architecture, integrating biomedical data through a Knowledge Graph and RAG engine to deliver evidence-based insights via a clinician dashboard.

For example, a *DMD* exon 48–50 deletion triggers automated identification of exon 51–skipping therapy (eteplirsen) and displays linked clinical evidence (Monaco et al., 1988).  
The system ensures HIPAA/GDPR compliance, provenance tracking, and reproducibility while reducing interpretation time from hours to minutes.


---


# Expected Clinical & Organizational Impact:

The integration of Knowledge Graph–Driven and Retrieval-Augmented Generation (RAG)–based Clinical Decision Support (CDS) is expected to yield substantial clinical and institutional benefits. Clinically, the system accelerates the diagnostic process by automating evidence synthesis and variant interpretation, reducing turnaround times from weeks to hours (Richards et al., 2015). By linking genotype–phenotype correlations with current therapeutic guidelines, it enhances diagnostic precision and supports timely initiation of mutation-specific treatments, such as exon-skipping therapies in Duchenne muscular dystrophy (Shirley, 2021; Vissing et al., 2016). The platform also empowers general clinicians with subspecialty-level decision support, improving confidence and reducing dependency on tertiary genetic centers.

From an organizational standpoint, the system streamlines workflows by minimizing redundant testing and manual literature review, yielding cost savings and operational efficiency. Its interoperable, structured data architecture supports research, registry development, and clinical trial enrollment. Furthermore, by extending genomic decision support to community hospitals and under-resourced settings, the system promotes health equity and broader access to precision medicine. Continuous clinician feedback and audit trails facilitate system learning and institutional knowledge growth, reinforcing its role as a sustainable, scalable component of modern genomic healthcare delivery.

# Conclusion:

The integration of Knowledge Graph–Driven and Retrieval-Augmented Generation (RAG) - based Clinical Decision Support (CDS) represents a transformative advance in genomic medicine. By harmonizing fragmented genomic, phenotypic, and therapeutic data, this framework enables real-time, evidence-based decision-making for rare muscular dystrophies. The system bridges the gap between genetic testing and actionable insights - accelerating variant interpretation, supporting precise differential diagnoses, and facilitating timely access to mutation-specific therapies such as exon-skipping treatments in Duchenne Muscular Dystrophy.

Through adherence to FAIR data principles, provenance tracking, and EBM-aligned transparency, the proposed system promotes interpretability, reproducibility, and clinical trust. Beyond diagnostic acceleration, its deployment within EHR-integrated, FHIR-compliant workflows ensures scalability across healthcare environments - from tertiary genetic centers to community hospitals. This democratization of subspecialty expertise aligns with the broader goals of precision medicine, enhancing equity and patient outcomes globally.

Future work should focus on prospective clinical validation, performance benchmarking across variant classes, and user-centered design optimization to ensure seamless adoption. The fusion of symbolic reasoning and neural retrieval heralds a paradigm shift toward truly intelligent, transparent, and equitable genomic decision support - turning data into actionable clinical wisdom.


---


# References:

Amberger, J. S., Bocchini, C. A., Schiettecatte, F., Scott, A. F., & Hamosh, A. (2015).  
OMIM.org: Online Mendelian Inheritance in Man (OMIM®), an online catalog of human genes and genetic disorders. *Nucleic Acids Research, 43*(D1), D789–D798.  
https://doi.org/10.1093/nar/gku1205

Banerjee, S., et al. (2024). Identification of novel pathogenic variants of Calpain-3 gene in limb-girdle muscular dystrophy type R1. *Orphanet Journal of Rare Diseases, 19*(1), 1–12.  
https://doi.org/10.1186/s13023-024-03158-1

Dhillon, S. (2020). Viltolarsen: First approval. *Drugs, 80*(10), 1027–1031.  
https://doi.org/10.1007/s40265-020-01326-4

Englund, M., et al. (2024). Epidemiology and healthcare resource utilisation associated with Duchenne muscular dystrophy: A population-based study. *Journal of Rare Diseases, 19*(1), 44.  
https://doi.org/10.1007/s44162-024-00044-z

Fanin, M., & Angelini, C. (2005). Muscle pathology in dysferlinopathy. *Neuropathology and Applied Neurobiology, 31*(5), 463–472.  
https://doi.org/10.1111/j.1365-2990.2005.00663.x

Frank, D. E., Schnell, F. J., Akana, C., El-Husayni, S. H., Desjardins, C. A., Morgan, J., Charleston, J. S., Sardone, V., Domingos, J., Dickson, G., Mercuri, E., & Muntoni, F. (2020). Assessment of exon skipping and dystrophin restoration in DMD patients treated with exon 51–skipping therapy. *JAMA Neurology, 77*(8), 928–938.  
https://doi.org/10.1001/jamaneurol.2020.1264

Landrum, M. J., Lee, J. M., Benson, M., Brown, G. R., Chao, C., Chitipiralla, S., Gu, B., Hart, J., Hoffman, D., Jang, W., Karapetyan, K., Katz, K., Liu, C., Maddipatla, Z., Malheiro, A., McDaniel, K., Ovetsky, M., Riley, G., Zhou, G., … Maglott, D. R. (2018). ClinVar: Improving access to variant interpretations and supporting evidence. *Nucleic Acids Research, 46*(D1), D1062–D1067.  
https://doi.org/10.1093/nar/gkx1153

Lin, F., et al. (2023). Clinical features, imaging findings and molecular data of limb-girdle muscular dystrophy: A cohort from Southeast China. *Orphanet Journal of Rare Diseases, 18*, 97.  
https://doi.org/10.1186/s13023-023-02897-x

Monaco, A. P., Bertelson, C. J., Liechti-Gallati, S., Moser, H., & Kunkel, L. M. (1988). An explanation for the phenotypic differences between patients bearing partial deletions of the DMD locus. *Genomics, 2*(1), 90–95.  
https://doi.org/10.1016/0888-7543(88)90113-9


---


Müthel, S., et al. (2023). CRISPR/Cas9 genome editing in LGMD2A/R1 patient-derived myoblasts. *Stem Cell Research & Therapy*, 14, 210. https://doi.org/10.1016/j.scrt.2023.9246825

National Institutes of Health, Office of Rare Diseases Research. (n.d.). *Rare Diseases Information Portal*. Retrieved October 21, 2025, from https://rarediseases.info.nih.gov

Ostojic, S., et al. (2020). Global epidemiology of Duchenne muscular dystrophy: an updated meta-analysis. *Orphanet Journal of Rare Diseases*, 15(1), 72. https://doi.org/10.1186/s13023-020-01430-8

Parent Project Muscular Dystrophy (PPMD). (2025). Fifteen Year Registry Report. The Duchenne Registry. https://www.parentprojectmd.org/wp-content/uploads/2023/08/PPMD_15-Year-Registry-Report_2023.pdf

Rare Disease Advisor. (2023). Muscular dystrophy epidemiology. *Rare Disease Advisor*. https://www.rarediseaseadvisor.com/disease-info-pages/muscular-dystrophy-epidemiology/

Richards, S., Aziz, N., Bale, S., Bick, D., Das, S., Gastier-Foster, J., Grody, W. W., Hegde, M., Lyon, E., Spector, E., Voelkerding, K., & Rehm, H. L. (2015). Standards and guidelines for the interpretation of sequence variants: A joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology. *Genetics in Medicine*, 17(5), 405–424. https://doi.org/10.1038/gim.2015.30

Sackett, D. L., Rosenberg, W. M. C., Gray, J. A. M., Haynes, R. B., & Richardson, W. S. (1996). Evidence based medicine: What it is and what it isn’t. *BMJ*, 312(7023), 71–72. https://doi.org/10.1136/bmj.312.7023.71

Shirley, M. (2021). Casimersen: First approval. *Drugs*, 81(7), 875–879. https://doi.org/10.1007/s40265-021-01506-3

Tomforde, M., et al. (2023). Family and literature analysis demonstrates phenotypic variability in Calpain 3-related limb-girdle muscular dystrophy. *Neuromuscular Disorders*, 69, 102–110. https://doi.org/10.1016/j.nmd.2023.10545561

Vissing, J., Duno, M., Olesen, J. H., Rafiq, J., Andersen, H., & Rahbek, J. (2016). Clinical heterogeneity in limb-girdle muscular dystrophy type 2I. *Brain*, 139(4), 1190–1200. https://doi.org/10.1093/brain/aww012

Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., Appleton, G., Axton, M., Baak, A., Blomberg, N., Boiten, J. W., da Silva Santos, L. B., Bourne, P. E., Bouwman, J., Brookes, A. J., Clark, T., Crosas, M., Dillo, I., Dumon, O., Edmunds, S., Evelo, C. T., Finkers, R., … Mons, B.


---


(2016). The FAIR guiding principles for scientific data management and stewardship. *Scientific Data, 3*, 160018. https://doi.org/10.1038/sdata.2016.18

National Organization for Rare Disorders. (n.d.). *Duchenne muscular dystrophy*. Retrieved October 21, 2025, from https://rarediseases.org

BioMed Central. (n.d.). *Global rare disease burden and DMD care considerations*. Retrieved October 21, 2025, from https://www.biomedcentral.com

PubMed Central. (n.d.). *CAPN3-related limb-girdle muscular dystrophy (LGMD2A) prevalence studies*. Retrieved October 21, 2025, from https://www.ncbi.nlm.nih.gov/pmc
