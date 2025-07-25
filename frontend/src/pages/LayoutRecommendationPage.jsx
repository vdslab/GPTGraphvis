import { useForm } from 'react-hook-form';
import useNetworkStore from '../services/networkStore';

const LayoutRecommendationPage = () => {
  const { getLayoutRecommendation, applyRecommendedLayout, recommendation, isLoading, error } = useNetworkStore();
  
  const { register, handleSubmit, formState: { errors } } = useForm();
  
  const onSubmit = async (data) => {
    await getLayoutRecommendation(data.description, data.purpose);
  };
  
  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-2xl font-semibold text-gray-900">Layout Recommendation</h1>
        <p className="mt-2 text-gray-600">
          Describe your network and visualization goals to get a recommendation for the best layout algorithm.
        </p>
        
        <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Request a Recommendation
              </h3>
              <div className="mt-5">
                <form onSubmit={handleSubmit(onSubmit)}>
                  <div className="mb-4">
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                      Network Description
                    </label>
                    <div className="mt-1">
                      <textarea
                        id="description"
                        name="description"
                        rows={4}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder="Describe your network (e.g., number of nodes, edges, type of network, etc.)"
                        {...register('description', { required: 'Network description is required' })}
                      />
                      {errors.description && (
                        <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <label htmlFor="purpose" className="block text-sm font-medium text-gray-700">
                      Visualization Purpose
                    </label>
                    <div className="mt-1">
                      <textarea
                        id="purpose"
                        name="purpose"
                        rows={4}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder="Describe your visualization goals (e.g., identify clusters, highlight central nodes, etc.)"
                        {...register('purpose', { required: 'Visualization purpose is required' })}
                      />
                      {errors.purpose && (
                        <p className="mt-1 text-sm text-red-600">{errors.purpose.message}</p>
                      )}
                    </div>
                  </div>
                  
                  {error && (
                    <div className="mb-4 rounded-md bg-red-50 p-4">
                      <div className="flex">
                        <div className="ml-3">
                          <h3 className="text-sm font-medium text-red-800">
                            {error}
                          </h3>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-300"
                    >
                      {isLoading ? 'Getting Recommendation...' : 'Get Recommendation'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Recommendation Result
              </h3>
              <div className="mt-5">
                {recommendation ? (
                  <div>
                    <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-4">
                      <div className="flex">
                        <div className="ml-3">
                          <p className="text-sm text-green-700">
                            Recommended Layout: <span className="font-bold">{recommendation.recommended_layout}</span>
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700">Explanation</h4>
                      <p className="mt-1 text-sm text-gray-600">
                        {recommendation.explanation}
                      </p>
                    </div>
                    
                    {recommendation.recommended_parameters && (
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-700">Recommended Parameters</h4>
                        <div className="mt-1 bg-gray-50 p-2 rounded-md">
                          <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                            {JSON.stringify(recommendation.recommended_parameters, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={applyRecommendedLayout}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Apply This Layout
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No recommendation yet</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Fill out the form to get a layout recommendation.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-8 bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Example Descriptions
            </h3>
            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="bg-gray-50 p-4 rounded-md">
                <h4 className="text-sm font-medium text-gray-700">Social Network</h4>
                <p className="mt-1 text-xs text-gray-500">
                  "A social network with about 500 nodes and 2000 edges. The network has community structures and some hub nodes."
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  "I want to visualize community structures and identify influential nodes."
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-md">
                <h4 className="text-sm font-medium text-gray-700">Hierarchical Organization</h4>
                <p className="mt-1 text-xs text-gray-500">
                  "An organizational hierarchy with 100 nodes and 120 edges. It has a tree-like structure with 3 levels."
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  "I want to clearly show the hierarchical structure and relationships between levels."
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-md">
                <h4 className="text-sm font-medium text-gray-700">Bipartite Network</h4>
                <p className="mt-1 text-xs text-gray-500">
                  "A bipartite network of users and products with 200 user nodes, 300 product nodes, and 1000 edges."
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  "I want to analyze user-product relationships and identify patterns."
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-md">
                <h4 className="text-sm font-medium text-gray-700">Small Network</h4>
                <p className="mt-1 text-xs text-gray-500">
                  "A small network with 20 nodes and 30 edges. It's a transportation network with a planar structure."
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  "I want to visualize the flow and identify key intersections."
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LayoutRecommendationPage;
