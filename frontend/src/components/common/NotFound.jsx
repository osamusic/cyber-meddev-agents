import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <h1 className="text-4xl font-bold text-red-600 mb-4">404</h1>
      <h2 className="text-2xl font-semibold mb-6">Page Not Found</h2>
      <p className="text-gray-600 mb-8">
        The page you are looking for does not exist or may have been moved.
      </p>
      <Link 
        to="/" 
        className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
      >
        Go Back Home
      </Link>
    </div>
  );
};

export default NotFound;
