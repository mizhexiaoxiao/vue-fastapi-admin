<template>
  <div class="my-requests-container">
    <h2>My Certificate Requests</h2>

    <div v-if="isLoading" class="loading-indicator">Loading requests...</div>
    <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

    <div v-if="!isLoading && requests.length === 0 && !errorMessage" class="no-requests-message">
      You have not made any certificate requests yet.
    </div>

    <table v-if="!isLoading && requests.length > 0">
      <thead>
        <tr>
          <th>Common Name</th>
          <th>Requested On</th>
          <th>Status</th>
          <th>Details</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="request in requests" :key="request.id">
          <td>{{ request.common_name }}</td>
          <td>{{ formatDate(request.created_at) }}</td>
          <td>
            <span :class="['status-badge', `status-${request.status.toLowerCase()}`]">
              {{ request.status }}
            </span>
          </td>
          <td>
            <div v-if="request.status === 'rejected' && request.rejection_reason">
              <strong>Rejection Reason:</strong> {{ request.rejection_reason }}
            </div>
            <div v-if="request.approved_at">
              <strong>Approved/Issued On:</strong> {{ formatDate(request.approved_at) }}
            </div>
            <div v-if="request.status === 'issued' && request.issued_certificate_id">
                Issued Certificate ID: {{ request.issued_certificate_id }}
            </div>
          </td>
          <td>
            <button 
              v-if="request.status === 'issued' && request.issued_certificate_id" 
              @click="handleDownload(request.issued_certificate_id, request.common_name)"
              :disabled="isDownloading === request.issued_certificate_id"
              class="button-download"
            >
              {{ isDownloading === request.issued_certificate_id ? 'Downloading...' : 'Download PEM' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="downloadError" class="error-message">{{ downloadError }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

// Mock API client (replace with actual API client later)
const mockApi = {
  listMyCertificateRequests: async () => {
    console.log("Mock API: listMyCertificateRequests called");
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          data: [
            { 
              id: 1, user_id: 1, common_name: "test1.example.com", created_at: new Date().toISOString(), 
              status: "pending", rejection_reason: null, approved_at: null, 
              public_key_pem: "pkey1", requested_days: 30, sans: [], ekus: [] 
            },
            { 
              id: 2, user_id: 1, common_name: "test2.example.com", created_at: new Date(Date.now() - 86400000).toISOString(), 
              status: "issued", rejection_reason: null, approved_at: new Date().toISOString(), 
              public_key_pem: "pkey2", requested_days: 90, sans: [], ekus: [],
              issued_certificate_id: 101 // Assumed field for download
            },
            { 
              id: 3, user_id: 1, common_name: "test3.example.com", created_at: new Date(Date.now() - 172800000).toISOString(), 
              status: "rejected", rejection_reason: "Policy violation.", approved_at: null, 
              public_key_pem: "pkey3", requested_days: 365, sans: [], ekus: [] 
            },
             { 
              id: 4, user_id: 1, common_name: "test4-no-issued-id.example.com", created_at: new Date(Date.now() - 86400000).toISOString(), 
              status: "issued", rejection_reason: null, approved_at: new Date().toISOString(), 
              public_key_pem: "pkey4", requested_days: 90, sans: [], ekus: [],
              issued_certificate_id: null // Test case: status is issued but no ID
            },
          ]
        });
      }, 500);
    });
  },
  downloadIssuedCertificateFile: async (issuedCertificateId) => {
    console.log(`Mock API: downloadIssuedCertificateFile called for ID ${issuedCertificateId}`);
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (issuedCertificateId === 101) {
          const pemContent = `-----BEGIN CERTIFICATE-----\nMIID... (Certificate for ID ${issuedCertificateId})\n-----END CERTIFICATE-----`;
          const blob = new Blob([pemContent], { type: 'application/x-pem-file' });
          resolve({ data: blob, headers: {'content-type': 'application/x-pem-file'} }); // Simulate FastAPI FileResponse structure
        } else {
          reject(new Error(`Certificate with ID ${issuedCertificateId} not found.`));
        }
      }, 500);
    });
  }
};
const api = mockApi; // Use the mock

const requests = ref([]);
const isLoading = ref(false);
const errorMessage = ref('');
const isDownloading = ref(null); // Stores the ID of the cert being downloaded
const downloadError = ref('');

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

async function fetchRequests() {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const response = await api.listMyCertificateRequests(); // Replace with actual API call
    // Assuming the backend returns CertificateRequestRead which now includes `issued_certificate_id`
    requests.value = response.data.map(req => ({
        ...req,
        // This mapping is based on the assumption that the backend list endpoint for
        // certificate requests will provide `issued_certificate_id` if status is 'issued'.
        // If not, this field would be undefined or handled differently.
        issued_certificate_id: req.status === 'issued' ? req.issued_certificate_id : null 
    }));
  } catch (error) {
    console.error("Failed to fetch certificate requests:", error);
    errorMessage.value = "Failed to load certificate requests. Please try again later.";
  } finally {
    isLoading.value = false;
  }
}

async function handleDownload(issuedCertificateId, commonName) {
  if (!issuedCertificateId) {
    downloadError.value = "Download failed: Issued certificate ID is missing.";
    return;
  }
  isDownloading.value = issuedCertificateId;
  downloadError.value = '';
  try {
    // The API client function should be responsible for setting responseType: 'blob'
    const response = await api.downloadIssuedCertificateFile(issuedCertificateId);

    const blob = response.data; // Assuming response.data is already a Blob
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    const safeCommonName = commonName.replace(/[^a-z0-9_.-]/gi, '_') || 'certificate';
    link.setAttribute('download', `${safeCommonName}_${issuedCertificateId}.pem`);
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

  } catch (error) {
    console.error(`Failed to download certificate ${issuedCertificateId}:`, error);
    downloadError.value = `Failed to download certificate. ${error.message || ''}`;
  } finally {
    isDownloading.value = null;
  }
}

onMounted(() => {
  fetchRequests();
});
</script>

<style scoped>
.my-requests-container {
  max-width: 1000px;
  margin: 2rem auto;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background-color: #fff;
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 1.5rem;
}

.loading-indicator, .no-requests-message {
  text-align: center;
  padding: 1rem;
  color: #555;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

th, td {
  border: 1px solid #e0e0e0;
  padding: 0.75rem 1rem;
  text-align: left;
  vertical-align: top;
}

th {
  background-color: #f9f9f9;
  font-weight: 600;
  color: #333;
}

tr:nth-child(even) {
  background-color: #fcfcfc;
}

.status-badge {
  padding: 0.25em 0.6em;
  font-size: 0.85em;
  font-weight: 600;
  border-radius: 0.25rem;
  color: #fff;
  text-transform: capitalize;
}
.status-pending { background-color: #ffc107; color: #333; } /* Amber */
.status-issued { background-color: #28a745; } /* Green */
.status-approved { background-color: #17a2b8; } /* Teal - for approved but not yet issued if that's a state */
.status-rejected { background-color: #dc3545; } /* Red */
.status-failed { background-color: #6c757d; } /* Grey */

.button-download {
  padding: 0.4rem 0.8rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}
.button-download:hover {
  background-color: #0056b3;
}
.button-download:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.error-message {
  color: #d9534f;
  background-color: #f2dede;
  border: 1px solid #ebccd1;
  padding: 0.75rem;
  border-radius: 4px;
  margin-top: 1rem;
  text-align: center;
}
</style>
