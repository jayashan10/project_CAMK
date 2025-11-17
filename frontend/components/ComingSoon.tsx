"use client";

const UPCOMING_FEATURES = [
  {
    icon: "📋",
    title: "Guideline Updates",
    description:
      "Automatically sync with latest TREAT-NMD and ACMG standards of care for muscular dystrophies",
    status: "Planned",
  },
  {
    icon: "🔬",
    title: "Clinical Trial Matching",
    description:
      "Find eligible clinical trials based on patient genetics and phenotype",
    status: "Planned",
  },
  {
    icon: "📊",
    title: "Multi-Scenario Comparison",
    description:
      "Compare multiple patient scenarios side-by-side to identify patterns",
    status: "Planned",
  },
];

export function ComingSoon() {
  return (
    <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg border-2 border-purple-200 p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Coming Soon</h2>
      <p className="text-gray-600 mb-6">
        We're actively developing new features to enhance clinical decision support:
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {UPCOMING_FEATURES.map((feature, index) => (
          <div
            key={index}
            className="bg-white rounded-lg p-4 border border-purple-200 shadow-sm"
          >
            <div className="flex items-start gap-3">
              <div className="text-3xl">{feature.icon}</div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-bold text-gray-900">{feature.title}</h3>
                  <span className="text-xs font-semibold px-2 py-1 bg-purple-100 text-purple-700 rounded">
                    {feature.status}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{feature.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-white rounded-lg border border-purple-200">
        <p className="text-sm text-gray-700">
          <strong>Note:</strong> This system currently uses the Monarch Initiative knowledge graph
          with curated clinical decision support data and RAG-powered guideline search (available above).
        </p>
      </div>
    </div>
  );
}
