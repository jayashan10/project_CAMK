"use client";

import type { ClinicalScenario } from "@/types/clinical";

interface ExampleScenariosProps {
  onLoadScenario: (scenario: ClinicalScenario) => void;
}

// Example scenarios from the demo notebook
const EXAMPLE_SCENARIOS: Array<{ title: string; description: string; scenario: ClinicalScenario }> = [
  {
    title: "Classic DMD Presentation",
    description: "6-year-old boy with progressive weakness, elevated CK, DMD exon 45-47 deletion",
    scenario: {
      patient: {
        age: "6 years",
        sex: "male",
        family_history: "Maternal uncle died at 22 with similar symptoms",
      },
      chief_complaint: "Progressive difficulty walking",
      presenting_symptoms: [
        "Frequent falls starting at age 4",
        "Difficulty climbing stairs",
        "Toe walking",
        "Calf muscle pseudohypertrophy",
        "Positive Gowers sign",
        "Unable to run or jump",
      ],
      symptom_onset: "Age 3-4 years",
      progression_pattern: "slowly progressive",
      physical_exam: {
        gowers_sign: "positive",
        proximal_weakness: "3/5 hip flexors, 4/5 shoulder abduction",
        calf_muscles: "bilateral pseudohypertrophy",
        reflexes: "diminished patellar and achilles",
      },
      lab_results: [
        {
          test_name: "Creatine Kinase",
          value: "18000",
          unit: "U/L",
          normal_range: "30-200 U/L",
          interpretation: "Markedly elevated (90x normal)",
        },
        {
          test_name: "AST",
          value: "280",
          unit: "U/L",
          normal_range: "10-40 U/L",
          interpretation: "Elevated",
        },
      ],
      genetic_findings: [
        {
          gene: "DMD",
          variant_type: "deletion",
          exons_affected: [45, 46, 47],
          zygosity: "hemizygous",
        },
      ],
      clinical_questions: [
        "What is the most likely diagnosis?",
        "Is this Duchenne or Becker muscular dystrophy?",
        "What treatments are available?",
      ],
    },
  },
  {
    title: "Becker Muscular Dystrophy",
    description: "15-year-old male, preserved ambulation, in-frame deletion",
    scenario: {
      patient: {
        age: "15 years",
        sex: "male",
        family_history: "No known family history",
      },
      chief_complaint: "Muscle weakness and fatigue",
      presenting_symptoms: [
        "Difficulty with sports activities",
        "Mild proximal weakness",
        "Calf muscle enlargement",
        "Still ambulatory",
        "Can climb stairs with handrail",
      ],
      symptom_onset: "Age 10 years",
      progression_pattern: "slowly progressive",
      lab_results: [
        {
          test_name: "Creatine Kinase",
          value: "8000",
          unit: "U/L",
          normal_range: "30-200 U/L",
          interpretation: "Markedly elevated",
        },
      ],
      genetic_findings: [
        {
          gene: "DMD",
          variant_type: "deletion",
          exons_affected: [45],
          zygosity: "hemizygous",
        },
      ],
      clinical_questions: [
        "Is this Duchenne or Becker muscular dystrophy?",
        "What surveillance is most critical?",
      ],
    },
  },
  {
    title: "Clinical Presentation Without Genetics",
    description: "5-year-old with delayed milestones, no genetic data yet",
    scenario: {
      patient: {
        age: "5 years",
        sex: "male",
        family_history: "Unknown (adopted)",
      },
      chief_complaint: "Delayed motor milestones",
      presenting_symptoms: [
        "Delayed walking (18 months)",
        "Frequent falls",
        "Proximal muscle weakness",
        "Positive Gowers sign",
        "Calf muscle hypertrophy",
      ],
      symptom_onset: "Since early childhood",
      lab_results: [
        {
          test_name: "Creatine Kinase",
          value: "10000",
          unit: "U/L",
          normal_range: "30-200 U/L",
          interpretation: "Markedly elevated",
        },
      ],
      clinical_questions: [
        "What is the most likely diagnosis?",
        "What testing should be ordered next?",
      ],
    },
  },
  {
    title: "Infant with Congenital MD",
    description: "6-month-old with severe hypotonia and white matter changes on MRI",
    scenario: {
      patient: {
        age: "6 months",
        sex: "female",
      },
      chief_complaint: "Severe hypotonia since birth",
      presenting_symptoms: [
        "Severe hypotonia from birth",
        "Poor head control",
        "Weak cry",
        "Feeding difficulties",
        "Reduced spontaneous movements",
      ],
      symptom_onset: "Birth",
      progression_pattern: "static",
      lab_results: [
        {
          test_name: "Creatine Kinase",
          value: "2000",
          unit: "U/L",
          normal_range: "30-200 U/L",
          interpretation: "Elevated",
        },
      ],
      imaging_findings: {
        brain_mri: "Diffuse white matter T2 hyperintensities",
      },
      clinical_questions: [
        "What is the most likely diagnosis given the MRI findings?",
        "What immediate management is needed?",
      ],
    },
  },
];

export function ExampleScenarios({ onLoadScenario }: ExampleScenariosProps) {
  return (
    <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Example Scenarios</h2>
      <p className="text-gray-600 mb-6">
        Try one of these clinical scenarios to see the system in action:
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {EXAMPLE_SCENARIOS.map((example, index) => (
          <button
            key={index}
            onClick={() => onLoadScenario(example.scenario)}
            className="text-left p-4 rounded-lg border-2 border-gray-200 hover:border-blue-500 hover:shadow-md transition-all"
          >
            <div className="font-bold text-gray-900 mb-1">{example.title}</div>
            <div className="text-sm text-gray-600">{example.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
