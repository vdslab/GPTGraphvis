import { Link } from 'react-router-dom';
import useAuthStore from '../services/authStore';

const HomePage = () => {
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="bg-white">
      <div className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
            Network Visualization API
          </h1>
          <p className="mt-5 max-w-xl mx-auto text-xl text-gray-500">
            Visualize network data with various layout algorithms and interact through a chat interface to analyze your networks.
          </p>
          <div className="mt-8 flex justify-center">
            {isAuthenticated ? (
              <div className="inline-flex rounded-md shadow">
                <Link
                  to="/dashboard"
                  className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Go to Dashboard
                </Link>
              </div>
            ) : (
              <div className="inline-flex rounded-md shadow">
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>

        <div className="mt-16">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
            <div className="bg-gray-50 p-6 rounded-lg shadow-md">
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-900">Network Visualization</h3>
                <p className="mt-2 text-base text-gray-500">
                  Visualize your network data using various layout algorithms from NetworkX.
                </p>
              </div>
            </div>

            <div className="bg-gray-50 p-6 rounded-lg shadow-md">
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-900">Layout Recommendation</h3>
                <p className="mt-2 text-base text-gray-500">
                  Get recommendations for the best layout algorithm based on your network characteristics.
                </p>
              </div>
            </div>

            <div className="bg-gray-50 p-6 rounded-lg shadow-md">
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-900">Network Chat</h3>
                <p className="mt-2 text-base text-gray-500">
                  Interact with your network through a chat interface to modify layouts and analyze properties.
                </p>
              </div>
            </div>

            <div className="bg-gray-50 p-6 rounded-lg shadow-md">
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-900">ChatGPT Integration</h3>
                <p className="mt-2 text-base text-gray-500">
                  Leverage ChatGPT to get insights and recommendations for your network data.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-16">
          <h2 className="text-3xl font-extrabold text-gray-900">
            Supported Layout Algorithms
          </h2>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900">Spring Layout</h3>
              <p className="mt-2 text-sm text-gray-500">
                Position nodes using a force-directed algorithm based on Fruchterman-Reingold.
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900">Circular Layout</h3>
              <p className="mt-2 text-sm text-gray-500">
                Position nodes on a circle.
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900">Spectral Layout</h3>
              <p className="mt-2 text-sm text-gray-500">
                Position nodes using the eigenvectors of the graph Laplacian.
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900">Shell Layout</h3>
              <p className="mt-2 text-sm text-gray-500">
                Position nodes in concentric circles.
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900">Kamada-Kawai Layout</h3>
              <p className="mt-2 text-sm text-gray-500">
                Position nodes using Kamada-Kawai force-directed algorithm.
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900">And More...</h3>
              <p className="mt-2 text-sm text-gray-500">
                Including Fruchterman-Reingold, Bipartite, Multipartite, and others.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
