example_claim = {
  "claimId": "DHC20240509001",
  "patientDetails": {
    "name": "Ranjit Sharma",
    "policyNumber": "HSI123456789",
    "dateOfBirth": "1985-06-15",
    "gender": "Male",
    "maritalStatus": "Married",
    "spouseName": "Anita Sharma",
    "contactNumber": "+91-9876543210",
    "email": "ranjit.sharma@example.com",
    "address": {
      "street": "15, MG Road",
      "city": "Bengaluru",
      "state": "Karnataka",
      "postalCode": "560001",
      "country": "India"
    }
  },
  "claimDetails": {
    "diagnosisCode": "A90",
    "diagnosisDescription": "Dengue fever [classical dengue]",
    "dateOfDiagnosis": "2024-05-01",
    "hospitalName": "Apollo Hospital, Bengaluru",
    "admissionDate": "2024-05-02",
    "dischargeDate": "2024-05-07",
    "totalBillAmount": 250000.00,
    "claimAmount": 225000.00,
    "claimDate": "2024-05-09"
  },
  "claimStatus": {
    "status": "REJECTED",
    "rejectionDate": "2024-05-15",
    "rejectionReasons": [
      "Pre-existing condition not disclosed",
      "Waiting period for vector-borne diseases not completed"
    ],
    "appealDeadline": "2024-06-14"
  },
  "insuranceCompany": {
    "name": "SBI Health Insurance",
    "contactNumber": "+91-1800-22-1111",
    "email": "customer.care@sbigeneral.in",
    "address": "Corporate Office, Fulcrum Building, 9th Floor, A & B Wing, Sahar Road, Andheri (East), Mumbai - 400099"
  },
  "policyDetails": {
    "policyProvider": "SBI Health Insurance",
    "policyPath": "docs/united india health insurance.pdf",
    "policyStartDate": "2020-01-01",
    "policyEndDate": "2025-01-01",
    "coverageAmount": 500000,
    "premiumAmount": 12000,
    "premiumFrequency": "Yearly"
  }
}


import claim_resolution
state_dict = {
    "type": "health",
    "claim_json":   example_claim 
}

print(claim_resolution.generate_resolution(state_dict))