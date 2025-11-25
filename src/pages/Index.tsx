const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
              GAINS Food Vision API
            </h1>
            <p className="text-2xl text-gray-300 mb-2">
              Free, Self-Hosted Food Recognition Backend
            </p>
            <p className="text-gray-400">
              PyTorch • FastAPI • CoFID • OpenFoodFacts
            </p>
          </div>

          {/* Alert Box */}
          <div className="bg-blue-900/30 border border-blue-500/50 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-2 flex items-center gap-2">
              <span>ℹ️</span> Backend API Project
            </h2>
            <p className="text-gray-300">
              This is a <strong>Python FastAPI backend</strong>, not a React frontend app. 
              The API runs separately from this page. See instructions below to start the server.
            </p>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-2 gap-4 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold mb-2">🧠 Food Recognition</h3>
              <p className="text-gray-400">
                Food-101 classifier with ResNet-50, CPU-optimized inference
              </p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold mb-2">📊 Nutrition Data</h3>
              <p className="text-gray-400">
                UK CoFID + OpenFoodFacts + USDA database integration
              </p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold mb-2">🏆 GAINS Scoring</h3>
              <p className="text-gray-400">
                Protein density, carb quality, processing, transparency metrics
              </p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold mb-2">🔎 Fuzzy Search</h3>
              <p className="text-gray-400">
                Intelligent food matching with barcode lookup
              </p>
            </div>
          </div>

          {/* Quick Start */}
          <div className="bg-gray-800/50 rounded-lg p-8 border border-gray-700 mb-8">
            <h2 className="text-2xl font-bold mb-4">🚀 Quick Start</h2>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-400 mb-2">1. Install dependencies:</p>
                <code className="block bg-gray-900 p-3 rounded text-green-400 text-sm">
                  pip install -r requirements.txt
                </code>
              </div>

              <div>
                <p className="text-sm text-gray-400 mb-2">2. Download model weights:</p>
                <code className="block bg-gray-900 p-3 rounded text-green-400 text-sm">
                  python tools/download_model.py
                </code>
              </div>

              <div>
                <p className="text-sm text-gray-400 mb-2">3. Seed database:</p>
                <code className="block bg-gray-900 p-3 rounded text-green-400 text-sm">
                  python seeds/import_cofid.py
                </code>
              </div>

              <div>
                <p className="text-sm text-gray-400 mb-2">4. Run server:</p>
                <code className="block bg-gray-900 p-3 rounded text-green-400 text-sm">
                  uvicorn main:app --reload
                </code>
              </div>
            </div>

            <p className="mt-4 text-gray-400">
              Server will start at <span className="text-green-400">http://localhost:8000</span>
            </p>
          </div>

          {/* API Endpoints */}
          <div className="bg-gray-800/50 rounded-lg p-8 border border-gray-700 mb-8">
            <h2 className="text-2xl font-bold mb-4">📡 API Endpoints</h2>
            
            <div className="space-y-3 text-sm">
              <div className="flex items-start gap-3">
                <span className="bg-blue-600 px-2 py-1 rounded text-xs font-mono">POST</span>
                <div>
                  <code className="text-green-400">/api/classify</code>
                  <p className="text-gray-400 mt-1">Classify food from image</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="bg-blue-600 px-2 py-1 rounded text-xs font-mono">POST</span>
                <div>
                  <code className="text-green-400">/api/map-to-food</code>
                  <p className="text-gray-400 mt-1">Map prediction to canonical food</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="bg-green-600 px-2 py-1 rounded text-xs font-mono">GET</span>
                <div>
                  <code className="text-green-400">/api/barcode/:gtin</code>
                  <p className="text-gray-400 mt-1">Lookup product by barcode</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="bg-green-600 px-2 py-1 rounded text-xs font-mono">GET</span>
                <div>
                  <code className="text-green-400">/api/foods/search</code>
                  <p className="text-gray-400 mt-1">Fuzzy search foods</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="bg-blue-600 px-2 py-1 rounded text-xs font-mono">POST</span>
                <div>
                  <code className="text-green-400">/api/score/gains</code>
                  <p className="text-gray-400 mt-1">Calculate GAINS score</p>
                </div>
              </div>
            </div>
          </div>

          {/* Documentation Links */}
          <div className="text-center space-y-4">
            <p className="text-gray-400">
              📖 Full documentation in <code className="text-green-400">README.md</code>
            </p>
            
            <div className="flex gap-4 justify-center">
              <a 
                href="/docs" 
                target="_blank"
                className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                View API Docs
              </a>
              <a 
                href="/health" 
                target="_blank"
                className="bg-gray-700 hover:bg-gray-600 px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Health Check
              </a>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-12 text-center text-gray-500 text-sm">
            <p>Built for GAINS • MIT License • Zero paid APIs</p>
            <p className="mt-2">Compatible with Expo React Native mobile app</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
