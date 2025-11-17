"use client";

import type { ScenarioResponse, ClinicalScenario } from "@/types/clinical";

interface ResultsPanelProps {
  response: ScenarioResponse;
  scenario: ClinicalScenario;
}

export function ResultsPanel({ response, scenario }: ResultsPanelProps) {
  return (
    <div className="space-y-6">
      {/* Clinical Scenario Details */}
      <div className="bg-white rounded-lg border-2 border-amber-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Clinical Scenario Details</h2>

        {/* Patient Demographics */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Patient Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="font-semibold text-gray-700">Age:</span>{" "}
              <span className="text-gray-900">{scenario.patient.age}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Sex:</span>{" "}
              <span className="text-gray-900 capitalize">{scenario.patient.sex}</span>
            </div>
            {scenario.patient.ethnicity && (
              <div>
                <span className="font-semibold text-gray-700">Ethnicity:</span>{" "}
                <span className="text-gray-900">{scenario.patient.ethnicity}</span>
              </div>
            )}
            {scenario.patient.family_history && (
              <div className="md:col-span-2">
                <span className="font-semibold text-gray-700">Family History:</span>{" "}
                <span className="text-gray-900">{scenario.patient.family_history}</span>
              </div>
            )}
          </div>
        </div>

        {/* Chief Complaint */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Presentation</h3>
          <div className="mb-3">
            <span className="font-semibold text-gray-700">Chief Complaint:</span>{" "}
            <span className="text-gray-900">{scenario.chief_complaint}</span>
          </div>
          {scenario.symptom_onset && (
            <div className="mb-3">
              <span className="font-semibold text-gray-700">Symptom Onset:</span>{" "}
              <span className="text-gray-900">{scenario.symptom_onset}</span>
            </div>
          )}
          {scenario.progression_pattern && (
            <div className="mb-3">
              <span className="font-semibold text-gray-700">Progression Pattern:</span>{" "}
              <span className="text-gray-900 capitalize">{scenario.progression_pattern}</span>
            </div>
          )}
        </div>

        {/* Presenting Symptoms */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Presenting Symptoms</h3>
          <ul className="list-disc list-inside space-y-1">
            {scenario.presenting_symptoms.map((symptom, idx) => (
              <li key={idx} className="text-gray-900">{symptom}</li>
            ))}
          </ul>
        </div>

        {/* Physical Exam Findings */}
        {scenario.physical_exam && Object.keys(scenario.physical_exam).length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Physical Examination</h3>
            <div className="space-y-2">
              {Object.entries(scenario.physical_exam).map(([key, value]) => (
                <div key={key} className="flex gap-2">
                  <span className="font-semibold text-gray-700 capitalize">{key.replace(/_/g, " ")}:</span>
                  <span className="text-gray-900">{value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Laboratory Results */}
        {scenario.lab_results && scenario.lab_results.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Laboratory Results</h3>
            <div className="space-y-3">
              {scenario.lab_results.map((lab, idx) => (
                <div key={idx} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="font-semibold text-gray-900 mb-1">{lab.test_name}</div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                    <div>
                      <span className="text-gray-600">Value:</span>{" "}
                      <span className="font-bold text-gray-900">{lab.value} {lab.unit}</span>
                    </div>
                    {lab.normal_range && (
                      <div>
                        <span className="text-gray-600">Normal Range:</span>{" "}
                        <span className="text-gray-900">{lab.normal_range}</span>
                      </div>
                    )}
                    {lab.interpretation && (
                      <div>
                        <span className="text-gray-600">Interpretation:</span>{" "}
                        <span className={`font-semibold ${
                          lab.interpretation.toLowerCase().includes("elevated") ||
                          lab.interpretation.toLowerCase().includes("high")
                            ? "text-red-600"
                            : "text-gray-900"
                        }`}>
                          {lab.interpretation}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Genetic Findings */}
        {scenario.genetic_findings && scenario.genetic_findings.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Genetic Findings</h3>
            <div className="space-y-3">
              {scenario.genetic_findings.map((gf, idx) => (
                <div key={idx} className="p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                  <div className="font-semibold text-indigo-900 mb-2">{gf.gene} Gene</div>
                  <div className="space-y-1 text-sm">
                    {gf.variant && (
                      <div>
                        <span className="text-gray-600">Variant:</span>{" "}
                        <span className="text-gray-900 font-mono">{gf.variant}</span>
                      </div>
                    )}
                    {gf.variant_type && (
                      <div>
                        <span className="text-gray-600">Type:</span>{" "}
                        <span className="text-gray-900 capitalize">{gf.variant_type}</span>
                      </div>
                    )}
                    {gf.exons_affected && gf.exons_affected.length > 0 && (
                      <div>
                        <span className="text-gray-600">Exons Affected:</span>{" "}
                        <span className="text-gray-900">{gf.exons_affected.join(", ")}</span>
                      </div>
                    )}
                    {gf.zygosity && (
                      <div>
                        <span className="text-gray-600">Zygosity:</span>{" "}
                        <span className="text-gray-900 capitalize">{gf.zygosity}</span>
                      </div>
                    )}
                    {gf.inheritance_pattern && (
                      <div>
                        <span className="text-gray-600">Inheritance:</span>{" "}
                        <span className="text-gray-900">{gf.inheritance_pattern}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Imaging Findings */}
        {scenario.imaging_findings && Object.keys(scenario.imaging_findings).length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Imaging Findings</h3>
            <div className="space-y-2">
              {Object.entries(scenario.imaging_findings).map(([key, value]) => (
                <div key={key} className="flex gap-2">
                  <span className="font-semibold text-gray-700 uppercase">{key}:</span>
                  <span className="text-gray-900">{value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Clinical Questions */}
        {scenario.clinical_questions && scenario.clinical_questions.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Clinical Questions</h3>
            <ul className="list-decimal list-inside space-y-1">
              {scenario.clinical_questions.map((question, idx) => (
                <li key={idx} className="text-gray-900">{question}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Additional Information */}
        {((scenario.prior_diagnoses && scenario.prior_diagnoses.length > 0) ||
          (scenario.current_medications && scenario.current_medications.length > 0)) && (
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Additional Information</h3>
            {scenario.prior_diagnoses && scenario.prior_diagnoses.length > 0 && (
              <div className="mb-3">
                <span className="font-semibold text-gray-700">Prior Diagnoses:</span>{" "}
                <span className="text-gray-900">{scenario.prior_diagnoses.join(", ")}</span>
              </div>
            )}
            {scenario.current_medications && scenario.current_medications.length > 0 && (
              <div>
                <span className="font-semibold text-gray-700">Current Medications:</span>{" "}
                <span className="text-gray-900">{scenario.current_medications.join(", ")}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Differential Diagnoses */}
      <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Differential Diagnosis</h2>

        {response.primary_diagnosis && (
          <div className="mb-4 p-4 bg-green-50 border-l-4 border-green-500">
            <div className="text-sm font-semibold text-green-700 uppercase">Primary Diagnosis</div>
            <div className="text-lg font-bold text-green-900">{response.primary_diagnosis}</div>
          </div>
        )}

        <div className="space-y-4">
          {response.differential_diagnoses.map((dx, index) => (
            <div
              key={index}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-bold text-gray-900">{dx.disease_name}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Confidence:</span>
                  <span className="text-lg font-bold text-green-600">
                    {dx.confidence_score.toFixed(0)}%
                  </span>
                </div>
              </div>

              {dx.supporting_features && dx.supporting_features.length > 0 && (
                <div className="mb-3">
                  <div className="text-sm font-semibold text-gray-700 mb-1">
                    Supporting Features:
                  </div>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {dx.supporting_features.map((feature, idx) => (
                      <li key={idx}>{feature}</li>
                    ))}
                  </ul>
                </div>
              )}

              {dx.recommended_tests && dx.recommended_tests.length > 0 && (
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-1">
                    Recommended Tests:
                  </div>
                  <ul className="list-disc list-inside text-sm text-blue-600 space-y-1">
                    {dx.recommended_tests.map((test, idx) => (
                      <li key={idx}>{test}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Knowledge Graph Search Results */}
      {response.monarch_search_summary && (
        <div className="bg-white rounded-lg border-2 border-blue-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Knowledge Graph Search
          </h2>
          <div className="bg-blue-50 rounded-lg p-4 mb-4">
            <div className="text-3xl font-bold text-blue-900 mb-2">
              {response.monarch_search_summary.total_diseases_found} diseases found
            </div>
            <div className="text-sm text-gray-600">
              Searched Monarch Initiative for {response.monarch_search_summary.hpo_ids_searched.length} HPO terms
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold text-gray-800">Match Distribution:</h3>
            {Object.entries(response.monarch_search_summary.diseases_by_match_count)
              .sort(([a], [b]) => parseInt(b) - parseInt(a))
              .map(([matchCount, diseaseCount]) => (
                <div key={matchCount} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="text-gray-700">
                    {matchCount} HPO {matchCount === "1" ? "match" : "matches"}
                  </span>
                  <span className="font-bold text-blue-600">{diseaseCount} diseases</span>
                </div>
              ))}
          </div>

          {response.top_monarch_matches && response.top_monarch_matches.length > 0 && (
            <div className="mt-6">
              <h3 className="font-semibold text-gray-800 mb-3">Top Matches from Monarch:</h3>
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {response.top_monarch_matches.slice(0, 15).map((match, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded border ${
                      match.match_count >= 2
                        ? "bg-teal-50 border-teal-300"
                        : "bg-cyan-50 border-cyan-200"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{match.disease_name}</div>
                        <div className="text-xs text-gray-500 font-mono">{match.disease_id}</div>
                      </div>
                      <div className="ml-4 text-right">
                        <div className="text-sm font-bold text-teal-700">
                          {match.match_count} HPO {match.match_count === 1 ? "match" : "matches"}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Scoring Breakdown */}
      {response.scoring_details && response.scoring_details.length > 0 && (
        <div className="bg-white rounded-lg border-2 border-indigo-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Disease Scoring Breakdown</h2>

          <div className="mb-4 p-4 bg-indigo-50 rounded-lg">
            <div className="text-sm text-gray-700">
              <strong>Scoring threshold:</strong> Diseases must score &gt; 30 points to be included in the differential diagnosis.
            </div>
          </div>

          <div className="space-y-4">
            {response.scoring_details.slice(0, 10).map((scoring, idx) => (
              <div
                key={idx}
                className={`border-2 rounded-lg p-4 ${
                  scoring.included_in_differential
                    ? "border-green-300 bg-green-50"
                    : "border-gray-300 bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{scoring.disease_name}</h3>
                    <div className="text-sm text-gray-600">{scoring.disease_code}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-indigo-600">
                      {scoring.final_score.toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-600">points</div>
                    {scoring.included_in_differential ? (
                      <div className="text-xs font-bold text-green-600 mt-1">✅ INCLUDED</div>
                    ) : (
                      <div className="text-xs font-bold text-gray-500 mt-1">❌ EXCLUDED</div>
                    )}
                  </div>
                </div>

                {scoring.scoring_components.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-sm font-semibold text-gray-700">Scoring Components:</div>
                    {scoring.scoring_components.map((component, compIdx) => (
                      <div key={compIdx} className="flex items-start gap-3 p-2 bg-white rounded">
                        <div className="font-bold text-indigo-600 min-w-[60px]">
                          +{component.points_added}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-800">{component.component_name}</div>
                          <div className="text-sm text-gray-600 italic">{component.reasoning}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {scoring.exclusion_reason && (
                  <div className="mt-3 p-2 bg-gray-100 rounded text-sm text-gray-700">
                    <strong>Exclusion reason:</strong> {scoring.exclusion_reason}
                  </div>
                )}
              </div>
            ))}
          </div>

          {response.scoring_details.length > 10 && (
            <div className="mt-4 text-center text-sm text-gray-600">
              Showing top 10 of {response.scoring_details.length} scored diseases
            </div>
          )}
        </div>
      )}

      {/* HPO Mappings */}
      {response.hpo_mappings && response.hpo_mappings.length > 0 && (
        <div className="bg-white rounded-lg border-2 border-purple-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">HPO Term Mappings</h2>
          <div className="space-y-2">
            {response.hpo_mappings.map((mapping, idx) => (
              <div key={idx} className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <span className="font-medium text-gray-900">"{mapping.clinical_feature}"</span>
                  </div>
                  <div className="text-purple-600 font-bold">→</div>
                  <div className="flex-1">
                    <div className="font-mono font-bold text-purple-700">{mapping.hpo_id}</div>
                    <div className="text-sm text-gray-600">{mapping.hpo_term}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Variant Interpretation */}
      {response.variant_interpretation && Object.keys(response.variant_interpretation).length > 0 && (
        <div className="bg-white rounded-lg border-2 border-indigo-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Genetic Findings</h2>

          <div className="space-y-4">
            {Object.entries(response.variant_interpretation).map(([key, variantData]: [string, any]) => (
              <div key={key} className="bg-indigo-50 rounded-lg p-5 border border-indigo-200">
                {/* Variant Header */}
                <div className="mb-4 pb-3 border-b border-indigo-200">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 mb-1">
                        {variantData.gene} {variantData.variant || `Exon ${variantData.exons?.join(', ')} ${variantData.variant_type}`}
                      </h3>
                      <div className="flex gap-2 flex-wrap mt-2">
                        {variantData.variant_type && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold uppercase">
                            {variantData.variant_type}
                          </span>
                        )}
                        {variantData.zygosity && (
                          <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-semibold capitalize">
                            {variantData.zygosity}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Exons */}
                {variantData.exons && variantData.exons.length > 0 && (
                  <div className="mb-3">
                    <span className="font-semibold text-gray-700 text-sm">Affected Exons:</span>{" "}
                    <span className="text-gray-900 font-mono">{variantData.exons.join(', ')}</span>
                  </div>
                )}

                {/* ClinVar Section */}
                {variantData.clinvar_variants && variantData.clinvar_variants.length > 0 ? (
                  <div className="mt-4 pt-4 border-t border-indigo-200">
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <h4 className="font-bold text-indigo-900">ClinVar Reference Data</h4>
                    </div>

                    <div className="bg-white rounded p-3">
                      <p className="text-sm text-gray-600 mb-3">
                        {variantData.clinvar_gene_summary || `${variantData.clinvar_variants.length} related variants in ClinVar database`}
                      </p>

                      {/* ClinVar Variants Table */}
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-xs border-collapse">
                          <thead>
                            <tr className="bg-gray-50 border-b border-gray-200">
                              <th className="px-2 py-2 text-left font-semibold text-gray-700">Accession</th>
                              <th className="px-2 py-2 text-left font-semibold text-gray-700">Variant</th>
                              <th className="px-2 py-2 text-left font-semibold text-gray-700">Type</th>
                              <th className="px-2 py-2 text-left font-semibold text-gray-700">Significance</th>
                              <th className="px-2 py-2 text-left font-semibold text-gray-700">Review Status</th>
                              <th className="px-2 py-2 text-left font-semibold text-gray-700">Location</th>
                              <th className="px-2 py-2 text-left font-semibold text-gray-700">Phenotype</th>
                            </tr>
                          </thead>
                          <tbody>
                            {variantData.clinvar_variants.slice(0, 5).map((cv: any, idx: number) => (
                              <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                                <td className="px-2 py-2">
                                  <a
                                    href={`https://www.ncbi.nlm.nih.gov/clinvar/variation/${cv.variation_id}/`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-indigo-600 hover:text-indigo-800 underline font-mono"
                                  >
                                    {cv.clinvar_accession || cv.variation_id}
                                  </a>
                                </td>
                                <td className="px-2 py-2 text-gray-900 font-mono max-w-[200px] truncate" title={cv.variant_name}>
                                  {cv.variant_name}
                                </td>
                                <td className="px-2 py-2">
                                  <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium">
                                    {cv.variant_type || 'N/A'}
                                  </span>
                                </td>
                                <td className="px-2 py-2">
                                  <span className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap ${
                                    cv.clinical_significance?.toLowerCase().includes('pathogenic') && !cv.clinical_significance?.toLowerCase().includes('uncertain')
                                      ? 'bg-red-100 text-red-800 border border-red-300'
                                      : cv.clinical_significance?.toLowerCase().includes('benign')
                                      ? 'bg-green-100 text-green-800 border border-green-300'
                                      : cv.clinical_significance?.toLowerCase().includes('uncertain')
                                      ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                                      : 'bg-gray-100 text-gray-600'
                                  }`}>
                                    {cv.clinical_significance || 'Not provided'}
                                  </span>
                                </td>
                                <td className="px-2 py-2 text-gray-600 max-w-[150px]">
                                  <div className="truncate" title={cv.review_status}>
                                    {cv.review_status || 'Not provided'}
                                  </div>
                                  {cv.last_evaluated && cv.last_evaluated !== 'Not provided' && (
                                    <div className="text-xs text-gray-400 mt-0.5">
                                      {cv.last_evaluated.split(' ')[0]}
                                    </div>
                                  )}
                                </td>
                                <td className="px-2 py-2 text-gray-600 font-mono">
                                  {cv.chromosome && cv.position_start ? (
                                    <div>
                                      <div>{cv.chromosome}:{cv.position_start}</div>
                                      {cv.position_stop && cv.position_stop !== cv.position_start && (
                                        <div className="text-gray-400">-{cv.position_stop}</div>
                                      )}
                                      {cv.assembly && (
                                        <div className="text-xs text-gray-400">{cv.assembly}</div>
                                      )}
                                    </div>
                                  ) : 'N/A'}
                                </td>
                                <td className="px-2 py-2 text-gray-600 max-w-[180px]">
                                  {cv.phenotypes && cv.phenotypes.length > 0 ? (
                                    <div className="truncate" title={cv.phenotypes.join(', ')}>
                                      {cv.phenotypes[0]}
                                    </div>
                                  ) : (
                                    <span className="text-gray-400">Not specified</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {variantData.clinvar_variants.length > 5 && (
                        <p className="text-xs text-gray-500 mt-2">
                          Showing 5 of {variantData.clinvar_variants.length} variants.{' '}
                          <a
                            href={`https://www.ncbi.nlm.nih.gov/clinvar?term=DMD[gene]`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-indigo-600 hover:text-indigo-800 underline"
                          >
                            View all in ClinVar →
                          </a>
                        </p>
                      )}
                    </div>
                  </div>
                ) : (variantData.clinvar_id || variantData.clinvar_significance) ? (
                  <div className="mt-4 pt-4 border-t border-indigo-200">
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <h4 className="font-bold text-indigo-900">ClinVar Validation</h4>
                    </div>

                    <div className="bg-white rounded p-3 space-y-2">
                      {variantData.clinvar_significance && (
                        <div className="flex items-start gap-2">
                          <span className="font-semibold text-gray-700 text-sm min-w-[140px]">Clinical Significance:</span>
                          <span className={`px-2 py-1 rounded text-sm font-bold ${
                            variantData.clinvar_significance.toLowerCase().includes('pathogenic')
                              ? 'bg-red-100 text-red-800 border border-red-300'
                              : variantData.clinvar_significance.toLowerCase().includes('benign')
                              ? 'bg-green-100 text-green-800 border border-green-300'
                              : 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                          }`}>
                            {variantData.clinvar_significance}
                          </span>
                        </div>
                      )}

                      {variantData.clinvar_review_status && (
                        <div className="flex items-start gap-2">
                          <span className="font-semibold text-gray-700 text-sm min-w-[140px]">Review Status:</span>
                          <span className="text-gray-900 text-sm">{variantData.clinvar_review_status}</span>
                        </div>
                      )}

                      {variantData.clinvar_id && (
                        <div className="flex items-start gap-2">
                          <span className="font-semibold text-gray-700 text-sm min-w-[140px]">ClinVar ID:</span>
                          <a
                            href={`https://www.ncbi.nlm.nih.gov/clinvar/variation/${variantData.clinvar_id}/`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-indigo-600 hover:text-indigo-800 underline text-sm font-mono"
                          >
                            {variantData.clinvar_id}
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="mt-4 pt-4 border-t border-indigo-200">
                    <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
                      ⚠️ No ClinVar data available for this variant
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clinical Recommendations */}
      <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Clinical Recommendations</h2>

        {["treatment", "surveillance", "diagnosis", "genetic_counseling"].map((category) => {
          const categoryRecs = response.recommendations.filter(
            (rec) => rec.category === category
          );

          if (categoryRecs.length === 0) return null;

          return (
            <div key={category} className="mb-6 last:mb-0">
              <h3 className="text-lg font-semibold text-gray-800 capitalize mb-3 border-b pb-2">
                {category.replace(/_/g, " ")}
              </h3>
              <div className="space-y-3">
                {categoryRecs.map((rec, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border-l-4 ${
                      rec.urgency === "immediate"
                        ? "bg-red-50 border-red-500"
                        : rec.urgency === "urgent"
                        ? "bg-yellow-50 border-yellow-500"
                        : "bg-blue-50 border-blue-500"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <p className="text-gray-900 flex-1">{rec.recommendation}</p>
                      <div className="flex gap-2 ml-4 flex-wrap">
                        {/* Source Type Badge (RAG vs Static) */}
                        {rec.source_type && (
                          <span
                            className={`px-2 py-1 rounded text-xs font-bold uppercase ${
                              rec.source_type === "RAG"
                                ? "bg-green-200 text-green-800 border border-green-400"
                                : "bg-gray-200 text-gray-700 border border-gray-400"
                            }`}
                            title={
                              rec.source_type === "RAG"
                                ? "Retrieved from uploaded clinical guidelines"
                                : "From curated clinical data"
                            }
                          >
                            {rec.source_type === "RAG" ? "📚 RAG" : "📋 Static"}
                          </span>
                        )}
                        {rec.evidence_level && (
                          <span className="px-2 py-1 bg-white rounded text-xs font-bold border border-gray-300">
                            {rec.evidence_level}
                          </span>
                        )}
                        {rec.urgency && (
                          <span
                            className={`px-2 py-1 rounded text-xs font-bold uppercase ${
                              rec.urgency === "immediate"
                                ? "bg-red-200 text-red-800"
                                : rec.urgency === "urgent"
                                ? "bg-yellow-200 text-yellow-800"
                                : "bg-blue-200 text-blue-800"
                            }`}
                          >
                            {rec.urgency}
                          </span>
                        )}
                        {/* Confidence Score for RAG */}
                        {rec.source_type === "RAG" && rec.confidence !== undefined && (
                          <span
                            className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-bold border border-purple-300"
                            title="RAG confidence score"
                          >
                            {(rec.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                    </div>

                    {/* RAG Citation Information */}
                    {rec.source_type === "RAG" && (rec.citation || rec.retrieved_text) && (
                      <div className="mt-2 p-3 bg-green-50 border border-green-300 rounded-lg">
                        <div className="flex items-start gap-2 mb-2">
                          <span className="font-bold text-green-700 text-sm">📄 Source:</span>
                          <span className="text-gray-700 flex-1 text-sm">
                            {rec.citation || "Retrieved from uploaded guideline"}
                          </span>
                        </div>

                        {/* Retrieved Text Passage */}
                        {rec.retrieved_text && (
                          <div className="mt-3 pt-3 border-t border-green-200">
                            <div className="font-semibold text-green-800 text-xs uppercase mb-2">
                              📖 Retrieved Text from Guideline:
                            </div>
                            <div className="bg-white p-3 rounded border border-green-200 text-sm text-gray-800 leading-relaxed max-h-60 overflow-y-auto">
                              {rec.retrieved_text}
                            </div>
                          </div>
                        )}

                        {rec.chunk_id && (
                          <div className="text-gray-500 mt-2 text-xs">
                            Chunk ID: <code className="font-mono bg-white px-1 py-0.5 rounded">{rec.chunk_id}</code>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Standard References */}
                    {rec.references && rec.references.length > 0 && (
                      <div className="text-xs text-gray-600 mt-2">
                        <span className="font-semibold">References:</span> {rec.references.join(", ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
