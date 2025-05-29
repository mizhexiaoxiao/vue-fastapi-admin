<template>
  <div class="ca-management-container">
    <h2>Certificate Authority Management</h2>

    <!-- Create/Upload CA Form -->
    <div class="form-section card">
      <h3>Add New Certificate Authority</h3>
      <form @submit.prevent="handleAddCA">
        <div class="form-group">
          <label for="caName">CA Name:</label>
          <input type="text" id="caName" v-model="newCA.name" required />
        </div>
        <div class="form-group">
          <label for="caDescription">Description (Optional):</label>
          <textarea id="caDescription" v-model="newCA.description" rows="3"></textarea>
        </div>
        <div class="form-group">
          <label for="caPemData">PEM Data (CA Certificate, include chain if any):</label>
          <textarea id="caPemData" v-model="newCA.pem_data" rows="10" required placeholder="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"></textarea>
        </div>
        <div class="form-group checkbox-group">
          <input type="checkbox" id="isActiveRoot" v-model="newCA.is_active_root" />
          <label for="isActiveRoot">Set as Active Root CA for signing new certificates</label>
        </div>
        <div v-if="formErrorMessage" class="error-message">{{ formErrorMessage }}</div>
        <button type="submit" :disabled="isSubmitting" class="button-primary">
          {{ isSubmitting ? 'Adding CA...' : 'Add CA' }}
        </button>
      </form>
    </div>

    <!-- List of Existing CAs -->
    <div class="list-section card">
      <h3>Existing Certificate Authorities</h3>
      <div v-if="isLoading" class="loading-indicator">Loading CAs...</div>
      <div v-if="listErrorMessage" class="error-message">{{ listErrorMessage }}</div>
      <div v-if="!isLoading && cas.length === 0 && !listErrorMessage" class="no-data-message">
        No Certificate Authorities found.
      </div>
      <table v-if="!isLoading && cas.length > 0">
        <thead>
          <tr>
            <th>Name</th>
            <th>Description</th>
            <th>Expires At</th>
            <th>Active Root</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ca in cas" :key="ca.id">
            <td>{{ ca.name }}</td>
            <td>{{ ca.description || 'N/A' }}</td>
            <td>{{ formatDate(ca.expires_at) }}</td>
            <td>
              <span :class="['status-badge', ca.is_active_root ? 'status-active' : 'status-inactive']">
                {{ ca.is_active_root ? 'Yes' : 'No' }}
              </span>
            </td>
            <td>
              <button @click="handleViewDetails(ca)" class="button-secondary">View Details</button>
              <button 
                @click="handleSetActive(ca)" 
                :disabled="ca.is_active_root || isProcessingAction === ca.id"
                v-if="!ca.is_active_root"
                class="button-set-active"
              >
                {{ isProcessingAction === ca.id ? 'Setting Active...' : 'Set Active Root' }}
              </button>
               <button 
                @click="handleDeactivate(ca)" 
                :disabled="isProcessingAction === ca.id"
                v-if="ca.is_active_root"
                class="button-deactivate"
              >
                {{ isProcessingAction === ca.id ? 'Deactivating...' : 'Deactivate Root' }}
              </button>
              <!-- Delete button can be added here later -->
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Details Modal -->
    <div v-if="showDetailsModal && selectedCAForDetails" class="modal-overlay">
      <div class="modal-content">
        <h3>CA Details: {{ selectedCAForDetails.name }}</h3>
        <div class="detail-item"><strong>ID:</strong> {{ selectedCAForDetails.id }}</div>
        <div class="detail-item"><strong>Description:</strong> {{ selectedCAForDetails.description || 'N/A' }}</div>
        <div class="detail-item"><strong>Active Root:</strong> {{ selectedCAForDetails.is_active_root ? 'Yes' : 'No' }}</div>
        <div class="detail-item"><strong>Expires At:</strong> {{ formatDate(selectedCAForDetails.expires_at) }}</div>
        <div class="detail-item"><strong>Created At:</strong> {{ formatDate(selectedCAForDetails.created_at) }}</div>
        <div class="detail-item"><strong>Updated At:</strong> {{ formatDate(selectedCAForDetails.updated_at) }}</div>
        <h4>PEM Data:</h4>
        <pre class="pem-data-display">{{ selectedCAForDetails.pem_data }}</pre>
        <div class="modal-actions">
          <button @click="showDetailsModal = false" class="button-primary">Close</button>
        </div>
      </div>
    </div>
    <div v-if="actionSuccessMessage" class="success-message">{{ actionSuccessMessage }}</div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';

// Mock API (replace with actual API client)
const mockApi = {
  listCAs: async () => {
    console.log("Mock API: listCAs called");
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({ data: caStore });
      }, 300);
    });
  },
  createCA: async (payload) => {
    console.log("Mock API: createCA called with:", payload);
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (!payload.name || !payload.pem_data) {
          return reject({ response: { data: { detail: "Name and PEM data are required." } } });
        }
        if (caStore.some(ca => ca.name === payload.name)) {
          return reject({ response: { data: { detail: "CA with this name already exists." } } });
        }
        if (payload.is_active_root) {
            caStore.forEach(ca => ca.is_active_root = false);
        }
        const newCAEntry = {
          id: Date.now(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          expires_at: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // Mock expiry
          ...payload
        };
        caStore.push(newCAEntry);
        resolve({ data: newCAEntry });
      }, 500);
    });
  },
  updateCA: async (caId, payload) => {
    console.log(`Mock API: updateCA called for ID ${caId} with:`, payload);
     return new Promise((resolve, reject) => {
      setTimeout(() => {
        const caIndex = caStore.findIndex(ca => ca.id === caId);
        if (caIndex === -1) {
          return reject({ response: { data: { detail: "CA not found." } } });
        }
        if (payload.is_active_root) {
            caStore.forEach(ca => ca.is_active_root = (ca.id === caId));
        }
        caStore[caIndex] = { ...caStore[caIndex], ...payload, updated_at: new Date().toISOString() };
        resolve({ data: caStore[caIndex] });
      }, 300);
    });
  }
};
let caStore = [ // Simulating a backend store
  { id: 1, name: "Org Root CA Alpha", description: "Primary Root CA", pem_data: "-----BEGIN CERTIFICATE-----\n(Alpha Root CA PEM)\n-----END CERTIFICATE-----", is_active_root: true, expires_at: new Date(Date.now() + 365*5*24*60*60*1000).toISOString(), created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: 2, name: "Backup CA Beta", description: "Backup CA, not active", pem_data: "-----BEGIN CERTIFICATE-----\n(Beta CA PEM)\n-----END CERTIFICATE-----", is_active_root: false, expires_at: new Date(Date.now() + 365*3*24*60*60*1000).toISOString(), created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
];
const api = mockApi; // Use the mock

const cas = ref([]);
const newCA = reactive({
  name: '',
  description: '',
  pem_data: '',
  is_active_root: false,
});

const isLoading = ref(false);
const isSubmitting = ref(false);
const isProcessingAction = ref(null); // Stores ID of CA being actioned upon

const listErrorMessage = ref('');
const formErrorMessage = ref('');
const actionSuccessMessage = ref('');


const showDetailsModal = ref(false);
const selectedCAForDetails = ref(null);

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

async function fetchCAs() {
  isLoading.value = true;
  listErrorMessage.value = '';
  actionSuccessMessage.value = '';
  try {
    const response = await api.listCAs();
    cas.value = response.data;
  } catch (error) {
    console.error("Failed to fetch CAs:", error);
    listErrorMessage.value = "Failed to load CAs. Please try again later.";
  } finally {
    isLoading.value = false;
  }
}

async function handleAddCA() {
  formErrorMessage.value = '';
  actionSuccessMessage.value = '';
  if (!newCA.name.trim() || !newCA.pem_data.trim()) {
    formErrorMessage.value = "CA Name and PEM Data are required.";
    return;
  }
  if (!newCA.pem_data.includes("-----BEGIN CERTIFICATE-----") || !newCA.pem_data.includes("-----END CERTIFICATE-----")) {
    formErrorMessage.value = "PEM Data format seems invalid. It should include BEGIN/END CERTIFICATE markers.";
    return;
  }

  isSubmitting.value = true;
  try {
    await api.createCA({ ...newCA });
    actionSuccessMessage.value = `CA "${newCA.name}" added successfully.`;
    // Reset form
    newCA.name = '';
    newCA.description = '';
    newCA.pem_data = '';
    newCA.is_active_root = false;
    await fetchCAs(); // Refresh the list
  } catch (error) {
    console.error("Error adding CA:", error);
    formErrorMessage.value = error.response?.data?.detail || "An unexpected error occurred while adding the CA.";
  } finally {
    isSubmitting.value = false;
  }
}

function handleViewDetails(ca) {
  selectedCAForDetails.value = ca;
  showDetailsModal.value = true;
}

async function handleSetActive(caToActivate) {
  if (!confirm(`Are you sure you want to set "${caToActivate.name}" as the active root CA? This will deactivate any other currently active root CA.`)) return;
  
  isProcessingAction.value = caToActivate.id;
  actionSuccessMessage.value = '';
  listErrorMessage.value = '';

  try {
    // The backend PUT should handle deactivating other CAs if this one is set to active.
    // We send the full state of the CA object we want to achieve.
    const payload = { 
        name: caToActivate.name, // name and description are not changing here
        description: caToActivate.description,
        pem_data: caToActivate.pem_data,
        is_active_root: true 
    };
    await api.updateCA(caToActivate.id, payload);
    actionSuccessMessage.value = `CA "${caToActivate.name}" is now the active root CA.`;
    await fetchCAs(); // Refresh the list to reflect changes
  } catch (error) {
    console.error(`Error setting CA ${caToActivate.id} active:`, error);
    listErrorMessage.value = `Failed to set CA active. ${error.response?.data?.detail || error.message || ''}`;
  } finally {
    isProcessingAction.value = null;
  }
}

async function handleDeactivate(caToDeactivate) {
   if (!confirm(`Are you sure you want to deactivate "${caToDeactivate.name}" as the active root CA? You may need to set another CA as active if one is required.`)) return;

  isProcessingAction.value = caToDeactivate.id;
  actionSuccessMessage.value = '';
  listErrorMessage.value = '';
  try {
    const payload = { 
        name: caToDeactivate.name,
        description: caToDeactivate.description,
        pem_data: caToDeactivate.pem_data,
        is_active_root: false 
    };
    await api.updateCA(caToDeactivate.id, payload);
    actionSuccessMessage.value = `CA "${caToDeactivate.name}" is no longer the active root CA.`;
    await fetchCAs();
  } catch (error) {
    console.error(`Error deactivating CA ${caToDeactivate.id}:`, error);
    listErrorMessage.value = `Failed to deactivate CA. ${error.response?.data?.detail || error.message || ''}`;
  } finally {
    isProcessingAction.value = null;
  }
}


onMounted(() => {
  fetchCAs();
});
</script>

<style scoped>
.ca-management-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 2rem;
  background-color: #f9f9f9; /* Light grey background for the whole page */
  border-radius: 8px;
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 2rem;
}

.card {
  background-color: #fff;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 2rem;
}

.card h3 {
  margin-top: 0;
  color: #007bff; /* Primary color for section titles */
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #eef;
  padding-bottom: 0.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.form-group label {
  font-weight: 500;
  color: #444;
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 1rem;
}
.form-group textarea {
  min-height: 80px;
  resize: vertical;
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}
.checkbox-group input[type="checkbox"] {
  width: auto;
  margin-right: 0.25rem;
}

.button-primary, .button-secondary, .button-set-active, .button-deactivate {
  padding: 0.7rem 1.2rem;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s, opacity 0.2s;
  margin-right: 0.5rem; /* For spacing between buttons */
}
.button-primary { background-color: #007bff; }
.button-primary:hover { background-color: #0056b3; }
.button-primary:disabled { background-color: #a0cfff; cursor: not-allowed; }

.button-secondary { background-color: #6c757d; }
.button-secondary:hover { background-color: #545b62; }

.button-set-active { background-color: #28a745; }
.button-set-active:hover { background-color: #1e7e34; }
.button-set-active:disabled { background-color: #89d8a2; opacity: 0.7; cursor: not-allowed; }

.button-deactivate { background-color: #ffc107; color: #212529; }
.button-deactivate:hover { background-color: #e0a800; }
.button-deactivate:disabled { background-color: #ffe083; opacity: 0.7; cursor: not-allowed; }


.loading-indicator, .no-data-message {
  text-align: center;
  padding: 1.5rem;
  color: #555;
  font-style: italic;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1.5rem;
}

th, td {
  border: 1px solid #e0e0e0;
  padding: 0.85rem 1.1rem;
  text-align: left;
  vertical-align: middle;
}

th {
  background-color: #f0f4f7; /* Lighter blueish header */
  font-weight: 600;
  color: #333;
}

tr:nth-child(even) {
  background-color: #f8f9fa;
}

.status-badge {
  padding: 0.3em 0.7em;
  font-size: 0.8rem;
  font-weight: 600;
  border-radius: 10px; /* More rounded badge */
  color: #fff;
  text-transform: capitalize;
  display: inline-block;
}
.status-active { background-color: #28a745; } /* Green for Yes */
.status-inactive { background-color: #6c757d; } /* Grey for No */


/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background-color: white;
  padding: 2.5rem;
  border-radius: 8px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
  width: 90%;
  max-width: 700px; /* Wider modal for PEM data */
}
.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #007bff;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}
.detail-item {
  margin-bottom: 0.75rem;
  font-size: 0.95rem;
}
.detail-item strong {
  color: #333;
}
pre.pem-data-display {
  background-color: #f8f9fa;
  border: 1px solid #e0e0e0;
  padding: 1rem;
  border-radius: 4px;
  white-space: pre-wrap;       /* Since CSS2.1 */
  white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
  white-space: -pre-wrap;      /* Opera 4-6 */
  white-space: -o-pre-wrap;    /* Opera 7 */
  word-wrap: break-word;       /* Internet Explorer 5.5+ */
  max-height: 300px;
  overflow-y: auto;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85rem;
}

.error-message, .success-message {
  padding: 0.85rem 1.25rem;
  border-radius: 4px;
  margin-top: 1rem;
  text-align: center;
  font-size: 0.95rem;
}
.error-message {
  color: #d9534f;
  background-color: #f2dede;
  border: 1px solid #ebccd1;
}
.success-message {
  color: #5cb85c; 
  background-color: #dff0d8;
  border: 1px solid #d6e9c6;
}
</style>
