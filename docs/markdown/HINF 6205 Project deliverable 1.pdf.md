
# Project Proposal: RAG-Based Computerized Clinical Decision Support for Rare Genetic Diseases Using a Knowledge Graph

**Submitted by:** Shradha Gajelli, Jayashanmuhesh Rajasekar, Shrikesh Chaudhari

## Problem Statement  
Muscular dystrophies (MDs) are a group of inherited disorders characterized by progressive muscle weakness and degeneration. Among them, Duchenne Muscular Dystrophy (DMD), Becker Muscular Dystrophy (BMD), Limb-Girdle Muscular Dystrophy (LGMD), and selected Congenital Muscular Dystrophies (CMDs) represent significant clinical and genetic heterogeneity. While genetic testing has advanced, clinicians still face challenges in interpreting gene variants, connecting them with phenotypes, and identifying appropriate treatments or trials. This gap leads to delays in diagnosis, inconsistent treatment recommendations, and missed opportunities for precision medicine. A computerized clinical decision support (CDS) system that leverages structured genomic knowledge could help clinicians make faster, evidence-based decisions.

## Opportunity for Retrieval-Augmented Generation (RAG) in Clinical Decision Support  
RAG combines retrieval of structured knowledge from curated databases with AI-driven generation of human-readable summaries or recommendations. In this project, a knowledge graph will serve as the retrieval backbone, representing entities (genes, variants, diseases, drugs) and their relationships (“causes,” “associated with,” “treated by”). A generation module will use this retrieved information to produce actionable guidance for clinicians or patient-friendly summaries. By integrating publicly available genomic databases such as OMIM, ClinVar, GeneReviews, PubMed, and LOVD, the RAG-based system can provide precise, evidence-informed recommendations for rare disease management.

## Importance of Addressing This Problem  
Timely interpretation of genomic data is critical to improving outcomes for patients with rare genetic diseases. Traditional knowledge retrieval is time-consuming and prone to error. A RAG-based CDS system can:

* Reduce diagnostic delays by linking patient variants to known disease associations.  
* Provide **AI-augmented recommendations** for therapy or management based on curated evidence.  
* Enhance clinician awareness and understanding of rare genetic disorders.  
* Integrate evidence-based genomic knowledge into routine clinical workflows efficiently.

## Rationale for Topic Selection  
We chose this topic because it merges our interests in health informatics, precision medicine, and AI-driven clinical decision support. This project allows the application of knowledge representation, semantic modeling, and AI techniques to solve a clinically meaningful problem. By combining a knowledge graph with RAG, the project demonstrates how AI can retrieve structured genomic knowledge and generate actionable insights, making CDS more effective and interpretable.

## Scope of the Project  
The project will focus on constructing a knowledge graph for the following three rare genetic diseases:

1. Duchenne Muscular Dystrophy (DMD gene) – mapping gene variants to clinical phenotypes and approved or experimental treatment options.


---


2. Becker Muscular Dystrophy (DMD gene) – related milder phenotype, enabling demonstration of variant–phenotype variability within the same gene.  
3. Limb-Girdle Muscular Dystrophy (selected subtype, e.g., LGMD2A, CAPN3 gene) – illustrating differential diagnosis and gene–phenotype relationships.  
4. Congenital Muscular Dystrophy (e.g., LAMA2-related) – supporting early-onset disease management and linking variants to clinical manifestations.  

The knowledge graph will support RAG functionality:  

* Retrieval: Query the graph for variant–disease–phenotype–drug relationships.  
* Generation: Produce AI-augmented summaries or clinical recommendations.  

Example queries:  

* “Which drugs are associated with variants in the MECP2 gene?”  
* “Which genes are linked to Duchenne Muscular Dystrophy, and what management options exist?”  

**Deliverables**  
* Knowledge graph visualization linking genes, variants, phenotypes, and treatments.  
* RAG-generated summaries for example queries, illustrating CDS outputs.  
* Summary report explaining the workflow, data sources, and potential clinical applications.  

This project will demonstrate the utility of RAG in supporting genomic precision medicine, providing actionable clinical insights from structured knowledge and AI augmentation.  

**Conclusion**  
This project will demonstrate how a RAG-powered knowledge graph for muscular dystrophies can serve as a foundation for computerized clinical decision support. By focusing on well-characterized genetic diseases with publicly available datasets, it balances feasibility with clinical relevance, while showcasing how AI-driven knowledge integration can improve decision-making in rare disease care.  
