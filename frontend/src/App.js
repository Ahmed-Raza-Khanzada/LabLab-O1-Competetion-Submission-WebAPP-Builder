import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { PaperClipOutlined, DownloadOutlined } from '@ant-design/icons';
import { v4 as uuidv4 } from 'uuid';
import { Tooltip, message } from 'antd'; 

function App() {
  const [inputText, setInputText] = useState('');
  const [uploadedImage, setUploadedImage] = useState(null);
  const [isInputActive, setIsInputActive] = useState(false);
  const [cursorVisible, setCursorVisible] = useState(true);
  const [sessionId, setSessionId] = useState(uuidv4());
  const [sessionRegistered, setSessionRegistered] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);
  const [iframeKey, setIframeKey] = useState(Date.now());
  const [loading, setLoading] = useState(false);
  
  const fileInputRef = useRef(null); 


  useEffect(() => {
    const cursorBlinkInterval = setInterval(() => {
      setCursorVisible((prev) => !prev);
    }, 500);
    return () => clearInterval(cursorBlinkInterval);
  }, []);


  useEffect(() => {
    const sendSessionIdToAPI = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ sessionId }),
        });
        const result = await response.json();
        console.log('Session registered:', result);
        setTimeout(() => {
          setSessionRegistered(true);
        }, 1000);
      } catch (error) {
        console.error('Error sending sessionId to API:', error);
      }
    };
    sendSessionIdToAPI();
  }, [sessionId]);


  useEffect(() => {
    const handleBeforeUnload = (event) => {
      if (!isLeaving) {
        event.preventDefault();
        setIsModalVisible(true);
        event.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isLeaving]);


  const handleInputChange = (event) => setInputText(event.target.value);

  const handleImageUpload = (event) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setUploadedImage(file);
      if (fileInputRef.current) {
        fileInputRef.current.value = ''; 
      }
    }
  };

 
  const handleKeyPress = async (event) => {
    if (event.key === 'Enter') {
      setLoading(true); 
      const formData = new FormData();
      formData.append('text', inputText);
      formData.append('session', sessionId);
      if (uploadedImage) formData.append('image', uploadedImage);

      try {
        const response = await fetch('http://localhost:5000/api/submit', {
          method: 'POST',
          body: formData,
        });
        const result = await response.json();
        console.log('API response:', result);
        setInputText(''); 
        setUploadedImage(null);
        refreshIframe(); 
      } catch (error) {
        console.error('Error calling API:', error);
      } finally {
        setLoading(false); 
      }
    }
  };

  
  const handleModalChoice = async (choice) => {
    setIsLeaving(true);
    try {
      await fetch('http://localhost:5000/api/leave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, choice }),
      });
      if (choice === 'yes') {
        window.open('http://localhost:5000/static/download');
      }
    } catch (error) {
      console.error('Error sending leave choice to API:', error);
    }
    setIsModalVisible(false);
    window.removeEventListener('beforeunload', () => {});
    if (choice === 'no') {
      window.location.reload();
    }
  };

  
  const refreshIframe = () => {
    setIframeKey(Date.now());
  };

  
  const handleDownloadCode = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/download/${sessionId}`, {
        method: 'GET',
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `code_${sessionId}.zip`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        message.success('Download started');
      } else if (response.status === 404) {
        message.error('No code exists');
      } else {
        message.error('Failed to download code');
      }
    } catch (error) {
      console.error('Error downloading code:', error);
      message.error('Error downloading code');
    }
  };

  return (
    <div className="container">
      {sessionRegistered && (
        <>
          <div className="embedded-html">
            <iframe
              title="Embedded HTML"
              key={iframeKey}
              src={`http://localhost:5000/static/${sessionId}/index.html`}
              className="iframe-content"
              sandbox
            />
            {uploadedImage && (
              <div className="uploaded-image-bubble">
                <div className="image-bubble">
                  <img
                    className="uploaded-image"
                    src={URL.createObjectURL(uploadedImage)}
                    alt="Uploaded Preview"
                  />
                </div>
                <div className="bubble-tail"></div>
              </div>
            )}
          </div>
          <div className="input-box">
            <span className="prompt">{'>'}</span>
            <div className="text-input-wrapper">
              <span className="text-input">
                {inputText}
                {isInputActive && cursorVisible && <span className="cursor">_</span>}
              </span>
              <input
                type="text"
                value={inputText}
                onChange={handleInputChange}
                onFocus={() => setIsInputActive(true)}
                onBlur={() => setIsInputActive(false)}
                onKeyDown={handleKeyPress}
                className="hidden-input"
              />
            </div>
            {/* Download Code Button */}
            <Tooltip title="Download code">
              <DownloadOutlined
                style={{ fontSize: '24px', color: '#81c14b', cursor: 'pointer', marginRight: '15px' }}
                onClick={handleDownloadCode}
              />
            </Tooltip>
            {/* Attachment Button */}
            <label htmlFor="file-upload" className="file-upload-label">
              <PaperClipOutlined style={{ fontSize: '24px', color: '#81c14b', cursor: 'pointer' }} />
            </label>
            <input
              id="file-upload"
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="file-input"
              ref={fileInputRef} 
            />
          </div>
          {loading && <div className="loader" />} {/* Loader display */}
        </>
      )}

      {isModalVisible && (
        <div className="modal">
          <div className="modal-content">
            <p>Do you want to download the website before closing?</p>
            <button onClick={() => handleModalChoice('yes')}>Yes</button>
            <button onClick={() => handleModalChoice('no')}>No</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
