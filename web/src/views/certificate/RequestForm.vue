<template>
  <div class="request-form-container">
    <h2>New Certificate Request</h2>
    <form @submit.prevent="handleSubmit">
      <!-- Common Name -->
      <div class="form-group">
        <label for="commonName">Common Name (CN):</label>
        <input type="text" id="commonName" v-model="formData.commonName" required />
      </div>

      <!-- Distinguished Name -->
      <fieldset>
        <legend>Distinguished Name (Optional)</legend>
        <div class="form-group">
          <label for="organization">Organization (O):</label>
          <input type="text" id="organization" v-model="formData.dn.organization" />
        </div>
        <div class="form-group">
          <label for="organizationalUnit">Organizational Unit (OU):</label>
          <input type="text" id="organizationalUnit" v-model="formData.dn.organizationalUnit" />
        </div>
        <div class="form-group">
          <label for="locality">Locality (L):</label>
          <input type="text" id="locality" v-model="formData.dn.locality" />
        </div>
        <div class="form-group">
          <label for="stateProvince">State/Province (ST):</label>
          <input type="text" id="stateProvince" v-model="formData.dn.stateProvince" />
        </div>
        <div class="form-group">
          <label for="country">Country (C):</label>
          <input type="text" id="country" v-model="formData.dn.country" />
        </div>
      </fieldset>

      <!-- Subject Alternative Names (SANs) -->
      <fieldset>
        <legend>Subject Alternative Names (SANs)</legend>
        <div v-for="(san, index) in formData.sans" :key="index" class="san-entry">
          <select v-model="san.type">
            <option value="DNS">DNS</option>
            <option value="IP">IP Address</option>
          </select>
          <input type="text" v-model="san.value" placeholder="e.g., example.com or 192.168.1.1" />
          <button type="button" @click="removeSanEntry(index)" v-if="formData.sans.length > 1">Remove</button>
        </div>
        <button type="button" @click="addSanEntry">Add SAN Entry</button>
      </fieldset>

      <!-- Enhanced Key Usages (EKUs) -->
      <fieldset>
        <legend>Enhanced Key Usages (EKUs)</legend>
        <div v-for="ekuKey in Object.keys(commonEKUs)" :key="ekuKey" class="checkbox-group">
          <input type="checkbox" :id="ekuKey" :value="ekuKey" v-model="formData.selectedEKUs" />
          <label :for="ekuKey">{{ commonEKUs[ekuKey].friendlyName }} ({{ commonEKUs[ekuKey].oid }})</label>
        </div>
        <div class="form-group">
          <label for="customEKUs">Custom EKUs (comma-separated OIDs):</label>
          <input type="text" id="customEKUs" v-model="formData.customEKUs" />
        </div>
      </fieldset>

      <!-- Requested Validity -->
      <div class="form-group">
        <label for="requestedDays">Requested Validity (Days):</label>
        <input type="number" id="requestedDays" v-model.number="formData.requestedDays" min="1" max="3650" />
      </div>

      <!-- Public Key PEM -->
      <div class="form-group">
        <label for="publicKeyPem">Public Key (PEM format):</label>
        <textarea id="publicKeyPem" v-model="formData.publicKeyPem" rows="10" required></textarea>
      </div>
      
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>

      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Submitting...' : 'Submit Request' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
// Assuming an API client exists, e.g., web/src/api/index.js or a dedicated module
// import api from '@/api'; // This path needs to be correct based on project structure
// For now, we'll mock it.
const mockApi = {
  submitCertificateRequest: async (payload) => {
    console.log("Mock API submitCertificateRequest called with:", payload);
    // Simulate API call
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (payload.common_name === "failtest.com") {
          reject({ response: { data: { detail: "Simulated server validation error." } } });
        } else if (!payload.public_key_pem.startsWith("-----BEGIN PUBLIC KEY-----")) {
            reject({ response: { data: { detail: "Invalid Public Key PEM format."}}});
        }
         else {
          resolve({ 
            data: { 
              id: Date.now(), 
              status: "pending", 
              ...payload 
            } 
          });
        }
      }, 1000);
    });
  }
};
const api = mockApi; // Use the mock for now

const formData = reactive({
  commonName: '',
  dn: {
    organization: '',
    organizationalUnit: '',
    locality: '',
    stateProvince: '',
    country: '',
  },
  sans: [{ type: 'DNS', value: '' }],
  selectedEKUs: [], // Will hold keys like 'serverAuth'
  customEKUs: '',
  requestedDays: 365,
  publicKeyPem: '',
});

const commonEKUs = {
  serverAuth: { friendlyName: "Server Authentication", oid: "1.3.6.1.5.5.7.3.1" },
  clientAuth: { friendlyName: "Client Authentication", oid: "1.3.6.1.5.5.7.3.2" },
  codeSigning: { friendlyName: "Code Signing", oid: "1.3.6.1.5.5.7.3.3" },
  emailProtection: { friendlyName: "Email Protection", oid: "1.3.6.1.5.5.7.3.4" },
  timeStamping: { friendlyName: "Time Stamping", oid: "1.3.6.1.5.5.7.3.8" },
  ocspSigning: { friendlyName: "OCSP Signing", oid: "1.3.6.1.5.5.7.3.9" },
};

const isSubmitting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

function addSanEntry() {
  formData.sans.push({ type: 'DNS', value: '' });
}

function removeSanEntry(index) {
  if (formData.sans.length > 1) {
    formData.sans.splice(index, 1);
  }
}

// Basic IP address validation (simplified)
function isValidIpAddress(ip) {
  if (!ip) return false;
  const parts = ip.split('.');
  if (parts.length !== 4) return false;
  return parts.every(part => {
    const num = parseInt(part, 10);
    return num >= 0 && num <= 255;
  });
}

async function handleSubmit() {
  errorMessage.value = '';
  successMessage.value = '';

  // Basic client-side validation
  if (!formData.commonName.trim()) {
    errorMessage.value = 'Common Name is required.';
    return;
  }
  if (!formData.publicKeyPem.trim()) {
    errorMessage.value = 'Public Key PEM is required.';
    return;
  }
   if (!formData.publicKeyPem.includes("-----BEGIN PUBLIC KEY-----") || !formData.publicKeyPem.includes("-----END PUBLIC KEY-----")) {
    errorMessage.value = 'Public Key PEM format seems invalid. It should include BEGIN/END PUBLIC KEY markers.';
    return;
  }


  isSubmitting.value = true;

  const distinguished_name_payload = {};
  if (formData.dn.organization) distinguished_name_payload.O = formData.dn.organization;
  if (formData.dn.organizationalUnit) distinguished_name_payload.OU = formData.dn.organizationalUnit;
  if (formData.dn.locality) distinguished_name_payload.L = formData.dn.locality;
  if (formData.dn.stateProvince) distinguished_name_payload.ST = formData.dn.stateProvince;
  if (formData.dn.country) distinguished_name_payload.C = formData.dn.country;

  const sans_payload = formData.sans
    .filter(san => san.value.trim() !== '')
    .map(san => {
      if (san.type === 'IP' && !isValidIpAddress(san.value.trim())) {
        throw new Error(`Invalid IP Address format for SAN: ${san.value}`);
      }
      return `${san.type.toLowerCase()}:${san.value.trim()}`;
    });

  let ekus_payload = formData.selectedEKUs.map(ekuKey => commonEKUs[ekuKey].oid);
  if (formData.customEKUs.trim()) {
    const customOids = formData.customEKUs.split(',').map(oid => oid.trim()).filter(oid => oid);
    // Basic OID validation (very simplified)
    customOids.forEach(oid => {
      if (!/^\d+(\.\d+)+$/.test(oid)) {
        throw new Error(`Invalid custom EKU OID format: ${oid}`);
      }
    });
    ekus_payload = [...ekus_payload, ...customOids];
  }
  // Remove duplicates
  ekus_payload = [...new Set(ekus_payload)];


  const payload = {
    common_name: formData.commonName.trim(),
    distinguished_name_json: Object.keys(distinguished_name_payload).length > 0 ? distinguished_name_payload : null,
    sans: sans_payload.length > 0 ? sans_payload : null,
    ekus: ekus_payload.length > 0 ? ekus_payload : null,
    requested_days: formData.requestedDays,
    public_key_pem: formData.publicKeyPem.trim(),
  };

  try {
    const response = await api.submitCertificateRequest(payload);
    successMessage.value = `Certificate request submitted successfully! Request ID: ${response.data.id}, Status: ${response.data.status}`;
    // Reset form or redirect
    // Object.assign(formData, initialFormData); // Need to define initialFormData
    formData.commonName = '';
    formData.dn = { organization: '', organizationalUnit: '', locality: '', stateProvince: '', country: '' };
    formData.sans = [{ type: 'DNS', value: '' }];
    formData.selectedEKUs = [];
    formData.customEKUs = '';
    formData.requestedDays = 365;
    formData.publicKeyPem = '';

  } catch (error) {
    console.error("Error submitting certificate request:", error);
    if (error.response && error.response.data && error.response.data.detail) {
        if (Array.isArray(error.response.data.detail)) {
             errorMessage.value = error.response.data.detail.map(err => `${err.loc.join(' -> ')}: ${err.msg}`).join('; ');
        } else {
            errorMessage.value = error.response.data.detail;
        }
    } else {
        errorMessage.value = 'An unexpected error occurred. Please try again.';
    }
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.request-form-container {
  max-width: 800px;
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

form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

fieldset {
  border: 1px solid #e0e0e0;
  padding: 1.5rem;
  border-radius: 6px;
  background-color: #f9f9f9;
}

legend {
  font-weight: bold;
  color: #555;
  padding: 0 0.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #444;
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 1rem;
}
.form-group textarea {
  min-height: 120px;
  resize: vertical;
}

.san-entry {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.san-entry select {
  width: auto;
  flex-grow: 0;
}
.san-entry input[type="text"] {
  flex-grow: 1;
}


.checkbox-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.checkbox-group input[type="checkbox"] {
    width: auto;
}


button[type="button"] {
  padding: 0.5rem 1rem;
  background-color: #e0e0e0;
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}
button[type="button"]:hover {
  background-color: #d0d0d0;
}

button[type="submit"] {
  padding: 0.8rem 1.5rem;
  background-color: #007bff; /* Primary color */
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}
button[type="submit"]:hover {
  background-color: #0056b3;
}
button[type="submit"]:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.error-message {
  color: #d9534f; /* Bootstrap danger color */
  background-color: #f2dede;
  border: 1px solid #ebccd1;
  padding: 0.75rem;
  border-radius: 4px;
  margin-top: 1rem;
}
.success-message {
  color: #5cb85c; /* Bootstrap success color */
  background-color: #dff0d8;
  border: 1px solid #d6e9c6;
  padding: 0.75rem;
  border-radius: 4px;
  margin-top: 1rem;
}
</style>
