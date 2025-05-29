<template>
  <div class="request-management-container">
    <h2>Certificate Request Management</h2>

    <div class="filter-controls">
      <label for="statusFilter">Filter by Status:</label>
      <select id="statusFilter" v-model="selectedFilter">
        <option value="All">All</option>
        <option value="pending">Pending</option>
        <option value="issued">Issued</option>
        <option value="rejected">Rejected</option>
        <option value="failed">Failed</option>
        <option value="approved">Approved (Awaiting Issuance)</option> 
      </select>
    </div>

    <div v-if="isLoading" class="loading-indicator">Loading requests...</div>
    <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
    
    <div v-if="!isLoading && filteredRequests.length === 0 && !errorMessage" class="no-requests-message">
      No certificate requests match the current filter, or no requests have been made.
    </div>

    <table v-if="!isLoading && filteredRequests.length > 0">
      <thead>
        <tr>
          <th>Request ID</th>
          <th>User ID</th>
          <th>Common Name</th>
          <th>Requested On</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="request in filteredRequests" :key="request.id">
          <td>{{ request.id }}</td>
          <td>{{ request.user_id }}</td>
          <td>{{ request.common_name }}</td>
          <td>{{ formatDate(request.created_at) }}</td>
          <td>
            <span :class="['status-badge', `status-${request.status.toLowerCase()}`]">
              {{ request.status }}
            </span>
          </td>
          <td>
            <button 
              v-if="request.status === 'pending'" 
              @click="handleApprove(request.id)"
              class="button-approve"
              :disabled="isProcessingAction === request.id"
            >
              {{ isProcessingAction === request.id && currentAction === 'approve' ? 'Approving...' : 'Approve' }}
            </button>
            <button 
              v-if="request.status === 'pending'" 
              @click="openRejectModal(request)"
              class="button-reject"
              :disabled="isProcessingAction === request.id"
            >
              {{ isProcessingAction === request.id && currentAction === 'reject' ? 'Rejecting...' : 'Reject' }}
            </button>
            <span v-if="request.status !== 'pending'">No actions available</span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Rejection Modal -->
    <div v-if="showRejectionModal" class="modal-overlay">
      <div class="modal-content">
        <h3>Reject Certificate Request</h3>
        <p><strong>Request ID:</strong> {{ currentRequestForAction?.id }}</p>
        <p><strong>Common Name:</strong> {{ currentRequestForAction?.common_name }}</p>
        <textarea 
          v-model="rejectionReason" 
          placeholder="Enter rejection reason (required)"
          rows="4"
        ></textarea>
        <div class="modal-actions">
          <button @click="handleRejectSubmit" :disabled="!rejectionReason.trim() || isProcessingAction === currentRequestForAction?.id" class="button-reject">
            {{ isProcessingAction === currentRequestForAction?.id && currentAction === 'rejectSubmit' ? 'Submitting...' : 'Confirm Rejection' }}
          </button>
          <button @click="closeRejectionModal" class="button-cancel">Cancel</button>
        </div>
        <div v-if="modalErrorMessage" class="error-message modal-error">{{ modalErrorMessage }}</div>
      </div>
    </div>
     <div v-if="actionSuccessMessage" class="success-message">{{ actionSuccessMessage }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';

// Mock API (replace with actual API client)
const mockApi = {
  adminListAllCertificateRequests: async (statusFilter = null) => {
    console.log("Mock API: adminListAllCertificateRequests called with filter:", statusFilter);
    return new Promise(resolve => {
      setTimeout(() => {
        const allRequests = [
          { id: 101, user_id: 1, common_name: "user1.example.com", created_at: new Date(Date.now() - 86400000 * 2).toISOString(), status: "pending", public_key_pem: "pkey1", requested_days: 30, sans: ["dns:user1.example.com"], ekus: ["1.3.6.1.5.5.7.3.1"] },
          { id: 102, user_id: 2, common_name: "user2.example.org", created_at: new Date(Date.now() - 86400000).toISOString(), status: "issued", approved_at: new Date().toISOString(), public_key_pem: "pkey2", requested_days: 90, sans: [], ekus: [] },
          { id: 103, user_id: 1, common_name: "user1.internal.net", created_at: new Date().toISOString(), status: "pending", public_key_pem: "pkey3", requested_days: 365, sans: [], ekus: [] },
          { id: 104, user_id: 3, common_name: "another.test.com", created_at: new Date(Date.now() - 86400000 * 3).toISOString(), status: "rejected", rejection_reason: "Domain not allowed.", public_key_pem: "pkey4", requested_days: 60, sans: [], ekus: [] },
          { id: 105, user_id: 2, common_name: "failed-gen.example.com", created_at: new Date(Date.now() - 86400000 * 4).toISOString(), status: "failed", rejection_reason:"CA system unavailable", public_key_pem: "pkey5", requested_days: 30, sans: [], ekus: [] },
        ];
        if (statusFilter && statusFilter !== "All") {
          resolve({ data: allRequests.filter(req => req.status === statusFilter) });
        } else {
          resolve({ data: allRequests });
        }
      }, 500);
    });
  },
  adminActOnCertificateRequest: async (requestId, payload) => {
    console.log(`Mock API: adminActOnCertificateRequest called for ID ${requestId} with payload:`, payload);
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const existingRequest = allRequestsStore.find(r => r.id === requestId); // Simulate finding the request
        if (!existingRequest) {
            return reject({ response: { data: { detail: "Request not found."}}});
        }
        if (payload.status === "approved") {
          // Simulate successful approval -> issued state
          const updatedRequest = { ...existingRequest, status: "issued", approved_at: new Date().toISOString(), rejection_reason: null };
          // Simulate issued cert details
          const issued_certificate_details = { certificate_pem: "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----", pfx_available: false, message: "Certificate issued successfully."};
          allRequestsStore = allRequestsStore.map(r => r.id === requestId ? updatedRequest : r);
          resolve({ data: { request_status: updatedRequest, issued_certificate_details } });
        } else if (payload.status === "rejected") {
          if (!payload.rejection_reason) return reject({ response: { data: { detail: "Rejection reason required."}}})
          const updatedRequest = { ...existingRequest, status: "rejected", rejection_reason: payload.rejection_reason, approved_at: null };
          allRequestsStore = allRequestsStore.map(r => r.id === requestId ? updatedRequest : r);
          resolve({ data: { request_status: updatedRequest, issued_certificate_details: null } });
        } else {
          reject(new Error("Mock API: Invalid action status."));
        }
      }, 500);
    });
  }
};
// Helper to simulate a persistent store for the mock API
let allRequestsStore = [
    { id: 101, user_id: 1, common_name: "user1.example.com", created_at: new Date(Date.now() - 86400000 * 2).toISOString(), status: "pending", public_key_pem: "pkey1", requested_days: 30, sans: ["dns:user1.example.com"], ekus: ["1.3.6.1.5.5.7.3.1"], rejection_reason: null, approved_at: null },
    { id: 102, user_id: 2, common_name: "user2.example.org", created_at: new Date(Date.now() - 86400000).toISOString(), status: "issued", approved_at: new Date().toISOString(), public_key_pem: "pkey2", requested_days: 90, sans: [], ekus: [], rejection_reason: null },
    { id: 103, user_id: 1, common_name: "user1.internal.net", created_at: new Date().toISOString(), status: "pending", public_key_pem: "pkey3", requested_days: 365, sans: [], ekus: [], rejection_reason: null, approved_at: null },
    { id: 104, user_id: 3, common_name: "another.test.com", created_at: new Date(Date.now() - 86400000 * 3).toISOString(), status: "rejected", rejection_reason: "Domain not allowed.", public_key_pem: "pkey4", requested_days: 60, sans: [], ekus: [], approved_at: null },
    { id: 105, user_id: 2, common_name: "failed-gen.example.com", created_at: new Date(Date.now() - 86400000 * 4).toISOString(), status: "failed", rejection_reason:"CA system unavailable", public_key_pem: "pkey5", requested_days: 30, sans: [], ekus: [], approved_at: null },
];

const api = mockApi; // Use the mock

const requests = ref([]);
const isLoading = ref(false);
const errorMessage = ref('');
const selectedFilter = ref('All'); // Default filter

const showRejectionModal = ref(false);
const currentRequestForAction = ref(null);
const rejectionReason = ref('');
const modalErrorMessage = ref('');
const isProcessingAction = ref(null); // Stores ID of request being processed
const currentAction = ref(''); // 'approve', 'rejectSubmit'
const actionSuccessMessage = ref('');


const filteredRequests = computed(() => {
  if (selectedFilter.value === 'All') {
    return requests.value;
  }
  return requests.value.filter(req => req.status === selectedFilter.value);
});

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

async function fetchRequests() {
  isLoading.value = true;
  errorMessage.value = '';
  actionSuccessMessage.value = ''; // Clear previous action messages
  try {
    // If backend supports filtering by status for admin, pass selectedFilter.value
    // For now, mock fetches all and then client-side filter applies via computed prop.
    const response = await api.adminListAllCertificateRequests(); 
    requests.value = response.data;
  } catch (error) {
    console.error("Failed to fetch certificate requests:", error);
    errorMessage.value = "Failed to load certificate requests. Please try again later.";
  } finally {
    isLoading.value = false;
  }
}

function openRejectModal(request) {
  currentRequestForAction.value = request;
  rejectionReason.value = '';
  modalErrorMessage.value = '';
  actionSuccessMessage.value = '';
  showRejectionModal.value = true;
}

function closeRejectionModal() {
  showRejectionModal.value = false;
  currentRequestForAction.value = null;
  rejectionReason.value = '';
  modalErrorMessage.value = '';
}

async function handleApprove(requestId) {
  if (!confirm(`Are you sure you want to approve request ID ${requestId}?`)) return;

  isProcessingAction.value = requestId;
  currentAction.value = 'approve';
  actionSuccessMessage.value = '';
  errorMessage.value = ''; // Clear main error message

  try {
    const response = await api.adminActOnCertificateRequest(requestId, { status: RequestStatusEnum.APPROVED.value });
    actionSuccessMessage.value = `Request ID ${requestId} approved and certificate issued. Status: ${response.data.request_status.status}`;
    fetchRequests(); // Refresh the list
  } catch (error) {
    console.error(`Error approving request ${requestId}:`, error);
    errorMessage.value = `Failed to approve request ${requestId}. ${error.response?.data?.detail || error.message || ''}`;
  } finally {
    isProcessingAction.value = null;
    currentAction.value = '';
  }
}

async function handleRejectSubmit() {
  if (!currentRequestForAction.value || !rejectionReason.value.trim()) {
    modalErrorMessage.value = "Rejection reason is required.";
    return;
  }
  modalErrorMessage.value = '';
  actionSuccessMessage.value = '';
  errorMessage.value = '';

  const requestId = currentRequestForAction.value.id;
  isProcessingAction.value = requestId;
  currentAction.value = 'rejectSubmit';

  try {
    const payload = {
      status: RequestStatusEnum.REJECTED.value,
      rejection_reason: rejectionReason.value.trim()
    };
    const response = await api.adminActOnCertificateRequest(requestId, payload);
    actionSuccessMessage.value = `Request ID ${requestId} rejected. Status: ${response.data.request_status.status}`;
    closeRejectionModal();
    fetchRequests(); // Refresh the list
  } catch (error) {
    console.error(`Error rejecting request ${requestId}:`, error);
    modalErrorMessage.value = `Failed to reject request. ${error.response?.data?.detail || error.message || ''}`;
    // Keep modal open if submission fails to allow correction or retry.
  } finally {
    isProcessingAction.value = null;
    currentAction.value = '';
  }
}

onMounted(() => {
  fetchRequests();
});

// No explicit watcher on selectedFilter needed if using computed property for display
// and backend doesn't support server-side filtering for this mock.
// If backend supported it, we would watch selectedFilter and call fetchRequests(selectedFilter.value).
</script>

<style scoped>
.request-management-container {
  max-width: 1200px;
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

.filter-controls {
  margin-bottom: 1.5rem;
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.filter-controls label {
  font-weight: 500;
}
.filter-controls select {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #ccc;
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
  vertical-align: middle;
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
.status-pending { background-color: #ffc107; color: #333; }
.status-issued { background-color: #28a745; }
.status-approved { background-color: #17a2b8; }
.status-rejected { background-color: #dc3545; }
.status-failed { background-color: #6c757d; }

.button-approve, .button-reject, .button-cancel {
  padding: 0.4rem 0.8rem;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
  margin-right: 0.5rem;
}
.button-approve { background-color: #28a745; }
.button-approve:hover { background-color: #218838; }
.button-reject { background-color: #dc3545; }
.button-reject:hover { background-color: #c82333; }
.button-cancel { background-color: #6c757d; }
.button-cancel:hover { background-color: #5a6268; }

.button-approve:disabled, .button-reject:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
  width: 90%;
  max-width: 500px;
}
.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}
.modal-content textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  margin-bottom: 1rem;
  min-height: 80px;
  box-sizing: border-box;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
.modal-error {
    margin-top: 1rem;
    text-align: left;
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
.success-message {
  color: #5cb85c; 
  background-color: #dff0d8;
  border: 1px solid #d6e9c6;
  padding: 0.75rem;
  border-radius: 4px;
  margin-top: 1rem;
  text-align: center;
}
</style>
