import React, { useRef } from 'react';
import useNetworkStore from '../services/networkStore';

/**
 * A prominent file upload button component for network files.
 * This component provides a button that opens a file dialog when clicked,
 * and handles the file upload process.
 */
const FileUploadButton = ({ 
  className = '', 
  buttonText = 'Upload Network File',
  onFileUpload = null // Add onFileUpload prop with default value of null
}) => {
  const { uploadNetworkFile } = useNetworkStore();
  const fileInputRef = useRef(null);

  // Handle file selection
  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      try {
        const file = e.target.files[0];
        console.log("File selected:", file.name);
        
        // If onFileUpload prop is provided, use it
        if (onFileUpload) {
          console.log("Using provided onFileUpload handler");
          await onFileUpload(file);
        } 
        // Otherwise use the default network store upload
        else {
          console.log("Using default uploadNetworkFile handler");
          // Upload the file using the network store
          const result = await uploadNetworkFile(file);
          
          if (result) {
            console.log("File uploaded successfully");
          } else {
            console.error("Failed to upload file");
          }
        }
      } catch (error) {
        console.error("Error uploading file:", error);
      } finally {
        // Reset the file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    }
  };

  // Handle button click
  const handleButtonClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className={`file-upload-button ${className}`}>
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".graphml,.gexf,.gml,.json,.net,.edgelist,.adjlist"
        className="hidden"
      />
      
      {/* Visible button - Using the className prop for styling */}
      <button
        onClick={handleButtonClick}
        className={className || "px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center"}
      >
        <svg 
          className="w-5 h-5 mr-2" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        {buttonText}
      </button>
    </div>
  );
};

export default FileUploadButton;
