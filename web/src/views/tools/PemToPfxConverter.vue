<template>
  <div class="pem-to-pfx-container card">
    <h2>PEM to PFX Converter</h2>
    <p class="instructions">
      Paste your PEM-encoded certificate chain (your certificate first, followed by any intermediate CA certificates) 
      and the corresponding PEM-encoded private key below. The PFX file will be password-protected with your username.
    </p>
    <p class="security-note">
      <strong>Note:</strong> Private key data is sensitive. Ensure this operation is performed in a secure environment.
    </p>

    <form @submit.prevent="handleConvertToPfx">
      <div class="form-group">
        <label for="pemCertChain">PEM Certificate(s):</label>
        <textarea 
          id="pemCertChain" 
          v-model="pemCertChain" 
          rows="10" 
          placeholder="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n-----BEGIN CERTIFICATE-----\n(Optional Intermediate CA)\n...\n-----END CERTIFICATE-----"
          required
        ></textarea>
      </div>

      <div class="form-group">
        <label for="privateKey">PEM Private Key:</label>
        <textarea 
          id="privateKey" 
          v-model="privateKey" 
          rows="8" 
          placeholder="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
          required
        ></textarea>
      </div>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
       <div v-if="successMessage" class="success-message"> <!-- Added for success feedback -->
        {{ successMessage }}
      </div>


      <button type="submit" :disabled="isLoading" class="button-convert">
        {{ isLoading ? 'Converting...' : 'Convert and Download PFX' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';

// Mock API client (replace with actual API client later)
const mockApi = {
  convertToPfx: async (payload) => {
    console.log("Mock API: convertToPfx called with:", payload);
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (!payload.pem_cert_chain.includes("-----BEGIN CERTIFICATE-----") || !payload.private_key.includes("-----BEGIN PRIVATE KEY-----")) {
          reject({ response: { data: { detail: "Invalid PEM data provided." } } });
        } else if (payload.private_key.includes("failkey")) {
            reject({ response: { data: { detail: "Simulated backend PFX conversion error." } } });
        }
        else {
          // Simulate a PFX file blob and Content-Disposition header
          const pfxContent = "dummy-pfx-content-for-" + Date.now();
          const blob = new Blob([pfxContent], { type: 'application/x-pkcs12' });
          
          // Simulate how Axios response might look for a blob with headers
          resolve({ 
            data: blob, 
            headers: {
              'content-disposition': 'attachment; filename="certificate_bundle_from_mock.pfx"'
            } 
          });
        }
      }, 1000);
    });
  }
};
const api = mockApi; // Use the mock

const pemCertChain = ref('');
const privateKey = ref('');
const isLoading = ref(false);
const errorMessage = ref('');
const successMessage = ref(''); // Added for success feedback

async function handleConvertToPfx() {
  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';


  if (!pemCertChain.value.trim() || !privateKey.value.trim()) {
    errorMessage.value = "Both PEM Certificate(s) and Private Key fields are required.";
    isLoading.value = false;
    return;
  }
  if (!pemCertChain.value.includes("-----BEGIN CERTIFICATE-----") || !pemCertChain.value.includes("-----END CERTIFICATE-----")) {
    errorMessage.value = "PEM Certificate(s) format seems invalid. It should include BEGIN/END CERTIFICATE markers.";
    isLoading.value = false;
    return;
  }
   if (!privateKey.value.includes("-----BEGIN PRIVATE KEY-----") && !privateKey.value.includes("-----BEGIN RSA PRIVATE KEY-----") && !privateKey.value.includes("-----BEGIN EC PRIVATE KEY-----") ) {
    errorMessage.value = "PEM Private Key format seems invalid. It should include BEGIN/END PRIVATE KEY markers.";
    isLoading.value = false;
    return;
  }


  const payload = {
    pem_cert_chain: pemCertChain.value,
    private_key: privateKey.value,
  };

  try {
    // Assume the API client is configured to handle blob response type for this endpoint
    const response = await api.convertToPfx(payload); 

    const blob = response.data; // data is already a Blob from the mock
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    // Try to get filename from Content-Disposition header
    let filename = "certificate.pfx"; // Default filename
    const contentDisposition = response.headers['content-disposition'];
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/i);
      if (filenameMatch && filenameMatch.length > 1) {
        filename = filenameMatch[1];
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    successMessage.value = `PFX file "${filename}" download initiated.`;
    // Clear form after successful download attempt
    pemCertChain.value = '';
    privateKey.value = '';

  } catch (error) {
    console.error("Error converting to PFX:", error);
    if (error.response && error.response.data && error.response.data.detail) {
      errorMessage.value = error.response.data.detail;
    } else {
      errorMessage.value = 'PFX conversion failed. Please check your PEM data and try again.';
    }
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.pem-to-pfx-container {
  max-width: 900px;
  margin: 2rem auto;
  padding: 2.5rem; /* Increased padding */
  border-radius: 8px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1); /* Enhanced shadow */
  background-color: #fff;
}

.card { /* Re-using card style from CAManagement for consistency */
  background-color: #fff;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 2rem;
}


h2 {
  text-align: center;
  color: #007bff; /* Primary color */
  margin-bottom: 1.5rem;
}

.instructions {
  font-size: 1rem;
  color: #555;
  margin-bottom: 1rem;
  line-height: 1.6;
}

.security-note {
  font-size: 0.9rem;
  color: #777;
  margin-bottom: 2rem;
  border-left: 3px solid #ffc107; /* Amber color for emphasis */
  padding-left: 1rem;
  background-color: #fff9e6;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 500;
  color: #333;
  margin-bottom: 0.5rem;
}

.form-group textarea {
  width: 100%;
  padding: 0.85rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 0.95rem;
  font-family: 'Courier New', Courier, monospace; /* Monospaced font for PEM data */
  line-height: 1.5;
}
.form-group textarea:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
}


.button-convert {
  display: block;
  width: 100%;
  padding: 0.8rem 1.5rem;
  background-color: #28a745; /* Green color for convert */
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 1rem;
}
.button-convert:hover {
  background-color: #218838;
}
.button-convert:disabled {
  background-color: #89d8a2; /* Lighter green for disabled */
  cursor: not-allowed;
}

.error-message {
  color: #d9534f;
  background-color: #f2dede;
  border: 1px solid #ebccd1;
  padding: 0.85rem;
  border-radius: 4px;
  margin-top: 1.5rem;
  text-align: center;
}
.success-message {
  color: #5cb85c; 
  background-color: #dff0d8;
  border: 1px solid #d6e9c6;
  padding: 0.85rem;
  border-radius: 4px;
  margin-top: 1.5rem;
  text-align: center;
}
</style>
